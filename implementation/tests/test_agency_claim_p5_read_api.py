from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mvp_vertical import agency_claims, project_claim_conflicts
from mvp_vertical.agency_claims_api import install_agency_claim_routes


def _app() -> FastAPI:
    app = FastAPI()

    def with_connection(operation):
        return operation(object())

    install_agency_claim_routes(
        app,
        with_connection=with_connection,
        require_global_agency_read=lambda: None,
        require_human_agency_writer=lambda: "human",
        require_actor=lambda: "human:test",
    )
    return app


def _claim(claim_id: str = "claim.current") -> dict:
    return {
        "claim_id": claim_id,
        "project_id": "project-a",
        "claim_type": "budget",
        "value": 375000,
        "unit": "EUR",
        "backing_ref": {"entity_type": "information", "entity_id": "info-1"},
        "provenance": {
            "source_kind": "information",
            "source_ref": "information:info-1",
            "candidate_ref": None,
            "basis_refs": [
                {
                    "entity_type": "information",
                    "entity_id": "info-1",
                    "observed_revision": 2,
                    "observed_status": "acted",
                }
            ],
            "asserted_by": "human:test",
            "derivation_note": None,
        },
        "status": "source_backed",
        "certainty": "E3",
        "observed_at": "2026-02-01T09:00:00+00:00",
        "effective_at": "2026-02-01T00:00:00+00:00",
        "revision": 0,
        "supersedes": None,
        "note": None,
        "governance_refs": [],
    }


def _conflict() -> dict:
    return {
        "conflict_candidate_id": "pcc-0123456789abcdef01234567",
        "project_id": "project-a",
        "claim_type": "budget",
        "claim_refs": [{"claim_id": "claim.a"}, {"claim_id": "claim.b"}],
        "classification": "temporal_ambiguity",
        "comparison": {
            "effective_time_relation": "different_explicit_start",
            "basis_relation": "disjoint_structured_basis",
            "backing_relation": "different",
            "scope_relation": "same_project_same_claim_type_only",
        },
        "detector": {
            "detector_id": "project_claim_pairwise_conflict",
            "version": "1",
            "scan_scope": "active_unsuperseded_scalar_claims",
        },
        "limitations": ["candidate only", "human review required"],
        "authority": {
            "is_evidence": False,
            "is_decision": False,
            "resolves_conflict": False,
            "mutates_project_claim": False,
            "authorizes_effect": False,
            "merges_identity": False,
        },
    }


def _install_current_claim_mocks(monkeypatch, current: dict) -> None:
    monkeypatch.setattr(agency_claims, "list_project_claims", lambda conn, project_id: [current])
    monkeypatch.setattr(agency_claims, "active_project_claims", lambda conn, project_id: [current])
    monkeypatch.setattr(
        agency_claims,
        "project_claim_projection",
        lambda conn, project_id: ({"budget": 375000}, {"budget": current}),
    )


def test_current_claim_read_projects_temporal_provenance_and_conflict_candidates(monkeypatch) -> None:
    current = _claim()
    conflict = _conflict()
    _install_current_claim_mocks(monkeypatch, current)
    monkeypatch.setattr(
        project_claim_conflicts,
        "detect_project_claim_conflicts",
        lambda conn, project_id: [conflict],
    )

    response = TestClient(_app()).get("/agency/projects/project-a/claims")
    assert response.status_code == 200
    payload = response.json()
    assert payload["perspective"] == {
        "mode": "current",
        "business_time": None,
        "knowledge_time": None,
        "claim_scope": "active_unsuperseded",
    }
    assert payload["claim_values"]["budget"] == 375000
    assert payload["claim_refs"]["budget"]["provenance"]["basis_refs"][0]["entity_id"] == "info-1"
    assert payload["conflict_candidates"] == [conflict]
    assert payload["conflict_projection"] == {
        "status": "available",
        "scope": "active_unsuperseded_scalar_claims",
        "candidate_count": 1,
        "absence_of_candidates_inferred": True,
        "resolves_conflict": False,
    }
    assert payload["conflicts_resolved"] is False
    assert payload["authorization_inferred"] is False
    assert payload["evidence_inferred"] is False


def test_conflict_detector_refusal_does_not_hide_current_claims(monkeypatch) -> None:
    current = _claim()
    _install_current_claim_mocks(monkeypatch, current)

    def refuse(conn, project_id):
        raise project_claim_conflicts.ProjectClaimConflictError(
            "same-type Claims carry different governed units"
        )

    monkeypatch.setattr(project_claim_conflicts, "detect_project_claim_conflicts", refuse)

    response = TestClient(_app()).get("/agency/projects/project-a/claims")
    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_values"]["budget"] == 375000
    assert payload["conflict_candidates"] == []
    assert payload["conflict_projection"]["status"] == "unavailable"
    assert payload["conflict_projection"]["absence_of_candidates_inferred"] is False
    assert "different governed units" in payload["conflict_projection"]["reason"]


def test_business_and_knowledge_as_of_reuses_temporal_owner_without_current_conflicts(monkeypatch) -> None:
    historical = _claim("claim.historical")
    observed: dict[str, object] = {}

    def applicable(conn, project_id, business_time, *, knowledge_time=None):
        observed.update(
            project_id=project_id,
            business_time=business_time,
            knowledge_time=knowledge_time,
        )
        return [historical]

    monkeypatch.setattr(agency_claims, "applicable_project_claims_as_of", applicable)
    monkeypatch.setattr(
        project_claim_conflicts,
        "detect_project_claim_conflicts",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("current conflict detector must not be reused for an as-of perspective")
        ),
    )

    response = TestClient(_app()).get(
        "/agency/projects/project-a/claims/as-of",
        params={
            "business_time": "2026-03-01T00:00:00Z",
            "knowledge_time": "2026-02-15T12:00:00Z",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["claims"] == [historical]
    assert payload["perspective"]["mode"] == "business_and_knowledge_as_of"
    assert payload["perspective"]["business_time"].startswith("2026-03-01T00:00:00")
    assert payload["perspective"]["knowledge_time"].startswith("2026-02-15T12:00:00")
    assert payload["conflict_candidates"] == []
    assert payload["conflict_projection"]["status"] == "not_evaluated"
    assert payload["conflict_projection"]["absence_of_candidates_inferred"] is False
    assert "bounded to current active unsuperseded scalar Claims" in payload["conflict_projection"]["reason"]
    assert observed["project_id"] == "project-a"
    assert observed["business_time"] is not None
    assert observed["knowledge_time"] is not None


def test_knowledge_as_of_uses_recording_time_owner(monkeypatch) -> None:
    historical = _claim("claim.known")
    monkeypatch.setattr(
        agency_claims,
        "project_claims_known_as_of",
        lambda conn, project_id, knowledge_time: [historical],
    )

    response = TestClient(_app()).get(
        "/agency/projects/project-a/claims/as-of",
        params={"knowledge_time": "2026-02-15T12:00:00Z"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["perspective"]["mode"] == "knowledge_as_of"
    assert payload["perspective"]["business_time"] is None
    assert payload["claims"][0]["claim_id"] == "claim.known"


def test_as_of_read_requires_at_least_one_temporal_cutoff() -> None:
    response = TestClient(_app()).get("/agency/projects/project-a/claims/as-of")
    assert response.status_code == 422
    assert "business_time or knowledge_time is required" in response.json()["detail"]
