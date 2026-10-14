"""Idempotent replay remains owned by the transactional Knowledge adapter."""

from __future__ import annotations

from mvp_vertical import knowledge, knowledge_update


class _Connection:
    pass


def test_exact_retry_reaches_immutable_replay_after_version_advanced_and_expiry(monkeypatch) -> None:
    base_card = {
        "knowledge_id": "knowledge.coverage",
        "parent_project_id": "project-verger",
        "title": "Couverture",
        "review_status": "needs_review",
        "version": 3,
    }
    current = "# Couverture\n\nÀ confirmer.\n"
    proposed = "# Couverture\n\nZinc naturel confirmé.\n"
    monkeypatch.setattr(knowledge, "get_knowledge_card", lambda _conn, _id: dict(base_card))
    monkeypatch.setattr(knowledge, "get_knowledge_markdown", lambda _conn, _id: current)
    preview = knowledge_update.preview_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=proposed,
        expected_version=3,
        actor="ifan.juang",
        signing_secret="server-signing-secret",
        now=1_000,
    )

    monkeypatch.setattr(
        knowledge,
        "get_knowledge_card",
        lambda _conn, _id: {**base_card, "version": 4},
    )
    observed = {}

    def replay(_conn, **values):
        observed.update(values)
        return {**base_card, "version": 4, "markdown_digest": "replayed"}

    monkeypatch.setattr(knowledge, "revise_knowledge", replay)
    result = knowledge_update.apply_knowledge_update(
        _Connection(),
        parent_project_id="project-verger",
        knowledge_id="knowledge.coverage",
        proposed_markdown=proposed,
        expected_version=3,
        base_markdown_digest=preview["base_markdown_digest"],
        actor="ifan.juang",
        signing_secret="server-signing-secret",
        confirmation_token=preview["confirmation"]["token"],
        confirmation_expires_at=preview["confirmation"]["expires_at"],
        confirmation_phrase="CONFIRMER UPDATE",
        idempotency_key="knowledge-update-retry-1",
        now=1_400,
    )

    assert result["knowledge"]["version"] == 4
    assert observed["expected_version"] == 3
    assert observed["idempotency_key"] == "knowledge-update-retry-1"
