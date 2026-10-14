"""Proposal-only navigation profiles for Knowledge-linked web sites.

The module classifies already-linked public sites and proposes bounded retrieval
strategies and candidate Hermes bindings. It performs no network request, does
not query a skill catalog, installs nothing, persists nothing and grants no
activation authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlsplit

from . import knowledge, resource_profiles


class SiteNavigationProfileError(ValueError):
    """A navigation profile cannot be produced inside the declared scope."""


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _normalize_task(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    if len(value) < 3 or len(value) > 500:
        raise SiteNavigationProfileError("task must contain between 3 and 500 characters")
    return value


def _site_archetype(host: str, site_kind: str) -> dict:
    host = host.lower()
    if "legifrance" in host:
        return {
            "id": "legal_database",
            "entry_points": ["site_search", "codes", "consolidated_texts", "jurisprudence"],
            "task_families": [
                "find_code_article",
                "check_version_in_force",
                "find_related_legal_texts",
                "retrieve_canonical_legal_url",
            ],
            "preferred_strategy": "structured_search_then_version_check",
            "verification_fields": ["canonical_url", "document_title", "version_date", "status_in_force"],
        }
    if "sitesecurite" in host:
        return {
            "id": "hierarchical_safety_reference",
            "entry_points": ["site_search", "erp_tree", "topic_navigation"],
            "task_families": [
                "find_erp_rule",
                "navigate_regulation_tree",
                "retrieve_article_reference",
            ],
            "preferred_strategy": "hierarchical_browse_then_article_check",
            "verification_fields": ["canonical_url", "section_path", "article_reference", "page_title"],
        }
    if site_kind == "geodata" or any(token in host for token in ("geoportail", "cadastre", "geodata")):
        return {
            "id": "interactive_geospatial_portal",
            "entry_points": ["place_search", "layer_catalog", "map_view", "data_download"],
            "task_families": [
                "locate_place_or_parcel",
                "identify_available_layer",
                "retrieve_dataset_metadata",
            ],
            "preferred_strategy": "api_or_catalog_first_then_browser_map",
            "verification_fields": ["canonical_url", "dataset_or_layer_id", "geographic_scope", "source_authority"],
        }
    if site_kind in {"official_public_site", "public_data"}:
        return {
            "id": "public_information_portal",
            "entry_points": ["site_search", "topic_navigation", "dataset_catalog"],
            "task_families": ["find_official_information", "retrieve_public_dataset_metadata"],
            "preferred_strategy": "search_or_catalog_first",
            "verification_fields": ["canonical_url", "page_title", "publisher", "updated_at"],
        }
    return {
        "id": "generic_web_information_site",
        "entry_points": ["site_search", "navigation_tree", "direct_page"],
        "task_families": ["find_relevant_page", "retrieve_page_metadata"],
        "preferred_strategy": "extract_first_then_browser_fallback",
        "verification_fields": ["canonical_url", "page_title", "publisher", "retrieved_at"],
    }


def _candidate_bindings(host: str, archetype: str) -> list[dict]:
    slug = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return [
        {
            "binding_kind": "browse_sh_skill",
            "candidate_ref": f"browse-sh/{host}/<task-specific-skill>",
            "discovery_query": host,
            "status": "to_verify",
            "installed": False,
            "approved": False,
            "healthy": "not_checked",
            "activation": "not_authorized",
        },
        {
            "binding_kind": "hermes_local_skill",
            "candidate_ref": f"local/{slug}/{archetype}/<task>",
            "status": "candidate_not_created",
            "installed": False,
            "approved": False,
            "healthy": "not_checked",
            "activation": "not_authorized",
        },
        {
            "binding_kind": "hermes_generic_web_tools",
            "candidate_ref": "hermes:web_search|web_extract|browser",
            "status": "fallback_candidate",
            "installed": "runtime_dependent",
            "approved": False,
            "healthy": "not_checked",
            "activation": "task_contract_required",
        },
    ]


def preview_site_navigation_profiles(
    conn,
    *,
    parent_project_id: str,
    knowledge_id: str,
    task: str,
    selected_urls: list[str] | None = None,
) -> dict:
    """Return deterministic navigation candidates for exact linked sites only."""
    parent_project_id = parent_project_id.strip()
    knowledge_id = knowledge_id.strip()
    task = _normalize_task(task)
    if not parent_project_id or not knowledge_id:
        raise SiteNavigationProfileError("parent_project_id and knowledge_id are required")

    card = knowledge.get_knowledge_card(conn, knowledge_id)
    if card.get("parent_project_id") != parent_project_id:
        raise SiteNavigationProfileError("Knowledge does not belong to the exact opened project")

    linked_sites = resource_profiles.extract_linked_sites(
        knowledge.get_knowledge_markdown(conn, knowledge_id)
    )
    if not linked_sites:
        raise SiteNavigationProfileError("Knowledge contains no linked web address")
    linked_by_url = {site["url"]: site for site in linked_sites}

    chosen_urls = selected_urls or list(linked_by_url)
    if not 1 <= len(chosen_urls) <= 10:
        raise SiteNavigationProfileError("between 1 and 10 linked sites must be selected")

    profiles = []
    seen = set()
    for raw_url in chosen_urls:
        canonical_matches = resource_profiles.extract_linked_sites(str(raw_url))
        if len(canonical_matches) != 1:
            raise SiteNavigationProfileError("each selected site must contain one valid HTTP(S) URL")
        canonical_url = canonical_matches[0]["url"]
        if canonical_url not in linked_by_url:
            raise SiteNavigationProfileError(
                "selected URL is not already present in the exact Knowledge item"
            )
        if canonical_url in seen:
            continue
        seen.add(canonical_url)
        site = linked_by_url[canonical_url]
        host = urlsplit(canonical_url).hostname or ""
        archetype = _site_archetype(host, site["site_kind"])
        profiles.append(
            {
                "url": canonical_url,
                "host": host,
                "site_kind": site["site_kind"],
                "profile_status": "candidate",
                "profile_basis": "deterministic_host_and_site_kind_mapping",
                "archetype": archetype,
                "navigation_plan": {
                    "task": task,
                    "sequence": [
                        "prefer an official API or structured search when exposed",
                        "otherwise use the site's own search and bounded hierarchy",
                        "use interactive browser navigation only when extraction is insufficient",
                        "retain canonical URL and verification fields",
                        "return result and trace as candidates for human review",
                    ],
                    "read_only": True,
                    "login_allowed": False,
                    "external_submission_allowed": False,
                },
                "candidate_bindings": _candidate_bindings(host, archetype["id"]),
            }
        )

    profiles.sort(key=lambda item: (item["host"], item["url"]))
    payload = {
        "schema": "pantheon.site_navigation_profile_candidate.v1",
        "parent_project_id": parent_project_id,
        "knowledge_id": knowledge_id,
        "task": task,
        "profiles": profiles,
    }
    return {
        "status": "proposal_only",
        "profile_digest": _digest(payload),
        **payload,
        "capability_slot": {
            "function": "site_specific_information_retrieval",
            "candidate_hermes_binding": "per_site_and_task_to_verify",
            "installation_status": "not_assessed",
            "health": "not_checked",
            "update_status": "not_checked",
            "activation": "not_authorized",
        },
        "gates": [
            {"gate": "skill_discovery_or_local_skill_review", "status": "open"},
            {"gate": "human_task_scope_approval", "status": "open"},
            {"gate": "binding_health_review", "status": "open"},
            {"gate": "activation_authorization", "status": "open"},
        ],
        "execution": {
            "status": "not_created",
            "network_requests": 0,
            "catalog_queries": 0,
            "skills_installed": 0,
            "persisted": False,
        },
        "distinctions": [
            "profile candidate != site understood",
            "skill discovered != skill installed",
            "installed != approved",
            "healthy != safe",
            "navigation success != Evidence",
            "page found != rule applicable to the project",
        ],
    }
