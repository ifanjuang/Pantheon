"""Stable route-identity guards for Work review and Decision Requests."""

from __future__ import annotations

from pathlib import Path

from mvp_vertical.cockpit_shell import create_cockpit_app


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


class _Connection:
    def close(self) -> None:
        pass


def test_mounted_work_routes_use_review_responsibility_paths() -> None:
    app = create_cockpit_app(
        connect_fn=_Connection,
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
    )
    mounted = {route.path for route in app.routes if getattr(route, "path", None)}

    assert "/work/issues" in mounted
    assert "/work/issues/{issue_id}/review" in mounted
    assert "/work/issues/{issue_id}/review/accept" in mounted
    assert "/work/issues/{issue_id}/review/return" in mounted
    assert "/work/issues/{issue_id}/decision" not in mounted
    assert "/work/issues/{issue_id}/decision/validate" not in mounted
    assert "/work/issues/{issue_id}/decision/refuse" not in mounted
    assert "/v1/projects/{parent_project_id}/work-issues" not in mounted
    assert not [path for path in mounted if path.startswith("/v1/work-issues")]


def test_active_cockpit_consumers_use_scoped_work_and_classified_decision_routes() -> None:
    consumers = (
        COCKPIT / "data" / "cockpit_data_loader.js",
        COCKPIT / "demo_bootstrap.js",
        COCKPIT / "actions" / "decision_request_actions.js",
    )
    for path in consumers:
        content = path.read_text(encoding="utf-8")
        assert "/v1/work-issues" not in content, path
        assert "/work-issues" not in content, path

    loader = consumers[0].read_text(encoding="utf-8")
    demo = consumers[1].read_text(encoding="utf-8")
    decision_actions = consumers[2].read_text(encoding="utf-8")
    assert "../work/scopes/project/${encoded}/issues" in loader
    assert "../work/issues?case_ref=${encoded}" not in loader
    assert "../decision-inbox?status=pending&limit=200" in loader
    assert "../decision-requests?status=pending&limit=200" not in loader
    assert "../agency/projects/${encoded}/decision-requests?status=pending&limit=100" in loader
    assert "routes.projectWorkIssues(projectId)" in demo
    assert "routes.projectDecisionRequests(projectId)" in demo
    assert 'url.pathname.endsWith("/work/issues")' not in demo
    assert "../decision-requests/${encodeURIComponent(requestId)}" in decision_actions
    assert "decision-requests/${encodeURIComponent(requestId)}/resolve" in decision_actions
    assert "/work/issues/" not in decision_actions


def test_document_and_knowledge_routes_remain_distinct_from_work() -> None:
    loader = (COCKPIT / "data" / "cockpit_data_loader.js").read_text(encoding="utf-8")
    actions = (COCKPIT / "actions" / "card_actions.js").read_text(encoding="utf-8")

    assert "../projects/${encoded}/documents" in loader
    assert "../projects/${encoded}/knowledge" in loader
    assert "../documents/${encodeURIComponent(id)}/chunks" in actions
    assert "../v1/projects/" not in loader
    assert "../v1/documents/" not in actions
