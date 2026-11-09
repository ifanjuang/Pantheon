"""Observe one index of an IFC model as an Observation Bundle reconciled with the Project Anatomy.

A model is read at one professional index (the drawing set's E, F...). Its
storeys and spaces are compared with what the Project Anatomy already holds,
by IFC GlobalId, and the bundle proposes only the difference:

```text
+ object   storey or space the Anatomy does not know       -> object_candidates
= match    known object observed without its GlobalId yet   -> identity candidate (name, storey, area)
~ value    same object, another surface                     -> superseding claim candidate
- retire   object of an earlier index absent from this one  -> retirement candidate
```

Nothing here writes the Anatomy: the bundle goes through the reviewed chain
(``apu-batch``). A higher index is not truer by itself; a value of this index
replaces the previous one only once a human approves the batch. The model's
issuer and the index travel with every representation so that later checks can
compare sources of the same index.

Reading needs ``ifcopenshell`` (optional ``ifc`` extra).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

ADAPTER = "pantheon.ifc.ifcopenshell"
ADAPTER_VERSION = "1.0.0"
AREA_TOLERANCE = 0.05  # m2: below this, two surfaces are the same value
AREA_QUANTITIES = ("NetFloorArea", "GrossFloorArea", "NetArea", "Area")


class IfcObservationError(ValueError):
    pass


@dataclass
class ModelElement:
    guid: str
    ifc_class: str
    name: str
    number: str | None = None
    elevation: float | None = None
    storey_guid: str | None = None
    area: float | None = None


@dataclass
class Model:
    digest: str
    building: ModelElement | None
    storeys: list[ModelElement] = field(default_factory=list)
    spaces: list[ModelElement] = field(default_factory=list)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _space_area(element, util_element, geom) -> float | None:
    for quantities in util_element.get_psets(element, qtos_only=True).values():
        for key in AREA_QUANTITIES:
            value = quantities.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return round(float(value), 2)
    if geom is None:
        return None
    try:
        settings, shape_util = geom
        shape = settings[0].create_shape(settings[1], element)
        area = shape_util.get_footprint_area(shape.geometry)
    except Exception:  # geometry is a fallback; a space without it simply has no surface
        return None
    return round(float(area), 2) if area and area > 0 else None


def read_model(path: Path, *, with_geometry: bool = True) -> Model:
    """Storeys and spaces of one IFC file, with their GlobalIds and surfaces."""
    try:
        import ifcopenshell
        import ifcopenshell.util.element as util_element
    except ImportError as exc:  # pragma: no cover - depends on the optional extra
        raise IfcObservationError("reading IFC needs ifcopenshell (install the 'ifc' extra)") from exc
    geom = None
    if with_geometry:
        try:
            import ifcopenshell.geom as ifc_geom
            import ifcopenshell.util.shape as shape_util
            settings = ifc_geom.settings()
            settings.set("use-world-coords", True)
            geom = ((ifc_geom, settings), shape_util)
        except Exception:  # pragma: no cover - geometry kernel unavailable
            geom = None
    model_file = ifcopenshell.open(str(path))
    buildings = model_file.by_type("IfcBuilding")
    building = (
        ModelElement(guid=buildings[0].GlobalId, ifc_class="IfcBuilding", name=buildings[0].Name or "Bâtiment")
        if buildings else None
    )
    storeys = [
        ModelElement(guid=s.GlobalId, ifc_class="IfcBuildingStorey", name=s.Name or s.GlobalId,
                     elevation=round(float(s.Elevation), 2) if s.Elevation is not None else None)
        for s in model_file.by_type("IfcBuildingStorey")
    ]
    spaces = []
    for space in model_file.by_type("IfcSpace"):
        parent = util_element.get_aggregate(space) or util_element.get_container(space)
        spaces.append(ModelElement(
            guid=space.GlobalId,
            ifc_class="IfcSpace",
            name=space.LongName or space.Name or space.GlobalId,
            number=space.Name if space.LongName else None,
            storey_guid=parent.GlobalId if parent is not None and parent.is_a("IfcBuildingStorey") else None,
            area=_space_area(space, util_element, geom),
        ))
    return Model(digest=_sha256(path), building=building, storeys=storeys, spaces=spaces)


def _norm(text: Any) -> str:
    value = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def object_id(project_id: str, guid: str) -> str:
    return f"obj.{project_id}.ifc.{guid}"


def _representation(project_id: str, element: ModelElement, *, artifact_ref: str, version_ref: str,
                    index: str, issuer: str, observed_at: str, digest: str) -> dict[str, Any]:
    content = {"guid": element.guid, "class": element.ifc_class, "name": element.name, "number": element.number,
               "storey": element.storey_guid, "area": element.area, "elevation": element.elevation}
    return {
        "representation_id": f"rep.{project_id}.ifc.{index}.{element.guid}",
        "project_ref": project_id,
        "source_artifact_ref": artifact_ref,
        "source_version_ref": version_ref,
        "source_kind": "ifc",
        "identifiers": [{"scheme": "ifc.global_id", "value": element.guid}],
        "observed_at": observed_at,
        "binding_ref": ADAPTER,
        "adapter_version": ADAPTER_VERSION,
        "freshness_token": f"sha256:{digest}",
        "content_digest": "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest(),
        "context": {
            "document_ref": artifact_ref,
            **({"level_ref": element.storey_guid} if element.storey_guid else {}),
            "native_context": {"index": index, "issuer": issuer, "ifc_class": element.ifc_class},
        },
        "proof_status": "candidate",
    }


def _known_guids(anatomy: dict[str, Any]) -> dict[str, str]:
    """GlobalId -> current object id, from the identity links of IFC representations."""
    reps = {rep["representation_id"]: rep for rep in anatomy.get("source_representations") or []}
    current = {item["object_id"] for item in anatomy.get("stable_objects") or []}
    known: dict[str, str] = {}
    for relation in anatomy.get("relation_claims") or []:
        if relation.get("relation_type") != "identity.represents":
            continue
        rep = reps.get((relation.get("subject_ref") or {}).get("entity_id"))
        target = (relation.get("object_ref") or {}).get("entity_id")
        if rep is None or target not in current:
            continue
        for identifier in rep.get("identifiers") or []:
            if identifier.get("scheme") == "ifc.global_id":
                known[identifier["value"]] = target
    for item in anatomy.get("stable_objects") or []:  # objects this adapter created
        prefix = item["object_id"].split(".ifc.", 1)
        if len(prefix) == 2 and item["object_id"] not in known.values():
            known.setdefault(prefix[1], item["object_id"])
    return known


def build_bundle(project_id: str, model: Model, anatomy: dict[str, Any], *, artifact_ref: str, index: str,
                 issuer: str, observed_at: str, task_contract_ref: str,
                 authority: str = "project_working_document") -> dict[str, Any]:
    """Reconcile one model index with the current Anatomy; propose only the difference."""
    index = str(index).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,20}", index):
        raise IfcObservationError("index must be a short label such as E or T2")
    version_ref = f"sha256:{model.digest}"
    known = _known_guids(anatomy)
    objects = {item["object_id"]: item for item in anatomy.get("stable_objects") or []}
    claims = list(anatomy.get("attribute_claims") or [])
    relations = list(anatomy.get("relation_claims") or [])
    reps, object_candidates, attribute_candidates, relation_candidates, retirements = [], [], [], [], []

    def rep_for(element):
        rep = _representation(project_id, element, artifact_ref=artifact_ref, version_ref=version_ref, index=index,
                              issuer=issuer, observed_at=observed_at, digest=model.digest)
        reps.append(rep)
        return rep["representation_id"]

    def current_area(target):
        for claim in claims:
            if (claim.get("subject_ref") or {}).get("entity_id") == target and claim.get("attribute_key") == "space.area":
                return claim
        return None

    def unknown_match(element, storey_target):
        """A known object that was observed without its GlobalId (an earlier drawing, say)."""
        for target, item in objects.items():
            if target in known.values() or ".ifc." in target:
                continue
            nomenclature = item["stable_object"].get("nomenclature") or {}
            names = {_norm(nomenclature.get("display_name")), _norm(nomenclature.get("internal_code"))}
            if _norm(element.name) not in names and _norm(element.number) not in names - {""}:
                continue
            if element.ifc_class == "IfcSpace":
                contained = any(r.get("relation_type") == "spatial.contains"
                                and (r.get("object_ref") or {}).get("entity_id") == target
                                and (r.get("subject_ref") or {}).get("entity_id") == storey_target for r in relations)
                area = current_area(target)
                same_area = area is None or element.area is None or abs(float(area["value"]["value"]) - element.area) <= AREA_TOLERANCE
                if not (contained and same_area):
                    continue
            return target
        return None

    resolved: dict[str, str] = {}
    for element in model.storeys + model.spaces:
        rep_id = rep_for(element)
        target = known.get(element.guid)
        note = "Même GlobalId que l'objet déjà connu : nouvelle observation à cet indice."
        if target is None:
            target = unknown_match(element, resolved.get(element.storey_guid or ""))
            note = "Même nom, même niveau et même surface que l'objet déjà connu, sans GlobalId jusqu'ici."
        if target is not None:
            # "=" : the object is known; this index's occurrence joins its history, so a
            # value of this index can cite it.
            relation_candidates.append({
                "relation_claim_id": f"identity.{project_id}.ifc.{index}.{element.guid}",
                "subject_ref": {"entity_type": "source_representation", "entity_id": rep_id},
                "relation_type": "identity.represents",
                "object_ref": {"entity_type": "stable_object", "entity_id": target},
                "assertion_mode": "proposed", "source_authority": "model_interpretation_candidate",
                "proof_status": "candidate", "certainty": "E4" if element.guid in known else "E3",
                "source_representation_refs": [rep_id], "notes": note,
            })
        else:
            target = object_id(project_id, element.guid)
            object_candidates.append({
                "object_candidate_id": f"object.{project_id}.ifc.{index}.{element.guid}",
                "stable_object": {"stable_object_id": target, "project_ref": project_id, "object_family": "spatial",
                                  "nomenclature": {"internal_code": element.number or element.name,
                                                   "display_name": element.name}},
                "source_representation_ref": rep_id, "certainty": "E4",
                "rationale": f"{element.ifc_class} présent à l'indice {index} et inconnu de l'Anatomie.",
            })
            storey_target = resolved.get(element.storey_guid or "")
            if element.ifc_class == "IfcSpace" and storey_target:
                relation_candidates.append({
                    "relation_claim_id": f"claim.{project_id}.ifc.{index}.{element.guid}.contained",
                    "subject_ref": {"entity_type": "stable_object", "entity_id": storey_target},
                    "relation_type": "spatial.contains",
                    "object_ref": {"entity_type": "stable_object", "entity_id": target},
                    "qualifier": {"containment": "decomposition"},
                    "assertion_mode": "observed", "source_authority": authority, "proof_status": "candidate",
                    "certainty": "E4", "source_representation_refs": [rep_id],
                })
        resolved[element.guid] = target
        if element.ifc_class == "IfcSpace" and element.area is not None:
            previous = current_area(target)
            if previous is not None and abs(float(previous["value"]["value"]) - element.area) <= AREA_TOLERANCE:
                continue
            claim = {
                "attribute_claim_id": f"claim.{project_id}.ifc.{index}.{element.guid}.area",
                "subject_ref": {"entity_type": "stable_object", "entity_id": target},
                "attribute_key": "space.area",
                "value": {"value_type": "number", "value": element.area, "unit": "m2"},
                "assertion_mode": "observed", "source_authority": authority, "proof_status": "candidate",
                "certainty": "E4", "source_representation_refs": [rep_id],
            }
            if previous is not None:
                claim["supersedes_claim_ref"] = previous["attribute_claim_id"]
            attribute_candidates.append(claim)

    seen = {element.guid for element in model.storeys + model.spaces}
    for guid, target in known.items():
        if guid not in seen and target in objects:
            retirements.append({
                "retirement_candidate_id": f"retire.{project_id}.ifc.{index}.{guid}",
                "stable_object_ref": target,
                "reason": f"Absent de la maquette à l'indice {index}.",
                "rationale": "Absence d'un indice complet : à confirmer (démoli, supprimé ou export partiel).",
            })

    return {
        "observation_bundle_id": f"observation-bundle.{project_id}.ifc.{index}.{model.digest[:12]}",
        "project_ref": project_id,
        "task_contract_ref": task_contract_ref,
        "basis": {"source_artifact_refs": [artifact_ref], "source_version_refs": [version_ref],
                  "exact_digests": [{"source_artifact_ref": artifact_ref, "source_version_ref": version_ref,
                                     "digest": version_ref}]},
        "method": {"capability_id": "ifc.observe.spatial_structure", "binding_id": ADAPTER,
                   "operation_id": "ifc.observe.storeys_spaces.v1", "adapter_ref": ADAPTER,
                   "adapter_version": ADAPTER_VERSION, "request_ref": f"ifc:{index}"},
        "observed_at": observed_at,
        "freshness_token": version_ref,
        "scope": {"document_refs": [artifact_ref]},
        "coverage": {"completeness": "complete_for_declared_scope",
                     "observed_scope": {"document_refs": [artifact_ref]},
                     "excluded_reasons": ["storeys_and_spaces_only"], "absence_inference_allowed": False},
        "limitations": [
            f"Niveaux et locaux de la maquette à l'indice {index}, émise par {issuer} ; éléments non lus.",
            "Les surfaces viennent des quantités IFC ou, à défaut, de l'emprise géométrique du local.",
            "L'état existant/projeté n'est pas lu (propriétés Revit non exportées).",
        ],
        "source_representations": reps,
        "object_candidates": object_candidates,
        "attribute_claim_candidates": attribute_candidates,
        "relation_claim_candidates": relation_candidates,
        "retirement_candidates": retirements,
        "gaps": [], "withheld": [], "warnings": [],
        "operational_outcome": "success",
        "authority": {"is_fact": False, "is_evidence": False, "is_decision": False, "is_memory": False,
                      "is_apu_write": False, "authorizes_external_effect": False},
    }
