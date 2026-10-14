"""Tests for candidate-only fragment qualification to APU mapping conversion."""

from copy import deepcopy

import pytest

from mvp_vertical import apu_mapping_converter, execution_results


SOURCE = {
    "execution_result": {
        "execution_result_id": "execution.source.001",
        "task_contract_ref": "task-contracts/source.yaml",
        "project_ref": "project-tilleul",
        "evidence_pack_candidate_ref": "evidence-pack.source.001",
    },
    "results": [
        {
            "result_id": "result.fragment.001",
            "result_kind": "fragment_qualification",
            "schema_ref": "schemas/fragment_qualification_candidate.schema.yaml",
            "payload": {
                "document_ref": "document.avp",
                "structure_ref": "structure.avp",
                "qualifications": [
                    {
                        "fragment_ref": "fragment.chambre",
                        "topic": "chambre",
                        "discipline": "architecture",
                        "representation_kind": "floor_plan",
                        "project_state": "projected",
                        "coverage_refs": ["space.chambre-r2"],
                        "certainty": "E3",
                        "rationale": "Le libellé et la position indiquent une chambre.",
                    },
                    {
                        "fragment_ref": "fragment.escalier",
                        "object_kind": "vertical_connection",
                        "certainty": "E2",
                        "rationale": "La volée est visible mais sa liaison exacte reste ambiguë.",
                        "question": "Relie-t-il le RDC au R+1 ?",
                    },
                ],
            },
        }
    ],
    "clarification_requests": [],
    "review_dispositions": [
        {
            "result_ref": "result.fragment.001",
            "disposition": "accepted_for_mapping",
            "occurred_at": "2026-08-05T10:00:00+00:00",
        }
    ],
    "authority": dict(execution_results.AUTHORITY),
}


def test_conversion_is_deterministic_and_candidate_only() -> None:
    first = apu_mapping_converter.build_mapping_execution(
        deepcopy(SOURCE), source_result_ref="result.fragment.001"
    )
    second = apu_mapping_converter.build_mapping_execution(
        deepcopy(SOURCE), source_result_ref="result.fragment.001"
    )
    assert first == second
    assert first["authority"] == execution_results.AUTHORITY
    result = first["results"][0]
    assert result["result_kind"] == "apu_object_mapping"
    assert result["schema_ref"] == apu_mapping_converter.SCHEMA_REF
    assert result["payload"]["authority"]["is_apu_write"] is False


def test_coverage_refs_become_proposed_matches_not_confirmed_identity() -> None:
    converted = apu_mapping_converter.build_mapping_execution(
        deepcopy(SOURCE), source_result_ref="result.fragment.001"
    )
    mapping = converted["results"][0]["payload"]["mappings"][0]
    assert mapping["status"] == "candidate_matches"
    assert mapping["match_candidates"] == [
        {
            "stable_object_ref": "space.chambre-r2",
            "certainty": "E3",
            "rationale": "Référence de couverture proposée par la qualification revue.",
        }
    ]
    assert "confirmed" not in str(mapping).lower()


def test_converter_preserves_ambiguity_as_clarification() -> None:
    converted = apu_mapping_converter.build_mapping_execution(
        deepcopy(SOURCE), source_result_ref="result.fragment.001"
    )
    mapping = converted["results"][0]["payload"]["mappings"][1]
    assert mapping["status"] == "needs_clarification"
    assert mapping["proposed_object_family"] == "spatial"
    assert converted["clarification_requests"][0]["question"] == "Relie-t-il le RDC au R+1 ?"


def test_converter_refuses_non_accepted_or_wrong_result_kind() -> None:
    pending = deepcopy(SOURCE)
    pending["review_dispositions"][0]["disposition"] = "pending"
    with pytest.raises(apu_mapping_converter.MappingConversionError):
        apu_mapping_converter.build_mapping_execution(
            pending, source_result_ref="result.fragment.001"
        )

    wrong = deepcopy(SOURCE)
    wrong["results"][0]["result_kind"] = "spatial_observation"
    with pytest.raises(apu_mapping_converter.MappingConversionError):
        apu_mapping_converter.build_mapping_execution(
            wrong, source_result_ref="result.fragment.001"
        )


def test_converter_does_not_invent_object_family() -> None:
    converted = apu_mapping_converter.build_mapping_execution(
        deepcopy(SOURCE), source_result_ref="result.fragment.001"
    )
    first_mapping = converted["results"][0]["payload"]["mappings"][0]
    assert "proposed_object_family" not in first_mapping
