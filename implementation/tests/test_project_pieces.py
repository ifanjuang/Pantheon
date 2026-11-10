"""The current state of an affaire's documents: the latest index of each piece.

Built on a synthetic Workspace database and a synthetic affaire folder; no real
project data is involved. Index rule: A, B, C successive; C1, C2 variants of C.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mvp_vertical import project_pieces as pieces


@pytest.mark.parametrize("label, expected", [
    ("E", ("E", None)), ("C1", ("C", 1)), ("C.1", ("C", 1)), ("Ind C-2", ("C", 2)), ("indice b", ("B", None)),
    ("ESQ", None), ("", None), ("12", None), ("IND9", ("09", None)), ("Ind 0", ("00", None)),
])
def test_the_agency_index_rule(label, expected) -> None:
    assert pieces.parse_index(label) == expected


@pytest.mark.parametrize("title, expected", [
    ("DCE_DEMO_PLAN MAC-DEM.pdf", "PLAN MAC-DEM"),
    ("DEMO_DPGF_C - DPGF_DCE_C.pdf", "DPGF"),
    ("PERMIS DEMO D.1.pdf", "PERMIS"),
    ("DEMO_E_261006.ifc", "MAQUETTE"),
    ("Devis LOT 4 (1).pdf", "DEVIS LOT 4"),
    ("20.01.2025_DEMO_ELECTRICITE_C.pdf", "ELECTRICITE"),
    ("DP 15.06.23", "DP"),
])
def test_a_piece_is_named_from_the_file_without_code_phase_index_or_date(title, expected) -> None:
    assert pieces.piece_name(title, "DEMO") == expected


def test_file_names_give_a_probable_index_and_a_date() -> None:
    assert pieces.filename_index("DEMO_E_261006.ifc") == ("E", None)
    assert pieces.filename_index("Devis PPR1 Ind A.pdf") == ("A", None)
    assert pieces.filename_date("DEMO_E_261006.ifc") == "2026-10-06"
    assert pieces.parse_date("19 mai 2026") == "2026-05-19" and pieces.parse_date("17/08/2026") == "2026-08-17"


def _workspace(path: Path, files: dict[str, dict]) -> Path:
    db = path / "workspace.sqlite3"
    connection = sqlite3.connect(db)
    connection.executescript("""
        CREATE TABLE workspace_entries (entry_key TEXT, workspace TEXT, kind TEXT, path TEXT, payload_json TEXT);
        CREATE TABLE workspace_document_identity (workspace TEXT, source_path TEXT, source_sha256 TEXT);
        CREATE TABLE hindsight_metadata_preflight (cache_key TEXT, result_json TEXT);
        CREATE TABLE hindsight_metadata_preflight_source (workspace TEXT, source_path TEXT, cache_key TEXT);
        CREATE TABLE workspace_document_metadata_overrides (workspace TEXT, source_path TEXT, overrides_json TEXT);
    """)
    for number, (name, info) in enumerate(files.items()):
        path_in = f"DEMO/{name}"
        connection.execute("INSERT INTO workspace_entries VALUES (?, 'Affaires', 'document', ?, ?)",
                           (path_in, path_in, json.dumps({"name": Path(name).name})))
        connection.execute("INSERT INTO workspace_document_identity VALUES ('Affaires', ?, ?)", (path_in, info["sha"]))
        fields = {key: {"value": info[key]} for key in ("index", "document_date", "pdf_creation_date") if key in info}
        connection.execute("INSERT INTO hindsight_metadata_preflight VALUES (?, ?)", (f"k{number}", json.dumps({"fields": fields})))
        connection.execute("INSERT INTO hindsight_metadata_preflight_source VALUES ('Affaires', ?, ?)", (path_in, f"k{number}"))
        if "card" in info:
            connection.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', ?, ?)",
                               (path_in, json.dumps(info["card"])))
    # Another affaire whose code starts like this one is never read.
    connection.execute("INSERT INTO workspace_entries VALUES ('x', 'Affaires', 'document', 'DEMO2/DCE/PLAN X.pdf', '{}')")
    connection.commit()
    connection.close()
    return db


def _state(tmp_path: Path, files: dict[str, dict], models: tuple[str, ...] = ()) -> dict:
    db = _workspace(tmp_path, files)
    root = tmp_path / "affaires"
    for model in models:
        (root / "DEMO" / model).parent.mkdir(parents=True, exist_ok=True)
        (root / "DEMO" / model).write_text("ISO-10303-21;")
    return pieces.read_project_pieces("DEMO", workspace_db=db, affaires_root=root)


def test_the_latest_index_is_current_and_a_card_correction_wins(tmp_path) -> None:
    state = _state(tmp_path, {
        "ARCHIVE-LIKE/DCE_DEMO_PLAN RDC B.pdf": {"sha": "1", "index": "B", "pdf_creation_date": "01/03/2026"},
        "DCE/DCE_DEMO_PLAN RDC.pdf": {"sha": "2", "index": "A", "card": {"index": "C", "document_date": "2026-04-02"}},
    })
    plan = next(p for p in state["pieces"] if p["piece"] == "PLAN RDC")
    assert plan["current"]["index"] == "C" and plan["current"]["position"] == "certaine"
    assert plan["current"]["date"] == "2026-04-02" and plan["current"]["date_source"] == "fiche"
    assert plan["revisions"] == 2 and not state["questions"]


def test_variants_same_index_and_unindexed_newer_files_become_questions(tmp_path) -> None:
    state = _state(tmp_path, {
        "DCE/CCTP C1.pdf": {"sha": "1", "index": "C1"},
        "DCE/CCTP C2.pdf": {"sha": "2", "index": "C.2"},
        "DCE/DPGF.pdf": {"sha": "3", "index": "C"},
        "ACT/DPGF.pdf": {"sha": "4", "index": "C"},
        "DCE/PLAN ELEC.pdf": {"sha": "5", "index": "D", "document_date": "01/02/2026"},
        "DCE/PLAN ELEC export.pdf": {"sha": "6", "card": {"title": "PLAN ELEC.pdf", "document_date": "2026-03-01"}},
    })
    kinds = {(q["piece"], q["kind"]) for q in state["questions"]}
    assert kinds == {("CCTP", "variantes"), ("DPGF", "meme_indice_contenus_differents"),
                     ("PLAN ELEC", "fichier_sans_indice_plus_recent")}
    cctp = next(p for p in state["pieces"] if p["piece"] == "CCTP")
    assert cctp["variants"] == ["C1", "C2"] and cctp["current"]["index"] == "C2"


def test_a_file_marked_as_project_reference_wins_and_a_newer_index_is_asked(tmp_path) -> None:
    state = _state(tmp_path, {
        "DCE/PLAN RDC D.pdf": {"sha": "1", "index": "D", "card": {"reference": True}},
        "DCE/PLAN RDC E.pdf": {"sha": "2", "index": "E"},
    })
    plan = state["pieces"][0]
    assert (plan["current"]["index"], plan["current"]["position"], plan["current"]["reference"]) == ("D", "référence", True)
    assert [q["kind"] for q in state["questions"]] == ["reference_depassee"]


def test_two_references_on_one_piece_are_asked(tmp_path) -> None:
    state = _state(tmp_path, {
        "DCE/CCTP C.pdf": {"sha": "1", "index": "C", "card": {"reference": True}},
        "ACT/CCTP C.pdf": {"sha": "2", "index": "C", "card": {"reference": True}},
    })
    assert {q["kind"] for q in state["questions"]} == {"plusieurs_references", "meme_indice_contenus_differents"}


def test_a_file_without_index_is_kept_with_an_uncertain_position(tmp_path) -> None:
    state = _state(tmp_path, {"DCE/AE.pdf": {"sha": "1", "pdf_creation_date": "05/05/2026"}})
    current = state["pieces"][0]["current"]
    assert (current["index"], current["position"], current["date"], current["date_source"]) == (None, "incertaine", "2026-05-05", "pdf")


def test_copies_merge_quotes_are_confronted_and_administrative_files_are_not_followed(tmp_path) -> None:
    state = _state(tmp_path, {
        "DCE/PERMIS DEMO D.1.pdf": {"sha": "same"},
        "Dossier Permis/PERMIS DEMO D.1.pdf": {"sha": "same"},
        "ACT/Devis menuiserie.pdf": {"sha": "q"},
        "Etudes/Attestation assurance.pdf": {"sha": "a"},
    })
    permis = next(p for p in state["pieces"] if p["piece"] == "PERMIS")
    assert permis["revisions"] == 1 and len(permis["current"]["paths"]) == 2
    assert permis["current"]["index"] == "D1" and permis["current"]["position"] == "probable"
    assert next(p for p in state["pieces"] if p["piece"].startswith("DEVIS"))["category"] == "a_confronter"
    assert state["documents_not_followed"] == 1
    assert not any(p["piece"] == "PLAN X" for p in state["pieces"])


def test_only_project_pieces_are_followed(tmp_path) -> None:
    state = _state(tmp_path, {
        "Contentieux/PV AGO 2 OCTOBRE.pdf": {"sha": "1"},
        "Chantier/WhatsApp chat.pdf": {"sha": "2"},
        "Etudes/DEMO_C.pdf": {"sha": "3", "index": "C"},
        "Etudes/DEMO-X CCTP G.pdf": {"sha": "4", "index": "G"},
        "Conception/PLAN SALLE DE BAIN DEMOPDF.pdf": {"sha": "5", "index": "B"},
    })
    assert sorted(p["piece"] for p in state["pieces"]) == ["CCTP", "PLAN SALLE DE BAIN"]
    assert state["documents_not_followed"] == 3 and not state["questions"]


@pytest.mark.parametrize("title, expected", [
    ("LIE FRONT PLN INDICE H.pdf", "projet"),
    ("DEMO-X CCTP-CCAP.pdf", "projet"),
    ("D-202609-000418.pdf", "autre"),
    ("Statuts ASL.pdf", "autre"),
    ("DEMO_AE.pdf", "projet"),
    ("Coupe longitudinale.pdf", "projet"),
])
def test_a_piece_of_project_is_recognised_by_its_name(title, expected) -> None:
    assert pieces.category(pieces.piece_name(title, "DEMO"), None, title) == expected


def test_dates_in_names_and_words_repeated_across_the_affaire_are_dropped(tmp_path) -> None:
    state = _state(tmp_path, {
        f"DCE/MAISON DUPONT RUE X {name}.pdf": {"sha": str(n)}
        for n, name in enumerate(["PLAN RDC", "PLAN R01", "COUPE AA", "CCTP LOT 2", "NOTICE"])
    } | {"DCE/2025.05.28 CCTP LOT 6.pdf": {"sha": "9"}})
    assert sorted(p["piece"] for p in state["pieces"]) == ["CCTP LOT 2", "CCTP LOT 6", "COUPE AA", "NOTICE", "PLAN R01", "PLAN RDC"]
    lot6 = next(p for p in state["pieces"] if p["piece"] == "CCTP LOT 6")
    assert lot6["current"]["date"] == "2025-05-28" and lot6["current"]["date_source"] == "nom"


def test_models_come_from_the_folder_and_archives_are_skipped(tmp_path) -> None:
    state = _state(tmp_path, {}, models=("Conception/CAD/DEMO_E_261006.ifc", "Conception/ARCHIVES/DEMO_D_260901.ifc"))
    maquette = next(p for p in state["pieces"] if p["piece"] == "MAQUETTE")
    assert maquette["current"]["index"] == "E" and maquette["revisions"] == 1
    assert maquette["current"]["date"] == "2026-10-06"


def test_nothing_is_read_without_configuration(monkeypatch) -> None:
    monkeypatch.delenv(pieces.WORKSPACE_DB_ENV, raising=False)
    monkeypatch.delenv(pieces.AFFAIRES_ROOT_ENV, raising=False)
    assert pieces.read_project_pieces("DEMO") is None


def test_a_drawing_and_its_model_under_one_index_raise_no_question(tmp_path) -> None:
    state = _state(tmp_path, {"Etudes/PLN STRUCTURE Indice H.pdf": {"sha": "1"}},
                   models=("Etudes/PLN STRUCTURE Indice H.ifc",))
    piece = next(p for p in state["pieces"] if p["piece"] == "PLN STRUCTURE")
    assert piece["current"]["index"] == "H" and piece["revisions"] == 2 and not state["questions"]


def test_numbered_engineer_indices_are_ordered(tmp_path) -> None:
    state = _state(tmp_path, {"Etudes/CCTP LOT 08 IND8.pdf": {"sha": "1"}, "Etudes/CCTP LOT 08 IND10.pdf": {"sha": "2"},
                              "Etudes/NOTE STRUCTURE.pdf": {"sha": "3", "index": "0"}})
    cctp = next(p for p in state["pieces"] if p["piece"] == "CCTP LOT 08")
    assert (cctp["current"]["index"], cctp["revisions"]) == ("10", 2)
    assert next(p for p in state["pieces"] if p["piece"] == "NOTE STRUCTURE")["current"]["index"] == "0"
