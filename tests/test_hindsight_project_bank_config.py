import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "deployment" / "ubuntu" / "hindsight-project-bank-config.json"
SCRIPT = ROOT / "deployment" / "ubuntu" / "configure-hindsight-project-bank"


def test_project_bank_config_preserves_scope_and_source_authority_boundaries() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))["updates"]
    assert payload["enable_observations"] is True
    assert payload["audit_log_enabled"] is True
    assert payload["store_document_text"] is True
    assert payload["retain_extraction_mode"] == "concise"
    assert "Never merge projects" in payload["observations_mission"]
    assert "unresolved references" in payload["retain_mission"]
    assert "not professional source authority" in payload["reflect_mission"]


def test_project_bank_configurator_uses_per_bank_config_endpoint() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "HINDSIGHT_PROJECT_BANK_ID:-AGENCY_PROJECTS" in text
    assert 'banks/$BANK_ID/config' in text
    assert "-X PATCH" in text
    assert "--check" in text and "--apply" in text
