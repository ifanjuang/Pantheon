from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvp_vertical import (
    card_tag_context,
    hermes_handoff_preview,
    tag_registry,
)
from mvp_vertical.work_activity_projection import (
    WorkActivityProjectionError,
    project_work_activity,
)


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
REGISTRY = COCKPIT / "registries" / "tag_registry.json"
DEMO = COCKPIT / "demo-data.json"
DEMO_WORK = COCKPIT / "demo-work-activity.json"


class _OwnerReadableConnection:
    def cursor(self):  # pragma: no cover - owner read is monkeypatched in this unit test
        raise AssertionError("unexpected SQL owner read")


def test_unified_tag_registry_is_contextual_and_replaces_split_files() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    loaded = tag_registry.load_registry()

    assert payload["schema_id"] == "cockpit.tag_registry"
    assert payload["revision"] == 1
    assert loaded["groups"]["subject"]["max_per_card"] == 5
    assert not (COCKPIT / "registries" / "type_tags.json").exists()
    assert not (COCKPIT / "registries" / "subject_tags.json").exists()
    assert not (COCKPIT / "demo-tags.json").exists()

    identities = set()
    for item in payload["tags"]:
        identity = (item["group"], item["slug"])
        assert identity not in identities
        identities.add(identity)
        assert item["description"].strip()
        assert item["hermes_context"].strip()
        assert item["presentation"]["icon_key"]
        assert item["group"] in {"type", "subject"}


def test_subject_context_is_capped_and_unknown_tags_are_not_interpreted() -> None:
    context = tag_registry.resolve_entity_tag_context(
        entity_id="work:test",
        entity_type="work_issue",
        type_tags=["verification"],
        subject_tags=[
            "budget",
            "urbanisme",
            "chantier",
            "assurance",
            "responsabilite",
            "unknown-sixth",
        ],
    )

    subjects = [item for item in context["tags"] if item["group"] == "subject"]
    assert len(subjects) == 5
    assert {item["slug"] for item in subjects} == {
        "budget",
        "urbanisme",
        "chantier",
        "assurance",
        "responsabilite",
    }
    assert context["unregistered_tags"] == []

    unknown = tag_registry.resolve_entity_tag_context(
        entity_id="information:test",
        entity_type="information",
        subject_tags=["not-registered"],
    )
    assert unknown["tags"] == []
    assert unknown["unregistered_tags"] == [
        {"group": "subject", "slug": "not-registered"}
    ]


def test_card_tag_context_uses_owner_projection_without_inference(monkeypatch) -> None:
    monkeypatch.setattr(
        card_tag_context,
        "_entity_record",
        lambda _conn, *, entity_id, entity_type: {
            "type_tags": ["analyse"],
            "subject_tags": ["budget", "options"],
        },
    )

    contexts = card_tag_context.resolve_tag_context(
        _OwnerReadableConnection(),
        entity_refs=[{"entity_id": "information:test", "entity_type": "information"}],
    )

    assert len(contexts) == 1
    assert contexts[0]["entity_ref"]["entity_id"] == "information:test"
    assert {item["slug"] for item in contexts[0]["tags"]} == {
        "analyse",
        "budget",
        "options",
    }
    assert contexts[0]["unregistered_tags"] == []


def test_scope_only_connection_does_not_accept_client_tag_meaning() -> None:
    contexts = card_tag_context.resolve_tag_context(
        object(),
        entity_refs=[{"entity_id": "project:test", "entity_type": "project"}],
    )
    assert contexts == []


def test_work_activity_projection_is_strict_and_keeps_bounded_card_fields() -> None:
    aggregate = {
        "work_issue": {
            "issue_id": "work-1",
            "status": "review",
            "assigned_to": "hermes",
            "version": 3,
            "task_contract_ref": "task-contract:1",
            "context_pack_ref": "context-pack:1",
            "type_tags": ["decision"],
            "subject_tags": [
                "budget",
                "options",
                "maison-neuve",
                "re2020",
                "paysage",
                "urbanisme",
            ],
            "limits": ["human review required"],
        },
        "comments": [],
        "hermes_runs": [
            {
                "run_id": "run-1",
                "status": "returned",
                "requested_effect": "read_only",
                "started_at": "2026-08-02T10:00:00Z",
                "returned_at": "2026-08-02T10:10:00Z",
                "updated_at": "2026-08-02T10:10:00Z",
                "normalized_return": {
                    "outcome": "result_candidate",
                    "summary": "Candidate result",
                    "result_refs": ["result://1"],
                    "evidence_candidate_refs": [],
                    "trace_refs": ["trace://1"],
                },
            }
        ],
        "events": [
            {
                "event_type": "issue_created",
                "occurred_at": "2026-08-02T09:00:00Z",
                "actor": "human",
                "actor_kind": "human",
                "run_ref": None,
            }
        ],
    }

    projected = project_work_activity(aggregate)

    assert projected["issue"]["type_tags"] == ["decision"]
    assert projected["issue"]["subject_tags"] == [
        "budget",
        "options",
        "maison-neuve",
        "re2020",
        "paysage",
    ]
    assert projected["issue"]["limits"] == ["human review required"]
    assert projected["result_candidate"]["outcome"] == "result_candidate"
    assert projected["trace_refs"] == ["trace://1"]
    assert projected["review_required"] is True

    with pytest.raises(WorkActivityProjectionError, match="work_issue must be an object"):
        project_work_activity(
            {"comments": [], "hermes_runs": [], "events": []}
        )


def test_hermes_preview_carries_descriptive_tag_context_without_authority() -> None:
    context = tag_registry.resolve_entity_tag_context(
        entity_id="project:demo",
        entity_type="project",
        subject_tags=["budget", "urbanisme"],
    )
    preview = hermes_handoff_preview.build_preview(
        question="Comparer les contraintes",
        card_context_envelope={
            "root_entity": {"entity_id": "project:demo", "entity_type": "project"},
            "descendants": [],
            "explicit_additions": [],
            "explicit_exclusions": [],
            "source_refs": [],
            "tag_context": [context],
        },
        selected_context=[],
    )

    tag_context = preview["context_pack"]["tag_context"]
    assert tag_context[0]["tags"][0]["description"]
    assert tag_context[0]["tags"][0]["hermes_context"]
    assert "tag context != source authority" in preview["non_equivalences"]
    assert preview["execution_authorized"] is False


def test_demo_cards_use_strict_work_activity_and_registered_tags() -> None:
    demo = json.loads(DEMO.read_text(encoding="utf-8"))
    work = json.loads(DEMO_WORK.read_text(encoding="utf-8"))

    assert work["schema_id"] == "cockpit.demo_work_activity"
    assert work["revision"] == 1
    assert "demo-work-activity.json" in (
        COCKPIT / "demo_bootstrap.js"
    ).read_text(encoding="utf-8")

    for project in demo["projects"]:
        context = tag_registry.resolve_entity_tag_context(
            entity_id=project["project_id"],
            entity_type="project",
            subject_tags=project.get("tags"),
        )
        assert context["unregistered_tags"] == []
        assert len([item for item in context["tags"] if item["group"] == "subject"]) <= 5

    expected_issue_ids = set()
    for payload in demo["project_payloads"].values():
        for information in payload["information"]:
            context = tag_registry.resolve_entity_tag_context(
                entity_id=information["information_id"],
                entity_type="information",
                type_tags=information.get("type_tags"),
                subject_tags=information.get("subject_tags"),
            )
            assert context["unregistered_tags"] == []
        for raw in payload["work_issues"]:
            expected_issue_ids.add(raw["work_issue"]["issue_id"])

    assert set(work["items"]) == expected_issue_ids
    for issue_id, aggregate in work["items"].items():
        issue = aggregate["work_issue"]
        assert len(issue["subject_tags"]) <= 5, issue_id
        context = tag_registry.resolve_entity_tag_context(
            entity_id=issue_id,
            entity_type="work_issue",
            type_tags=issue["type_tags"],
            subject_tags=issue["subject_tags"],
        )
        assert context["unregistered_tags"] == [], issue_id
        assert aggregate["work_activity"]["schema"] == {
            "id": "cockpit.work_activity",
            "revision": 1,
        }
