from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "implementation" / "workspace_cockpit" / "server.py"
INSTALLER = ROOT / "deployment" / "ubuntu" / "configure-workspace-cockpit-local"
COMPOSE = ROOT / "deployment" / "ubuntu" / "compose.workspace-cockpit-local.yaml"
MOUNT_QUALIFIER = ROOT / "deployment" / "ubuntu" / "qualify-affaires-linux-mount.py"
PRODUCER_DAEMON = ROOT / "implementation" / "workspace_cockpit" / "producer_daemon.py"
ENRICHMENT_HOOK = ROOT / "implementation" / "workspace_cockpit" / "hindsight_enrichment_hook.py"
ENRICHMENT_INSTALLER = ROOT / "deployment" / "ubuntu" / "configure-hindsight-enrichment-hook"


def _module():
    spec = importlib.util.spec_from_file_location("workspace_cockpit_server", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hook_module():
    spec = importlib.util.spec_from_file_location("hindsight_enrichment_hook", ENRICHMENT_HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hindsight_enrichment_hook_validates_and_deduplicates_completed_retains(tmp_path: Path) -> None:
    hook = _hook_module()
    payload = {
        "event": "retain.completed",
        "status": "completed",
        "bank_id": "AGENCY_PROJECTS",
        "operation_id": "op-1",
        "data": {"document_id": "doc-1", "memory_unit_count": 2},
    }
    state_db = tmp_path / "state.sqlite3"
    hook._ensure_schema(state_db)
    assert hook._queue(state_db, payload, "AGENCY_PROJECTS") is True
    assert hook._queue(state_db, payload, "AGENCY_PROJECTS") is True
    assert hook._queue(state_db, {**payload, "bank_id": "OTHER"}, "AGENCY_PROJECTS") is False
    body = b'{"event":"retain.completed"}'
    signature = "sha256=" + hook.hmac.new(b"secret", body, hook.hashlib.sha256).hexdigest()
    assert hook._valid_signature("secret", body, signature) is True
    assert hook._valid_signature("secret", body, "sha256=invalid") is False


def _cards(result: dict) -> list[dict]:
    return result["workspaces"][0]["cards"]


def test_complete_source_cartouche_bundle_projects_rich_card(tmp_path: Path) -> None:
    module = _module()
    dce = tmp_path / "DCE"
    dce.mkdir()
    (dce / "CCTP_IND_C.pdf").write_bytes(b"%PDF-fixture")
    (dce / ".CCTP_IND_C.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-cctp-c
source: CCTP_IND_C.pdf
project: VERGER
phase: DCE
type: CCTP
index: C
document_date: 2026-09-12
issuer: StructureCo
scope_move_confirmed: true
tags:
  - structure
  - ossature-bois
---
# CCTP — Lot 03 Ossature bois

## Résumé
CCTP du lot structure pour la consultation DCE.

## Limites / incertitudes
À vérifier avec les plans structure.
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    cards = _cards(result)
    document = next(card for card in cards if card["kind"] == "document")
    folder = next(card for card in cards if card["kind"] == "folder")

    assert result["projection"] == "affaires_hindsight_project_scope_v5"
    assert document["status"] == "COMPLETE"
    assert document["document_id"] == "doc-cctp-c"
    assert document["source"] == "CCTP_IND_C.pdf"
    assert document["source_present"] is True
    assert document["cartouche"] == ".CCTP_IND_C.pdf.md"
    assert document["cartouche_present"] is True
    assert document["title"] == "CCTP — Lot 03 Ossature bois"
    assert document["document_type"] == "CCTP"
    assert document["phase"] == "DCE"
    assert document["index"] == "C"
    assert document["tags"] == ["structure", "ossature-bois"]
    assert "CCTP du lot structure" in document["summary"]
    assert document["hindsight_format_supported"] is True
    assert document["hindsight_eligible"] is True
    assert document["hindsight_representation_candidate"] == "source"
    assert document["project"] == "VERGER"
    assert document["scope_project"] == "DCE"
    assert document["project_declared"] == "VERGER"
    assert document["project_scope_source"] == "top_level_folder"
    assert document["project_scope_conflict"] is True
    assert document["scope_move_confirmed"] is True
    assert document["warnings"] == []
    assert folder["status"] == "FOLDER"
    assert folder["folder_context_present"] is False
    assert folder["can_generate_folder_context"] is True
    assert result["document_count"] == 1
    assert result["folder_count"] == 1


def test_markdown_source_is_not_confused_with_hidden_cartouche(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "notes.md").write_text("# Notes source\n\nContenu métier.", encoding="utf-8")
    (tmp_path / ".notes.md.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-notes
source: notes.md
type: NOTE
---
# Cartouche de notes

## Résumé
Notes de réunion.
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = [card for card in _cards(result) if card["kind"] == "document"]

    assert len(documents) == 1
    card = documents[0]
    assert card["name"] == "notes.md"
    assert card["cartouche"] == ".notes.md.md"
    assert card["status"] == "COMPLETE"
    assert card["document_id"] == "doc-notes"
    assert card["hindsight_format_supported"] is True
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"


def test_plain_markdown_with_matching_stem_is_never_treated_as_pdf_cartouche(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "CCTP.pdf").write_bytes(b"%PDF")
    (tmp_path / "CCTP.md").write_text("# CCTP source Markdown\n", encoding="utf-8")

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = sorted(
        (card for card in _cards(result) if card["kind"] == "document"),
        key=lambda card: card["name"],
    )

    assert [card["name"] for card in documents] == ["CCTP.md", "CCTP.pdf"]
    assert all(card["status"] == "PENDING_SCOPE" for card in documents)
    assert all(card["cartouche_present"] is False for card in documents)


def test_same_stem_different_source_extensions_have_distinct_cartouches(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "CCTP.pdf").write_bytes(b"%PDF")
    (tmp_path / "CCTP.docx").write_bytes(b"DOCX")
    (tmp_path / ".CCTP.pdf.md").write_text(
        "---\nschema: pantheon/cartouche/v1\ndocument_id: doc-pdf\nsource: CCTP.pdf\n---\n# PDF\n",
        encoding="utf-8",
    )
    (tmp_path / ".CCTP.docx.md").write_text(
        "---\nschema: pantheon/cartouche/v1\ndocument_id: doc-docx\nsource: CCTP.docx\n---\n# DOCX\n",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = sorted(
        (card for card in _cards(result) if card["kind"] == "document"),
        key=lambda card: card["name"],
    )

    assert [(card["name"], card["cartouche"], card["document_id"]) for card in documents] == [
        ("CCTP.docx", ".CCTP.docx.md", "doc-docx"),
        ("CCTP.pdf", ".CCTP.pdf.md", "doc-pdf"),
    ]
    assert all(card["status"] == "COMPLETE" for card in documents)


def test_pairing_is_exact_case_sensitive_and_never_reuses_one_cartouche(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Report.PDF").write_bytes(b"%PDF-upper")
    (tmp_path / "report.pdf").write_bytes(b"%PDF-lower")
    (tmp_path / ".Report.PDF.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-upper
source: Report.PDF
---
# Upper
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = {card["name"]: card for card in _cards(result) if card["kind"] == "document"}

    assert documents["Report.PDF"]["cartouche"] == ".Report.PDF.md"
    assert documents["Report.PDF"]["document_id"] == "doc-upper"
    assert documents["report.pdf"]["cartouche_present"] is False
    assert documents["report.pdf"]["status"] == "CHECK"
    assert documents["Report.PDF"]["status"] == "CHECK"
    assert documents["Report.PDF"]["name_conflict"] == "CASE_OR_UNICODE_COLLISION"
    assert documents["report.pdf"]["name_conflict"] == "CASE_OR_UNICODE_COLLISION"
    assert documents["Report.PDF"]["hindsight_eligible"] is False
    assert documents["Report.PDF"]["hindsight_representation_candidate"] is None


def test_duplicate_document_id_marks_both_copied_bundles_check(tmp_path: Path) -> None:
    module = _module()
    for folder_name in ("DCE", "COPIE"):
        folder = tmp_path / folder_name
        folder.mkdir()
        (folder / "CCTP.pdf").write_bytes(b"%PDF")
        (folder / ".CCTP.pdf.md").write_text(
            """---
schema: pantheon/cartouche/v1
document_id: doc-shared
source: CCTP.pdf
---
# CCTP
""",
            encoding="utf-8",
        )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    duplicates = [
        card for card in _cards(result)
        if card["kind"] == "document" and card.get("document_id") == "doc-shared"
    ]

    assert len(duplicates) == 2
    assert all(card["status"] == "CHECK" for card in duplicates)
    assert all(card["hindsight_eligible"] is False for card in duplicates)
    assert all(card["hindsight_representation_candidate"] is None for card in duplicates)
    assert all(card["identity_conflict"] == "DUPLICATE_DOCUMENT_ID" for card in duplicates)
    assert all(any("document_id dupliqué" in warning for warning in card["warnings"]) for card in duplicates)


def test_missing_or_wrong_cartouche_schema_is_check(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
document_id: doc-notice
source: Notice.pdf
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "CHECK"
    assert any("schema absent" in warning for warning in card["warnings"])


def test_unrelated_hidden_markdown_without_cartouche_metadata_is_ignored(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / ".tooling.md").write_text("# Tooling private note\n", encoding="utf-8")

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)

    assert result["document_count"] == 0
    assert _cards(result) == []


def test_source_without_cartouche_is_visible_with_generate_affordance(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-fixture")

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = _cards(result)[0]

    assert card["kind"] == "document"
    assert card["name"] == "Notice.pdf"
    assert card["status"] == "PENDING_SCOPE"
    assert card["source_present"] is True
    assert card["cartouche_present"] is False
    assert card["can_generate_cartouche"] is False
    assert card["hindsight_format_supported"] is True
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"
def test_nested_pdf_without_cartouche_inherits_project_and_folder_scope(tmp_path: Path) -> None:
    module = _module()
    structure = tmp_path / "Projet Alpha" / "DCE" / "Structure"
    structure.mkdir(parents=True)
    (structure / "Plan.pdf").write_bytes(b"%PDF-folder-scoped")

    result = module.scan_workspaces([("project-platform", tmp_path)], max_depth=3)
    card = next(card for card in _cards(result) if card.get("name") == "Plan.pdf")

    assert card["status"] == "FOLDER_SCOPED"
    assert card["project"] == "Projet Alpha"
    assert card["scope_project"] == "Projet Alpha"
    assert card["project_declared"] is None
    assert card["project_scope_conflict"] is False
    assert card["project_scope_source"] == "top_level_folder"
    assert card["folder_ancestry"] == ["Projet Alpha", "DCE", "Structure"]
    assert card["document_identity_source"] == "technical"
    assert card["document_id"] is None
    assert card["cartouche_present"] is False
    assert card["can_generate_cartouche"] is False
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"


def test_archive_directories_and_all_descendants_are_excluded(tmp_path: Path) -> None:
    module = _module()
    active = tmp_path / "Projet Alpha" / "Plans"
    archived = tmp_path / "Projet Alpha" / "_ARCHIVES" / "Ancien" / "Plans"
    active.mkdir(parents=True)
    archived.mkdir(parents=True)
    (active / "registre-archives.pdf").write_bytes(b"%PDF-active")
    (archived / "ancien-plan.pdf").write_bytes(b"%PDF-archived")

    result = module.scan_workspaces([("project-platform", tmp_path)], max_depth=5)
    names = {card.get("name") for card in _cards(result)}

    assert "registre-archives.pdf" in names
    assert "ancien-plan.pdf" not in names
    assert not any("ARCHIVES" in (card.get("path") or "") for card in _cards(result))
    assert result["workspaces"][0]["excluded_folders"] == ["Projet Alpha/_ARCHIVES"]


def test_archive_word_inside_directory_name_excludes_the_whole_subtree(tmp_path: Path) -> None:
    module = _module()
    archived = tmp_path / "Projet Alpha" / "PLANS ARCHIVES" / "Anciens indices"
    archived.mkdir(parents=True)
    (archived / "ancien-plan.pdf").write_bytes(b"%PDF-archived")
    active = tmp_path / "Projet Alpha" / "Plans"
    active.mkdir(parents=True)
    (active / "registre-archives.pdf").write_bytes(b"%PDF-active")

    result = module.scan_workspaces([("project-platform", tmp_path)], max_depth=5)
    paths = {card.get("path") for card in _cards(result)}

    assert "Projet Alpha/Plans/registre-archives.pdf" in paths
    assert not any("PLANS ARCHIVES" in (path or "") for path in paths)
    assert result["workspaces"][0]["excluded_folders"] == [
        "Projet Alpha/PLANS ARCHIVES"
    ]


def test_archive_backup_and_old_filename_markers_are_not_scanned(tmp_path: Path) -> None:
    module = _module()
    folder = tmp_path / "Projet Alpha" / "Plans"
    folder.mkdir(parents=True)
    for filename in (
        "plan_archive.pdf",
        "plan-bak.pdf",
        "plan backup.pdf",
        "plan_old.pdf",
        "_archive.pdf",
    ):
        (folder / filename).write_bytes(b"%PDF-ignored")
    (folder / "plan-actif.pdf").write_bytes(b"%PDF-active")

    result = module.scan_workspaces([("project-platform", tmp_path)], max_depth=3)
    names = {card.get("name") for card in _cards(result)}

    assert "plan-actif.pdf" in names
    assert not names.intersection(
        {"plan_archive.pdf", "plan-bak.pdf", "plan backup.pdf", "plan_old.pdf", "_archive.pdf"}
    )


def test_configured_ratp_directories_and_descendants_are_not_scanned(tmp_path: Path) -> None:
    module = _module()
    for folder_name in ("RATP", "AGENCY_RATP"):
        ratp = tmp_path / folder_name / "Sous-dossier"
        ratp.mkdir(parents=True)
        (ratp / "plan.pdf").write_bytes(b"%PDF-excluded")
    active = tmp_path / "Projet Alpha" / "Plans"
    active.mkdir(parents=True)
    (active / "plan.pdf").write_bytes(b"%PDF-active")

    result = module.scan_workspaces(
        [("project-platform", tmp_path)],
        max_depth=5,
        excluded_folder_names=("RATP", "AGENCY_RATP"),
    )
    paths = {card.get("path") for card in _cards(result)}

    assert "Projet Alpha/Plans/plan.pdf" in paths
    assert not any("ratp" in Path(path).parts[0].casefold() for path in paths if path)
    assert result["workspaces"][0]["excluded_folders"] == ["AGENCY_RATP", "RATP"]


def test_explicit_filename_indices_create_non_authoritative_family_hints(tmp_path: Path) -> None:
    module = _module()
    folder = tmp_path / "Projet Alpha" / "Plans"
    folder.mkdir(parents=True)
    for filename in ("Facade_IND_A.pdf", "Facade_IND_B.pdf", "Autre.pdf"):
        (folder / filename).write_bytes(b"%PDF")

    result = module.scan_workspaces([("project-platform", tmp_path)], max_depth=2)
    documents = {
        card["name"]: card
        for card in _cards(result)
        if card.get("kind") == "document"
    }

    assert documents["Facade_IND_A.pdf"]["document_family_hint"] == documents["Facade_IND_B.pdf"]["document_family_hint"]
    assert documents["Facade_IND_A.pdf"]["filename_revision_hint"] == "A"
    assert documents["Facade_IND_B.pdf"]["filename_revision_hint"] == "B"
    assert documents["Autre.pdf"]["document_family_hint"] is None
    assert documents["Autre.pdf"]["filename_revision_hint"] is None


def test_cartouche_without_source_is_explicitly_missing(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / ".DPGF.xlsx.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-dpgf
source: DPGF.xlsx
type: DPGF
---
# DPGF

## Résumé
Décomposition du prix global et forfaitaire.
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = _cards(result)[0]

    assert card["status"] == "SOURCE_MISSING"
    assert card["source"] == "DPGF.xlsx"
    assert card["source_present"] is False
    assert card["cartouche_present"] is True
    assert card["document_id"] == "doc-dpgf"


def test_folder_context_is_projected_without_creating_identity(tmp_path: Path) -> None:
    module = _module()
    dce = tmp_path / "DCE"
    dce.mkdir()
    (dce / "_folder.md").write_text(
        """---
schema: pantheon/folder-context/v1
project: VERGER
phase: DCE
tags:
  - consultation
---
# Consultation des entreprises

Pièces utilisées pour la consultation.
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    folder = next(card for card in _cards(result) if card["kind"] == "folder")

    assert folder["status"] == "FOLDER"
    assert folder["title"] == "Consultation des entreprises"
    assert folder["project"] == "VERGER"
    assert folder["phase"] == "DCE"
    assert folder["tags"] == ["consultation"]
    assert folder["folder_context"] == "_folder.md"
    assert folder["folder_context_present"] is True
    assert folder["can_generate_folder_context"] is False
    assert "document_id" not in folder



def test_folder_without_folder_md_is_explicitly_detected_but_not_invalid(tmp_path: Path) -> None:
    module = _module()
    dossier = tmp_path / "CHANTIER"
    dossier.mkdir()
    (dossier / "Photo.pdf").write_bytes(b"%PDF-fixture")

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    folder = next(card for card in _cards(result) if card["kind"] == "folder")

    assert folder["status"] == "FOLDER"
    assert folder["folder_context"] is None
    assert folder["folder_context_present"] is False
    assert folder["can_generate_folder_context"] is True
    assert folder["warnings"] == []


def test_workspace_index_persists_reconstructible_snapshot_and_detects_changes(tmp_path: Path) -> None:
    module = _module()
    affaires = tmp_path / "affaires"
    state = tmp_path / "state" / "index.sqlite3"
    affaires.mkdir()
    dce = affaires / "DCE"
    dce.mkdir()
    (dce / "CCTP.pdf").write_bytes(b"%PDF-v1")

    index = module.WorkspaceIndex(
        [("Affaires", affaires)],
        2,
        state,
        reconcile_seconds=60,
        debounce_seconds=0.01,
        enable_watcher=False,
    )

    first = index.reconcile("test-initial")
    assert state.is_file()
    first_doc = next(card for card in first["workspaces"][0]["cards"] if card["kind"] == "document")
    first_folder = next(card for card in first["workspaces"][0]["cards"] if card["kind"] == "folder")
    assert first_doc["status"] == "FOLDER_SCOPED"
    assert first_doc["hindsight_eligible"] is True
    assert first_folder["folder_context_present"] is False
    assert first["index_state"]["last_reconcile_reason"] == "test-initial"

    (dce / ".CCTP.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-cctp
source: CCTP.pdf
type: CCTP
---
# CCTP
""",
        encoding="utf-8",
    )
    (dce / "_folder.md").write_text("---\nschema: pantheon/folder-context/v1\n---\n# DCE\n", encoding="utf-8")

    second = index.reconcile("test-change")
    second_doc = next(card for card in second["workspaces"][0]["cards"] if card["kind"] == "document")
    second_folder = next(card for card in second["workspaces"][0]["cards"] if card["kind"] == "folder")
    assert second_doc["status"] == "COMPLETE"
    assert second_doc["document_id"] == "doc-cctp"
    assert second_folder["folder_context_present"] is True
    assert second["index_state"]["last_reconcile_reason"] == "test-change"

    state.unlink()
    rebuilt = index.reconcile("test-rebuild")
    assert state.is_file()
    assert rebuilt["item_count"] == second["item_count"]
    assert rebuilt["index_state"]["last_reconcile_reason"] == "test-rebuild"


def test_workspace_index_dirty_signal_reconciles_without_ui_scan(tmp_path: Path) -> None:
    module = _module()
    affaires = tmp_path / "affaires"
    state = tmp_path / "state" / "index.sqlite3"
    affaires.mkdir()

    index = module.WorkspaceIndex(
        [("Affaires", affaires)],
        2,
        state,
        reconcile_seconds=60,
        debounce_seconds=0.01,
        enable_watcher=False,
    )
    index.start()
    try:
        assert index.snapshot()["item_count"] == 0
        (affaires / "Notice.pdf").write_bytes(b"%PDF")
        index.mark_dirty()

        deadline = module.time.monotonic() + 3
        while module.time.monotonic() < deadline:
            if index.snapshot()["item_count"] == 1:
                break
            module.time.sleep(0.02)

        snapshot = index.snapshot()
        assert snapshot["item_count"] == 1
        assert snapshot["index_state"]["last_reconcile_reason"] == "watch"
        assert snapshot["workspaces"][0]["cards"][0]["status"] == "PENDING_SCOPE"
    finally:
        index.stop()


def test_index_state_must_remain_outside_workspace_root(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "AFFAIRES"
    root.mkdir()
    assert module._path_is_within(root / ".state" / "index.sqlite3", root) is True
    assert module._path_is_within(tmp_path / "state" / "index.sqlite3", root) is False



def test_reconcile_move_preserves_cartouche_identity_when_pair_moves_together(tmp_path: Path) -> None:
    module = _module()
    affaires = tmp_path / "AFFAIRES"
    state = tmp_path / "state" / "index.sqlite3"
    source_dir = affaires / "DCE"
    target_dir = affaires / "MARCHE"
    source_dir.mkdir(parents=True)
    target_dir.mkdir()

    (source_dir / "CCTP_IND_C.pdf").write_bytes(b"%PDF")
    (source_dir / ".CCTP_IND_C.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-cctp-c
source: CCTP_IND_C.pdf
---
# CCTP
""",
        encoding="utf-8",
    )

    index = module.WorkspaceIndex(
        [("Affaires", affaires)],
        3,
        state,
        reconcile_seconds=60,
        debounce_seconds=0.01,
        enable_watcher=False,
    )
    before = index.reconcile("before-move")
    before_doc = next(
        card
        for card in before["workspaces"][0]["cards"]
        if card["kind"] == "document" and card["document_id"] == "doc-cctp-c"
    )
    assert before_doc["path"] == "DCE/CCTP_IND_C.pdf"
    assert before_doc["status"] == "COMPLETE"

    (source_dir / "CCTP_IND_C.pdf").rename(target_dir / "CCTP_IND_C.pdf")
    (source_dir / ".CCTP_IND_C.pdf.md").rename(target_dir / ".CCTP_IND_C.pdf.md")

    after = index.reconcile("after-move")
    after_doc = next(
        card
        for card in after["workspaces"][0]["cards"]
        if card["kind"] == "document" and card["document_id"] == "doc-cctp-c"
    )
    assert after_doc["path"] == "MARCHE/CCTP_IND_C.pdf"
    assert after_doc["status"] == "COMPLETE"
    assert after_doc["document_id"] == before_doc["document_id"]


def test_linux_inotify_accelerates_change_detection_when_available(tmp_path: Path) -> None:
    module = _module()
    if not module.sys.platform.startswith("linux"):
        return

    root = tmp_path / "AFFAIRES"
    root.mkdir()
    observed = module.threading.Event()
    watcher = module._InotifyWatcher([("Affaires", root)], 2, observed.set)
    assert watcher.start() is True
    try:
        (root / "Notice.pdf").write_bytes(b"%PDF")
        assert observed.wait(2.0) is True
        assert watcher.mode == "inotify"
    finally:
        watcher.stop()


def test_declared_source_cannot_escape_cartouche_directory(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "outside.pdf").write_bytes(b"%PDF-outside")
    package = tmp_path / "Rapport"
    package.mkdir()
    (package / "Rapport.pdf").write_bytes(b"%PDF-report")
    (package / ".Rapport.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-rapport
source: ../outside.pdf
---
# Rapport
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    card = next(card for card in _cards(result) if card["name"] == "Rapport.pdf")

    assert card["status"] == "CHECK"
    assert card["source"] == "Rapport.pdf"
    assert any("même dossier" in warning for warning in card["warnings"])


def test_unsupported_and_heavy_sources_are_not_scanned(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Maquette.rvt").write_bytes(b"revit")
    (tmp_path / "Maquette.0001.rvt").write_bytes(b"revit-backup")
    (tmp_path / "Perspective.psd").write_bytes(b"photoshop")
    (tmp_path / "~$Notice.docx").write_bytes(b"office-lock")
    (tmp_path / "cache.tmp").write_bytes(b"temp")

    (tmp_path / "photo.jpg").write_bytes(b"jpeg")
    (tmp_path / "application.log").write_text("log", encoding="utf-8")
    (tmp_path / "archive.zip").write_bytes(b"zip")

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = [card for card in _cards(result) if card["kind"] == "document"]

    assert documents == []


def test_invalid_optional_cartouche_does_not_block_supported_source(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
schema: wrong/schema
document_id: doc-notice
source: Notice.pdf
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "CHECK"
    assert card["hindsight_format_supported"] is True
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"
    assert card["document_identity_source"] == "workspace_path_fallback"
    assert card["document_id"].startswith("path-")
    assert card["scope_project"] is None
    assert card["project_scope_source"] == "pending_identification"


def test_declared_source_sha256_is_verified_when_present(tmp_path: Path) -> None:
    module = _module()
    source_bytes = b"exact-source-bytes"
    digest = hashlib.sha256(source_bytes).hexdigest()
    (tmp_path / "Notice.pdf").write_bytes(source_bytes)
    (tmp_path / ".Notice.pdf.md").write_text(
        f"""---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
source_sha256: {digest}
source_size_bytes: {len(source_bytes)}
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "COMPLETE"
    assert card["source_sha256"] == digest
    assert card["source_sha256_verified"] is True
    assert card["source_integrity"] == "VERIFIED"
    assert card["declared_source_size"] == len(source_bytes)
    assert card["hindsight_eligible"] is True


def test_declared_source_sha256_mismatch_is_check(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"actual-bytes")
    wrong_digest = hashlib.sha256(b"other-bytes").hexdigest()
    (tmp_path / ".Notice.pdf.md").write_text(
        f"""---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
source_sha256: {wrong_digest}
source_size_bytes: 12
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "CHECK"
    assert card["source_sha256_verified"] is False
    assert card["source_integrity"] == "MISMATCH"
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"
    assert card["document_identity_source"] == "workspace_path_fallback"


def test_declared_non_string_sha256_is_invalid_and_blocks_producer(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"actual-bytes")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
source_sha256: true
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "CHECK"
    assert card["source_integrity"] == "INVALID"
    assert card["source_sha256_verified"] is False
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"


def test_unreasonably_long_declared_source_size_is_check_not_reconcile_failure(tmp_path: Path) -> None:
    module = _module()
    source_bytes = b"exact-source-bytes"
    digest = hashlib.sha256(source_bytes).hexdigest()
    (tmp_path / "Notice.pdf").write_bytes(source_bytes)
    (tmp_path / ".Notice.pdf.md").write_text(
        f"""---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
source_sha256: {digest}
source_size_bytes: "{'9' * 5000}"
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "Notice.pdf")

    assert card["status"] == "CHECK"
    assert card["source_sha256_verified"] is True
    assert any("source_size_bytes invalide" in warning for warning in card["warnings"])
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"


def test_email_bundle_requires_verified_sha256_and_exact_size(tmp_path: Path) -> None:
    module = _module()
    raw = b"From: a@example.com\r\nTo: b@example.com\r\nSubject: Test\r\n\r\nBody\r\n"
    digest = hashlib.sha256(raw).hexdigest()
    (tmp_path / "mail.eml").write_bytes(raw)
    (tmp_path / ".mail.eml.md").write_text(
        f"""---
schema: pantheon/cartouche/v1
document_id: email-thread-123
source: mail.eml
source_sha256: {digest}
source_size_bytes: {len(raw)}
type: email
gmail_message_id: msg-123
gmail_thread_id: thread-123
---
# Test
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "mail.eml")

    assert card["status"] == "COMPLETE"
    assert card["source_integrity"] == "VERIFIED"
    assert card["source_sha256_verified"] is True
    assert card["hindsight_format_supported"] is False
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "cartouche"


def test_email_bundle_without_integrity_fields_is_check(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "mail.eml").write_bytes(b"Subject: Test\r\n\r\nBody")
    (tmp_path / ".mail.eml.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: email-thread-123
source: mail.eml
type: email
gmail_message_id: msg-123
gmail_thread_id: thread-123
---
# Test
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["name"] == "mail.eml")

    assert card["status"] == "CHECK"
    assert card["source_integrity"] == "UNDECLARED"
    assert card["hindsight_eligible"] is False
    assert card["hindsight_representation_candidate"] is None
    assert any("source_sha256 absent" in warning for warning in card["warnings"])
    assert any("source_size_bytes absent" in warning for warning in card["warnings"])


def test_malformed_cartouche_is_check_not_source_loss(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF-fixture")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: [
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = _cards(result)[0]

    assert card["status"] == "CHECK"
    assert card["source_present"] is True
    assert card["cartouche_present"] is True
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"
    assert card["document_identity_source"] == "workspace_path_fallback"
    assert any("YAML" in warning for warning in card["warnings"])


def test_check_mode_returns_affaires_projection_without_database(tmp_path: Path) -> None:
    dossier = tmp_path / "Libre"
    dossier.mkdir()
    result = subprocess.run(
        ["python3", str(SERVER), "--root", f"Test={tmp_path}", "--check"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["read_only"] is True
    assert payload["projection"] == "affaires_hindsight_project_scope_v5"
    assert payload["totals"]["FOLDER"] == 1
    assert payload["item_count"] == 1


def test_duplicate_document_id_preserves_source_missing_status(tmp_path: Path) -> None:
    module = _module()
    for folder_name in ("A", "B"):
        folder = tmp_path / folder_name
        folder.mkdir()
        (folder / ".Missing.pdf.md").write_text(
            """---
schema: pantheon/cartouche/v1
document_id: doc-orphan-shared
source: Missing.pdf
---
# Missing
""",
            encoding="utf-8",
        )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=2)
    cards = [
        card for card in _cards(result)
        if card.get("document_id") == "doc-orphan-shared"
    ]

    assert len(cards) == 2
    assert all(card["status"] == "SOURCE_MISSING" for card in cards)
    assert all(card["identity_conflict"] == "DUPLICATE_DOCUMENT_ID" for card in cards)


def test_mount_probe_keep_mode_qualifies_without_cleanup(tmp_path: Path) -> None:
    result = subprocess.run(
        ["python3", str(MOUNT_QUALIFIER), "--root", str(tmp_path), "--keep"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["qualified_core"] is True
    assert payload["qualified"] is True
    assert payload["cleanup"] is False

    probe = Path(payload["probe"])
    assert probe.is_dir()
    subprocess.run(["rm", "-rf", str(probe)], check=True)


def test_linux_affaires_mount_qualification_probe_runs_on_local_filesystem(tmp_path: Path) -> None:
    result = subprocess.run(
        ["python3", str(MOUNT_QUALIFIER), "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["qualified"] is True
    assert payload["mount"]["network_mount"] is False
    assert payload["dotfile_roundtrip"] is True
    assert payload["initial_projection"] is True
    assert payload["rename_projection"] is True
    assert payload["identity_preserved"] is True
    assert payload["reconcile_rebuild"] is True
    assert payload["cleanup"] is True
    assert payload["inotify"] in {
        "observed",
        "not-observed-reconcile-required",
        "unavailable-reconcile-required",
    }


def test_mount_probe_rejects_local_or_session_mount_in_production_mode(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "python3", str(MOUNT_QUALIFIER), "--root", str(tmp_path),
            "--require-network-mount",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["qualified"] is False
    assert payload["qualified_core"] is False
    assert payload["mount"]["network_mount"] is False
    assert not Path(payload["probe"]).exists()


def test_project_catalogue_uses_only_active_affaires_source_and_fails_closed_on_collision(tmp_path: Path) -> None:
    module = _module()
    active = tmp_path / "AFFAIRES"
    (active / "VERGER").mkdir(parents=True)
    (active / "DOUBLON").mkdir()
    (active / "doublon").mkdir()
    unadmitted_archive = tmp_path / "ARCHIVES" / "PROJET"
    (unadmitted_archive / "PINEDE").mkdir(parents=True)
    nested_archive = active / "VERGER" / "PLANS ARCHIVES" / "Ancien"
    nested_archive.mkdir(parents=True)
    (nested_archive / "plan.pdf").write_bytes(b"%PDF-archived")

    result = module.scan_workspaces(
        [("Affaires", active)],
        max_depth=4,
    )
    catalogue = result["project_catalogue"]

    assert catalogue["read_only"] is True
    assert catalogue["bounded"] is True
    assert catalogue["truncated"] is False
    assert catalogue["project_count"] == 3
    assert catalogue["conflict_count"] == 1

    by_key = {
        (item["root_kind"], item["name"].casefold()): item
        for item in catalogue["projects"]
    }
    active_project = by_key[("AFFAIRES", "verger")]
    assert active_project["state"] == "active"
    assert active_project["automatic_routing_allowed"] is True
    assert active_project["write_requires_confirmation"] is False
    assert active_project["relative_root"] == "VERGER"

    assert all(item["root_kind"] == "AFFAIRES" for item in catalogue["projects"])
    assert not any(item["name"] == "PINEDE" for item in catalogue["projects"])

    duplicates = [
        item for item in catalogue["projects"] if item["name"].casefold() == "doublon"
    ]
    assert len(duplicates) == 2
    assert all(item["routing_status"] == "conflict" for item in duplicates)
    assert all(item["automatic_routing_allowed"] is False for item in duplicates)

    affaires_workspace = next(
        item for item in result["workspaces"] if item["name"] == "Affaires"
    )
    assert "VERGER/PLANS ARCHIVES" in affaires_workspace["excluded_folders"]
    assert not any(
        "PLANS ARCHIVES" in str(card.get("path") or "")
        for card in affaires_workspace["cards"]
    )


def test_affaires_project_catalogue_is_reloaded_from_producer_sqlite_without_cockpit_scan(tmp_path: Path) -> None:
    module = _module()
    active = tmp_path / "AFFAIRES"
    (active / "VERGER").mkdir(parents=True)
    state_db = tmp_path / "state" / "index.sqlite3"

    index = module.WorkspaceIndex(
        [("Affaires", active)],
        2,
        state_db,
        enable_watcher=False,
    )
    produced = index.reconcile("test")
    persisted = module.PersistedWorkspaceProjection(
        [("Affaires", active)],
        state_db,
    )

    assert persisted.project_catalogue() == produced["project_catalogue"]
    assert persisted.snapshot()["project_catalogue"] == produced["project_catalogue"]
    assert 'if path == "/api/project-catalogue":' in SERVER.read_text(encoding="utf-8")


def test_projection_router_serves_each_workspace_from_its_own_producer_index(tmp_path: Path) -> None:
    module = _module()
    affaires = tmp_path / "AFFAIRES"
    (affaires / "VERGER").mkdir(parents=True)
    (affaires / "VERGER" / "plan.pdf").write_bytes(b"%PDF")
    library = tmp_path / "BIBLIOTHEQUE"
    library.mkdir()
    (library / "norme.pdf").write_bytes(b"%PDF")
    (library / "guide.pdf").write_bytes(b"%PDF")
    affaires_db = tmp_path / "state" / "affaires.sqlite3"
    library_db = tmp_path / "state" / "library.sqlite3"
    module.WorkspaceIndex([("Affaires", affaires)], 2, affaires_db, enable_watcher=False).reconcile("affaires")
    module.WorkspaceIndex([("Bibliotheque", library)], 1, library_db, enable_watcher=False).reconcile("library")

    router = module.WorkspaceProjectionRouter([
        (["Affaires"], module.PersistedWorkspaceProjection([("Affaires", affaires)], affaires_db)),
        (["Bibliotheque"], module.PersistedWorkspaceProjection([("Bibliotheque", library)], library_db)),
    ])
    snapshot = router.snapshot()

    assert [workspace["name"] for workspace in snapshot["workspaces"]] == ["Affaires", "Bibliotheque"]
    assert snapshot["workspace_count"] == 2
    assert snapshot["document_count"] == 3
    assert snapshot["index_state"]["mode"] == "multiple-persisted-projections"
    assert set(router.health()["workspaces"]) == {"Affaires", "Bibliotheque"}
    assert router.children("Bibliotheque", "")["workspace"] == "Bibliotheque"
    assert router.project_catalogue() == router.projections[0][1].project_catalogue()
    try:
        router.children("Absent", "")
    except ValueError as error:
        assert str(error) == "workspace_not_found"
    else:
        raise AssertionError("unknown workspace must be rejected")


def test_workspace_db_requires_projection_only_and_a_configured_root(tmp_path: Path) -> None:
    module = _module()
    root = tmp_path / "AFFAIRES"
    root.mkdir()
    base = ["--root", f"Affaires={root}", "--state-db", str(tmp_path / "index.sqlite3"), "--check"]
    args = module.build_parser().parse_args([*base, "--workspace-db", f"Affaires={tmp_path / 'a.sqlite3'}"])
    assert args.workspace_db == [("Affaires", tmp_path / "a.sqlite3")]
    for extra, message in (
        (["--workspace-db", f"Affaires={tmp_path / 'a.sqlite3'}"], "--workspace-db requires --projection-only"),
        (["--projection-only", "--workspace-db", f"Absent={tmp_path / 'a.sqlite3'}"], "--workspace-db names must be unique configured roots"),
        (["--projection-only", "--workspace-db", f"Affaires={root / 'a.sqlite3'}"], "--workspace-db paths must be absolute and outside every watched workspace root"),
    ):
        argv = [arg for arg in base if arg != "--check"] + extra
        try:
            module.main(argv)
        except SystemExit as error:
            assert str(error) == message
        else:
            raise AssertionError(f"expected rejection for {extra}")


def test_linux_installer_and_browser_assets_are_syntax_valid() -> None:
    subprocess.run(["bash", "-n", str(INSTALLER)], check=True)
    subprocess.run(["python3", "-m", "py_compile", str(MOUNT_QUALIFIER)], check=True)
    subprocess.run(["python3", "-m", "py_compile", str(PRODUCER_DAEMON)], check=True)
    subprocess.run(
        ["node", "--check", str(ROOT / "implementation" / "workspace_cockpit" / "static" / "app.js")],
        check=True,
    )
    text = INSTALLER.read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "StateDirectory=pantheon-workspace-cockpit" in text
    assert "--state-db /var/lib/pantheon-workspace-cockpit/index.sqlite3" in text
    assert "--reconcile-seconds 60" in text
    assert "--affaires-root" in text
    assert "AFFAIRES_ROOT" in text
    assert "--archives-projet-root" not in text
    assert "ARCHIVES_PROJET_ROOT" not in text
    assert "--root ArchivesProjet=%s" not in text
    assert "hindsight_producer.py" in text
    assert "producer_daemon.py" in text
    assert "pantheon-affaires-producer.service" in text
    assert "--projection-only" in text
    assert "memory_reconciliation.py" in text
    assert "EnvironmentFile=-/etc/pantheon-workspace-cockpit.env" in text
    assert text.count("printf 'RequiresMountsFor=%s\\n' \"$AFFAIRES_ROOT\"") == 2
    assert "setfacl" not in text
    assert "vault mirror" not in text.lower()
    assert "pgvector" not in text.lower()
    compose = COMPOSE.read_text(encoding="utf-8")
    assert "read_only: true" in compose
    assert "${AFFAIRES_ROOT:?set AFFAIRES_ROOT to the Linux-mounted NAS AFFAIRES path}:/workspace/affaires:ro" in compose
    assert "${AFFAIRES_GID:?set AFFAIRES_GID to the Linux-mounted NAS AFFAIRES group id}" in compose
    assert "group_add:" in compose
    assert "workspace-producer:" in compose
    assert 'entrypoint: ["/opt/hermes/.venv/bin/python", "/app/producer_daemon.py"]' in compose
    assert "--projection-only" in compose
    assert compose.count("${AFFAIRES_ROOT:?set AFFAIRES_ROOT to the Linux-mounted NAS AFFAIRES path}:/workspace/affaires:ro") == 2
    assert "ARCHIVES_PROJET_ROOT" not in compose
    assert "ArchivesProjet" not in compose
    assert "workspace-cockpit-state:/state:ro" in compose
    assert "/srv/pantheon/obsidian" not in compose
    assert "workspace-cockpit-state:/state" in compose
    assert "WORKSPACE_INDEX_DB: /state/index.sqlite3" in compose
    assert "WORKSPACE_RECONCILE_SECONDS" in compose
    assert "WORKSPACE_WATCH_DEBOUNCE_MS" in compose
    assert "WORKSPACE_HINDSIGHT_URL" in compose
    assert "WORKSPACE_HINDSIGHT_BANK_ID" in compose
    assert "WORKSPACE_HINDSIGHT_PARSER" in compose
    assert "WORKSPACE_HINDSIGHT_MAX_SUBMITS_PER_RECONCILE" in compose
    assert "WORKSPACE_HINDSIGHT_MAX_FILE_MB" in compose
    assert "WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS" in compose
    assert "WORKSPACE_HINDSIGHT_SOURCE_KIND" in compose
    assert "WORKSPACE_RECONCILE_HERMES_URL" in compose
    assert "WORKSPACE_RECONCILE_HERMES_KEY" in compose
    assert "WORKSPACE_RECONCILE_MAX_CONTEXT_CHARS" in compose
    readme = (ROOT / "deployment" / "ubuntu" / "README.md").read_text(encoding="utf-8")
    assert "AFFAIRES_ROOT=/mnt/pantheon-affaires/AFFAIRES" in readme
    assert "ARCHIVES_PROJET_ROOT" not in readme
    assert "ARCHIVES/PROJET` is not a Workspace source" in readme
    assert "AFFAIRES_GID=replace-with-affaires-mount-group-id" in readme
    assert "127.0.0.1" in compose
    assert "role-trace:" in compose
    assert "ROLE_TRACE_ATTACH_KEY" in compose
    assert "ROLE_TRACE_READ_KEY" in compose
    assert "HERMES_ROLE_TRACE_API_KEY" in compose
    assert "hindsight-enrichment-hook:" in compose
    assert 'profiles: ["enrichment"]' in compose
    assert "HINDSIGHT_ENRICHMENT_BANK_ID" in compose
    assert "/etc/pantheon-hindsight-enrichment-hook.env" in compose
    assert ENRICHMENT_INSTALLER.exists()
    assert "retain.completed" in ENRICHMENT_INSTALLER.read_text(encoding="utf-8")

    html = (ROOT / "implementation" / "workspace_cockpit" / "static" / "index.html").read_text(encoding="utf-8")
    javascript = (ROOT / "implementation" / "workspace_cockpit" / "static" / "app.js").read_text(encoding="utf-8")
    graph_css = (ROOT / "implementation" / "workspace_cockpit" / "static" / "role_trace_graph.css").read_text(encoding="utf-8")

    assert "AFFAIRES" in html
    assert 'id="tool-links"' in html
    assert "SOURCE_ONLY" in javascript
    assert "SOURCE_MISSING" in javascript
    assert "Remplace" in javascript
    assert "Complète" in javascript
    assert "Ouvrir le fichier" in javascript
    assert 'workspaceUrl(`api/source?workspace=' in javascript
    assert 'workspaceUrl("api/navigation")' in javascript
    assert "loadNavigation" in javascript
    assert "Réconcilier avec Hermes" in javascript
    assert "X-Pantheon-Intent" in javascript
    assert "/reconcile-memory" in javascript
    assert "source NAS non ouverte" in javascript
    assert "Ouverture depuis le chemin NAS validé par le producer." in javascript
    assert "Cartouche dossier" in javascript
    assert "Sans _folder.md" in javascript
    assert 'href="role_trace_graph.css"' in html
    assert 'id="role-dialogue-events"' in html
    assert 'id="role-view-graph"' in html
    assert 'id="role-graph"' in html
    assert 'id="role-graph-lanes"' in html
    assert "Ordre observable" in html
    assert 'workspaceUrl("api/role-traces/latest")' in javascript
    assert "Last-Event-ID" in javascript
    assert 'roleView.stageEvents.set(event.stage_id, { ...event });' in javascript
    assert 'button.dataset.roleTraceView === roleView.activeView' in javascript
    assert 'parent_stage_id' not in javascript
    assert 'caused_by' not in javascript
    assert '.role-graph-lane' in graph_css
    assert '.role-graph-node[data-projection="derived_transient"]' in graph_css


def test_revision_relation_is_explicit_and_never_inferred_from_index_or_date(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Plan_IND_B.pdf").write_bytes(b"%PDF-old")
    (tmp_path / ".Plan_IND_B.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-plan-old
source: Plan_IND_B.pdf
index: B
document_date: 2026-09-20
---
# Plan ancien
""",
        encoding="utf-8",
    )
    (tmp_path / "Plan_CORRIGE_IND_B.pdf").write_bytes(b"%PDF-new")
    (tmp_path / ".Plan_CORRIGE_IND_B.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-plan-new
source: Plan_CORRIGE_IND_B.pdf
index: B
document_date: 2026-09-10
revision_mode: supersedes
revision_of: doc-plan-old
---
# Plan corrigé
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = {card["document_id"]: card for card in _cards(result) if card["kind"] == "document"}

    old = documents["doc-plan-old"]
    new = documents["doc-plan-new"]
    assert old["status"] == "COMPLETE"
    assert old["revision_mode"] is None
    assert old["revision_target_status"] == "NONE"
    assert new["status"] == "COMPLETE"
    assert new["index"] == "B"
    assert new["document_date"] == "2026-09-10"
    assert new["revision_mode"] == "supersedes"
    assert new["revision_of"] == "doc-plan-old"
    assert new["revision_target_present"] is True
    assert new["revision_target_status"] == "RESOLVED"
    assert new["hindsight_eligible"] is True


def test_higher_index_and_earlier_date_do_not_create_or_change_revision_semantics(tmp_path: Path) -> None:
    module = _module()
    for filename, document_id, index, document_date in (
        ("Notice_IND_B.pdf", "doc-b", "B", "2026-09-20"),
        ("Notice_IND_C.pdf", "doc-c", "C", "2026-09-01"),
    ):
        (tmp_path / filename).write_bytes(b"%PDF")
        (tmp_path / f".{filename}.md").write_text(
            f"""---
schema: pantheon/cartouche/v1
document_id: {document_id}
source: {filename}
index: {index}
document_date: {document_date}
---
# {filename}
""",
            encoding="utf-8",
        )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = [card for card in _cards(result) if card["kind"] == "document"]

    assert len(documents) == 2
    assert all(card["status"] == "COMPLETE" for card in documents)
    assert all(card["revision_mode"] is None for card in documents)
    assert all(card["revision_of"] is None for card in documents)
    assert all(card["revision_target_status"] == "NONE" for card in documents)


def test_supplement_relation_keeps_both_documents_independent_and_resolved(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "CCTP.pdf").write_bytes(b"%PDF-base")
    (tmp_path / ".CCTP.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-cctp
source: CCTP.pdf
index: A
---
# CCTP
""",
        encoding="utf-8",
    )
    (tmp_path / "ADDENDUM.pdf").write_bytes(b"%PDF-add")
    (tmp_path / ".ADDENDUM.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-addendum
source: ADDENDUM.pdf
index: A
revision_mode: supplements
revision_of: doc-cctp
---
# Addendum
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    documents = {card["document_id"]: card for card in _cards(result) if card["kind"] == "document"}

    assert documents["doc-cctp"]["status"] == "COMPLETE"
    assert documents["doc-addendum"]["status"] == "COMPLETE"
    assert documents["doc-addendum"]["revision_mode"] == "supplements"
    assert documents["doc-addendum"]["revision_target_status"] == "RESOLVED"


def test_invalid_or_self_revision_relation_is_check(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
revision_mode: supersedes
revision_of: doc-notice
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["kind"] == "document")

    assert card["status"] == "CHECK"
    assert card["revision_target_status"] == "INVALID"
    assert card["hindsight_eligible"] is True
    assert card["hindsight_representation_candidate"] == "source"
    assert card["document_identity_source"] == "workspace_path_fallback"
    assert any("ne peut pas référencer le document lui-même" in warning for warning in card["warnings"])


def test_missing_revision_target_is_observable_but_does_not_block_valid_document(tmp_path: Path) -> None:
    module = _module()
    (tmp_path / "Notice.pdf").write_bytes(b"%PDF")
    (tmp_path / ".Notice.pdf.md").write_text(
        """---
schema: pantheon/cartouche/v1
document_id: doc-notice
source: Notice.pdf
revision_mode: supersedes
revision_of: doc-archived-elsewhere
index: Z
document_date: 1999-01-01
---
# Notice
""",
        encoding="utf-8",
    )

    result = module.scan_workspaces([("Affaires", tmp_path)], max_depth=1)
    card = next(card for card in _cards(result) if card["kind"] == "document")

    assert card["status"] == "COMPLETE"
    assert card["revision_target_present"] is False
    assert card["revision_target_status"] == "MISSING"
    assert card["hindsight_eligible"] is True



def test_persisted_projection_reads_producer_owned_index_without_rescan(tmp_path: Path) -> None:
    module = _module()
    source = tmp_path / "Notice.pdf"
    source.write_bytes(b"%PDF")
    state = tmp_path.parent / f"{tmp_path.name}-projection.sqlite3"
    index = module.WorkspaceIndex(
        [("Affaires", tmp_path)],
        2,
        state,
        enable_watcher=False,
        producer=None,
    )
    written = index.reconcile("test-producer")
    assert written["document_count"] == 1

    projection = module.PersistedWorkspaceProjection([("Affaires", tmp_path)], state)
    snapshot = projection.snapshot()

    assert snapshot["document_count"] == 1
    assert snapshot["index_state"]["mode"] == "persisted-projection"
    assert snapshot["index_state"]["watcher"] == "external-producer"
    assert snapshot["index_state"]["last_reconcile_reason"] == "test-producer"
