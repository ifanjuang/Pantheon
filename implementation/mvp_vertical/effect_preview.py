"""Deterministic, proposal-only information-to-object rapprochement.

This module never persists a proposal, mutates an object, applies an effect or
creates a card. It searches only the exact opened project scope and returns
reviewable candidates for human confirmation.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Literal

from . import knowledge, store, work_issue_read, work_issues

EffectKind = Literal["CREATE", "UPDATE", "SUPERSEDE", "CONFLICT"]
ObjectKind = Literal["document", "knowledge", "work_issue"]

_STOPWORDS = {
    "avec", "avoir", "cette", "dans", "des", "elle", "elles", "est", "etre",
    "pour", "plus", "projet", "que", "qui", "sans", "ses", "son", "sur", "une",
    "aux", "les", "leur", "leurs", "nous", "vous", "mais", "donc", "comme",
    "the", "and", "for", "from", "that", "this", "with", "project",
}

_CUES: dict[EffectKind, tuple[str, ...]] = {
    "CONFLICT": (
        "contredit", "contradictoire", "contradiction", "conflit", "contraire",
        "incompatible", "non conforme", "different de", "ne correspond pas",
    ),
    "SUPERSEDE": (
        "remplace", "remplacer", "annule", "annuler", "supprime", "supprimer",
        "abandonne", "abandonner", "desormais", "finalement", "n est plus",
        "ne sera plus", "nouvelle version fait foi",
    ),
    "UPDATE": (
        "precise", "preciser", "complete", "completer", "detaille", "detailler",
        "modifie", "modifier", "corrige", "corriger", "confirme", "confirmer",
        "ajoute", "ajouter", "met a jour", "mise a jour", "indique",
    ),
    "CREATE": (
        "nouvel objet", "nouvelle carte", "creer", "creation", "ouvrir un sujet",
    ),
}


class EffectPreviewError(ValueError):
    """The bounded preview request cannot be evaluated safely."""


@dataclass(frozen=True)
class ProjectObject:
    object_type: ObjectKind
    object_id: str
    card_id: str
    title: str
    status: str
    searchable_text: str
    explicit_refs: tuple[str, ...]


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_marks.lower()).strip()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalize(value))
        if len(token) >= 3 and token not in _STOPWORDS
    }


def _confidence(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.38:
        return "medium"
    return "low"


def _proposal_id(project_id: str, information: str, effect: str, target_id: str) -> str:
    payload = "\0".join((project_id, information, effect, target_id))
    return f"proposal-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def _information_digest(information: str) -> str:
    return f"sha256:{hashlib.sha256(information.encode('utf-8')).hexdigest()}"


def _effect_from_text(
    information: str,
    hint: EffectKind | None,
    has_target: bool,
) -> tuple[EffectKind, str]:
    if hint is not None:
        return hint, "explicit_hint"
    if not has_target:
        return "CREATE", "no_matching_object"
    normalized = _normalize(information)
    for effect in ("CONFLICT", "SUPERSEDE", "UPDATE"):
        for cue in _CUES[effect]:
            if cue in normalized:
                return effect, f"deterministic_cue:{cue}"
    return "UPDATE", "matched_object_default"


def _object_score(
    information: str,
    obj: ProjectObject,
    explicit_refs: set[str],
) -> tuple[float, list[str]]:
    normalized_refs = {_normalize(ref) for ref in obj.explicit_refs if ref}
    if normalized_refs & explicit_refs:
        return 1.0, ["Référence d’objet explicitement fournie."]

    info_norm = _normalize(information)
    title_norm = _normalize(obj.title)
    info_tokens = _tokens(information)
    title_tokens = _tokens(obj.title)
    all_tokens = _tokens(obj.searchable_text)

    if title_norm and len(title_norm) >= 5 and title_norm in info_norm:
        return 0.96, ["Le titre de l’objet apparaît dans l’information."]

    title_overlap = len(info_tokens & title_tokens) / max(1, len(title_tokens))
    information_overlap = len(info_tokens & all_tokens) / max(1, len(info_tokens))
    score = min(0.94, title_overlap * 0.62 + information_overlap * 0.38)
    reasons: list[str] = []
    common_title = sorted(info_tokens & title_tokens)
    common_all = sorted((info_tokens & all_tokens) - set(common_title))
    if common_title:
        reasons.append(f"Termes communs au titre : {', '.join(common_title[:6])}.")
    if common_all:
        reasons.append(f"Termes communs au contexte : {', '.join(common_all[:6])}.")
    return score, reasons


def _document_object(item: dict) -> ProjectObject:
    naming = item.get("naming") or {}
    title = naming.get("object_name") or naming.get("document_type") or item.get("title") or "Document"
    searchable = " ".join(
        str(value)
        for value in (
            title,
            item.get("title"),
            item.get("source_ref"),
            naming.get("project_code"),
            naming.get("phase_code"),
            naming.get("phase_folder"),
            naming.get("document_type"),
            naming.get("object_name"),
        )
        if value
    )
    document_id = str(item.get("document_id") or "")
    card_id = str(item.get("card_id") or f"card-{document_id}")
    return ProjectObject(
        object_type="document",
        object_id=document_id,
        card_id=card_id,
        title=str(title),
        status=str(item.get("analysis_status") or "unknown"),
        searchable_text=searchable,
        explicit_refs=tuple(filter(None, (document_id, card_id, item.get("source_ref")))),
    )


def _knowledge_object(item: dict) -> ProjectObject:
    knowledge_id = str(item.get("knowledge_id") or "")
    card_id = str(item.get("card_id") or f"card-{knowledge_id}")
    title = str(item.get("title") or "Knowledge")
    searchable = " ".join(
        str(value)
        for value in (title, knowledge_id, item.get("family"), item.get("document_ref"))
        if value
    )
    return ProjectObject(
        object_type="knowledge",
        object_id=knowledge_id,
        card_id=card_id,
        title=title,
        status=str(item.get("review_status") or "unknown"),
        searchable_text=searchable,
        explicit_refs=tuple(filter(None, (knowledge_id, card_id, item.get("document_ref")))),
    )


def _work_issue_object(projection: dict) -> ProjectObject:
    issue = projection.get("work_issue") or {}
    issue_id = str(issue.get("issue_id") or "")
    card_id = f"card-{issue_id}"
    title = str(issue.get("title") or "Work Issue")
    comments = " ".join(str(item.get("body") or "") for item in projection.get("comments") or [])
    searchable = " ".join(
        str(value)
        for value in (
            title,
            issue_id,
            issue.get("description"),
            issue.get("issue_type"),
            issue.get("priority"),
            issue.get("assigned_to"),
            issue.get("task_contract_ref"),
            issue.get("context_pack_ref"),
            comments,
        )
        if value
    )
    return ProjectObject(
        object_type="work_issue",
        object_id=issue_id,
        card_id=card_id,
        title=title,
        status=str(issue.get("status") or "unknown"),
        searchable_text=searchable,
        explicit_refs=tuple(filter(None, (issue_id, card_id, issue.get("primary_card_ref")))),
    )


def collect_project_objects(conn, parent_project_id: str) -> list[ProjectObject]:
    """Collect only owner projections whose exact project parent is opened."""
    documents = store.list_document_cards(conn, parent_project_id)
    knowledge_items = knowledge.list_knowledge_cards(conn, parent_project_id)
    issues = work_issue_read.list_issue_projections(
        conn,
        parent_project_id,
        include_terminal=True,
        limit=100,
    )
    return [
        *(_document_object(item) for item in documents),
        *(_knowledge_object(item) for item in knowledge_items),
        *(_work_issue_object(item) for item in issues),
    ]


def preview_from_objects(
    *,
    parent_project_id: str,
    information: str,
    objects: Iterable[ProjectObject],
    explicit_object_refs: Iterable[str] = (),
    effect_hint: EffectKind | None = None,
    max_proposals: int = 5,
) -> dict:
    """Return deterministic candidate effects without persisting or applying them."""
    information = information.strip()
    parent_project_id = parent_project_id.strip()
    refs = {_normalize(ref) for ref in explicit_object_refs if ref.strip()}
    if not parent_project_id:
        raise EffectPreviewError("parent_project_id is required")
    if len(information) < 3 or len(information) > 4000:
        raise EffectPreviewError("information length must be between 3 and 4000 characters")
    if len(refs) > 10:
        raise EffectPreviewError("at most 10 explicit object references are allowed")
    if max_proposals < 1 or max_proposals > 10:
        raise EffectPreviewError("max_proposals must be between 1 and 10")

    ranked: list[tuple[float, ProjectObject, list[str]]] = []
    for obj in objects:
        score, reasons = _object_score(information, obj, refs)
        if score >= 0.18 or score == 1.0:
            ranked.append((score, obj, reasons))
    ranked.sort(key=lambda item: (-item[0], item[1].object_type, item[1].object_id))
    ranked = ranked[:max_proposals]

    proposals: list[dict] = []
    if not ranked:
        effect, effect_source = _effect_from_text(information, effect_hint, has_target=False)
        proposals.append(
            {
                "proposal_id": _proposal_id(parent_project_id, information, effect, "unclassified"),
                "effect": effect,
                "effect_source": effect_source,
                "target": None,
                "candidate_object_type": "unclassified",
                "score": 0.0,
                "confidence": "low",
                "reasons": [
                    "Aucun objet existant n’atteint le seuil de rapprochement déterministe.",
                    "Le type du nouvel objet doit être choisi par un humain avant toute création.",
                ],
                "requires_human_confirmation": True,
                "apply_route": None,
            }
        )
    else:
        for score, obj, reasons in ranked:
            effect, effect_source = _effect_from_text(information, effect_hint, has_target=True)
            proposals.append(
                {
                    "proposal_id": _proposal_id(parent_project_id, information, effect, obj.object_id),
                    "effect": effect,
                    "effect_source": effect_source,
                    "target": {
                        "object_type": obj.object_type,
                        "object_id": obj.object_id,
                        "card_id": obj.card_id,
                        "title": obj.title,
                        "current_status": obj.status,
                    },
                    "candidate_object_type": obj.object_type,
                    "score": round(score, 4),
                    "confidence": _confidence(score),
                    "reasons": reasons or ["Rapprochement lexical faible à vérifier."],
                    "requires_human_confirmation": True,
                    "apply_route": None,
                }
            )

    ambiguous = len(proposals) > 1 and proposals[0]["score"] - proposals[1]["score"] < 0.12
    return {
        "parent_project_id": parent_project_id,
        "status": "proposal_only",
        "matching_mode": "exact_project_then_deterministic_lexical",
        "information_digest": _information_digest(information),
        "explicit_object_refs": sorted(refs),
        "ambiguous": ambiguous,
        "proposals": proposals,
        "limits": [
            "No proposal is persisted.",
            "No object or card is created, updated, superseded or marked in conflict.",
            "Lexical similarity is orientation, not evidence or truth.",
            "Human confirmation and an owner-specific write path remain required.",
        ],
    }


def preview_project_effects(
    conn,
    *,
    parent_project_id: str,
    information: str,
    explicit_object_refs: Iterable[str] = (),
    effect_hint: EffectKind | None = None,
    max_proposals: int = 5,
) -> dict:
    try:
        objects = collect_project_objects(conn, parent_project_id)
    except work_issues.WorkIssueError as exc:
        raise EffectPreviewError(str(exc)) from exc
    return preview_from_objects(
        parent_project_id=parent_project_id,
        information=information,
        objects=objects,
        explicit_object_refs=explicit_object_refs,
        effect_hint=effect_hint,
        max_proposals=max_proposals,
    )
