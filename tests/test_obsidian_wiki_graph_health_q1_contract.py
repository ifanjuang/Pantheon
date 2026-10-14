from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "obsidian-wiki-graph-health-q1.yml"
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"
CORPUS = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"
OBSERVED = ROOT / "tests" / "fixtures" / "obsidian_graph_health_observed_v2026.08.6.json"


def _numeric_version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def test_q1_uses_canonical_obsidian_wiki_pin() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    observed = json.loads(OBSERVED.read_text(encoding="utf-8"))
    pin = registry["pins"]["obsidian-wiki"]
    provider = observed["provider"]

    assert pin["kind"] == "git"
    assert pin["env_prefix"] == "OBSIDIAN_WIKI"
    assert pin["repository"] == provider["repository"]
    assert _numeric_version(pin["version"]) == _numeric_version(provider["stable_release"])
    assert pin["ref"] == provider["stable_release_sha"]
    assert "export_external_qualification_pins.py" in raw
    assert "obsidian-wiki" in raw
    assert "${{ env.OBSIDIAN_WIKI_REPOSITORY }}" in raw
    assert "${{ env.OBSIDIAN_WIKI_REF }}" in raw
    assert pin["ref"] not in raw
    assert pin["version"] not in raw
    assert "latest" not in raw.lower()


def test_q1_executes_bounded_real_upstream_surfaces() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    assert 'python -m obsidian_wiki graph-analyse "$VAULT/projects/maison"' in raw
    assert '--path programme cctp' in raw
    assert 'python -m obsidian_wiki lint "$VAULT/projects/maison" --json' in raw
    assert 'graph-analyse "$VAULT" --top 20 --pretty' in raw
    assert "root-graph-negative-control.json" in raw
    assert "scoped-lint.exit-code.txt" in raw
    assert "actions/upload-artifact@v4" in raw
    assert "tests/test_obsidian_graph_health_observed.py" in raw


def test_q1_distinguishes_expected_lint_findings_from_harness_failure() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    assert "if exit_code not in {0, 1}:" in raw
    assert "unexpected obsidian-wiki lint exit code" in raw
    assert "lint did not produce valid JSON" in raw
    assert '{"status", "stats", "findings"}' in raw
    assert "exit 1 is not an expected finding result" in raw


def test_q1_materializes_same_corpus_and_preserves_report_only_boundary() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))

    assert corpus["pilot_id"] == "obsidian-graph-health-001"
    assert corpus["execution_status"] == "prepared_not_executed"
    assert corpus["workspace"]["authorized_scope"]["include_prefixes"] == ["projects/maison/"]
    assert "SCOPE_SENTINEL_7F3A" in json.dumps(corpus, ensure_ascii=False)

    assert 'corpus = json.loads(Path("monorepo/tests/fixtures/obsidian_graph_health_pilot.json")' in raw
    assert 'path.relative_to(vault).as_posix()' in raw
    assert 'for path in vault.rglob("*")' in raw
    assert '"added_files": added' in raw
    assert '"missing_tracked_files": missing' in raw
    assert '"modified_tracked_files": modified' in raw
    assert '"complete_vault_inventory_unchanged": not added and not missing and not modified' in raw
    assert '"pantheon_state_mutated": False' in raw
    assert '"evidence_admitted": False' in raw
    assert '"provider_binding_changed": False' in raw
    assert '"automatic_rewrite_qualified": False' in raw


def test_q1_does_not_enable_excluded_provider_surfaces() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    for forbidden in (
        "obsidian-wiki setup",
        "wiki-capture",
        "cache-update",
        "trust-record",
        "sync-setup",
        "uvicorn",
        "memory server",
    ):
        assert forbidden not in raw.lower()
