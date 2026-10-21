import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / "deployment" / "ubuntu" / "hindsight-bank-presets"
SCRIPT = ROOT / "deployment" / "ubuntu" / "configure-hindsight-bank"


def _preset(usage: str) -> dict:
    return json.loads((PRESETS / f"{usage}.json").read_text(encoding="utf-8"))["updates"]


def _merge_filter() -> str:
    lines = SCRIPT.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('expected="$(jq -c --argjson overlay'))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("' \"$PRESET\")\""))
    return "\n".join(lines[start + 1 : end])


def _merge(usage: str, overlay: dict) -> dict:
    jq = shutil.which("jq")
    if jq is None:
        pytest.skip("jq is required")
    result = subprocess.run(
        [jq, "-c", "--argjson", "overlay", json.dumps(overlay), _merge_filter(), str(PRESETS / f"{usage}.json")],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("usage", ["projects", "knowledge"])
def test_presets_declare_the_raw_text_strategy_without_changing_the_default(usage: str) -> None:
    payload = _preset(usage)
    # A named strategy a producer may request per file (raw passages, no fact extraction).
    # It is declared, never the bank's default: existing retains behave exactly as before.
    assert payload["retain_strategies"] == {
        "text": {"retain_extraction_mode": "chunks", "retain_chunk_size": 800}
    }
    assert "retain_default_strategy" not in payload
    assert payload["retain_extraction_mode"] == "concise"


def test_overlay_cannot_redefine_the_raw_text_strategy() -> None:
    merged = _merge("projects", {"mission_additions": {"retain_mission": "Local context."}})
    assert merged["retain_strategies"] == _preset("projects")["retain_strategies"]
    assert 'keys - ["mission_additions", "entity_labels"] | length == 0' in SCRIPT.read_text(encoding="utf-8")


def test_presets_exist_for_exactly_the_two_vault_usages() -> None:
    assert sorted(p.stem for p in PRESETS.glob("*.json")) == ["knowledge", "projects"]


@pytest.mark.parametrize("usage", ["projects", "knowledge"])
def test_presets_keep_audit_and_never_auto_consolidate(usage: str) -> None:
    payload = _preset(usage)
    assert payload["enable_observations"] is True
    assert payload["enable_auto_consolidation"] is False
    assert payload["audit_log_enabled"] is True
    assert payload["store_document_text"] is True
    assert payload["retain_extraction_mode"] == "concise"
    assert "not professional source authority" in payload["reflect_mission"]


def test_projects_preset_preserves_scope_and_source_authority_boundaries() -> None:
    payload = _preset("projects")
    assert "Never merge projects" in payload["observations_mission"]
    assert "unresolved references" in payload["retain_mission"]


def test_knowledge_preset_never_turns_references_into_project_obligations() -> None:
    payload = _preset("knowledge")
    assert "Never infer that a reference document applies to a specific project" in payload["retain_mission"]
    assert "never automatic obligations" in payload["reflect_mission"]
    assert "Never merge with project-scoped memories" in payload["observations_mission"]
    assert {label["key"] for label in payload["entity_labels"]} == {"document_family"}


def test_presets_carry_no_organization_specific_names() -> None:
    text = "".join((PRESETS / f"{u}.json").read_text(encoding="utf-8") for u in ("projects", "knowledge"))
    for name in ("IFJA", "KROQI", "MAF", "Legifrance"):
        assert name not in text


def test_without_overlay_the_preset_is_applied_unchanged() -> None:
    assert _merge("knowledge", {}) == _preset("knowledge")


def test_overlay_only_appends_missions_and_adds_labels() -> None:
    merged = _merge(
        "knowledge",
        {
            "mission_additions": {"retain_mission": "Local context."},
            "entity_labels": [
                {"key": "document_family", "values": [{"value": "regulatory"}, {"value": "internal"}]},
                {"key": "domain", "type": "value", "values": [{"value": "facade"}]},
            ],
        },
    )
    base = _preset("knowledge")
    assert merged["retain_mission"].startswith(base["retain_mission"])
    assert merged["retain_mission"].endswith("Organization context: Local context.")
    families = [v["value"] for v in next(l for l in merged["entity_labels"] if l["key"] == "document_family")["values"]]
    assert families.count("regulatory") == 1 and "internal" in families
    assert any(l["key"] == "domain" for l in merged["entity_labels"])
    for key in ("enable_auto_consolidation", "audit_log_enabled", "store_document_text"):
        assert merged[key] == base[key]


def test_configurator_rejects_overlay_keys_beyond_additions_and_uses_per_bank_endpoint() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'keys - ["mission_additions", "entity_labels"] | length == 0' in text
    assert 'BANK_ID="${BANK_ID:-PROJECTS}"' in text
    assert 'BANK_ID="${BANK_ID:-KNOWLEDGE}"' in text
    assert 'banks/$BANK_ID/config' in text
    assert "-X PATCH" in text
    assert "--check" in text and "--apply" in text


def test_configurator_refuses_an_overlay_that_changes_a_safety_setting(tmp_path: Path) -> None:
    if shutil.which("jq") is None:
        pytest.skip("jq is required")
    overlay = tmp_path / "overlay.json"
    overlay.write_text(json.dumps({"enable_auto_consolidation": True}), encoding="utf-8")
    result = subprocess.run(
        ["bash", str(SCRIPT), "--usage", "knowledge", "--overlay", str(overlay), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "overlay may only contain mission_additions and entity_labels" in result.stderr
