from __future__ import annotations

import ast
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MONOREPO_ROOT = ROOT.parent
WORKFLOW = MONOREPO_ROOT / ".github" / "workflows" / "implementation-hermes-runtime-lab-acceptance.yml"
VARIANT_WORKFLOW = (
    MONOREPO_ROOT
    / ".github"
    / "workflows"
    / "implementation-hermes-project-variant-lab.yml"
)
SEQUENCE = ROOT / "tools" / "run_hermes_runtime_lab_acceptance.sh"
VARIANT_SEQUENCE = ROOT / "tools" / "run_hermes_project_variant_lab_acceptance.sh"
HARNESS = ROOT / "tools" / "run_hermes_runtime_lab_acceptance.py"
FIXTURE = ROOT / "tools" / "hermes_runtime_lab_fixture.py"
SENTINEL_PLUGIN = (
    ROOT
    / "tests"
    / "fixtures"
    / "hermes_plugins"
    / "pantheon-effect-sentinel"
)
VARIANT_HARNESS = ROOT / "tools" / "run_hermes_project_variant_lab_acceptance.py"
VARIANT_FIXTURE = ROOT / "tools" / "hermes_project_variant_lab_fixture.py"
DISTRIBUTION = ROOT / "mvp_vertical" / "hermes_distribution.py"
DISTRIBUTION_AUTHORITY_REF = "1afbcdb25209fa6e411dc3792ddeb56447685ebf"


def _workflow(path: Path) -> tuple[str, dict]:
    raw = path.read_text(encoding="utf-8")
    value = yaml.safe_load(raw)
    assert isinstance(value, dict)
    return raw, value


def test_lab_acceptance_is_registry_pinned_and_ephemeral() -> None:
    raw, workflow = _workflow(WORKFLOW)
    assert workflow["name"] == "Hermes Runtime Lab Acceptance"
    assert "workflow_dispatch" in workflow[True]
    job = workflow["jobs"]["ephemeral-lab"]
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 35
    env = job["env"]
    assert "HERMES_RELEASE_COMMIT" not in env
    assert "HERMES_VERSION" not in env
    assert env["PANTHEON_DISTRIBUTION_AUTHORITY_REF"] == DISTRIBUTION_AUTHORITY_REF
    assert env["PANTHEON_RUN_PRETOOL_SENTINEL"] == "1"
    assert "PANTHEON_NEXT_REF" not in env
    assert env["HERMES_API_BASE"].endswith("/p/pantheon-governed")
    assert "export_external_qualification_pins.py" in raw
    assert "hermes-agent" in raw
    assert "${{ env.HERMES_REPOSITORY }}" in raw
    assert "${{ env.HERMES_REF }}" in raw
    assert "bash tools/run_hermes_runtime_lab_acceptance.sh" in raw
    assert "implementation/qualification/external-pins.json" in workflow[True]["pull_request"]["paths"]
    assert "implementation/tools/run_hermes_runtime_lab_acceptance.sh" in workflow[True]["pull_request"]["paths"]
    assert (
        "implementation/tests/fixtures/hermes_plugins/pantheon-effect-sentinel/**"
        in workflow[True]["pull_request"]["paths"]
    )
    assert "Expose transitional pantheon-mvp workspace alias" not in raw
    assert "path: distribution-authority" in raw
    assert "templates/hermes/distribution/distribution-lock.schema.yaml" in raw
    assert "secrets." not in raw
    assert "self-hosted" not in raw
    assert "artifact_digest:" not in raw
    assert "status: observed" not in raw
    assert "status: qualified" not in raw


def test_variant_lab_uses_same_bounded_distribution_authority_and_registry_pin() -> None:
    raw, workflow = _workflow(VARIANT_WORKFLOW)
    job = workflow["jobs"]["ephemeral-project-variant-lab"]
    env = job["env"]
    assert workflow["name"] == "Hermes Project Variant Lab"
    assert env["PANTHEON_DISTRIBUTION_AUTHORITY_REF"] == DISTRIBUTION_AUTHORITY_REF
    assert "PANTHEON_RUN_PRETOOL_SENTINEL" not in env
    assert "HERMES_RELEASE_COMMIT" not in env
    assert "HERMES_VERSION" not in env
    assert "PANTHEON_NEXT_REF" not in env
    assert "export_external_qualification_pins.py" in raw
    assert "hermes-agent" in raw
    assert "${{ env.HERMES_REPOSITORY }}" in raw
    assert "${{ env.HERMES_REF }}" in raw
    assert "Expose transitional pantheon-mvp workspace alias" not in raw
    assert "path: distribution-authority" in raw
    assert "templates/hermes/distribution/distribution-lock.schema.yaml" in raw


def test_active_runtime_lab_paths_are_version_neutral() -> None:
    active_paths = [WORKFLOW, VARIANT_WORKFLOW, SEQUENCE, VARIANT_SEQUENCE, HARNESS, FIXTURE, VARIANT_HARNESS, VARIANT_FIXTURE]
    assert all("020" not in path.name for path in active_paths)
    variant_harness = VARIANT_HARNESS.read_text(encoding="utf-8")
    variant_fixture = VARIANT_FIXTURE.read_text(encoding="utf-8")
    assert '"0.20.0"' not in variant_harness
    assert '"0.20.0"' not in variant_fixture
    assert 'baseline["hermes_version"]' in variant_harness
    assert 'os.environ.get("HERMES_VERSION"' in variant_fixture


def test_sequence_uses_supported_exact_source_artifact() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    assert raw.startswith("#!/usr/bin/env bash\nset -euo pipefail")
    assert "git archive --format=tar.gz" in raw
    assert "hermes-source-artifact.sha256" in raw
    assert 'grep -F "version = \\"$HERMES_VERSION\\""' in raw
    assert 'uv pip install --python "$HERMES_VENV/bin/python"' in raw
    assert '-e "$HERMES_SOURCE_DIR"' in raw
    assert 'IMPLEMENTATION_ROOT="$MONOREPO_ROOT/implementation"' in raw
    assert 'DISTRIBUTION_AUTHORITY_ROOT="$GITHUB_WORKSPACE/distribution-authority"' in raw
    assert 'PANTHEON_CONTEXT_PLUGIN_SOURCE="file://$MONOREPO_ROOT#implementation/hermes/plugins/pantheon-context-bridge"' in raw
    assert "$GITHUB_WORKSPACE/pantheon-mvp" not in raw
    assert "MVP_ROOT=" not in raw
    assert "NEXT_ROOT=" not in raw
    assert "python -m build" not in raw
    assert "bdist_wheel" not in raw
    assert "hermes-wheel" not in raw
    variant = VARIANT_SEQUENCE.read_text(encoding="utf-8")
    assert 'IMPLEMENTATION_ROOT="$GITHUB_WORKSPACE/monorepo/implementation"' in variant
    assert "$GITHUB_WORKSPACE/pantheon-mvp" not in variant
    assert "MVP_ROOT=" not in variant


def test_install_activation_run_and_rollback_remain_ordered() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    install = raw.index('hermes -p "$PROFILE" plugins install "$PLUGIN_SOURCE" --no-enable')
    inspect = raw.index("plugin-files.sha256")
    enable = raw.index('hermes -p "$PROFILE" plugins enable pantheon-context-bridge')
    observe = raw.index("pantheon-hermes observe")
    launch = raw.index("pantheon-hermes launch")
    reconcile = raw.index("pantheon-hermes reconcile")
    disable = raw.index('hermes -p "$PROFILE" plugins disable pantheon-context-bridge', enable)
    assert install < inspect < enable < observe < launch < reconcile < disable
    assert raw.count("capture-memory-status") == 3
    assert raw.count("--allowed-tool pantheon_context_manifest") == 2
    assert raw.count("--allowed-tool pantheon_context_entity") == 2
    assert "default API key unexpectedly authenticated the named profile route" in raw
    assert "profile route remained reachable after gateway rollback" in raw
    assert "trap cleanup EXIT" in raw


def test_gateway_listener_and_profile_plugin_policy_are_distinct() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    sequence = SEQUENCE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert '"api_server": ["pantheon_context"]' in raw
    assert '"cli": []' in raw
    assert '"platforms": {' in raw
    assert '"enabled": False' in raw
    assert '"API_SERVER_KEY": PROFILE_KEY' in raw
    assert '"gateway_plugin_scope": "profile_home"' in raw
    assert '"profile_plugin_copy": True' in raw
    assert 'PLUGIN_DIR="$HERMES_HOME/profiles/$PROFILE/plugins/pantheon-context-bridge"' in sequence
    assert 'hermes -p "$PROFILE" config set agent.disabled_toolsets \'["bfl"]\'' in sequence
    assert 'tool-policy-disabled.txt' in sequence
    assert 'hermes -p "$PROFILE" plugins install "$PLUGIN_SOURCE" --no-enable' in sequence
    assert 'hermes -p "$PROFILE" plugins enable pantheon-context-bridge' in sequence
    assert 'hermes plugins install "$PLUGIN_SOURCE" --no-enable' not in sequence


def test_distribution_receipt_exposes_only_verified_composition_fields() -> None:
    raw = DISTRIBUTION.read_text(encoding="utf-8")
    ast.parse(raw)
    projected = raw.split("def _verified_component_receipt", 1)[1].split("def validate", 1)[0]
    assert '"component_id": component["component_id"]' in projected
    assert '"content_digest": component["content_digest"]' in projected
    assert '"enabled_by_default": component["enabled_by_default"]' in projected
    assert '"source_repository"' not in projected
    assert '"capabilities"' not in projected


def test_harness_fails_closed_and_does_not_claim_target_acceptance() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'os.environ.get("HERMES_VERSION"' in raw
    assert '"status": "passed"' in raw
    assert '"target_installation_observed": False' in raw
    assert '"production_activated": False' in raw
    assert '"future_tasks_authorized": False' in raw
    assert '"result_accepted": False' in raw
    assert '"evidence_admitted": False' in raw
    assert '"source_artifact_digest": source_digest' in raw
    assert '"hermes_version": expected_version' in raw
    assert "EXPECTED_TOOLS" in raw
    assert "EXPECTED_COMPONENTS" in raw
    assert "X-Hermes-Session-Key reached a fixture" in raw
    assert 'rollback.get("plugin_disabled") is True' in raw
    assert "This qualifies an ephemeral GitHub-hosted laboratory installation only." in raw
    assert '"pre_tool_call_sentinel_exercised": sentinel_required' in raw
    assert '"pre_tool_call_block_observed": bool(' in raw
    assert '"pre_tool_call_exception_fail_open_observed": bool(' in raw
    assert '"pre_tool_call_is_pantheon_pep": False' in raw
    assert '"pre_tool_call_sentinel_claim_scope": (' in raw
    assert '"ephemeral_pinned_release_lab_only" if sentinel_required else None' in raw
    assert '"deployed_route_guard_qualified": False' in raw
    assert '"repeat_sentinel_on_claimed_deployed_route": sentinel_required' in raw
    assert "sentinel-observation.json" in raw


def test_fixture_uses_native_progressive_tool_disclosure() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'BRIDGE_TOOLS = {"tool_search", "tool_describe", "tool_call"}' in raw
    assert '"name": "pantheon_context_manifest"' in raw
    assert '"name": "pantheon_context_entity"' in raw
    assert '"queries": ["pantheon context manifest", "pantheon context entity"]' in raw
    assert raw.count('"tool_call"') >= 4
    assert "progressive tool checks failed" in raw
    assert "LAB_ACCEPTANCE_COMPLETED: progressive discovery" in raw


def test_fixture_honors_the_streaming_provider_contract() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'request_body.get("stream") is not True' in raw
    assert 'self.send_header("Content-Type", "text/event-stream")' in raw
    assert '"object": "chat.completion.chunk"' in raw
    assert '"finish_reason": finish_reason' in raw
    assert 'b"data: [DONE]\\n\\n"' in raw
    assert 'stream_options.get("include_usage") is True' in raw
    assert "_send_completion(body, response)" in raw
    assert "_disable_streaming" not in raw
    assert '"stream": False' not in raw


def test_fixture_is_local_bounded_and_exercises_context_refusal() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'default="127.0.0.1"' in raw
    assert "ThreadingHTTPServer" in raw
    assert "pantheon_context_manifest" in raw
    assert "pantheon_context_entity" in raw
    assert "project-outside" in raw
    assert "entity is outside the admitted Context Pack" in raw
    assert '"evidence_admitted": False' in raw
    assert '"result_accepted": False' in raw
    assert '"project_mutated": False' in raw
    assert "requests" not in raw
    assert "subprocess" not in raw


# Keep this path in the runtime-lab trigger set: changing the proof ceiling must
# re-run the exact pinned Hermes sentinel characterization, not only static CI.
def test_pre_tool_sentinel_is_lab_only_and_exercises_real_runs_route() -> None:
    sequence = SEQUENCE.read_text(encoding="utf-8")
    fixture = FIXTURE.read_text(encoding="utf-8")
    plugin = (SENTINEL_PLUGIN / "__init__.py").read_text(encoding="utf-8")
    manifest = yaml.safe_load(
        (SENTINEL_PLUGIN / "plugin.yaml").read_text(encoding="utf-8")
    )

    ast.parse(plugin)
    assert manifest["name"] == "pantheon-effect-sentinel"
    assert manifest["provides_tools"] == ["pantheon_effect_sentinel"]
    assert manifest["provides_hooks"] == ["pre_tool_call"]

    assert "implementation/tests/fixtures/hermes_plugins/pantheon-effect-sentinel" in sequence
    assert 'if [ "${PANTHEON_RUN_PRETOOL_SENTINEL:-0}" = "1" ]; then' in sequence
    assert 'hermes plugins validate "$SENTINEL_SOURCE_DIR" --json' in sequence
    assert 'hermes -p "$PROFILE" plugins doctor pantheon-effect-sentinel --ci' in sequence
    assert '"$HERMES_API_BASE/v1/runs"' in sequence
    assert "EXPECT_BLOCK" in sequence
    assert "EXPECT_FAIL_OPEN" in sequence
    assert 'test ! -e "$PANTHEON_SENTINEL_SINK"' in sequence
    assert 'test -f "$PANTHEON_SENTINEL_SINK"' in sequence
    assert '"pantheon_pep_qualified_by_this_test": False' in sequence
    assert '"claim_scope": "ephemeral_pinned_release_lab_only"' in sequence
    assert '"deployed_route_guard_qualified": False' in sequence
    assert '"repeat_on_claimed_deployed_route": True' in sequence
    assert "sentinel_plugin_disabled" in sequence
    assert "sentinel_tool_policy_restored" in sequence

    assert 'SENTINEL_MARKER = "PANTHEON_EFFECT_SENTINEL_V1"' in fixture
    assert '"pantheon effect sentinel"' in fixture
    assert "SENTINEL_BLOCK_CONFIRMED" in fixture
    assert "SENTINEL_FAIL_OPEN_CONFIRMED" in fixture

    assert 'ctx.register_hook("pre_tool_call", _pre_tool_call)' in plugin
    assert 'if mode == "block":' in plugin
    assert 'if mode == "raise":' in plugin
    assert 'raise RuntimeError("PANTHEON_SENTINEL_HOOK_EXCEPTION")' in plugin
    assert '"effect_ran": True' in plugin
    assert "governed_effect" not in plugin
    assert "Decision" not in plugin
    assert "Evidence" not in plugin


def test_sentinel_qualification_runs_after_bounded_context_proof_and_before_rollback() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    reconcile = raw.index('pantheon-hermes reconcile')
    sentinel = raw.index('phase "Qualify pre_tool_call with a synthetic effect sentinel"')
    restore = raw.index('phase "Restore governed profile after sentinel qualification"')
    disable_context = raw.index('hermes -p "$PROFILE" plugins disable pantheon-context-bridge')
    assert reconcile < sentinel < restore < disable_context
