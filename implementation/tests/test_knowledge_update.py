"""Signed and human-confirmed Knowledge UPDATE gate tests."""

from __future__ import annotations

import pytest

from mvp_vertical import knowledge, knowledge_update


CARD = {
    "knowledge_id": "knowledge.coverage",
    "parent_project_id": "project-verger",
    "title": "Choix de couverture",
    "review_status": "needs_review",
    "version": 3,
}
CURRENT = "# Couverture\n\nLe zinc reste à confirmer.\n"
PROPOSED = "# Couverture\n\nLe client confirme le zinc naturel.\n"
GATE_REFS = {
    "task_contract_ref": "task-contract:reviewed-001",
    "evidence_pack_candidate_ref": "evidence-pack-candidate:001",
    "human_decision_ref": "human-decision:001",
}


class _Connection:
    pass


class _RecordingPolicyClient:
    def __init__(self) -> None:
        self.preflight_payload = None
        self.decision_payload = None

    def preflight(self, candidate):
        self.preflight_payload = candidate
        return {
            "policy_disposition": "eligible_with_gate_signals_unverified",
            "missing_requirements": [],
            "external_effect_allowed": False,
            "canonical_effect_allowed": False,
            "gate_signal_validation_performed": False,
            "replay_guard_required": False,
        }

    def validate_decision(self, payload):
        self.decision_payload = payload
        return {"verdict": "valid", "findings": []}


class _UnavailablePolicyClient:
    def preflight(self, _candidate):
        raise OSError("PDP offline")

    def validate_decision(self, _payload):  # pragma: no cover - preflight fails first
        raise AssertionError("decision validation must not run")


def _patch_reads(monkeypatch, *, card=None, markdown=CURRENT):
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_card",
        lambda _conn, _knowledge_id: dict(card or CARD),
    )
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_markdown",
        lambda _conn, _knowledge_id: markdown,
    )


def _preview(monkeypatch):
    _patch_reads(monkeypatch)
    return knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        actor="ifan.juang",
        signing_secret="editor-secret",
        now=1_000,
    )


def _policy_apply_args(preview: dict) -> dict:
    return {
        "conn": _Connection(),
        "parent_project_id": "project-verger",
        "knowledge_id": "knowledge.coverage",
        "proposed_markdown": PROPOSED,
        "expected_version": 3,
        "base_markdown_digest": preview["base_markdown_digest"],
        "actor": "ifan.juang",
        "signing_secret": "editor-secret",
        "confirmation_token": preview["confirmation"]["token"],
        "confirmation_expires_at": preview["confirmation"]["expires_at"],
        "confirmation_phrase": "CONFIRMER UPDATE",
        "idempotency_key": "update-knowledge-policy-0001",
        "now": 1_010,
        **GATE_REFS,
    }


def test_preview_returns_signed_diff_without_writing(monkeypatch) -> None:
    _patch_reads(monkeypatch)
    preview = knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        actor="ifan.juang",
        signing_secret="editor-secret",
        now=1_000,
    )

    assert preview["status"] == "confirmation_required"
    assert preview["effect"] == "UPDATE"
    assert preview["target"]["current_version"] == 3
    assert preview["target"]["proposed_review_status"] == "needs_review"
    assert "-Le zinc reste à confirmer." in preview["diff"]
    assert "+Le client confirme le zinc naturel." in preview["diff"]
    assert preview["confirmation"]["phrase"] == "CONFIRMER UPDATE"
    assert preview["confirmation"]["expires_at"] == 1_300
    assert preview["identity"]["assurance"] == "partial"


def test_apply_verifies_exact_preview_and_delegates_transactional_write(monkeypatch) -> None:
    _patch_reads(monkeypatch)
    preview = knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        actor="ifan.juang",
        signing_secret="editor-secret",
        review_status="needs_review",
        now=1_000,
    )
    observed = {}

    def revise(_conn, **values):
        observed.update(values)
        return {**CARD, "version": 4, "markdown_digest": "new"}

    monkeypatch.setattr(knowledge, "revise_knowledge", revise)
    result = knowledge_update.apply_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        base_markdown_digest=preview["base_markdown_digest"],
        actor="ifan.juang",
        signing_secret="editor-secret",
        confirmation_token=preview["confirmation"]["token"],
        confirmation_expires_at=preview["confirmation"]["expires_at"],
        confirmation_phrase="CONFIRMER UPDATE",
        idempotency_key="update-knowledge-0001",
        review_status="needs_review",
        now=1_010,
    )

    assert result["status"] == "applied"
    assert result["knowledge"]["version"] == 4
    assert "effect_binding" not in result
    assert observed == {
        "knowledge_id": "knowledge.coverage",
        "markdown": PROPOSED,
        "expected_version": 3,
        "actor": "ifan.juang",
        "actor_kind": "human",
        "idempotency_key": "update-knowledge-0001",
        "review_status": None,
    }


def test_apply_rejects_expiry_tampering_scope_and_stale_markdown(monkeypatch) -> None:
    _patch_reads(monkeypatch)
    preview = knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        actor="ifan.juang",
        signing_secret="editor-secret",
        now=1_000,
    )
    common = dict(
        conn=_Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=PROPOSED,
        expected_version=3,
        base_markdown_digest=preview["base_markdown_digest"],
        actor="ifan.juang",
        signing_secret="editor-secret",
        confirmation_token=preview["confirmation"]["token"],
        confirmation_expires_at=preview["confirmation"]["expires_at"],
        confirmation_phrase="CONFIRMER UPDATE",
        idempotency_key="update-knowledge-0002",
    )

    with pytest.raises(knowledge_update.KnowledgeUpdateExpired):
        knowledge_update.apply_knowledge_update(**common, now=1_301)

    with pytest.raises(knowledge_update.KnowledgeUpdateError, match="immutable UPDATE"):
        knowledge_update.apply_knowledge_update(
            **{**common, "proposed_markdown": PROPOSED + "\nAltération"}, now=1_010
        )

    _patch_reads(monkeypatch, card={**CARD, "parent_project_id": "project-other"})
    with pytest.raises(knowledge_update.KnowledgeUpdateError, match="exact opened project"):
        knowledge_update.apply_knowledge_update(**common, now=1_010)

    _patch_reads(monkeypatch, markdown=CURRENT + "\nChangement concurrent")
    with pytest.raises(knowledge.StaleKnowledgeWrite, match="changed after"):
        knowledge_update.apply_knowledge_update(**common, now=1_010)


def test_preview_refuses_noop_stale_version_and_status_change(monkeypatch) -> None:
    _patch_reads(monkeypatch)
    with pytest.raises(knowledge_update.KnowledgeUpdateError, match="no material change"):
        knowledge_update.preview_knowledge_update(
            _Connection(),
            parent_project_id="project-verger",
            knowledge_id="knowledge.coverage",
            proposed_markdown=CURRENT,
            expected_version=3,
            actor="ifan.juang",
            signing_secret="editor-secret",
        )
    with pytest.raises(knowledge.StaleKnowledgeWrite, match="current 3"):
        knowledge_update.preview_knowledge_update(
            _Connection(),
            parent_project_id="project-verger",
            knowledge_id="knowledge.coverage",
            proposed_markdown=PROPOSED,
            expected_version=2,
            actor="ifan.juang",
            signing_secret="editor-secret",
        )
    with pytest.raises(knowledge_update.KnowledgeUpdateError, match="separate governed"):
        knowledge_update.preview_knowledge_update(
            _Connection(),
            parent_project_id="project-verger",
            knowledge_id="knowledge.coverage",
            proposed_markdown=PROPOSED,
            expected_version=3,
            actor="ifan.juang",
            signing_secret="editor-secret",
            review_status="reviewed",
        )


def test_policy_client_receives_gate_signals_and_effect_binding(monkeypatch) -> None:
    preview = _preview(monkeypatch)
    proposed_digest = knowledge_update._digest(PROPOSED)
    observed_write = {}

    def revise(_conn, **values):
        observed_write.update(values)
        return {
            **CARD,
            "version": 4,
            "markdown_digest": proposed_digest,
        }

    monkeypatch.setattr(knowledge, "revise_knowledge", revise)
    client = _RecordingPolicyClient()
    result = knowledge_update.apply_knowledge_update(
        **_policy_apply_args(preview),
        policy_client=client,
    )

    assert result["status"] == "applied"
    assert client.preflight_payload["gate_signals"] == {
        "task_contract_ref": GATE_REFS["task_contract_ref"],
        "evidence_pack_candidate_ref": GATE_REFS["evidence_pack_candidate_ref"],
        "human_decision_ref": GATE_REFS["human_decision_ref"],
        "human_decision_level": "C2",
    }
    assert client.decision_payload["decision"]["decision_id"] == GATE_REFS["human_decision_ref"]
    assert client.decision_payload["decision"]["scope"] == {
        "scope_type": "project",
        "scope_id": "project-verger",
    }
    assert result["effect_binding"] == {
        "human_decision_ref": GATE_REFS["human_decision_ref"],
        "required_ceiling": "C2",
        "scope": {"scope_type": "project", "scope_id": "project-verger"},
        "object_identity": f"knowledge:knowledge.coverage:{proposed_digest}",
        "authorized_content_digest": proposed_digest,
        "applied_knowledge_id": "knowledge.coverage",
        "applied_markdown_digest": proposed_digest,
        "applied_version": 4,
    }
    assert observed_write["knowledge_id"] == "knowledge.coverage"


def test_candidate_cannot_broaden_the_exact_knowledge_effect(monkeypatch) -> None:
    preview = _preview(monkeypatch)
    proposed_digest = knowledge_update._digest(PROPOSED)
    monkeypatch.setattr(
        knowledge,
        "revise_knowledge",
        lambda _conn, **_values: {
            **CARD,
            "version": 4,
            "markdown_digest": proposed_digest,
        },
    )
    client = _RecordingPolicyClient()
    attacker_scope = {"scope_type": "project", "scope_id": "project-attacker"}
    attacker_candidate = {
        "request": {
            "intent": "harmless_read",
            "external_effect": True,
            "writes_state": False,
            "scope": attacker_scope,
        },
        "gate_signals": dict(GATE_REFS),
        "decision_expectation": {
            "required_ceiling": "C0",
            "required_scope": attacker_scope,
            "object_identity": "attacker-controlled",
            "expected_digest": "sha256:attacker-controlled",
        },
    }

    knowledge_update.apply_knowledge_update(
        **_policy_apply_args(preview),
        policy_client=client,
        preflight_candidate=attacker_candidate,
    )

    assert client.preflight_payload["request"]["intent"] == "knowledge_update"
    assert client.preflight_payload["request"]["writes_state"] is True
    assert client.preflight_payload["request"]["external_effect"] is False
    assert client.preflight_payload["request"]["scope"] == {
        "scope_type": "project",
        "scope_id": "project-verger",
    }
    assert client.decision_payload["expectation"] == {
        "required_ceiling": "C2",
        "required_scope": {"scope_type": "project", "scope_id": "project-verger"},
        "object_identity": f"knowledge:knowledge.coverage:{proposed_digest}",
        "expected_digest": proposed_digest,
    }


def test_policy_enabled_apply_refuses_missing_gate_references_before_write(monkeypatch) -> None:
    preview = _preview(monkeypatch)
    monkeypatch.setattr(
        knowledge,
        "revise_knowledge",
        lambda *_args, **_kwargs: pytest.fail("write must not run without gate references"),
    )

    args = _policy_apply_args(preview)
    args["task_contract_ref"] = None
    with pytest.raises(knowledge_update.KnowledgeUpdateError, match="task_contract_ref"):
        knowledge_update.apply_knowledge_update(
            **args,
            policy_client=_RecordingPolicyClient(),
        )


def test_policy_transport_failure_has_distinct_unavailable_error(monkeypatch) -> None:
    preview = _preview(monkeypatch)
    monkeypatch.setattr(
        knowledge,
        "revise_knowledge",
        lambda *_args, **_kwargs: pytest.fail("write must not run when PDP is unavailable"),
    )

    with pytest.raises(
        knowledge_update.KnowledgeUpdatePolicyUnavailable,
        match="policy_unavailable",
    ):
        knowledge_update.apply_knowledge_update(
            **_policy_apply_args(preview),
            policy_client=_UnavailablePolicyClient(),
        )
