from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_COMPOSE = ROOT / "compose.phase-b.yaml"


def _compose(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_phase_b_core_uses_external_ai_net_and_current_services_only():
    compose = _compose(CORE_COMPOSE)
    services = compose["services"]

    assert compose["networks"]["ai-net"]["external"] is True
    assert compose["networks"]["ai-net"]["name"] == "ai-net"

    expected = {"pgvector", "docling", "cockpit-api", "hermes"}
    assert set(services) == expected
    for name in expected:
        assert "ai-net" in services[name]["networks"]
        assert "ports" not in services[name]


def test_phase_b_core_has_no_retired_document_runtime_bindings():
    text = CORE_COMPOSE.read_text(encoding="utf-8").lower()
    for token in (
        "paperless",
        "document-runtime-observer",
        "mvp_document_source_binding",
        "pantheon_paperless_gateway_url",
    ):
        assert token not in text


def test_phase_b_cockpit_does_not_receive_backing_policy_secrets():
    services = _compose(CORE_COMPOSE)["services"]
    cockpit_env = services["cockpit-api"]["environment"]
    assert "PANTHEON_POLICY_API_KEY" not in cockpit_env
    assert "PANTHEON_DECISION_ISSUER_SIGNING_SECRET" not in cockpit_env
    assert "PANTHEON_DECISION_ISSUER_KEYS_PATH" not in cockpit_env


def test_phase_b_cockpit_uses_reviewable_build_image():
    service = _compose(CORE_COMPOSE)["services"]["cockpit-api"]
    assert service["build"] == {"context": ".", "dockerfile": "Dockerfile"}
    assert service["image"] == (
        "${PANTHEON_MVP_IMAGE_NAME:-pantheon-mvp}:"
        "${PANTHEON_MVP_IMAGE_TAG:-phase-b}"
    )
