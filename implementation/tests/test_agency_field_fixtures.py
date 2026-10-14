from __future__ import annotations

import json
from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures" / "agency"
FIXTURE_FILES = (
    "f01_maison_neuve.json",
    "f02_patrimoine_renovation.json",
    "f03_chantier_reserves.json",
    "f04_erp_reglementaire.json",
    "f05_dce_marches.json",
    "f06_agence_bindings.json",
    "f07_bim_revit.json",
    "f08_outils_ia.json",
)
CONSEQUENTIAL_PROJECT_FIELDS = {
    "surface_projet",
    "surface_existante",
    "surface_terrain",
    "zone_plu",
    "budget",
    "parcelles",
    "permit_number",
    "permit_date",
    "reception_date",
    "montant_marche",
    "erp_type",
}


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _fixtures() -> list[dict]:
    return [_load(name) for name in FIXTURE_FILES]


def test_agency_fixtures_are_synthetic_and_use_existing_v2_families() -> None:
    fixtures = _fixtures()

    assert {fixture["fixture_id"] for fixture in fixtures} == {f"F{index:02d}" for index in range(1, 9)}
    for fixture in fixtures:
        assert fixture["synthetic"] is True
        assert fixture["project"]["project_id"].startswith("fixture-project-")
        assert fixture["information"]
        assert fixture["contacts"]
        assert fixture["work"]
        assert fixture["decisions"]


def test_consequential_project_values_do_not_return_to_flexible_attributes() -> None:
    for fixture in _fixtures():
        attributes = fixture["project"].get("attributes") or {}
        assert not (CONSEQUENTIAL_PROJECT_FIELDS & set(attributes))


def test_source_backed_claims_resolve_to_information() -> None:
    for fixture in _fixtures():
        information_keys = {item["key"] for item in fixture["information"]}
        for claim in fixture.get("project_claims") or []:
            if claim["status"] == "source_backed":
                assert claim["backing_information_key"] in information_keys


def test_asserted_claims_are_allowed_without_fake_backing() -> None:
    asserted = [
        claim
        for fixture in _fixtures()
        for claim in fixture.get("project_claims") or []
        if claim["status"] == "asserted"
    ]

    assert asserted
    assert any(claim.get("backing_information_key") is None for claim in asserted)


def test_information_taxonomy_axes_remain_distinct() -> None:
    for fixture in _fixtures():
        for information in fixture["information"]:
            type_tags = set(information["type_tags"])
            subject_tags = set(information["subject_tags"])
            limits = set(information["limits"])
            assert information["status"] in {"draft", "in_progress", "acted", "superseded"}
            assert not (type_tags & limits)
            assert not (subject_tags & limits)


def test_work_review_requires_separate_human_decision_in_consequential_cases() -> None:
    for fixture in (
        _load("f02_patrimoine_renovation.json"),
        _load("f03_chantier_reserves.json"),
        _load("f04_erp_reglementaire.json"),
        _load("f05_dce_marches.json"),
    ):
        reviewed_work = {item["id"] for item in fixture["work"] if item.get("status") == "review"}
        decision_triggers = {item["trigger"] for item in fixture["decisions"] if item.get("human_required")}
        assert reviewed_work <= decision_triggers


def test_change_candidates_keep_revision_diff_provenance_and_idempotency() -> None:
    for fixture in (_load("f03_chantier_reserves.json"), _load("f05_dce_marches.json")):
        for candidate in fixture.get("change_candidates") or []:
            assert isinstance(candidate["base_revision"], int)
            assert candidate["changes"]
            assert candidate["provenance"]
            assert candidate["idempotency_key"]
            assert candidate["status"] == "pending_review"


def test_dce_document_types_do_not_collapse_into_subject_tags() -> None:
    fixture = _load("f05_dce_marches.json")
    type_vocab = {tag for item in fixture["information"] for tag in item["type_tags"]}
    subject_vocab = {tag for item in fixture["information"] for tag in item["subject_tags"]}

    assert {"DCE", "CCTP", "CCAP", "devis", "contrat"} <= type_vocab
    assert {"structure", "budget", "entreprise"} & subject_vocab
    assert not ({"CCTP", "CCAP"} & subject_vocab)


def test_erp_fixture_keeps_questions_distinct_from_acted_requirements() -> None:
    fixture = _load("f04_erp_reglementaire.json")
    acted = [item for item in fixture["information"] if item["status"] == "acted"]
    working = [item for item in fixture["information"] if item["status"] == "in_progress"]

    assert any("obligatoire" in item["limits"] for item in acted)
    assert any("questionnement" in item["limits"] for item in working)
    assert any("retrouvée" in observation for observation in fixture["expected_observations"])


def test_external_bindings_are_optional_mapped_and_non_authoritative() -> None:
    fixture = _load("f06_agence_bindings.json")
    bindings = fixture["bindings"]

    assert {item["binding"] for item in bindings} == {"notion", "google_contacts", "gmail", "drive"}
    assert all(item["optional"] is True for item in bindings)
    assert all(item["authority"] in {"projection_only", "source_only"} for item in bindings)
    assert all(item["sync_rules_required"] is True for item in bindings)
    notion = next(item for item in bindings if item["binding"] == "notion")
    assert notion["archives_external"] is False


def test_contacts_remain_grouped_without_participation_entity() -> None:
    fixture = _load("f06_agence_bindings.json")
    groups = fixture["contacts"]["groups"]

    assert {"maitrise_ouvrage", "maitrise_oeuvre", "bureaux_etudes", "entreprises_travaux"} <= set(groups)
    assert "participation" not in json.dumps(fixture).lower()


def test_bim_fixture_changes_index_only_when_source_changes() -> None:
    fixture = _load("f07_bim_revit.json")
    plans = [item for item in fixture["information"] if item.get("series") == "plans-pro"]
    detail = [item for item in fixture["information"] if item.get("series") == "detail-bardage"]

    assert {item["index_label"] for item in plans} == {"A01", "A02"}
    assert len({item["source_ref"] for item in plans}) == 2
    assert {item["index_label"] for item in detail} == {"A01"}
    assert any(item["status"] == "in_progress" for item in detail)


def test_tools_fixture_keeps_governance_axes_independent() -> None:
    fixture = _load("f08_outils_ia.json")
    comfy = next(tool for tool in fixture["tools"] if tool["tool_id"] == "comfyui")
    haystack = next(tool for tool in fixture["tools"] if tool["tool_id"] == "haystack")

    assert comfy["installed"] is True
    assert comfy["approved"] is False
    assert comfy["update_available"] is True
    assert comfy["update_authorized"] is False
    assert comfy["task_authorized"] is False
    assert haystack["catalogued"] is True
    assert haystack["installed"] is False
    assert haystack["approved"] is False
    assert "runtime_success != Evidence" in fixture["expected_observations"]


def test_patrimoine_fixture_preserves_acted_and_working_context() -> None:
    fixture = _load("f02_patrimoine_renovation.json")
    diagnostics = [item for item in fixture["information"] if item.get("series") == "diagnostic-structure"]

    assert {item["status"] for item in diagnostics} == {"acted", "in_progress"}
    assert {item["index_label"] for item in diagnostics} == {"A01", "A02"}
    assert any("hypothese" in item["limits"] for item in diagnostics if item["status"] == "in_progress")


def test_sensitive_affair_fixture_keeps_mail_insurance_and_responsibility_qualified() -> None:
    fixture = _load("f03_chantier_reserves.json")
    maf = next(item for item in fixture["information"] if item["key"] == "maf-a01")
    mail = next(item for item in fixture["information"] if item["key"] == "email-maf-a01")

    assert maf["status"] == "acted"
    assert {"assurance", "sinistre", "responsabilite"} <= set(maf["subject_tags"])
    assert maf["source_ref"].startswith("fixture://")
    assert mail["source_type"] == "link"
    assert "ne reconnaît aucune responsabilité" in fixture["expected_observations"][-2]
