from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical import decision_request_views
from mvp_vertical.decision_inbox_api import install_decision_inbox_routes


def test_global_decision_inbox_is_unclassified_only(monkeypatch) -> None:
    app = FastAPI()

    def with_connection(operation):
        return operation(None)

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer read-secret":
            raise HTTPException(status_code=401, detail="invalid read key")

    observed = {}

    def list_unclassified(_conn, *, status, limit):
        observed.update(status=status, limit=limit)
        return [
            {
                "decision_request": {
                    "request_id": "request-unclassified",
                    "project_ref": None,
                    "status": "pending",
                }
            }
        ]

    monkeypatch.setattr(
        decision_request_views,
        "list_unclassified_requests",
        list_unclassified,
    )
    install_decision_inbox_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
    )

    response = TestClient(app).get(
        "/decision-inbox?status=pending&limit=25",
        headers={"Authorization": "Bearer read-secret"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert observed == {"status": "pending", "limit": 25}
    assert payload["unclassified_only"] is True
    assert payload["project_ref"] is None
    assert payload["agency_decision_owner"] is False
    assert payload["decision_requests"][0]["decision_request"]["project_ref"] is None
