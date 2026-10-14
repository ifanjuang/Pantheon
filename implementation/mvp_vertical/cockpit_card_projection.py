"""Bounded server-side Card projections for resolved Cockpit collection items.

This module implements the existing Card projection responsibility. It does not
create a Card owner, persist Card records, change business lifecycle, infer
authorization or qualify Evidence. Each projector consumes an already-governed
owner read model and emits only presentation data for the Cockpit renderer.
"""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import quote


CardProjector = Callable[[dict[str, Any]], dict[str, Any]]


def _text(value: Any, fallback: str = "") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def _list(value: Any) -> list:
    return list(value) if isinstance(value, list) else []


def _back_row(label: str, value: Any, fallback: str = "Non renseigné") -> list[str]:
    return [label, _text(value, fallback)]


def _card(
    *,
    entity_id: str,
    entity_type: str,
    family: str,
    presentation_family: str,
    category: str,
    title: str,
    summary: str,
    status: str = "neutral",
    type_tags: list[str] | None = None,
    subject_tags: list[str] | None = None,
    limits: list[str] | None = None,
    back: list[list[str]] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "role": extra.pop("role", "entity"),
        "family": family,
        "presentation_family": presentation_family,
        "category": category,
        "title": title,
        "summary": summary,
        "status": status,
        "type_tags": list(type_tags or []),
        "subject_tags": list(subject_tags or []),
        "limits": list(limits or []),
        # Read-only collection projections do not infer actions from lifecycle.
        # Consequential actions remain server-owned and are absent unless an
        # owner projection explicitly provides them in a later bounded tranche.
        "available_actions": [],
        "back": list(back or []),
        **extra,
    }


def project_category(category: dict[str, Any]) -> dict[str, Any]:
    category_id = str(category["category_id"])
    applies_to = [str(value) for value in category.get("applies_to") or []]
    archived_at = category.get("archived_at")
    return _card(
        entity_id=f"category:{category_id}",
        entity_type="category",
        role="container",
        family="information",
        presentation_family="information",
        category="Catégorie",
        title=_text(category.get("title"), category_id),
        summary=_text(category.get("description"), "Classification Agency Data"),
        status="archived" if archived_at else "active",
        type_tags=["category"],
        back=[
            _back_row("Parent", category.get("parent_category_id"), "Racine"),
            ["Applicable à", " · ".join(applies_to) if applies_to else "Non renseigné"],
            _back_row("Révision", category.get("revision")),
        ],
        source_entity_ref={"entity_type": "category", "entity_id": category_id},
        child_collection={
            "state": "available",
            "collection_id": f"children:category:{category_id}",
            "load_action": {
                "kind": "collection_read",
                "href": f"/cockpit/category-collections/{quote(category_id, safe='')}",
            },
            "can_add": False,
            "create_action": None,
        },
    )


def project_project(item: dict[str, Any]) -> dict[str, Any]:
    project_id = str(item["project_id"])
    title = _text(item.get("display_name"), _text(item.get("code"), project_id))
    summary_parts = [
        item.get("code") if item.get("code") != title else None,
        item.get("phase"),
        item.get("location"),
    ]
    summary = " · ".join(str(value) for value in summary_parts if value) or "Affaire Agency Data"
    attributes = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
    back = [[str(key).replace("_", " "), _text(value)] for key, value in attributes.items() if value not in (None, "")]
    return _card(
        entity_id=f"project:{project_id}",
        entity_type="project",
        role="container",
        family="project",
        presentation_family="project",
        category="Projet",
        title=title,
        summary=summary,
        status=_text(item.get("status"), "active"),
        subject_tags=[str(value) for value in item.get("tags") or []],
        back=back,
        date=item.get("updated_at"),
        front={"issuer": item.get("primary_client")},
        source_entity_ref={"entity_type": "project", "entity_id": project_id},
        source_project_id=project_id,
        child_collection={
            "state": "available",
            "collection_id": f"children:project:{project_id}",
            "load_action": {"kind": "project_bundle", "context_id": project_id},
            "can_add": False,
            "create_action": None,
        },
    )


def project_information(projection: dict[str, Any]) -> dict[str, Any]:
    item = projection.get("information") if isinstance(projection.get("information"), dict) else projection
    information_id = str(item["information_id"])
    return _card(
        entity_id=f"information:{information_id}",
        entity_type="information",
        family="information",
        presentation_family="information",
        category=_text(item.get("category"), "Information"),
        title=_text(item.get("title"), "Information"),
        summary=_text(item.get("summary"), "Résumé non renseigné"),
        status=_text(item.get("status"), "draft"),
        type_tags=[str(value) for value in item.get("type_tags") or []],
        subject_tags=[str(value) for value in item.get("subject_tags") or []],
        limits=[str(value) for value in item.get("limits") or []],
        back=[
            _back_row("Résumé", item.get("summary"), "Résumé non renseigné"),
            _back_row("Informations détaillées", item.get("details"), "Informations détaillées non renseignées"),
            _back_row("Source", item.get("source_ref") or item.get("source_note"), "Source non renseignée"),
            _back_row("Version source", item.get("source_version")),
            _back_row("Révision technique", item.get("revision")),
            _back_row("Mis à jour le", item.get("updated_at")),
            _back_row("Auteur", item.get("author")),
        ],
        index=item.get("index_label"),
        date=item.get("information_date") or item.get("updated_at"),
        author=item.get("author"),
        source_refs=[item["source_ref"]] if item.get("source_ref") else [],
        source_entity_ref={"entity_type": "information", "entity_id": information_id},
        source_project_id=item.get("project_id"),
        series_id=item.get("series_id"),
        technical_revision=item.get("revision"),
    )


def project_document(item: dict[str, Any]) -> dict[str, Any]:
    document_id = str(item["document_id"])
    revision_count = int(item.get("revision_count") or 0)
    summary = (
        f"{revision_count} révision{'s' if revision_count != 1 else ''} professionnelle{'s' if revision_count != 1 else ''}"
        if revision_count
        else "Document professionnel sans révision liée"
    )
    return _card(
        entity_id=f"document:{document_id}",
        entity_type="document",
        family="information",
        presentation_family="information",
        category=_text(item.get("document_type"), "Document"),
        title=_text(item.get("title"), "Document"),
        summary=summary,
        status="neutral",
        type_tags=[_text(item.get("document_type"), "document")],
        back=[
            _back_row("Projet propriétaire", item.get("parent_project_id")),
            _back_row("Lot", item.get("lot_id")),
            _back_row("Discipline", item.get("discipline_code")),
            ["Révisions liées", str(revision_count)],
            ["Autorité", "Présence documentaire ≠ Evidence ≠ autorité d’exécution"],
        ],
        date=item.get("created_at"),
        source_entity_ref={"entity_type": "document", "entity_id": document_id},
        source_project_id=item.get("parent_project_id"),
    )


def project_knowledge(item: dict[str, Any]) -> dict[str, Any]:
    knowledge_id = str(item["knowledge_id"])
    return _card(
        entity_id=f"knowledge:{knowledge_id}",
        entity_type="knowledge",
        family="information",
        presentation_family="information",
        category=_text(item.get("family"), "Référence"),
        title=_text(item.get("title"), "Knowledge"),
        summary=_text(item.get("summary"), f"Version {item.get('version') or 1}"),
        status=_text(item.get("review_status"), "generated_unreviewed"),
        type_tags=[str(value) for value in item.get("type_tags") or ["etude"]],
        subject_tags=[str(value) for value in item.get("subject_tags") or item.get("tags") or []],
        limits=[str(value) for value in item.get("limits") or ["consultatif"]],
        back=[
            _back_row("Document source", item.get("document_ref")),
            _back_row("Version", item.get("version")),
            ["Limite", "Knowledge ≠ Evidence ≠ mémoire gouvernée"],
        ],
        date=item.get("updated_at"),
        source_entity_ref={"entity_type": "knowledge", "entity_id": knowledge_id},
        source_project_id=item.get("parent_project_id"),
    )


def project_work_issue(item: dict[str, Any]) -> dict[str, Any]:
    issue_id = str(item["issue_id"])
    milestones = item.get("milestones") or item.get("steps") or []
    resources = [
        *(item.get("responsibilities") or []),
        *(item.get("skills") or []),
        *(item.get("functions") or []),
        *(item.get("tools") or []),
    ]
    return _card(
        entity_id=f"work:{issue_id}",
        entity_type="work_issue",
        family="work",
        presentation_family="work",
        category="Travail",
        title=_text(item.get("title"), "Travail"),
        summary=_text(item.get("description"), "Objectif de travail non renseigné"),
        status=_text(item.get("status"), "open"),
        type_tags=[str(value) for value in item.get("type_tags") or []],
        subject_tags=[str(value) for value in item.get("subject_tags") or item.get("tags") or []],
        limits=[str(value) for value in item.get("limits") or []],
        back=[
            _back_row("Objectif", item.get("objective") or item.get("description")),
            ["Jalons", "\n".join(str(step.get("label") or step.get("title") or step) if isinstance(step, dict) else str(step) for step in milestones) if milestones else "Non renseignés"],
            ["Responsabilités · Skills · Fonctions · Outils", " · ".join(str(value) for value in resources) if resources else "Non renseignés"],
            _back_row("Résultat attendu", item.get("result_ref") or item.get("requested_effect")),
        ],
        date=item.get("updated_at") or item.get("created_at"),
        source_entity_ref={"entity_type": "work_issue", "entity_id": issue_id},
        source_work_id=issue_id,
    )


PROJECTORS: dict[str, CardProjector] = {
    "project": project_project,
    "information": project_information,
    "document": project_document,
    "knowledge": project_knowledge,
    "work_issue": project_work_issue,
}


def project_owner_card(entity_type: str, read_model: dict[str, Any]) -> dict[str, Any]:
    projector = PROJECTORS.get(str(entity_type))
    if projector is None:
        raise ValueError(f"unsupported Cockpit Card projection entity type: {entity_type}")
    return projector(read_model)
