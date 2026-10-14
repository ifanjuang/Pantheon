from __future__ import annotations

from pathlib import Path
from uuid import UUID

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "docs"
    / "examples"
    / "workspace_manifest_inspector"
    / "qualification"
    / "m2_document_information_routing.yaml"
)

FORBIDDEN_AUTHORITY_KEYS = {
    "authority_status",
    "effect_class",
    "version_status",
    "approved_by",
    "approved_at",
    "signed_by",
    "signed_at",
    "evidence_status",
    "decision_status",
    "current_for_coordination",
    "current_for_consultation",
    "current_contractual",
    "current_for_execution",
    "current_for_site",
}


def _fixture() -> dict:
    with FIXTURE.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def _documents() -> dict[str, dict]:
    docs = _fixture()["corpus"]
    assert isinstance(docs, list)
    return {doc["document_key"]: doc for doc in docs}


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested in value.values():
            keys.update(_all_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(_all_keys(nested))
        return keys
    return set()


def _all_information() -> list[dict]:
    items: list[dict] = []
    for doc in _documents().values():
        info = doc.get("information", [])
        assert isinstance(info, list)
        items.extend(info)
    return items


def _refs(item: dict) -> list[dict]:
    refs = item.get("refs", [])
    assert isinstance(refs, list)
    return refs


def test_m2_remains_fixture_only_and_reuses_existing_semantic_seam() -> None:
    fixture = _fixture()

    assert fixture["fixture_status"] == "synthetic_candidate"
    assert fixture["qualification"]["issue"] == 859
    assert fixture["qualification"]["tranche"] == "M2"
    assert fixture["qualification"]["production_manifest_schema"] == "not_adopted"
    assert fixture["qualification"]["anatomy_bridge"] == "reference_only_candidate"
    assert (
        fixture["qualification"]["semantic_promotion_path"]
        == "canonical_observation_bundle"
    )


def test_one_common_information_carrier_covers_heterogeneous_sources() -> None:
    docs = _documents()

    assert {
        "plan_a203_c",
        "plan_a203_d",
        "plan_structure_s102_b",
        "model_ifc_2026_08",
        "cctp_lot_menuiseries_c",
        "dpgf_lot_menuiseries_c",
        "email_bet_2026_08_21",
    }.issubset(docs)

    kinds = {doc["document_kind"] for doc in docs.values()}
    formats = {doc["format"] for doc in docs.values()}

    assert {"plan", "model", "specification", "price_schedule", "correspondence"}.issubset(kinds)
    assert {"pdf", "ifc", "xlsx", "eml"}.issubset(formats)

    for doc in docs.values():
        assert isinstance(doc.get("information"), list)
        assert doc["scope"]["coverage"] == "partial"


def test_information_shape_is_progressive_not_rigid() -> None:
    items = _all_information()

    assert all(isinstance(item["info_id"], str) and item["info_id"] for item in items)
    assert all(
        (isinstance(item.get("text"), str) and bool(item["text"]))
        or (isinstance(item.get("comment"), str) and bool(item["comment"]))
        for item in items
    )

    assert any("text" in item for item in items)
    assert any("text" not in item for item in items)
    assert any("comment" in item for item in items)
    assert any("comment" not in item for item in items)
    assert any("anchor" in item for item in items)
    assert any("anchor" not in item for item in items)
    assert any("status" in item for item in items)
    assert any("status" not in item for item in items)
    assert any(_refs(item) for item in items)
    assert any(not _refs(item) for item in items)


def test_localizers_can_be_strong_weak_or_source_native() -> None:
    items = _all_information()
    kinds = {item["anchor"]["locator_kind"] for item in items if "anchor" in item}

    assert {
        "page_bbox",
        "grid_ref",
        "native_element_id",
        "page_section",
        "sheet_range",
        "message_fragment",
    }.issubset(kinds)

    structure = _documents()["plan_structure_s102_b"]["information"][0]
    assert structure["anchor"] == {
        "locator_kind": "grid_ref",
        "grid_ref": "C-D/4-5",
    }
    assert _refs(structure) == []

    general = _documents()["plan_structure_s102_b"]["information"][1]
    assert "anchor" not in general
    assert "text" not in general
    assert _refs(general) == []


def test_same_information_can_be_repositioned_between_plan_versions() -> None:
    docs = _documents()
    before = docs["plan_a203_c"]["information"][0]
    after = docs["plan_a203_d"]["information"][0]

    assert docs["plan_a203_c"]["represented_version"] == "C"
    assert docs["plan_a203_d"]["represented_version"] == "D"
    assert before["info_id"] == after["info_id"] == "I-W17-DETAIL"
    assert before["anchor"]["page"] == 2
    assert after["anchor"]["page"] == 3
    assert before["anchor"]["bbox"] != after["anchor"]["bbox"]
    assert before["anchor"]["detail_ref"] == after["anchor"]["detail_ref"] == "D12"
    assert "grid_ref" in before["anchor"]
    assert "annotation_ref" in after["anchor"]


def test_refs_are_heterogeneous_navigation_context_not_a_new_relation_graph() -> None:
    schemes = {
        ref["scheme"]
        for item in _all_information()
        for ref in _refs(item)
    }

    assert {"anatomy", "document", "ifc", "web"}.issubset(schemes)

    keys = _all_keys(_fixture())
    assert "relation_claim" not in keys
    assert "attribute_claim" not in keys
    assert "requirement" not in keys
    assert "evidence" not in keys
    assert "decision" not in keys


def test_anatomy_refs_remain_candidates_and_do_not_fabricate_governed_identity() -> None:
    anatomy_refs = [
        ref
        for item in _all_information()
        for ref in _refs(item)
        if ref["scheme"] == "anatomy"
    ]

    assert anatomy_refs
    for ref in anatomy_refs:
        assert ref["resolution"] == "proposed"
        assert ref["ref"].startswith("candidate:")
        try:
            UUID(ref["ref"])
        except ValueError:
            pass
        else:
            raise AssertionError("M2 fixture must not fabricate governed Anatomy UUIDs")


def test_ifc_native_identifier_does_not_become_anatomy_identity() -> None:
    ifc_doc = _documents()["model_ifc_2026_08"]
    item = ifc_doc["information"][0]
    native_id = item["anchor"]["native_id"]
    anatomy_ref = next(ref for ref in _refs(item) if ref["scheme"] == "anatomy")

    assert native_id == "2MF28NhmDBiRVyFakgdbCT"
    assert anatomy_ref["ref"] == "candidate:window-17"
    assert anatomy_ref["ref"] != native_id


def test_document_refs_are_logical_versioned_refs_not_filesystem_paths() -> None:
    document_refs = [
        ref
        for item in _all_information()
        for ref in _refs(item)
        if ref["scheme"] == "document"
    ]

    assert document_refs
    for ref in document_refs:
        assert ref["document_ref"].startswith("fixture:")
        assert ref["version_ref"].startswith("fixture:")
        assert "/" not in ref["document_ref"]
        assert "\\" not in ref["document_ref"]


def test_ambiguous_email_reference_stays_unresolved_instead_of_guessing() -> None:
    email = _documents()["email_bet_2026_08_21"]
    ambiguous = next(
        item for item in email["information"] if item["info_id"] == "I-MAIL-AMBIGUOUS-002"
    )

    assert ambiguous["status"] == "to_check"
    assert _refs(ambiguous) == []
    assert "ne pas inventer de cible" in ambiguous["comment"].lower()


def test_manifest_candidate_does_not_acquire_authority_or_persist_preview() -> None:
    fixture = _fixture()
    keys = _all_keys(fixture)

    assert not FORBIDDEN_AUTHORITY_KEYS.intersection(keys)
    assert "preview" not in keys
    assert fixture["boundaries"]["preview_is_reconstructible_not_persisted"] is True
    assert fixture["boundaries"]["external_ref_is_not_evidence"] is True
    assert fixture["boundaries"]["comment_is_not_decision"] is True
    assert fixture["boundaries"]["status_is_not_professional_approval"] is True
