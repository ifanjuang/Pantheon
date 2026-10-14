import json

from mvp_vertical.hermes_tool_inventory import normalize_hermes_inventory, observe_hermes_tool_inventory


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def read(self, _limit):
        return json.dumps(self.payload).encode()


def test_normalizes_skills_toolsets_and_api_without_governance_promotion():
    rows = normalize_hermes_inventory(
        skills_payload={"skills": [{"name": "web-research", "enabled": True, "version": "1.2"}]},
        toolsets_payload=[{"name": "research", "configured": True, "enabled": True, "tools": ["search", "fetch"]}],
        capabilities_payload={"features": {"run_submission": True, "dangerous": False}},
        observed_at="2026-07-26T20:00:00Z",
    )
    assert [row["tool_id"] for row in rows] == [
        "hermes-skill-web-research",
        "hermes-toolset-research",
        "hermes-api-server",
    ]
    assert all(row["governance_state"] == "unreviewed" for row in rows)
    assert all(row["activation_state"] == "not_activated" for row in rows)
    assert rows[0]["provenance_mode"] == "hermes_dynamic_skill"
    assert rows[1]["capabilities"] == ["search", "fetch"]
    assert rows[2]["capabilities"] == ["run_submission"]


def test_observer_reads_only_reviewed_get_surfaces():
    seen = []
    payloads = {
        "/v1/skills": {"skills": [{"name": "alpha"}]},
        "/v1/toolsets": [],
        "/v1/capabilities": {"features": {}},
    }

    def opener(request, timeout):
        seen.append((request.full_url, request.get_method(), request.headers.get("Authorization"), timeout))
        path = request.full_url.removeprefix("http://hermes:8642")
        return Response(payloads[path])

    result = observe_hermes_tool_inventory("http://hermes:8642", "secret", opener=opener)
    assert result["status"] == "observed"
    assert [entry[1] for entry in seen] == ["GET", "GET", "GET"]
    assert [entry[0].split("8642", 1)[1] for entry in seen] == [
        "/v1/skills",
        "/v1/toolsets",
        "/v1/capabilities",
    ]
    assert all(entry[2] == "Bearer secret" for entry in seen)
    assert result["write_effect"] is False
    assert result["activation_changed"] is False
    assert result["authority_effect"] == "none"


def test_missing_key_does_not_invent_runtime_state():
    result = observe_hermes_tool_inventory("http://hermes:8642", "")
    assert result == {
        "status": "not_configured",
        "observed_at": result["observed_at"],
        "capabilities": [],
    }
