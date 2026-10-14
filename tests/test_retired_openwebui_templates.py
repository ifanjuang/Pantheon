from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_openwebui_template_namespace_stays_retired() -> None:
    assert not (ROOT / "templates/openwebui").exists()

    registry = _read("templates/TEMPLATE_REGISTRY.md")
    scaffold = _read("templates/README.md")
    manifest = _read("templates/hermes/run_manifests/devis_reprise_run_manifest.template.yaml")

    for active_entry in (
        "| OpenWebUI template index |",
        "| Pantheon cockpit safe profile |",
        "| Request Hermes execution |",
        "| Candidate status banner |",
        "| Urgent fiche triage |",
    ):
        assert active_entry not in registry

    assert "former `templates/openwebui/` namespace is retired" in registry
    assert "openwebui/        cockpit templates" not in scaffold
    assert "external_hermes_runtime" in manifest
    assert "templates/openwebui/actions/request_hermes_execution.template.yaml" not in manifest


def test_devis_reprise_example_uses_current_runtime_owners() -> None:
    runbook = _read("docs/examples/vertical_devis_reprise/RUNBOOK.md")
    protocol = _read("docs/examples/vertical_devis_reprise/EXTERNAL_LIVE_RUN_PROTOCOL.md")

    for text in (runbook, protocol):
        assert "Hermes Web/dashboard" in text
        assert "Hermes Agent" in text
        assert "templates/openwebui/" not in text

    assert "Pantheon Cockpit does not become a second generic chat frontend" in runbook


def test_devis_reprise_manifest_uses_the_canonical_cost_review_skill() -> None:
    manifest = _read("templates/hermes/run_manifests/devis_reprise_run_manifest.template.yaml")
    assert "skill_candidate: construction-cost-review" in manifest
    assert "depends_on: [construction-cost-review]" in manifest
    assert "skill_candidate: quote-variation-review" not in manifest
