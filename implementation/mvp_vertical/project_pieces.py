"""Current state of an affaire's documents: the latest index of each piece.

A piece is a series of files for one drawing, model or written document (plan
MAC-DEM, maquette, CCTP...) across indices. The latest index of the agency's and
engineers' pieces describes the current state of the project; quotes and other
contractors' documents never move it, they are confronted with it.

This is a reading, not a register: nothing is stored or approved here. It is
computed from what the Workspace Cockpit already knows about each file (index
read on the title block or corrected on the document card, date, title,
fingerprint) and from the IFC models present in the affaire folder, which the
Workspace does not list. ``ARCHIVES`` folders hold superseded indices and are
skipped, as the Workspace skips them.

Index rule of the agency: A, B, C are successive indices; C1, C2 (also written
C.1) are variants of C. A file without a readable index is kept with an
uncertain position, placed by its date. Discrepancies become questions, never
resolved here: two contents under one index, several variants of the latest
index, a file without index newer than the latest indexed one.

A file marked as project reference on its document card (``reference``) is the
current file of its piece whatever its index: the human choice wins over the
index order. A newer index of the same piece then becomes a question.

The Workspace database is read-only and its layout is the Workspace's: only the
few columns named in ``read_workspace`` are relied upon.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any

WORKSPACE_DB_ENV = "MVP_WORKSPACE_STATE_DB"
AFFAIRES_ROOT_ENV = "MVP_AFFAIRES_ROOT"
WORKSPACE_NAME = "Affaires"

_INDEX = re.compile(r"^(?:IND(?:ICE)?\.?\s*)?([A-Z])(?:[.\-_ ]?([1-9][0-9]?))?$")
# Engineers often number their indices (Ind 0, IND9): admitted when written as an index.
_NUMERIC_INDEX = re.compile(r"^(?:IND(?:ICE)?\.?\s*)(\d{1,2})$")
_PHASES = {"ESQ", "APS", "APD", "AVP", "PC", "DPC", "PRO", "DCE", "ACT", "VISA", "EXE", "DET", "AOR", "DOE"}
_ADMIN = ("ATTESTATION", "CERFA", "HONORAIRES", "FACTURE", "CONTRAT", "SIGNE", "ASSURANCE")
_CONFRONT = ("DEVIS", "OFFRE")
# Only these describe the state of the project: drawings, models, written pieces of the
# design and consultation. Everything else in an affaire folder (minutes, litigation,
# photos, chats, statutes...) is counted, not followed.
_PROJECT = ("PLAN", "COUPE", "FACADE", "ELEVATION", "MASSE", "SITUATION", "DETAIL", "AXONO", "PERSPECTIVE",
            "INSERTION", "CCTP", "CCAP", "DPGF", "DQE", "BPU", "NOTICE", "CARNET", "PERMIS", "ESTIMATIF",
            "MAQUETTE", "MENUISERIE", "CHARPENTE", "STRUCTURE", "FONDATION", "RACCORD", "ELEC", "PLOMBERIE",
            "PLATRERIE", "CVC", "VENTILATION", "NOTE DE CALCUL")
_PROJECT_TOKENS = {"AE", "RC", "PC", "DP", "PLN"}
_NOISE = {"INDICE", "IND", "PDF"}
_MONTHS = {m: i for i, m in enumerate(
    ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"], 1)}

POSITION_CERTAIN = "certaine"      # index read on the title block or corrected on the card
POSITION_PROBABLE = "probable"     # index taken from the file name
POSITION_UNCERTAIN = "incertaine"  # no index: placed by date
POSITION_REFERENCE = "référence"   # chosen as project reference on the document card


def parse_index(label: Any, *, numeric: bool = False) -> tuple[str, int | None] | None:
    """'E' -> ('E', None); 'C1', 'C.1', 'Ind C-1' -> ('C', 1); 'IND9' -> ('09', None); anything else -> None.

    A bare number ('9') is an index only where the source names it as one (``numeric``):
    the index field of a card or a title block, never a token of a file name.
    """
    text = str(label or "").strip().upper()
    match = _INDEX.fullmatch(text)
    if match:
        return match.group(1), int(match.group(2)) if match.group(2) else None
    number = _NUMERIC_INDEX.fullmatch(text) or (re.fullmatch(r"(\d{1,2})", text) if numeric else None)
    return (f"{int(number.group(1)):02d}", None) if number else None


def format_index(parsed: tuple[str, int | None] | None) -> str | None:
    if parsed is None:
        return None
    if parsed[0].isdigit():  # numbered indices sort before lettered ones and print without padding
        return str(int(parsed[0]))
    return parsed[0] + (str(parsed[1]) if parsed[1] else "")


def _fold(text: str) -> str:
    table = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    return text.lower().translate(table)


def parse_date(value: Any) -> str | None:
    """ISO date from '17/08/2026', '2026-08-17', '19 mai 2026' or a 'YYMMDD' file name token."""
    text = str(value or "").strip()
    candidates = []
    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text):
        candidates.append((int(m[3]), int(m[2]), int(m[1])))
    elif m := re.match(r"(\d{4})-(\d{2})-(\d{2})", text):
        candidates.append((int(m[1]), int(m[2]), int(m[3])))
    elif m := re.fullmatch(r"(\d{1,2})\s+(\w+)\s+(\d{4})", _fold(text)):
        if m[2] in _MONTHS:
            candidates.append((int(m[3]), _MONTHS[m[2]], int(m[1])))
    elif m := re.fullmatch(r"(\d{2})(\d{2})(\d{2})", text):
        candidates.append((2000 + int(m[1]), int(m[2]), int(m[3])))
    for year, month, day in candidates:
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None
    return None


_EXTENSIONS = {".pdf", ".ifc", ".dwg", ".dxf", ".docx", ".doc", ".xlsx", ".xls", ".odt", ".ods", ".rvt"}


def _stem(filename: str) -> str:
    """File name without its extension; '15.06.23' in 'DP 15.06.23' is not one."""
    path = Path(filename)
    return path.stem if path.suffix.lower() in _EXTENSIONS else path.name


def _tokens(stem: str) -> list[str]:
    return [token for token in re.split(r"[_\s]+", stem) if token]


def filename_index(filename: str) -> tuple[str, int | None] | None:
    stem = _stem(filename).upper()
    if m := re.search(r"\bIND(?:ICE)?\.?\s*([A-Z](?:[.\-]?[1-9][0-9]?)?|\d{1,2})\b", stem):
        return parse_index(m.group(1), numeric=True)
    for token in reversed(_tokens(stem)):
        parsed = parse_index(token) if len(token) <= 4 else None
        if parsed:
            return parsed
    return None


def filename_date(filename: str) -> str | None:
    stem = _stem(filename)
    if m := re.search(r"(?<!\d)(\d{4})[.\-](\d{2})[.\-](\d{2})(?!\d)", stem):
        return parse_date(f"{m[1]}-{m[2]}-{m[3]}")
    if m := re.search(r"(?<!\d)(\d{2})[.\-](\d{2})[.\-](\d{4})(?!\d)", stem):
        return parse_date(f"{m[1]}/{m[2]}/{m[3]}")
    for token in reversed(_tokens(stem)):
        if re.fullmatch(r"\d{6}", token) and (parsed := parse_date(token)):
            return parsed
    return None


def piece_name(title: str, project_code: str) -> str:
    """'DCE_CODE_PLAN MAC-DEM.pdf' -> 'PLAN MAC-DEM'; a bare model file -> 'MAQUETTE'."""
    path = Path(title)
    stem = re.sub(r"\bIND(?:ICE)?\.?\s*(?:[A-Z](?:[.\-]?\d{1,2})?|\d{1,2})\b", " ", _stem(title).upper())
    stem = re.sub(r"\(\d+\)", " ", stem)  # copies: "plan (1).pdf"
    stem = re.sub(r"(?<!\d)\d{2,4}[.\-]\d{2}[.\-]\d{2,4}(?!\d)", " ", stem)  # dates: 2025.05.28, 20.01.2025
    code_parts = {project_code.upper(), *project_code.upper().split("-")}
    words: list[str] = []
    for token in _tokens(stem.replace(project_code.upper(), " ")):
        token = token.strip("-.&")
        if len(token) > 3 and token.endswith("PDF"):  # "DUPONTPDF"
            token = token[:-3]
        if (not token or token in _PHASES or token in _NOISE or token in code_parts or parse_index(token)
                or re.fullmatch(r"\d{4,8}", token) or token in words):
            continue
        words.append(token)
    if words:
        return " ".join(words)
    return "MAQUETTE" if path.suffix.lower() == ".ifc" else _stem(title).upper()


def category(name: str, document_type: str | None = None, title: str = "") -> str:
    """'projet' (followed), 'a_confronter' (quotes), 'administratif' or 'autre' (counted, not followed)."""
    text = _fold(f"{name} {title} {document_type or ''}").upper()
    if any(word in text for word in _ADMIN):
        return "administratif"
    if any(word in text for word in _CONFRONT):
        return "a_confronter"
    tokens = set(re.split(r"[^A-Z0-9]+", text))
    if Path(title).suffix.lower() == ".ifc" or tokens & _PROJECT_TOKENS or any(word in text for word in _PROJECT):
        return "projet"
    return "autre"


def _field(fields: dict[str, Any], key: str) -> Any:
    value = fields.get(key)
    return value.get("value") if isinstance(value, dict) else value


def read_workspace(db_path: Path, project_code: str, *, workspace: str = WORKSPACE_NAME) -> list[dict[str, Any]]:
    """Files of one affaire as the Workspace knows them; card corrections win over title-block reading."""
    prefix = project_code + "/"
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

        def rows(sql: str, required: str) -> list[sqlite3.Row]:
            return connection.execute(sql, (workspace, len(prefix), prefix)).fetchall() if required in tables else []

        entries = rows("SELECT path, payload_json FROM workspace_entries WHERE workspace=? AND kind='document' "
                       "AND substr(path,1,?)=?", "workspace_entries")
        identity = {row["source_path"]: row["source_sha256"] for row in rows(
            "SELECT source_path, source_sha256 FROM workspace_document_identity WHERE workspace=? AND substr(source_path,1,?)=?",
            "workspace_document_identity")}
        preflight = {row["source_path"]: row["result_json"] for row in rows(
            "SELECT s.source_path, p.result_json FROM hindsight_metadata_preflight_source s "
            "JOIN hindsight_metadata_preflight p ON p.cache_key = s.cache_key "
            "WHERE s.workspace=? AND substr(s.source_path,1,?)=?", "hindsight_metadata_preflight_source")}
        overrides = {row["source_path"]: row["overrides_json"] for row in rows(
            "SELECT source_path, overrides_json FROM workspace_document_metadata_overrides "
            "WHERE workspace=? AND substr(source_path,1,?)=?", "workspace_document_metadata_overrides")}
    finally:
        connection.close()

    files = []
    for entry in entries:
        path = entry["path"]
        payload = _loads(entry["payload_json"])
        read = _loads(preflight.get(path))
        fields = read.get("fields") if isinstance(read.get("fields"), dict) else {}
        corrected = _loads(overrides.get(path))
        files.append({
            "path": path[len(prefix):],
            "title": corrected.get("title") or payload.get("name") or Path(path).name,
            "index_card": corrected.get("index"),
            "index_read": payload.get("index") or _field(fields, "index"),
            "date_card": corrected.get("document_date"),
            "date_read": payload.get("document_date") or _field(fields, "document_date"),
            "date_pdf": _field(fields, "pdf_creation_date"),
            "issuer": corrected.get("issuer") or payload.get("issuer"),
            "document_type": corrected.get("document_type") or payload.get("document_type"),
            "fingerprint": identity.get(path) or payload.get("source_sha256"),
            "reference": corrected.get("reference") is True,
        })
    return files


def read_declared_sources(db_path: Path, project_code: str, *, workspace: str = WORKSPACE_NAME) -> dict[str, dict[str, Any]]:
    """Files of the affaire declared as anatomy sources on their card (any file type, IFC included)."""
    from . import anatomy_sources

    prefix = project_code + "/"
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                                  "AND name='workspace_document_metadata_overrides'").fetchone():
            return {}
        columns = {row[1] for row in connection.execute("PRAGMA table_info(workspace_document_metadata_overrides)")}
        sha = "source_sha256" if "source_sha256" in columns else "NULL"
        rows = connection.execute(
            f"SELECT source_path, overrides_json, {sha} FROM workspace_document_metadata_overrides "
            "WHERE workspace=? AND substr(source_path,1,?)=?", (workspace, len(prefix), prefix)).fetchall()
    finally:
        connection.close()
    declared = {}
    for path, overrides, digest in rows:
        entry = anatomy_sources.normalize(_loads(overrides).get("anatomy_source"))
        if entry is not None:
            if digest:
                entry["_sha256"] = digest
            declared[path[len(prefix):]] = entry
    return declared


CONSOLIDATION_REQUESTS_TABLE = "workspace_anatomy_consolidation_requests"


def read_consolidation_triggers(db_path: Path, *, workspace: str = WORKSPACE_NAME) -> dict[str, dict[str, str]]:
    """When each affaire last asked for a consolidation, as the Workspace recorded it (read-only).

    Two triggers, both written by the Workspace only: ``requested`` is the latest
    press of the project card's "Consolider les sources" button (a row of
    ``workspace_anatomy_consolidation_requests``); ``changed`` the latest change of
    a card's ``anatomy_source`` (``updated_at`` of its corrections).
    """
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    triggers: dict[str, dict[str, str]] = {}
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if CONSOLIDATION_REQUESTS_TABLE in tables:
            for code, at in connection.execute(
                    f"SELECT project_code, MAX(requested_at) FROM {CONSOLIDATION_REQUESTS_TABLE} "
                    "WHERE workspace=? GROUP BY project_code", (workspace,)):
                if code and at:
                    triggers.setdefault(str(code), {})["requested"] = str(at)
        if "workspace_document_metadata_overrides" in tables:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(workspace_document_metadata_overrides)")}
            if "updated_at" in columns:
                for path, overrides, at in connection.execute(
                        "SELECT source_path, overrides_json, updated_at FROM workspace_document_metadata_overrides "
                        "WHERE workspace=?", (workspace,)):
                    if at and "/" in str(path) and "anatomy_source" in _loads(overrides):
                        entry = triggers.setdefault(str(path).split("/", 1)[0], {})
                        entry["changed"] = max(str(at), entry.get("changed", ""))
    finally:
        connection.close()
    return triggers


def follow_moved_sources(declared: dict[str, dict[str, Any]], files: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """A declared file that moved keeps its declaration: found again by its content digest."""
    paths = {file["path"] for file in files}
    by_digest = {file["fingerprint"]: file["path"] for file in files if file.get("fingerprint")}
    followed = {}
    for path, entry in declared.items():
        digest = entry.pop("_sha256", None)
        moved_to = by_digest.get(digest) if path not in paths and digest else None
        if moved_to and moved_to not in declared:
            followed[moved_to] = {**entry, "moved_from": path}
        else:
            followed[path] = entry
    return followed


def scan_models(affaires_root: Path, project_code: str) -> list[dict[str, Any]]:
    """IFC models of the affaire outside ARCHIVES folders (the Workspace lists neither)."""
    base = affaires_root / project_code
    if not base.is_dir():
        return []
    models = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base)
        if path.suffix.lower() != ".ifc" or not path.is_file():
            continue
        if any(_fold(part) in {"archive", "archives"} for part in relative.parts[:-1]):
            continue
        stat = path.stat()
        models.append({"path": relative.as_posix(), "title": path.name, "issuer": None, "document_type": "maquette",
                       "fingerprint": f"size:{stat.st_size}:mtime:{int(stat.st_mtime)}"})
    return models


def _loads(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


RELIABLE_DATES = {"fiche", "cartouche", "nom"}  # the PDF creation date is not the drawing's date


def _revision(file: dict[str, Any]) -> dict[str, Any]:
    parsed, position, index_source = None, POSITION_UNCERTAIN, None
    for key, level, source in (("index_card", POSITION_CERTAIN, "fiche"), ("index_read", POSITION_CERTAIN, "cartouche")):
        if parsed := parse_index(file.get(key), numeric=True):
            position, index_source = level, source
            break
    if parsed is None and (parsed := filename_index(file["title"])):
        position, index_source = POSITION_PROBABLE, "nom"
    when, when_source = None, None
    for key, source in (("date_card", "fiche"), ("date_read", "cartouche"), ("title", "nom"), ("date_pdf", "pdf")):
        value = filename_date(file["title"]) if key == "title" else parse_date(file.get(key))
        if value:
            when, when_source = value, source
            break
    revision = {"index": format_index(parsed), "position": position, "index_source": index_source,
                "date": when, "date_source": when_source,
                "paths": [file["path"]], "fingerprint": file.get("fingerprint"), "_parsed": parsed,
                "_format": Path(file["title"]).suffix.lower()}
    if file.get("issuer"):
        revision["issuer"] = file["issuer"]
    if file.get("reference"):
        revision["reference"] = True
    return revision


def _order(revision: dict[str, Any]) -> tuple:
    parsed = revision["_parsed"]
    return (parsed is not None, parsed[0] if parsed else "", (parsed[1] or 0) if parsed else 0, revision["date"] or "")


def _boilerplate(names: list[str]) -> set[str]:
    """Words repeated in at least a quarter of an affaire's names (client, address, project title)."""
    counts: dict[str, int] = {}
    for name in names:
        for word in set(name.split()):
            counts[word] = counts.get(word, 0) + 1
    floor = max(3, len(names) // 4)
    kept = {"PLANS", "LOT", *_PROJECT_TOKENS, *(w for words in (_PROJECT, _CONFRONT, _ADMIN) for w in words)}
    return {word for word, count in counts.items()
            if count >= floor and word not in kept and not any(word.startswith(k) for k in _PROJECT + _CONFRONT)}


def _without(name: str, words: set[str]) -> str:
    kept = [word for word in name.split() if word not in words]
    return " ".join(kept) if kept else name


def current_state(files: list[dict[str, Any]], project_code: str) -> dict[str, Any]:
    series: dict[str, dict[str, Any]] = {}
    not_followed = 0
    common = _boilerplate([piece_name(file["title"], project_code) for file in files])
    for file in files:
        name = _without(piece_name(file["title"], project_code), common)
        kind = category(name, file.get("document_type"), file["title"])
        if kind in {"administratif", "autre"}:
            not_followed += 1
            continue
        piece = series.setdefault(name, {"piece": name, "category": kind, "revisions": []})
        revision = _revision(file)
        same = next((r for r in piece["revisions"] if revision["fingerprint"] and r["fingerprint"] == revision["fingerprint"]), None)
        if same:  # the same file copied in another folder
            same["paths"].extend(revision["paths"])
            same["reference"] = same.get("reference") or revision.get("reference")
        else:
            piece["revisions"].append(revision)

    pieces, questions = [], []
    for name in sorted(series):
        piece = series[name]
        revisions = sorted(piece["revisions"], key=_order)
        current = revisions[-1]
        indexed = [r for r in revisions if r["_parsed"]]
        latest_letter = indexed[-1]["_parsed"][0] if indexed else None
        same_letter = [r for r in indexed if r["_parsed"][0] == latest_letter]
        if indexed:
            current = indexed[-1]
            newer = [r for r in revisions if not r["_parsed"] and r["date"] and current["date"] and r["date"] > current["date"]]
            if newer:
                questions.append({"piece": name, "kind": "fichier_sans_indice_plus_recent",
                                  "text": f"{name} : un fichier sans indice est plus récent que l'indice {current['index']}."})
            # Indices follow each other; a known date checks it. A lower index dated after the current one
            # (indices restarted at a new phase, a wrong index) is asked, never decided: the PDF creation
            # date is not the drawing's date and does not count.
            dated = lambda r: r["date"] and r.get("date_source") in RELIABLE_DATES
            if dated(current):
                later = [r for r in indexed if r is not current and r.get("_format") == current.get("_format")
                         and r["_parsed"][0] != current["_parsed"][0] and dated(r) and r["date"] > current["date"]]
                if later:
                    newest = max(later, key=lambda r: r["date"])
                    questions.append({"piece": name, "kind": "indice_et_date_contradictoires",
                                      "text": f"{name} : l'indice {newest['index']} est daté du {newest['date']}, après "
                                              f"l'indice {current['index']} ({current['date']}) ; les indices ont-ils "
                                              f"repris à une nouvelle phase ? lequel fait foi ?"})
        chosen = [r for r in revisions if r.get("reference")]
        if chosen:
            latest = current
            current = {**chosen[-1], "position": POSITION_REFERENCE}
            if len(chosen) > 1:
                questions.append({"piece": name, "kind": "plusieurs_references",
                                  "text": f"{name} : {len(chosen)} fichiers sont marqués comme référence projet."})
            elif latest is not chosen[-1] and _order(latest) > _order(chosen[-1]):
                questions.append({"piece": name, "kind": "reference_depassee",
                                  "text": f"{name} : la référence projet est à l'indice {chosen[-1]['index'] or '(sans indice)'}, "
                                          f"un indice plus récent existe ({latest['index'] or latest['date']})."})
        variants = sorted({r["index"] for r in same_letter if r["_parsed"][1]})
        if len(variants) > 1:
            questions.append({"piece": name, "kind": "variantes",
                              "text": f"{name} : plusieurs variantes de l'indice {latest_letter} ({', '.join(variants)}) ; laquelle fait foi ?"})
        # A drawing and its model under one index (plan.pdf, plan.ifc) are two formats of one piece.
        by_index: dict[tuple[str, str], int] = {}
        for revision in indexed:
            key = (revision["index"], revision["_format"])
            by_index[key] = by_index.get(key, 0) + 1
        for (label, _), count in sorted(by_index.items()):
            if count > 1:
                questions.append({"piece": name, "kind": "meme_indice_contenus_differents",
                                  "text": f"{name} : {count} fichiers différents portent l'indice {label}."})
        # The revision before the current one, in the same format: what a model index is compared with.
        # Variants of the current index (C1, C2 of C) are alternatives, not earlier revisions.
        letter = current["_parsed"][0] if current.get("_parsed") else None
        earlier = [r for r in revisions if r.get("_format") == current.get("_format") and r["paths"] != current["paths"]
                   and _order(r) < _order(current) and not (letter and r.get("_parsed") and r["_parsed"][0] == letter)]
        pieces.append({
            "piece": name,
            "category": piece["category"],
            "current": {k: v for k, v in current.items() if not k.startswith("_") and k != "fingerprint"},
            **({"previous": {k: earlier[-1][k] for k in ("index", "date", "paths") if earlier[-1].get(k)}} if earlier else {}),
            "revisions": len(revisions),
            **({"variants": variants} if len(variants) > 1 else {}),
        })
    return {
        "read_at": datetime.now(timezone.utc).isoformat(),
        "pieces": pieces,
        "questions": questions,
        "documents_not_followed": not_followed,
        "rule": "A, B, C : indices successifs ; C1, C2 : variantes de C ; sans indice : position incertaine, placée par la date ; "
                "une date connue (fiche, cartouche, nom) contrôle l'ordre des indices : un indice plus bas daté après "
                "l'indice courant est une question ; un fichier marqué référence projet sur sa fiche l'emporte.",
        "authority": {"is_register": False, "is_evidence": False, "is_decision": False},
    }


def read_project_pieces(project_code: str, *, workspace_db: Path | None = None,
                        affaires_root: Path | None = None) -> dict[str, Any] | None:
    """Current state for one affaire; None when neither source is configured."""
    workspace_db = workspace_db or _env_path(WORKSPACE_DB_ENV)
    affaires_root = affaires_root or _env_path(AFFAIRES_ROOT_ENV)
    if workspace_db is None and affaires_root is None:
        return None
    files = read_workspace(workspace_db, project_code) if workspace_db and workspace_db.is_file() else []
    declared = read_declared_sources(workspace_db, project_code) if workspace_db and workspace_db.is_file() else {}
    if affaires_root:
        files += scan_models(affaires_root, project_code)
    state = current_state(files, project_code)
    declared = follow_moved_sources(declared, files)
    if declared:
        state["declared_sources"] = declared
    return state


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name, "").strip()
    return Path(value) if value and Path(value).is_absolute() else None
