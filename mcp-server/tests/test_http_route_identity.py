"""Route-identity guard for the bounded Pantheon policy HTTP adapter."""

from __future__ import annotations

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp.http_api import create_app  # noqa: E402


def test_mounted_policy_routes_use_stable_responsibility_paths() -> None:
    app = create_app(api_key="route-identity-test", enable_docs=False)
    mounted = sorted(
        route.path
        for route in app.routes
        if getattr(route, "path", None)
    )

    assert mounted
    assert not [path for path in mounted if path == "/v1" or path.startswith("/v1/")]
    assert "/meta" in mounted
    assert "/policy/requests:classify" in mounted
    assert "/context-packs:validate" in mounted


def test_active_policy_contracts_do_not_publish_generation_prefixed_routes() -> None:
    stable_only = (
        MODULE_DIR / "pantheon_mcp" / "http_api.py",
        MODULE_DIR / "docs" / "HTTP_API_CONTRACT.md",
        MODULE_DIR / "docs" / "CONSULTATION_CONTRACT.md",
        REPO_ROOT / "templates" / "hermes" / "connection" / "pantheon_policy_http.template.yaml",
        REPO_ROOT / "docs" / "install" / "COMMON_BASELINE_RUNBOOK.md",
    )
    for path in stable_only:
        content = path.read_text(encoding="utf-8")
        assert "/v1/" not in content, path


def test_contract_revision_is_not_confused_with_route_identity() -> None:
    app = create_app(api_key="route-identity-test", enable_docs=False)
    assert app.version == "1.0.0-candidate"
    contract = (MODULE_DIR / "docs" / "HTTP_API_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    assert "pantheon.policy.v1" in contract
