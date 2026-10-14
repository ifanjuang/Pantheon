from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "mvp_vertical" / "hermes_handoff_api.py"
CLIENT = ROOT / "mvp_vertical" / "cockpit" / "handoff" / "handoff_lifecycle.js"


def test_handoff_preview_and_submit_use_stable_routes_without_aliases() -> None:
    api = API.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")

    stable = {
        "/cockpit/hermes-handoffs/preview",
        "/cockpit/hermes-handoffs/submit",
    }
    retired = {
        "/v1/cockpit/hermes-handoffs/preview",
        "/v1/cockpit/hermes-handoffs/submit",
    }

    for route in stable:
        assert route in api
        assert f"..{route}" in client
    for route in retired:
        assert route not in api
        assert route not in client


def test_handoff_and_admission_migrations_do_not_absorb_runtime_execution() -> None:
    client = CLIENT.read_text(encoding="utf-8")

    assert "../cockpit/hermes-handoffs/" in client
    assert "/admissions`" in client
    assert "../cockpit/hermes-execution-admissions/" in client
    assert "../v1/cockpit/hermes-handoffs/" not in client
    assert "../v1/cockpit/hermes-execution-admissions/" not in client

    # Handoff submission and admission remain distinct from runtime execution.
    assert "Aucun HermesRun" in client
    assert "Pantheon n’a pas lancé Hermes" in client
    assert "/runs/start" not in client
    assert "/v1/hermes/execution-admissions" not in client
