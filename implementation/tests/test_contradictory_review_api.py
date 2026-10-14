from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical.contradictory_review import report_from_payload
from mvp_vertical.contradictory_review_api import install_contradictory_review_routes

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "mvp_vertical" / "sql" / "003_contradictory_review_candidates.sql"
STORE = ROOT / "mvp_vertical" / "contradictory_review_store.py"


def _payload() -> dict:
    return {
        "rite_id": "AUTOCRITIQUE_CONTRADICTOIRE",
        "task_contract_ref": "task-contract:42",
        "trigger_reason": "material completion claim",
        "proposed_by": "ATHENA",
        "authorized_by": "ZEUS-candidate",
        "review_mode": "mode_standard",
        "review_posture": "independent_review",
        "candidate_id": "artifact:abc",
        "candidate_digest": "sha256:candidate",
        "binding_id": "hermes-contradictory-review",
        "binding_version": "1.0.0",
        "execution_id": "run-42",
        "claims": [
            {
                "claim_id": "claim-1",
                "statement": "The artifact parses.",
                "kind": "fact",
                "source_refs": ["artifact:abc"],
            }
        ],
        "observations": [
            {
                "observation_id": "obs-1",
                "claim_id": "claim-1",
                "support_status": "supported",
                "severity": "notice",
                "method": "fresh parser invocation",
                "detail": "Parser exited successfully.",
                "artifact_refs": ["artifact:abc"],
                "fresh_observation": True,
            }
        ],
    }


def _row(project_id: str, actor: str, payload: dict) -> dict:
    report = report_from_payload(payload).as_dict()
    return {
        "review_id": report["review_id"],
        "project_id": project_id,
        "task_contract_ref": report["task_contract_ref"],
        "candidate_id": report["candidate"]["candidate_id"],
        "candidate_digest": report["candidate"]["digest"],
        "execution_id": report["produced_by"]["execution_id"],
        "review_status": report["status"],
        "report_digest": "sha256:report",
        "report": report,
        "submitted_by": actor,
        "submitted_at": None,
    }


def _app() -> FastAPI:
    app = FastAPI()
    rows: dict[str, dict] = {}

    def with_connection(operation):
        return operation(object())

    def require_read_key():
        return None

    def require_hermes_key(authorization: str | None = None):
        if authorization == "refused":
            raise HTTPException(status_code=401, detail="invalid Hermes key")
        return None

    def persist(_conn, *, project_id, submitted_by, report_payload):
        row = _row(project_id, submitted_by, report_payload)
        rows[row["review_id"]] = row
        return row

    def get(_conn, review_id):
        return rows[review_id]

    def list_rows(_conn, project_id, *, limit):
        return [row for row in rows.values() if row["project_id"] == project_id][:limit]

    install_contradictory_review_routes(
        app,
        with_connection=with_connection,
        require_read_key=require_read_key,
        require_hermes_key=require_hermes_key,
        persist_fn=persist,
        get_fn=get,
        list_fn=list_rows,
    )
    return app


def test_hermes_can_submit_candidate_but_output_stays_non_authoritative():
    client = TestClient(_app())
    response = client.post(
        "/projects/project-1/contradictory-reviews",
        headers={"X-Pantheon-Actor": "hermes:reviewer"},
        json={"report": _payload()},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == "project-1"
    assert body["review_status"] == "review_completed"
    assert body["authority"] == {
        "is_evidence": False,
        "is_approval": False,
        "is_zeus_closure": False,
        "is_task_authorization": False,
    }
    assert body["report"]["authority"]["requires_zeus_closure"] is True


def test_submission_requires_an_explicit_actor_header():
    response = TestClient(_app()).post(
        "/projects/project-1/contradictory-reviews",
        json={"report": _payload()},
    )
    assert response.status_code == 422
    assert "X-Pantheon-Actor" in response.json()["detail"]


def test_candidate_can_be_listed_without_gaining_authority():
    client = TestClient(_app())
    created = client.post(
        "/projects/project-1/contradictory-reviews",
        headers={"X-Pantheon-Actor": "hermes:reviewer"},
        json={"report": _payload()},
    ).json()

    listed = client.get("/projects/project-1/contradictory-reviews").json()
    fetched = client.get(f"/contradictory-reviews/{created['review_id']}").json()

    assert listed["authority"] == "candidate_projection_only"
    assert len(listed["reviews"]) == 1
    assert fetched["review_id"] == created["review_id"]
    assert fetched["authority"]["is_approval"] is False


def test_legacy_v1_routes_are_not_mounted():
    app = _app()
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/v1/projects/{project_id}/contradictory-reviews" not in paths
    assert "/v1/contradictory-reviews/{review_id}" not in paths


def test_sql_storage_is_append_only_and_rejects_authority_promotion():
    sql = MIGRATION.read_text(encoding="utf-8")
    store = STORE.read_text(encoding="utf-8")

    assert "BEFORE UPDATE" in sql
    assert "BEFORE DELETE" in sql
    assert "append-only" in sql
    for field in ("is_evidence", "is_approval", "is_zeus_closure", "is_task_authorization"):
        assert field in sql
        assert field in store
    for forbidden in ("UPDATE contradictory_review_candidates", "DELETE FROM contradictory_review_candidates"):
        assert forbidden not in store
