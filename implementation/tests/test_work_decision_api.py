from fastapi.testclient import TestClient

from mvp_vertical.cockpit_shell import create_cockpit_app


def test_work_review_routes_are_installed_and_require_editor_key():
    app = create_cockpit_app(
        connect_fn=lambda: None,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
    )
    paths = {route.path for route in app.routes}
    assert "/work/issues/{issue_id}/review" in paths
    assert "/work/issues/{issue_id}/review/accept" in paths
    assert "/work/issues/{issue_id}/review/return" in paths
    assert "/work/issues/{issue_id}/decision" not in paths
    assert "/work/issues/{issue_id}/decision/validate" not in paths
    assert "/work/issues/{issue_id}/decision/refuse" not in paths
    assert not [path for path in paths if path.startswith("/v1/work-issues")]

    client = TestClient(app)
    response = client.get("/work/issues/issue-1/review")
    assert response.status_code == 401


def test_decision_request_action_module_is_loaded_and_keeps_hermes_out():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    cockpit = root / "mvp_vertical" / "cockpit"
    bootstrap = (cockpit / "live_bootstrap.js").read_text(encoding="utf-8")
    actions = (cockpit / "actions" / "decision_request_actions.js").read_text(encoding="utf-8")

    assert '"actions/decision_request_actions.js"' in bootstrap
    assert "../decision-requests/${encodeURIComponent(requestId)}" in actions
    assert "decision-requests/${encodeURIComponent(requestId)}/resolve" in actions
    assert 'identity_assurance: "declared"' in actions
    assert "work_issue_transitioned" not in actions
    assert "runtime_continuation_authorized" not in actions
    assert "handoff-submit" not in actions
    assert "handoff-admit" not in actions
    assert "/v1/work-issues/" not in actions
