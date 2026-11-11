"""Anatomy sources: declared on the file card, consolidated on the agency side.

Synthetic Workspace database, synthetic affaire folder and synthetic model
readings; no real project data is involved.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path

import pytest

from mvp_vertical import anatomy_export, anatomy_sources, model_reading, project_pieces

ARCHI = "DCE/MAQUETTE ARCHI B.ifc"
ARCHI_NEW = "DCE/MAQUETTE ARCHI C.ifc"
BET = "DCE/MAQUETTE STRUCTURE A.ifc"


def _reading(discipline: str, *, quality: str = "bonne", alignment: dict | None = None) -> dict:
    reading = {"discipline": discipline, "quality": {"niveau": quality, "conseils_export": ["exporter les locaux"]},
               "elements": [{"id": "e1"}], "openings": [], "spaces": [{"id": "s1", "name": "Séjour"}] if discipline == "architecture" else []}
    if alignment is not None:
        reading["alignment"] = alignment
    return reading


@pytest.fixture
def affaire(tmp_path, monkeypatch):
    """An affaire folder, a Workspace database whose cards the test fills, and canned model readings."""
    root = tmp_path / "affaires"
    for name in (ARCHI, ARCHI_NEW, BET):
        (root / "DEMO" / name).parent.mkdir(parents=True, exist_ok=True)
        (root / "DEMO" / name).write_text("ISO-10303-21;")
    monkeypatch.setenv(project_pieces.AFFAIRES_ROOT_ENV, str(root))
    readings: dict[str, dict | None] = {ARCHI: _reading("architecture"), ARCHI_NEW: _reading("architecture"),
                                        BET: _reading("structure")}

    reads: list[str] = []

    def fake_ensure(path, out_file, *, piece, index=None):
        reading = readings[path.relative_to(root / "DEMO").as_posix()]
        if reading is None:
            return {"piece": piece, "index": index, "file": out_file.name, "status": "unreadable", "error": "ValueError"}
        if out_file.exists():  # the real ensure keeps a sheet whose file is unchanged
            return {"piece": piece, "index": index, "file": out_file.name, "status": "cached"}
        reads.append(out_file.name)
        out_file.write_text(json.dumps({"source": {"piece": piece, "fingerprint": "f"}, **reading}), encoding="utf-8")
        return {"piece": piece, "index": index, "file": out_file.name, "status": "read"}

    monkeypatch.setattr(model_reading, "ensure", fake_ensure)
    monkeypatch.setattr(anatomy_export, "align_structural_models", lambda directory, statuses: None)

    db = tmp_path / "workspace.sqlite3"
    connection = sqlite3.connect(db)
    connection.execute("CREATE TABLE workspace_document_metadata_overrides (workspace TEXT, source_path TEXT, overrides_json TEXT)")
    connection.commit()
    connection.close()

    class Affaire:
        directory = tmp_path / "anatomie"
        models = readings
        read_log = reads
        files = root / "DEMO"

        def declare(self, path: str, **source) -> None:
            with sqlite3.connect(db) as c:
                c.execute("DELETE FROM workspace_document_metadata_overrides WHERE source_path = ?", (f"DEMO/{path}",))
                c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', ?, ?)",
                          (f"DEMO/{path}", json.dumps({"title": "x", "anatomy_source": source})))

        def consolidate(self, force: bool = False) -> tuple[list, dict]:
            declared = project_pieces.read_declared_sources(db, "DEMO")
            self.directory.mkdir(exist_ok=True)
            return anatomy_export.read_declared_sources("DEMO", {"pieces": [], "questions": []}, declared,
                                                        self.directory, consolidate=force)

    return Affaire()


def _states(section: dict) -> dict[str, str]:
    return {line["fichier"]: line["état"] for line in section["liste"]}


def test_a_declaration_is_normalized_with_defaults_and_bounded() -> None:
    declared = anatomy_sources.normalize({"active": True, "mode": "n'importe", "role": "référence", "note": "x" * 900,
                                          "replaces": "ignored without replacement mode"})
    assert declared["mode"] == "complément" and declared["role"] == "référence"
    assert "replaces" not in declared and len(declared["note"]) == 300
    assert anatomy_sources.normalize("oui") is None


def test_only_card_declarations_are_read_and_another_affaire_is_not(tmp_path) -> None:
    db = tmp_path / "w.sqlite3"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE workspace_document_metadata_overrides (workspace TEXT, source_path TEXT, overrides_json TEXT)")
        c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', 'DEMO/a.ifc', ?)",
                  (json.dumps({"anatomy_source": {"active": True}}),))
        c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', 'DEMO/b.pdf', ?)",
                  (json.dumps({"index": "C"}),))
        c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', 'DEMO2/c.ifc', ?)",
                  (json.dumps({"anatomy_source": {"active": True}}),))
    assert list(project_pieces.read_declared_sources(db, "DEMO")) == ["a.ifc"]


def test_a_source_waits_until_consolidated_unless_its_card_asks_for_it_now(affaire) -> None:
    affaire.declare(ARCHI, active=True, role="référence")
    affaire.declare(BET, active=True, consolidate_now=True, declared_alignment="aucun")
    models, section = affaire.consolidate()
    assert _states(section) == {ARCHI: "en attente", BET: "avertissement"}
    assert section["en_attente"] == 1 and [m["piece"] for m in models] == [Path(BET).stem]

    models, section = affaire.consolidate(force=True)
    assert _states(section)[ARCHI] == "activée" and section["en_attente"] == 0 and len(models) == 2

    # A later export without consolidation keeps what was consolidated.
    _, section = affaire.consolidate()
    assert _states(section)[ARCHI] == "activée"


def test_a_changed_declaration_waits_for_a_new_consolidation(affaire) -> None:
    affaire.declare(ARCHI, active=True)
    affaire.consolidate(force=True)
    affaire.declare(ARCHI, active=True, declared_alignment="coordonnées partagées")
    _, section = affaire.consolidate()
    assert _states(section)[ARCHI] == "en attente"
    assert "relancer" in section["liste"][0]["messages"][0]


def test_states_say_why_warning_and_error(affaire) -> None:
    affaire.models[ARCHI] = _reading("architecture", quality="à améliorer")
    affaire.models[BET] = _reading("structure", alignment={"verdict": "incertain", "score": 0.3, "margin": 0.02})
    affaire.declare(ARCHI, active=True)
    affaire.declare(BET, active=True)
    models, section = affaire.consolidate(force=True)
    lines = {line["fichier"]: line for line in section["liste"]}
    assert lines[ARCHI]["état"] == "avertissement" and "qualité" in lines[ARCHI]["messages"][0]
    assert lines[BET]["état"] == "erreur" and "rapprochement impossible" in lines[BET]["messages"][0]
    assert [m["piece"] for m in models] == [Path(ARCHI).stem]


def test_a_probable_overlay_is_usable_but_to_confirm_until_confirmed(affaire) -> None:
    alignment = {"verdict": "probable", "score": 0.84, "margin": 0.3, "reference_fingerprint": "ref-1",
                 "rotation_deg": 90.0, "dx": 1.0, "dy": 2.0, "dz": 0.0}
    affaire.models[BET] = _reading("structure", alignment=alignment)
    affaire.declare(BET, active=True)
    _, section = affaire.consolidate(force=True)
    line = section["liste"][0]
    assert line["état"] == "avertissement" and "à confirmer" in line["messages"][0] and line["calage"]["confirmé"] is False

    affaire.declare(BET, active=True, alignment_confirmed={"by": "archi", "at": "2026-11-11", "reference_fingerprint": "ref-1"})
    _, section = affaire.consolidate(force=True)
    assert section["liste"][0]["état"] == "activée" and section["liste"][0]["calage"]["confirmé"]["par"] == "archi"


def test_a_replacement_happens_only_when_the_new_source_succeeds(affaire) -> None:
    affaire.declare(ARCHI, active=True)
    affaire.consolidate(force=True)
    affaire.models[ARCHI_NEW] = None  # unreadable
    affaire.declare(ARCHI_NEW, active=True, mode="remplacement", replaces=ARCHI)
    models, section = affaire.consolidate(force=True)
    assert _states(section) == {ARCHI: "activée", ARCHI_NEW: "erreur"}
    assert "l'ancienne source reste active" in section["liste"][1]["messages"][-1]

    affaire.models[ARCHI_NEW] = _reading("architecture")
    affaire.declare(ARCHI_NEW, active=True, mode="remplacement", replaces=ARCHI, note="nouvel indice")
    models, section = affaire.consolidate(force=True)
    lines = {line["fichier"]: line for line in section["liste"]}
    assert lines[ARCHI]["état"] == "remplacée" and lines[ARCHI]["remplacée_par"] == ARCHI_NEW
    assert lines[ARCHI_NEW]["remplace"] == ARCHI and len(models) == 1


def test_a_pending_replacement_keeps_the_old_source(affaire) -> None:
    affaire.declare(ARCHI, active=True)
    affaire.consolidate(force=True)
    affaire.declare(ARCHI_NEW, active=True, mode="remplacement", replaces=ARCHI)
    _, section = affaire.consolidate()
    assert _states(section) == {ARCHI: "activée", ARCHI_NEW: "en attente"}
    assert "remplacement en attente" in section["liste"][1]["messages"][-1]


def test_a_switched_off_source_is_listed_but_not_read(affaire) -> None:
    affaire.declare(ARCHI, active=False)
    models, section = affaire.consolidate(force=True)
    assert _states(section) == {ARCHI: "inactive"} and models == []


def test_a_drawing_source_is_read_for_its_index_only() -> None:
    piece = {"piece": "PLAN RDC", "current": {"index": "C", "position": "probable"}}
    state, messages = anatomy_sources.document_state(piece, ["PLAN RDC : deux variantes de l'indice C ; laquelle fait foi ?"])
    assert state == "avertissement" and messages[0] == "indice lu dans le nom du fichier" and len(messages) == 3


def test_reactivating_an_unchanged_file_reads_nothing_again(affaire) -> None:
    affaire.declare(ARCHI, active=True)
    affaire.consolidate(force=True)
    assert len(affaire.read_log) == 1
    affaire.declare(ARCHI, active=False)
    models, section = affaire.consolidate()
    assert _states(section) == {ARCHI: "inactive"} and models == []
    affaire.declare(ARCHI, active=True)
    models, section = affaire.consolidate()
    assert _states(section) == {ARCHI: "activée"} and len(models) == 1
    assert len(affaire.read_log) == 1  # same fingerprint: the sheet was kept


def test_a_changed_file_gets_a_new_sheet_and_each_consolidation_a_snapshot(affaire) -> None:
    affaire.declare(ARCHI, active=True)
    first, _ = affaire.consolidate(force=True)
    target = affaire.files / ARCHI
    target.write_text("ISO-10303-21; changed")
    os.utime(target, (1_900_000_000, 1_900_000_000))
    second, section = affaire.consolidate(force=True)
    assert first[0]["file"] != second[0]["file"] and len(affaire.read_log) == 2
    snapshots = json.loads((affaire.directory / "DEMO.consolidations.json").read_text(encoding="utf-8"))
    assert len(snapshots) == 2 and snapshots[-1]["sources"][0]["fiche"] == second[0]["file"]
    assert section["dernière_consolidation"] == snapshots[-1]["at"]
    # An export without consolidation adds no snapshot.
    affaire.consolidate()
    assert len(json.loads((affaire.directory / "DEMO.consolidations.json").read_text(encoding="utf-8"))) == 2


def test_a_moved_file_keeps_its_declaration_through_its_digest() -> None:
    declared = {"OLD/plan.pdf": {"active": True, "_sha256": "abc"}, "gone.pdf": {"active": True, "_sha256": "zzz"}}
    files = [{"path": "DCE/plan.pdf", "fingerprint": "abc"}]
    followed = project_pieces.follow_moved_sources(declared, files)
    assert followed["DCE/plan.pdf"] == {"active": True, "moved_from": "OLD/plan.pdf"}
    assert "gone.pdf" in followed and "_sha256" not in followed["gone.pdf"]


def test_sheet_names_follow_the_file_fingerprint(tmp_path) -> None:
    model = tmp_path / "m.ifc"
    model.write_text("x")
    a = anatomy_export.sheet_file(tmp_path, "DEMO", "Maquette architecte très longue pour un nom", model)
    assert a == anatomy_export.sheet_file(tmp_path, "DEMO", "Maquette architecte très longue pour un nom", model)
    assert re.fullmatch(r"DEMO\.maquette-[a-z0-9-]{1,40}\.json", a.name)
