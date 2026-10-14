"""The chokepoint on installing one reviewed canonical APU dossier.

`store_reviewed_dossier` writes the whole canonical Architecture Project
Understanding baseline for one Project in one shot. `review_ref` is a
caller-supplied string; nothing in `apu_owner.py` verifies it against a
completed review, because no table of such reviews exists there. What the
chokepoint adds is narrower than full verification: `_normalize_dossier`
folds `review_ref` into the same structure as the stable objects,
representations and claims, so the digest the decision must cover binds this
exact `review_ref` to this exact dossier as one unit — a decision taken over
one pairing cannot be replayed against a different dossier under the same
`review_ref`, or the same dossier under a different one. Same repair shape
`apu_write_preparation.append_authorization` already carries.
"""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_data, apu_owner, store
from mvp_vertical.policy_gate import StandInPolicyClient


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


class _UnreachablePolicyClient:
    def preflight(self, candidate):
        raise RuntimeError("decision point unreachable")

    def validate_decision(self, payload):  # pragma: no cover - never reached
        raise AssertionError("validation must not be attempted after a failed preflight")


def _dossier(project_id: str) -> dict:
    opening = _id("apu-opening")
    boundary = _id("apu-boundary")
    representation = _id("representation")
    return {
        "stable_objects": [
            {
                "stable_object_id": opening,
                "project_ref": project_id,
                "object_family": "element",
                "nomenclature": {
                    "internal_code": opening[-12:],
                    "display_name": f"Objet {opening[-8:]}",
                },
            },
            {
                "stable_object_id": boundary,
                "project_ref": project_id,
                "object_family": "element",
                "nomenclature": {
                    "internal_code": boundary[-12:],
                    "display_name": f"Objet {boundary[-8:]}",
                },
            },
        ],
        "source_representations": [
            {
                "representation_id": representation,
                "project_ref": project_id,
                "source_artifact_ref": "drawing.A",
                "source_kind": "drawing",
                "identifiers": [{"scheme": "drawing.fragment", "value": representation}],
                "observed_at": "2026-09-02T10:00:00Z",
                "binding_ref": "fixture.drawing",
                "adapter_version": "1.0",
                "freshness_token": f"{representation}:1",
                "proof_status": "candidate",
            }
        ],
        "attribute_claims": [],
        "relation_claims": [],
    }


def _decision_payload(
    *,
    project_id: str,
    dossier: dict,
    decision_id: str,
    decided_by: str = "human:architect",
    review_ref: str = "review:architect:2026-09-02",
) -> dict:
    digest = apu_owner._digest(
        apu_owner._normalize_dossier(
            project_id=project_id,
            review_ref=review_ref,
            **dossier,
        )
    )
    return {
        "decision": {
            "decision_id": decision_id,
            "decided_by": decided_by,
            "approval_level": "C3",
            "scope": {"scope_type": "project", "scope_id": project_id},
            "object_identity": f"apu_reviewed_dossier:{project_id}",
            "content_digest": digest,
            "expires_at": "2099-01-01T00:00:00Z",
            "signature": "signed-canonical-decision",
        }
    }


def test_the_digest_binds_review_ref_to_the_dossier_as_one_unit() -> None:
    """A decision covers this dossier claiming this review_ref, not either alone."""
    project_id = _id("project")
    dossier = _dossier(project_id)

    def _dossier_digest(review_ref: str, stable_objects=None) -> str:
        normalized = apu_owner._normalize_dossier(
            project_id=project_id,
            review_ref=review_ref,
            **{**dossier, "stable_objects": stable_objects or dossier["stable_objects"]},
        )
        return apu_owner._digest(normalized)

    base = _dossier_digest("review:architect:2026-09-02")
    assert base == _dossier_digest("review:architect:2026-09-02"), (
        "the same dossier under the same review_ref must digest identically"
    )
    assert base != _dossier_digest("review:architect:2026-09-03"), (
        "changing review_ref must change the digest a decision would have to "
        "be retaken against"
    )
    reordered_but_same_objects = list(reversed(dossier["stable_objects"]))
    assert base == _dossier_digest(
        "review:architect:2026-09-02", stable_objects=reordered_but_same_objects
    ), "normalization sorts stable_objects, so insertion order must not affect the digest"


@pytest.fixture
def conn():
    try:
        connection = store.connect()
        connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
        connection.commit()
    except Exception as exc:  # pragma: no cover - local unit-only lane
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _project(conn) -> str:
    project_id = _id("project")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id("code")[:30], "Projet gate"),
    )
    return project_id


def _has_state(conn, project_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM agency_apu_project_state WHERE project_id = %s",
            (project_id,),
        )
        return cur.fetchone() is not None


def test_an_allowed_import_carries_the_dossier_digest_to_the_decision_point(conn) -> None:
    project_id = _project(conn)
    dossier = _dossier(project_id)
    client = StandInPolicyClient()

    projection = apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        **dossier,
        review_ref="review:architect:2026-09-02",
        actor="human:architect",
        idempotency_key=_id("apu-bootstrap"),
        policy_client=client,
        decision_payload=_decision_payload(
            project_id=project_id,
            dossier=dossier,
            decision_id="decision-1",
            decided_by="human:architect",
        ),
    )
    conn.commit()

    assert projection["project_ref"] == project_id
    expected_digest = apu_owner._digest(
        apu_owner._normalize_dossier(
            project_id=project_id,
            review_ref="review:architect:2026-09-02",
            **dossier,
        )
    )
    expectation = client.last_decision["expectation"]
    assert expectation["expected_digest"] == expected_digest, (
        "the decision the PDP validated must cover this exact dossier bound "
        "to this exact review_ref"
    )
    assert expectation["object_identity"] == f"apu_reviewed_dossier:{project_id}"
    assert expectation["required_scope"] == {
        "scope_type": "project",
        "scope_id": project_id,
    }

    request = client.last_preflight["request"]
    assert request["writes_state"] is True
    assert request["external_effect"] is False


def test_a_refused_import_installs_no_apu_state(conn) -> None:
    project_id = _project(conn)
    dossier = _dossier(project_id)
    client = StandInPolicyClient(disposition="blocked_missing_task_contract")

    with pytest.raises(apu_owner.ApuOwnerRefused):
        apu_owner.store_reviewed_dossier(
            conn,
            project_id=project_id,
            **dossier,
            review_ref="review:architect:2026-09-02",
            actor="human:architect",
            idempotency_key=_id("apu-bootstrap"),
            policy_client=client,
            decision_payload=_decision_payload(
            project_id=project_id,
            dossier=dossier,
            decision_id="decision-2",
            decided_by="human:architect",
        ),
        )
    conn.rollback()
    assert not _has_state(conn, project_id), (
        "a refused import must leave the Project without APU owner state"
    )


def test_an_unreachable_decision_point_fails_closed(conn) -> None:
    project_id = _project(conn)
    dossier = _dossier(project_id)

    with pytest.raises(apu_owner.ApuOwnerPolicyUnavailable):
        apu_owner.store_reviewed_dossier(
            conn,
            project_id=project_id,
            **dossier,
            review_ref="review:architect:2026-09-02",
            actor="human:architect",
            idempotency_key=_id("apu-bootstrap"),
            policy_client=_UnreachablePolicyClient(),
            decision_payload=_decision_payload(
            project_id=project_id,
            dossier=dossier,
            decision_id="decision-3",
            decided_by="human:architect",
        ),
        )
    conn.rollback()
    assert not _has_state(conn, project_id)


def test_a_dossier_decided_by_a_non_human_is_refused(conn) -> None:
    """The stand-in refuses a system signer, and this is where that has to bite."""
    project_id = _project(conn)
    dossier = _dossier(project_id)

    with pytest.raises(apu_owner.ApuOwnerRefused):
        apu_owner.store_reviewed_dossier(
            conn,
            project_id=project_id,
            **dossier,
            review_ref="review:architect:2026-09-02",
            actor="hermes:profile",
            idempotency_key=_id("apu-bootstrap"),
            policy_client=StandInPolicyClient(),
            decision_payload=_decision_payload(
            project_id=project_id,
            dossier=dossier,
            decision_id="decision-4",
            decided_by="hermes:profile",
        ),
        )
    conn.rollback()
    assert not _has_state(conn, project_id)


def _run_cli(monkeypatch, capsys, tmp_path, env: dict[str, str | None]):
    from mvp_vertical import cli

    for key in ("MVP_POLICY_API_URL", "MVP_POLICY_API_KEY", "MVP_POLICY_ENFORCEMENT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        if value is not None:
            monkeypatch.setenv(key, value)
    dossier_path = tmp_path / "dossier.yaml"
    dossier_path.write_text(
        "project_id: project-x\n"
        "stable_objects: []\n"
        "source_representations: []\n"
        "attribute_claims: []\n"
        "relation_claims: []\n"
        "review_ref: review:architect:2026-09-02\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "mvp-vertical",
            "store-reviewed-dossier",
            "--dossier", str(dossier_path),
            "--actor", "human:architect",
            "--decision-ref", "decision-1",
            "--idempotency-key", "key-1",
        ],
    )
    monkeypatch.setattr(
        store,
        "connect",
        lambda *args, **kwargs: pytest.fail(
            "the CLI opened a connection before deciding it was allowed to install"
        ),
    )
    code = cli.main()
    return code, capsys.readouterr().err


def test_the_cli_refuses_to_install_without_a_decision_point(monkeypatch, capsys, tmp_path) -> None:
    code, stderr = _run_cli(monkeypatch, capsys, tmp_path, {})
    assert code == 1
    assert "decision point is not configured" in stderr
    assert "MVP_POLICY_ENFORCEMENT=disabled explicitly" in stderr


def test_the_cli_refuses_an_unreadable_enforcement_setting(monkeypatch, capsys, tmp_path) -> None:
    code, stderr = _run_cli(monkeypatch, capsys, tmp_path, {"MVP_POLICY_ENFORCEMENT": "maybe"})
    assert code == 1
    assert "must be 'required' or 'disabled'" in stderr
