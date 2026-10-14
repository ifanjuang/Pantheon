"""Proposal-only site structure manifest preview.

This module validates an explicit crawl perimeter against web addresses already
written in one exact Knowledge item. It performs no network request, persists no
manifest, selects no runtime binding and grants no activation authority.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
from urllib.parse import urlsplit, urlunsplit

from . import knowledge, resource_profiles


class SiteManifestPreviewError(ValueError):
    """A structure manifest candidate exceeds the bounded preview contract."""


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _canonical_selected_url(value: str) -> str:
    raw = value.strip()
    parsed = urlsplit(raw)
    if parsed.username or parsed.password:
        raise SiteManifestPreviewError("credential-bearing URLs are forbidden")
    matches = resource_profiles.extract_linked_sites(raw)
    if len(matches) != 1:
        raise SiteManifestPreviewError("each selected site must contain one valid HTTP(S) URL")
    return matches[0]["url"]


def _assert_public_host(host: str) -> None:
    lowered = host.lower().rstrip(".")
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".local"):
        raise SiteManifestPreviewError("local or mDNS hosts cannot enter a crawl manifest")
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        return
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise SiteManifestPreviewError("private, loopback or reserved IP targets are forbidden")


def _normalize_path_prefix(value: str) -> str:
    value = value.strip()
    if not value:
        return "/"
    if not value.startswith("/"):
        raise SiteManifestPreviewError("path prefixes must start with /")
    segments = value.split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise SiteManifestPreviewError("path prefixes cannot contain dot traversal segments")
    normalized = "/" + "/".join(segment for segment in segments if segment)
    if value.endswith("/") and normalized != "/":
        normalized += "/"
    return normalized or "/"


def _prefix_contains_path(prefix: str, path: str) -> bool:
    normalized_prefix = prefix.rstrip("/") or "/"
    normalized_path = path.rstrip("/") or "/"
    if normalized_prefix == "/":
        return True
    return normalized_path == normalized_prefix or normalized_path.startswith(normalized_prefix + "/")


def preview_structure_manifest(
    conn,
    *,
    parent_project_id: str,
    knowledge_id: str,
    mode: str,
    sites: list[dict],
) -> dict:
    """Return a deterministic, non-persisted structure-only manifest candidate."""
    parent_project_id = parent_project_id.strip()
    knowledge_id = knowledge_id.strip()
    if not parent_project_id or not knowledge_id:
        raise SiteManifestPreviewError("parent_project_id and knowledge_id are required")
    if mode != "structure_only":
        raise SiteManifestPreviewError("this bounded preview supports structure_only only")
    if not 1 <= len(sites) <= 10:
        raise SiteManifestPreviewError("between 1 and 10 linked sites must be selected")

    card = knowledge.get_knowledge_card(conn, knowledge_id)
    if card.get("parent_project_id") != parent_project_id:
        raise SiteManifestPreviewError("Knowledge does not belong to the exact opened project")

    markdown = knowledge.get_knowledge_markdown(conn, knowledge_id)
    linked = {
        item["url"]: item
        for item in resource_profiles.extract_linked_sites(markdown)
    }
    if not linked:
        raise SiteManifestPreviewError("Knowledge contains no linked web address")

    manifest_sites: list[dict] = []
    warnings: list[str] = []
    seen_scopes: set[tuple] = set()
    for requested in sites:
        selected_url = _canonical_selected_url(str(requested.get("url") or ""))
        linked_site = linked.get(selected_url)
        if linked_site is None:
            raise SiteManifestPreviewError(
                "selected URL is not already present in the exact Knowledge item"
            )

        parsed = urlsplit(selected_url)
        host = parsed.hostname or ""
        _assert_public_host(host)
        if parsed.scheme == "http":
            warnings.append(f"{host}: insecure HTTP transport remains visible")

        max_depth = int(requested.get("max_depth", 2))
        if not 0 <= max_depth <= 5:
            raise SiteManifestPreviewError("max_depth must be between 0 and 5")
        raw_prefixes = requested.get("path_prefixes") or [parsed.path or "/"]
        if not 1 <= len(raw_prefixes) <= 8:
            raise SiteManifestPreviewError("each site requires between 1 and 8 path prefixes")
        prefixes = sorted({_normalize_path_prefix(str(prefix)) for prefix in raw_prefixes})
        seed_path = parsed.path or "/"
        scope_expansion = any(
            prefix != _normalize_path_prefix(seed_path)
            and _prefix_contains_path(prefix, seed_path)
            for prefix in prefixes
        )
        if scope_expansion:
            warnings.append(
                f"{host}: proposed path scope is broader than the linked seed URL"
            )
        if max_depth > 3:
            warnings.append(f"{host}: depth {max_depth} requires heightened review")

        origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        scope_key = (origin, tuple(prefixes), max_depth)
        if scope_key in seen_scopes:
            continue
        seen_scopes.add(scope_key)
        manifest_sites.append(
            {
                "seed_url": selected_url,
                "origin": origin,
                "host": host,
                "site_kind": linked_site["site_kind"],
                "path_prefixes": prefixes,
                "max_depth": max_depth,
                "same_host_only": True,
                "follow_subdomains": False,
                "query_policy": "drop_for_traversal",
                "fragment_policy": "drop",
                "scope_expansion_from_seed": scope_expansion,
            }
        )

    manifest_sites.sort(key=lambda item: (item["host"], item["seed_url"]))
    if not manifest_sites:
        raise SiteManifestPreviewError("no distinct site scope remains after normalization")
    if len({item["origin"] for item in manifest_sites}) > 1:
        warnings.append("multiple origins are grouped in one candidate and require explicit review")

    manifest = {
        "schema": "pantheon.web_structure_manifest_candidate.v1",
        "parent_project_id": parent_project_id,
        "knowledge_id": knowledge_id,
        "mode": "structure_only",
        "sites": manifest_sites,
        "capture": {
            "page_url": True,
            "page_title": True,
            "headings": True,
            "link_graph": True,
            "short_description": False,
            "body_text": False,
            "images": False,
            "downloads": False,
        },
        "politeness_candidate": {
            "respect_robots_txt": True,
            "max_requests_per_second": 0.5,
            "max_pages_per_origin": 500,
        },
    }
    manifest_digest = _digest(manifest)
    return {
        "status": "proposal_only",
        "manifest_id": f"manifest-preview-{manifest_digest.removeprefix('sha256:')[:24]}",
        "manifest_digest": manifest_digest,
        "manifest": manifest,
        "warnings": sorted(set(warnings)),
        "capability_slot": {
            "function": "web_structure_discovery",
            "candidate_hermes_binding": None,
            "installation_status": "not_assessed",
            "health": "not_checked",
            "update_status": "not_checked",
            "activation": "not_authorized",
        },
        "gates": [
            {"gate": "human_scope_approval", "status": "open"},
            {"gate": "binding_selection", "status": "open"},
            {"gate": "runtime_health_review", "status": "open"},
            {"gate": "activation_authorization", "status": "open"},
        ],
        "execution": {
            "status": "not_created",
            "network_requests": 0,
            "persisted": False,
            "scheduled": False,
        },
        "indexing": {
            "status": "not_indexed",
            "structure_indexed": False,
            "body_vectorization": False,
            "content_adopted": False,
        },
        "distinctions": [
            "manifest preview != crawl authorization",
            "binding selected != dependency adopted",
            "structure indexed != content adopted",
            "vectorized != Evidence",
            "runtime success != proof",
        ],
    }
