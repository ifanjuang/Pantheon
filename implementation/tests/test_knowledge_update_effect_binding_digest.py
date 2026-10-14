"""Effect-binding digests stay comparable to the persisted Knowledge snapshot."""

from __future__ import annotations

from mvp_vertical import knowledge, knowledge_update


class _Connection:
    pass


class _AllowingPolicyClient:
    def preflight(self, candidate):
        self.candidate = candidate
        return {
            "policy_disposition": "eligible_with_gate_signals_unverified",
            "missing_requirements": [],
            "external_effect_allowed": False,
            "canonical_effect_allowed": False,
            "gate_signal_validation_performed": False,
            "replay_guard_required": False,
        }

    def validate_decision(self, payload):
        self.decision = payload
        return {"verdict": "valid", "findings": []}


def test_raw_persisted_digest_is_canonicalized_in_effect_binding(monkeypatch) -> None:
    current = "# Base\n\nold\n"
    proposed = "# Base\n\nnew\n"
    knowledge_id = "knowledge.digest-binding"
    project_id = "project-digest-binding"
    card = {
        "knowledge_id": knowledge_id,
        "parent_project_id": project_id,
        "title": "Digest binding",
        "review_status": "needs_review",
        "version": 1,
    }
    monkeypatch.setattr(knowledge, "get_knowledge_card", lambda *_args: dict(card))
    monkeypatch.setattr(knowledge, "get_knowledge_markdown", lambda *_args: current)

    preview = knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id=project_id,
        knowledge_id=knowledge_id,
        proposed_markdown=proposed,
        expected_version=1,
        actor="human:test",
        signing_secret="editor-secret",
        now=1_000,
    )
    canonical_digest = knowledge_update._digest(proposed)
    persisted_raw_digest = canonical_digest.removeprefix("sha256:")

    def revise(_conn, **_values):
        # This is the representation returned by the current Knowledge persistence
        # owner: raw SHA-256 hex, without the decision-facing ``sha256:`` prefix.
        return {
            **card,
            "version": 2,
            "markdown_digest": persisted_raw_digest,
        }

    monkeypatch.setattr(knowledge, "revise_knowledge", revise)
    result = knowledge_update.apply_knowledge_update(
        _Connection(),
        parent_project_id=project_id,
        knowledge_id=knowledge_id,
        proposed_markdown=proposed,
        expected_version=1,
        base_markdown_digest=preview["base_markdown_digest"],
        actor="human:test",
        signing_secret="editor-secret",
        confirmation_token=preview["confirmation"]["token"],
        confirmation_expires_at=preview["confirmation"]["expires_at"],
        confirmation_phrase=knowledge_update.CONFIRMATION_PHRASE,
        idempotency_key="digest-binding-0001",
        now=1_010,
        policy_client=_AllowingPolicyClient(),
        task_contract_ref="task-contract:test",
        evidence_pack_candidate_ref="evidence-pack-candidate:test",
        human_decision_ref="human-decision:test",
    )

    binding = result["effect_binding"]
    assert binding["authorized_content_digest"] == canonical_digest
    assert binding["applied_markdown_digest"] == canonical_digest
    assert binding["authorized_content_digest"] == binding["applied_markdown_digest"]
    assert result["knowledge"]["markdown_digest"] == persisted_raw_digest


def test_canonical_digest_normalizer_preserves_unknown_legacy_value() -> None:
    assert knowledge_update._canonical_sha256_digest("legacy-digest") == "legacy-digest"
    assert knowledge_update._canonical_sha256_digest(None) is None
