"""Q1 qualification for multidisciplinary Hermes context composition.

This is deliberately a context-composition test, not a model-reasoning test.
It proves that existing owners can be admitted together around one architectural
change question without a Lens Engine, graph traversal, requirement matcher or
new persistence owner. A live Hermes/model run is still required to qualify the
quality of multidisciplinary reasoning itself.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest
from psycopg.types.json import Jsonb

from mvp_vertical import (
    agency_data,
    agency_information,
    apu_owner,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    hermes_scoped_context,
    store,
    work_issues,
)


QUESTION = "Si je déplace cette cloison de 200 mm, quelles conséquences vois-tu ?"


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.commit()
    yield connection
    connection.close()


def _stable(project_id: str, object_id: str, family: str, name: str) -> dict:
    return {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": family,
        "nomenclature": {
            "internal_code": object_id[-12:],
            "display_name": name,
        },
    }


def _representation(project_id: str, representation_id: str) -> dict:
    return {
        "representation_id": representation_id,
        "project_ref": project_id,
        "source_artifact_ref": "drawing://P2/A-101",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.fragment", "value": "A-101/RDC"}],
        "observed_at": "2026-09-06T12:00:00Z",
        "binding_ref": "fixture.p2.plan",
        "adapter_version": "1.0",
        "freshness_token": "P2-A101-r1",
        "proof_status": "candidate",
    }


def _attribute(
    object_id: str,
    claim_id: str,
    representation_id: str,
    key: str,
    value: float,
    unit: str,
) -> dict:
    return {
        "attribute_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "attribute_key": key,
        "value": {"value_type": "number", "value": value, "unit": unit},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [representation_id],
    }


def _relation(
    subject_id: str,
    object_id: str,
    claim_id: str,
    representation_id: str,
    relation_type: str,
) -> dict:
    return {
        "relation_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": subject_id},
        "relation_type": relation_type,
        "object_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "assertion_mode": "human_asserted",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation_id],
    }


def _document_and_knowledge(conn, project_id: str) -> tuple[str, str]:
    document_id = _id("document")
    extraction_id = _id("extraction")
    knowledge_id = _id("knowledge")
    source_ref = "Projects/P2/30_DCE/CCTP-LOT-PLATRERIE.md"
    source_digest = "sha256:" + "4" * 64
    document_markdown = (
        "# Extrait CCTP synthétique\n\n"
        "La cloison reçoit une porte et une traversée technique. "
        "Toute modification de position doit être coordonnée avec les lots concernés."
    )
    knowledge_markdown = (
        "# Repères de revue synthétiques\n\n"
        "Contexte annoncé : circulation d'un ERP et travaux en phase PRO.\n\n"
        "Pour une modification de cloison, examiner selon les données disponibles : "
        "largeur de circulation et accessibilité, portes et sens de passage, "
        "compartimentage/incendie si applicable, traversées de réseaux, phasage, lots et coût.\n\n"
        "Ces repères orientent la revue ; ils ne démontrent ni l'applicabilité "
        "d'une règle ni la conformité du projet."
    )
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'text/markdown', %s, 'extracted')
        """,
        (
            document_id,
            project_id,
            project_id,
            source_ref,
            source_digest,
            len(document_markdown.encode("utf-8")),
        ),
    )
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest, source_digest,
            converter, converter_version, config_digest, status, markdown_content,
            chunk_count, quality_flags
        ) VALUES (%s, %s, 'p2-context-q1', 'contract-digest', %s,
                  'fixture', '1', 'config-digest', 'complete', %s, 0, '[]'::jsonb)
        """,
        (extraction_id, document_id, source_digest, document_markdown),
    )
    conn.execute(
        "UPDATE source_documents SET current_extraction_id = %s WHERE document_id = %s",
        (extraction_id, document_id),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'text/markdown', %s)
        """,
        (
            document_id,
            source_ref,
            source_digest,
            len(document_markdown.encode("utf-8")),
        ),
    )
    conn.execute(
        """
        INSERT INTO knowledge_items (
            knowledge_id, document_id, source_version, source_digest, extraction_id,
            title, family, markdown, markdown_digest, source_chunk_refs,
            review_status, version, created_by
        ) VALUES (%s, %s, 1, %s, %s, 'Repères modification cloison', 'reglementations',
                  %s, %s, %s, 'reviewed', 1, 'human:test')
        """,
        (
            knowledge_id,
            document_id,
            source_digest,
            extraction_id,
            knowledge_markdown,
            hashlib.sha256(knowledge_markdown.encode("utf-8")).hexdigest(),
            Jsonb([]),
        ),
    )
    conn.commit()
    return document_id, knowledge_id


def _admit_and_start(conn, project_id: str, selected: list[dict[str, str]]) -> tuple[dict, str]:
    envelope = {
        "root_entity": {
            "entity_id": f"project:{project_id}",
            "entity_type": "project",
        },
        "descendants": [],
        "source_refs": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question=QUESTION,
        card_context_envelope=envelope,
        selected_context=selected,
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question=QUESTION,
        preview=preview,
        card_context_envelope=envelope,
        selected_context=selected,
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
        idempotency_key=_id("admit"),
        ttl_seconds=900,
    )
    run_id = _id("hermes-run")
    hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
        expected_issue_version=handoff["work_issue"]["version"],
        idempotency_key=_id("start"),
    )
    return admission, run_id


def _entity(entity_type: str, entity_id: str) -> dict[str, str]:
    return {"entity_type": entity_type, "entity_id": f"{entity_type}:{entity_id}"}


def _scenario(conn) -> dict:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("P2").upper(),
        display_name="Qualification changement cloison",
        description="Fixture synthétique non client pour P2.",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    project_id = project["project_id"]
    partition = _id("apu-partition")
    corridor = _id("apu-corridor")
    office = _id("apu-office")
    door = _id("apu-door")
    duct = _id("apu-duct")
    unrelated = _id("apu-unrelated")
    representation_id = _id("representation")

    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[
            _stable(project_id, partition, "element", "Cloison P2"),
            _stable(project_id, corridor, "spatial", "Circulation P2"),
            _stable(project_id, office, "spatial", "Bureau P2"),
            _stable(project_id, door, "element", "Porte P2"),
            _stable(project_id, duct, "system", "Réseau technique P2"),
            _stable(project_id, unrelated, "element", "Objet hors contexte P2"),
        ],
        source_representations=[_representation(project_id, representation_id)],
        attribute_claims=[
            _attribute(partition, _id("attribute"), representation_id, "geometry.thickness", 120, "mm"),
            _attribute(corridor, _id("attribute"), representation_id, "geometry.clear_width", 1400, "mm"),
        ],
        relation_claims=[
            _relation(partition, corridor, _id("relation"), representation_id, "spatial.adjacent_to"),
            _relation(partition, office, _id("relation"), representation_id, "spatial.adjacent_to"),
            _relation(door, partition, _id("relation"), representation_id, "architecture.hosted_by"),
            _relation(duct, partition, _id("relation"), representation_id, "building_services.passes_through"),
        ],
        review_ref="review:architect:p2-context-q1",
        actor="human:architect",
        idempotency_key=_id("apu-bootstrap"),
    )

    information = agency_information.create_information(
        conn,
        project_id=project_id,
        title="Prémisse de contexte P2",
        category="Programme",
        source_type="document",
        source_ref="fixture://p2/programme",
        index_label="A01",
        summary="Circulation ERP étudiée en phase PRO.",
        details=(
            "Pour cette qualification synthétique uniquement, la circulation adjacente "
            "est déclarée comme participant à un cheminement ERP. Cette Information est "
            "une prémisse de contexte, pas une preuve de conformité."
        ),
        actor_kind="human",
        author="human:test",
    )
    document_id, knowledge_id = _document_and_knowledge(conn, project_id)

    return {
        "project_id": project_id,
        "partition": partition,
        "corridor": corridor,
        "office": office,
        "door": door,
        "duct": duct,
        "unrelated": unrelated,
        "representation_id": representation_id,
        "information_id": information["information_id"],
        "document_id": document_id,
        "knowledge_id": knowledge_id,
    }


def test_q1_structured_context_stays_local_and_does_not_follow_relations(conn) -> None:
    state = _scenario(conn)
    admission, run_id = _admit_and_start(
        conn,
        state["project_id"],
        [_entity("stable_object", state["partition"])],
    )

    manifest = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
    )
    assert {(item["entity_type"], item["entity_id"]) for item in manifest["entities"]} == {
        ("project", f"project:{state['project_id']}"),
        ("stable_object", f"stable_object:{state['partition']}"),
    }
    assert manifest["global_search_available"] is False
    assert manifest["global_listing_available"] is False
    assert manifest["source_dereference_available"] is False

    partition = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="stable_object",
        entity_id=f"stable_object:{state['partition']}",
        actor="hermes-runtime",
    )
    record = partition["record"]
    assert record["stable_object"]["nomenclature"]["display_name"] == "Cloison P2"
    assert {claim["relation_type"] for claim in record["relation_claims"]} == {
        "spatial.adjacent_to",
        "architecture.hosted_by",
        "building_services.passes_through",
    }
    assert record["scope"]["relation_traversal_performed"] is False
    assert record["scope"]["neighbour_records_materialized"] is False
    assert record["source_representation_refs"] == [state["representation_id"]]

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="outside the exact admitted Context Pack",
    ):
        hermes_scoped_context.get_context_entity(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            entity_type="stable_object",
            entity_id=f"stable_object:{state['corridor']}",
            actor="hermes-runtime",
        )


def test_q1_composed_context_reuses_existing_owners_without_new_lens_or_graph(conn) -> None:
    state = _scenario(conn)
    selected = [
        _entity("stable_object", state["partition"]),
        _entity("stable_object", state["corridor"]),
        _entity("stable_object", state["office"]),
        _entity("stable_object", state["door"]),
        _entity("stable_object", state["duct"]),
        _entity("information", state["information_id"]),
        _entity("document", state["document_id"]),
        _entity("knowledge", state["knowledge_id"]),
    ]
    admission, run_id = _admit_and_start(conn, state["project_id"], selected)

    manifest = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
    )
    admitted = {(item["entity_type"], item["entity_id"]) for item in manifest["entities"]}
    expected = {
        ("project", f"project:{state['project_id']}"),
        *{(item["entity_type"], item["entity_id"]) for item in selected},
    }
    assert admitted == expected
    assert ("stable_object", f"stable_object:{state['unrelated']}") not in admitted
    assert manifest["global_search_available"] is False
    assert manifest["global_listing_available"] is False
    assert manifest["source_dereference_available"] is False
    assert manifest["write_effect"] is False

    corridor = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="stable_object",
        entity_id=f"stable_object:{state['corridor']}",
        actor="hermes-runtime",
    )
    assert any(
        claim["attribute_key"] == "geometry.clear_width"
        for claim in corridor["record"]["attribute_claims"]
    )

    information = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="information",
        entity_id=f"information:{state['information_id']}",
        actor="hermes-runtime",
    )
    assert "ERP" in information["representation"]["details"]
    assert information["representation"]["working_assumptions_are_not_acted"] is True

    document = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="document",
        entity_id=f"document:{state['document_id']}",
        actor="hermes-runtime",
    )
    assert document["representation"]["kind"] == "derived_markdown"
    assert "traversée technique" in document["representation"]["content"]
    assert document["source_binary_included"] is False

    knowledge = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        entity_type="knowledge",
        entity_id=f"knowledge:{state['knowledge_id']}",
        actor="hermes-runtime",
    )
    assert knowledge["representation"]["kind"] == "knowledge_markdown"
    assert "accessibilité" in knowledge["representation"]["content"]
    assert "incendie" in knowledge["representation"]["content"]
    assert knowledge["record"]["review_status"] == "reviewed"

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="outside the exact admitted Context Pack",
    ):
        hermes_scoped_context.get_context_entity(
            conn,
            admission_id=admission["admission_id"],
            run_id=run_id,
            entity_type="stable_object",
            entity_id=f"stable_object:{state['unrelated']}",
            actor="hermes-runtime",
        )
