from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "architecture" / "WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md"


def _architecture() -> str:
    return ARCH.read_text(encoding="utf-8")


def test_affaires_workspace_has_one_source_cartouche_contract() -> None:
    text = _architecture()

    for invariant in (
        "NAS / AFFAIRES",
        "Linux AFFAIRES indexer/sync daemon",
        "source.ext = source",
        ".source.ext.md = cartouche",
        "watcher   = responsiveness",
        "reconcile = convergence guarantee",
        "folder != governed identity",
        "memory != Evidence",
        "source bytes != cartouche interpretation",
        "schema: pantheon/cartouche/v1",
        "case-sensitive on Linux",
        "DUPLICATE_DOCUMENT_ID",
        "mounted on the Linux compute host",
        "The filesystem watcher belongs to the AFFAIRES daemon, not to Hindsight.",
        "inotify observed != convergence proof",
        "no separate JSON/YAML business sidecar is required",
    ):
        assert invariant in text


def test_existing_workspace_cockpit_is_the_single_projection_owner() -> None:
    text = _architecture()

    assert "The existing `implementation/workspace_cockpit` is the component to evolve." in text
    assert "Do not add a parallel filesystem Cockpit." in text
    assert "Cockpit watcher\n+\nHindsight watcher" in text
    assert "AFFAIRES daemon" in text
    assert "maintains Cockpit index" in text
    assert "emits Hindsight synchronization operations" in text


def test_obsolete_workspace_stack_is_historical_not_selected_target() -> None:
    text = _architecture()
    marker = "## 19. Historical topology"
    assert marker in text
    historical = text.split(marker, 1)[1]

    assert "no longer required by the selected AFFAIRES target" in historical
    for obsolete in (
        "Obsidian",
        "Self-hosted LiveSync",
        "CouchDB",
        "headless LiveSync filesystem mirror",
        "hindsight-obsidian-sync",
        "document.yaml as the default business sidecar",
    ):
        assert obsolete in historical


def test_cartouche_does_not_absorb_governed_authorities() -> None:
    text = _architecture()

    for invariant in (
        "project hint != governed project_id",
        "index label != professional currentness",
        "summary != source claim",
        "Information\n= canonical Postgres-backed Information object",
        "Do not make Cockpit rendering itself persistence.",
        "no cartouche/retrieval result is promoted into Evidence automatically",
    ):
        assert invariant in text
