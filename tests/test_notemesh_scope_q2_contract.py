"""Static contract for the qualification-only NoteMesh caller-bounded scope Q2."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "notemesh-scope-q2.yml"
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"
CORPUS = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"


def test_q2_reuses_q1_pin_and_existing_scope_oracle_without_redeclaring_pin() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    pin = registry["pins"]["notemesh"]

    assert pin["kind"] == "git"
    assert pin["env_prefix"] == "NOTEMESH"
    assert pin["repository"] == "ChangeNode/notemesh"
    assert pin["version"]
    assert len(pin["ref"]) == 40
    assert corpus["workspace"]["authorized_scope"]["include_prefixes"] == ["projects/maison/"]
    assert corpus["workspace"]["authorized_scope"]["explicitly_out_of_scope_prefixes"] == [
        "projects/autre-projet/"
    ]


def test_q2_bounds_provider_input_before_notemesh_execution() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for invariant in (
        'include_prefixes = corpus["workspace"]["authorized_scope"]["include_prefixes"]',
        "source_vault = out / \"source-vault\"",
        "scoped_vault = out / \"data\" / \"vault\"",
        "if not any(rel.startswith(prefix) for prefix in include_prefixes):",
        "shutil.copy2(source, target)",
        "scope-manifest.json",
    ):
        assert invariant in workflow

    materialize_pos = workflow.index("Materialize whole synthetic workspace and caller-bounded projection")
    execute_pos = workflow.index("Execute exact NoteMesh indexer against bounded projection")
    assert materialize_pos < execute_pos


def test_q2_does_not_rely_on_post_query_filtering() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "filtered_results" not in workflow
    assert "WHERE path LIKE" not in workflow
    assert "DELETE FROM notes" not in workflow
    assert "DELETE FROM attachments" not in workflow
    assert "provider input is bounded before indexing" in workflow


def test_q2_executes_real_upstream_indexer() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for invariant in (
        "pnpm --dir notemesh install --frozen-lockfile",
        'import { db } from "../src/server/db";',
        'import { indexer } from "../src/server/vault/indexer";',
        "await indexer().rebuild();",
        'SELECT source_path, target, resolved_path FROM links',
    ):
        assert invariant in workflow


def test_q2_proves_negative_controls_are_absent_from_provider_view() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for forbidden in (
        "index.md",
        "_raw/hypothese-non-verifiee.md",
        "projects/autre-projet/sentinel-hors-perimetre.md",
        "sources/cctp-original.pdf",
        "evidence/admitted-cctp-record",
        "SCOPE_SENTINEL_7F3A",
    ):
        assert forbidden in workflow

    for observation in (
        "all_indexed_paths_within_scope",
        "sentinel_absent",
        "raw_absent",
        "bookkeeping_absent",
        "source_absent",
        "evidence_absent",
        "scope_widening_errors",
    ):
        assert observation in workflow


def test_q2_preserves_useful_structural_observation_and_report_only_boundary() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for invariant in (
        "true_missing_link_observed",
        "attachment_aware_resolution_observed",
        "destructive_write_attempts",
        "authority_promotion_errors",
        "projection != authorization",
        "workspace note != Evidence",
        "provider path != governed identity",
        "provider input is bounded before indexing",
    ):
        assert invariant in workflow

    assert "create_note" not in workflow
    assert "update_note" not in workflow
    assert "delete_note" not in workflow
    assert "vault:write" not in workflow
    assert "indexer().start()" not in workflow
