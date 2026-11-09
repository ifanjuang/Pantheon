"""One IFC model index reconciled with the Project Anatomy: only the difference is proposed.

The model here is synthetic, built by the test with ifcopenshell, so no real
project data is involved. Surfaces come from Qto quantities (the geometry
fallback is exercised on real models only).
"""

from __future__ import annotations

from pathlib import Path

import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")
import ifcopenshell.api  # noqa: E402

from mvp_vertical import apu_batch, apu_owner, execution_results, ifc_observation as ifc  # noqa: E402
from test_apu_progressive_claims import _id, _project, conn  # noqa: E402,F401 - conn is a fixture

HUMAN = "human:architect"


def _model(path: Path, spaces: dict[str, tuple[str, str, float]]) -> dict[str, str]:
    """Write a model with storeys RDC and R01; spaces = {key: (name, storey, area)}. Returns GlobalIds."""
    run = ifcopenshell.api.run
    model = ifcopenshell.file(schema="IFC4")
    project = run("root.create_entity", model, ifc_class="IfcProject", name="Démo")
    run("unit.assign_unit", model)
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Site")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Maison")
    run("aggregate.assign_object", model, products=[site], relating_object=project)
    run("aggregate.assign_object", model, products=[building], relating_object=site)
    storeys = {}
    for name, elevation in (("RDC", 0.0), ("R01", 2.8)):
        storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name=name)
        storey.Elevation = elevation
        storey.GlobalId = GUIDS[name]
        run("aggregate.assign_object", model, products=[storey], relating_object=building)
        storeys[name] = storey
    guids = {name: storey.GlobalId for name, storey in storeys.items()}
    for key, (name, storey_name, area) in spaces.items():
        space = run("root.create_entity", model, ifc_class="IfcSpace", name=key)
        space.LongName = name
        if key in GUIDS:
            space.GlobalId = GUIDS[key]
        run("aggregate.assign_object", model, products=[space], relating_object=storeys[storey_name])
        qto = run("pset.add_qto", model, product=space, name="Qto_SpaceBaseQuantities")
        run("pset.edit_qto", model, qto=qto, properties={"NetFloorArea": area})
        guids[key] = space.GlobalId
    model.write(str(path))
    return guids


# Stable GlobalIds across indices, as Revit keeps them from one export to the next.
GUIDS = {"S1": "0aaaaaaaaaaaaaaaaaaaa1", "S2": "0aaaaaaaaaaaaaaaaaaaa2", "S3": "0aaaaaaaaaaaaaaaaaaaa3",
         "RDC": "0bbbbbbbbbbbbbbbbbbbb1", "R01": "0bbbbbbbbbbbbbbbbbbbb2"}


def test_reading_a_model_gives_storeys_spaces_and_surfaces(tmp_path) -> None:
    _model(tmp_path / "a.ifc", {"S1": ("Cuisine", "RDC", 12.0), "S2": ("Chambre", "R01", 11.5)})
    model = ifc.read_model(tmp_path / "a.ifc", with_geometry=False)
    assert model.building.name == "Maison"
    assert [s.name for s in model.storeys] == ["RDC", "R01"]
    by_name = {s.name: s for s in model.spaces}
    assert by_name["Cuisine"].area == 12.0 and by_name["Cuisine"].number == "S1"
    assert by_name["Chambre"].storey_guid == next(s.guid for s in model.storeys if s.name == "R01")


def test_an_index_label_must_be_short(tmp_path) -> None:
    _model(tmp_path / "a.ifc", {})
    model = ifc.read_model(tmp_path / "a.ifc", with_geometry=False)
    with pytest.raises(ifc.IfcObservationError, match="index"):
        ifc.build_bundle("p", model, {}, artifact_ref="ifc:a", index="indice E", issuer="agence",
                         observed_at="2026-01-01T00:00:00Z", task_contract_ref="t")


def _install(conn, project_id: str) -> None:
    """A Project known from an earlier drawing: storey RDC (code RDC) holding the kitchen, 12 m2."""
    rep = {"representation_id": "rep.drawing.cuisine", "project_ref": project_id, "source_artifact_ref": "plan.a101",
           "source_version_ref": "plan:a101:E", "source_kind": "drawing",
           "identifiers": [{"scheme": "drawing.local_label", "value": "Cuisine"}], "observed_at": "2026-01-01T00:00:00Z",
           "binding_ref": "fixture", "adapter_version": "1", "freshness_token": "fixture", "proof_status": "candidate"}
    objects = [
        {"stable_object_id": "obj.rdc", "project_ref": project_id, "object_family": "spatial",
         "nomenclature": {"internal_code": "RDC", "display_name": "Rez-de-chaussée"}},
        {"stable_object_id": "obj.cuisine", "project_ref": project_id, "object_family": "spatial",
         "nomenclature": {"internal_code": "CUI", "display_name": "Cuisine"}},
    ]
    contains = {"relation_claim_id": "rel.rdc.cuisine", "subject_ref": {"entity_type": "stable_object", "entity_id": "obj.rdc"},
                "relation_type": "spatial.contains", "object_ref": {"entity_type": "stable_object", "entity_id": "obj.cuisine"},
                "assertion_mode": "observed", "source_authority": "project_working_document", "proof_status": "candidate",
                "source_representation_refs": ["rep.drawing.cuisine"]}
    area = {"attribute_claim_id": "claim.cuisine.area", "subject_ref": {"entity_type": "stable_object", "entity_id": "obj.cuisine"},
            "attribute_key": "space.area", "value": {"value_type": "number", "value": 12.0, "unit": "m2"},
            "assertion_mode": "observed", "source_authority": "project_working_document", "proof_status": "candidate",
            "source_representation_refs": ["rep.drawing.cuisine"]}
    apu_owner.store_reviewed_dossier(conn, project_id=project_id, stable_objects=objects, source_representations=[rep],
                                     attribute_claims=[area], relation_claims=[contains], review_ref="review:fixture",
                                     actor=HUMAN, idempotency_key=_id("install"))


def _observe(conn, project_id: str, path: Path, index: str) -> tuple[str, str, dict]:
    model = ifc.read_model(path, with_geometry=False)
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    contract = f"ifc-observation:{project_id}:{index}"
    payload = ifc.build_bundle(project_id, model, anatomy, artifact_ref=f"ifc:{path.name}", index=index, issuer="agence",
                               observed_at="2026-02-01T00:00:00Z", task_contract_ref=contract)
    execution_id, result_id = _id("execution-ifc"), _id("result-ifc")
    execution_results.store_execution_result(conn, execution_result={
        "execution_result_id": execution_id, "task_contract_ref": contract, "project_ref": project_id,
        "producer": {"kind": "adapter", "version": ifc.ADAPTER_VERSION}, "produced_at": "2026-02-01T00:00:00Z",
        "authority": dict(execution_results.AUTHORITY),
        "results": [{"result_id": result_id, "result_kind": "observation_bundle",
                     "schema_ref": execution_results.OBSERVATION_BUNDLE_SCHEMA_REF, "payload": payload}],
        "clarification_requests": []}, idempotency_key=_id("ifc"))
    return execution_id, result_id, payload


def _apply(conn, execution_id: str, result_id: str) -> list[str]:
    preview = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)
    changes = [apu_batch.preview_row(item)["change"] for item in preview["items"]]
    apu_batch.apply_batch(conn, execution_result_id=execution_id, result_ref=result_id, batch_digest=preview["batch_digest"],
                          reviewer=HUMAN, authorized_by=HUMAN, applied_by="system:test")
    return changes


def _current(conn, project_id: str) -> dict:
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    names = {item["object_id"]: item["stable_object"]["nomenclature"]["display_name"] for item in anatomy["stable_objects"]}
    areas = {names[c["subject_ref"]["entity_id"]]: c["value"]["value"] for c in anatomy["attribute_claims"]
             if c["attribute_key"] == "space.area" and c["subject_ref"]["entity_id"] in names}
    return {"names": sorted(names.values()), "areas": areas}


def test_a_first_model_matches_known_objects_and_adds_the_others(conn, tmp_path) -> None:
    project_id = _project(conn)
    _install(conn, project_id)
    _model(tmp_path / "a.ifc", {"S1": ("Cuisine", "RDC", 12.0), "S2": ("Chambre", "R01", 11.5)})
    execution_id, result_id, payload = _observe(conn, project_id, tmp_path / "a.ifc", "A")
    changes = _apply(conn, execution_id, result_id)
    # R01 and the bedroom are new; RDC and the kitchen are recognised, the kitchen's 12 m2 unchanged.
    assert changes.count("+ objet") == 2 and changes.count("= rattache") == 2
    assert changes.count("+ valeur") == 2  # the bedroom's surface and its containment
    current = _current(conn, project_id)
    assert current["names"] == ["Chambre", "Cuisine", "R01", "Rez-de-chaussée"]
    assert current["areas"] == {"Cuisine": 12.0, "Chambre": 11.5}


def test_the_next_index_proposes_only_the_difference(conn, tmp_path) -> None:
    project_id = _project(conn)
    _install(conn, project_id)
    _model(tmp_path / "a.ifc", {"S1": ("Cuisine", "RDC", 12.0), "S2": ("Chambre", "R01", 11.5)})
    _apply(conn, *_observe(conn, project_id, tmp_path / "a.ifc", "A")[:2])
    # Index B: the kitchen grows, the bedroom is gone, an office appears.
    _model(tmp_path / "b.ifc", {"S1": ("Cuisine", "RDC", 14.0), "S3": ("Bureau", "R01", 9.0)})
    execution_id, result_id, payload = _observe(conn, project_id, tmp_path / "b.ifc", "B")
    assert len(payload["retirement_candidates"]) == 1
    assert [c for c in payload["attribute_claim_candidates"] if c.get("supersedes_claim_ref")]
    changes = _apply(conn, execution_id, result_id)
    assert changes.count("- retrait") == 1 and changes.count("~ remplace") == 1 and changes.count("+ objet") == 1
    current = _current(conn, project_id)
    assert "Chambre" not in current["names"] and "Bureau" in current["names"]
    assert current["areas"]["Cuisine"] == 14.0
