from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_openwebui_is_not_an_active_mcp_owner() -> None:
    source_map = _read("mcp-server/pantheon_mcp/source_map.py")
    consultation = _read("mcp-server/pantheon_mcp/consultation.py")

    assert '"openwebui-integration"' not in source_map
    assert '"openwebui": {' not in consultation
    assert '"cockpit", "exposure", "exposure-surface"' not in consultation
    assert '"pantheon-cockpit": {' in consultation
    assert '"hermes-client": {' in consultation


def test_exposure_verification_remains_client_agnostic() -> None:
    exposure = _read("mcp-server/pantheon_mcp/exposure.py")
    exposure_test = _read("mcp-server/tests/test_exposure.py")

    assert "component: runtime_client" in exposure
    assert '"component": "runtime_client"' in exposure_test
    assert '"component": "hermes_web"' in exposure_test
    assert "component: openwebui" not in exposure
