#!/usr/bin/env python3
"""Summarize raw Graphify structural output without granting it Pantheon authority.

This is a qualification reader only. It does not write Pantheon state, admit
Evidence, qualify consequential mutations, or turn provider edges into governed
relations. The consequential-mutation inventory remains the owner of mutation
and policy-gate qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

TARGETS = (
    "policy_gate",
    "enforce_consequential",
    "execution_results",
    "apu_owner",
    "knowledge",
    "project_claim",
)


def _edge_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("edges")
    if raw is None:
        raw = payload.get("links")
    return [edge for edge in (raw or []) if isinstance(edge, dict)]


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or node.get("key") or "")


def _node_label(node: dict[str, Any]) -> str:
    return str(node.get("label") or node.get("name") or node.get("title") or _node_id(node))


def _endpoint(edge: dict[str, Any], key: str) -> str:
    value = edge.get(key)
    if isinstance(value, dict):
        return str(value.get("id") or value.get("node_id") or value.get("key") or "")
    return str(value or "")


def _relation(edge: dict[str, Any]) -> str:
    return str(edge.get("relation") or edge.get("type") or edge.get("label") or "unknown")


def _normalized_fingerprint(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    normalized_nodes = sorted(
        (
            _node_id(node),
            _node_label(node),
            str(node.get("type") or node.get("kind") or ""),
            str(node.get("source_file") or node.get("file") or ""),
            str(node.get("source_location") or node.get("location") or ""),
        )
        for node in nodes
    )
    normalized_edges = sorted(
        (
            _endpoint(edge, "source"),
            _endpoint(edge, "target"),
            _relation(edge),
            str(edge.get("confidence") or edge.get("status") or ""),
            str(edge.get("source_file") or edge.get("file") or ""),
            str(edge.get("source_location") or edge.get("location") or ""),
        )
        for edge in edges
    )
    blob = json.dumps(
        {"nodes": normalized_nodes, "edges": normalized_edges},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _sccs(node_ids: set[str], adjacency: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    result: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for nxt in sorted(adjacency.get(node, ())):
            if nxt not in indices:
                visit(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])

        if lowlink[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            result.append(sorted(component))

    for node in sorted(node_ids):
        if node not in indices:
            visit(node)
    return result


def _reachable(start: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    seen = set(start)
    queue = deque(sorted(start))
    while queue:
        current = queue.popleft()
        for nxt in sorted(adjacency.get(current, ())):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    nodes = [node for node in (payload.get("nodes") or []) if isinstance(node, dict)]
    edges = _edge_list(payload)
    labels = {_node_id(node): _node_label(node) for node in nodes if _node_id(node)}
    node_ids = set(labels)

    adjacency: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    degree: Counter[str] = Counter()
    relations: Counter[str] = Counter()
    confidence: Counter[str] = Counter()

    for edge in edges:
        source = _endpoint(edge, "source")
        target = _endpoint(edge, "target")
        if not source or not target:
            continue
        node_ids.update((source, target))
        adjacency[source].add(target)
        reverse[target].add(source)
        degree[source] += 1
        degree[target] += 1
        relations[_relation(edge)] += 1
        tag = str(edge.get("confidence") or edge.get("status") or "unspecified")
        confidence[tag] += 1

    components = _sccs(node_ids, adjacency)
    cyclic = [component for component in components if len(component) > 1]

    target_report: dict[str, Any] = {}
    for needle in TARGETS:
        matches = {
            node_id
            for node_id, label in labels.items()
            if needle.lower() in f"{node_id} {label}".lower()
        }
        downstream = _reachable(matches, adjacency) - matches if matches else set()
        upstream = _reachable(matches, reverse) - matches if matches else set()
        target_report[needle] = {
            "matched_node_count": len(matches),
            "matched_nodes": [
                {"id": node_id, "label": labels.get(node_id, node_id)}
                for node_id in sorted(matches)[:25]
            ],
            "downstream_reachable_count": len(downstream),
            "upstream_reachable_count": len(upstream),
        }

    top_nodes = [
        {"id": node_id, "label": labels.get(node_id, node_id), "degree": count}
        for node_id, count in sorted(degree.items(), key=lambda item: (-item[1], item[0]))[:30]
    ]

    return {
        "schema_id": "pantheon.graphify_structural_qualification_observation",
        "status": "observation_only",
        "authority": {
            "is_evidence": False,
            "is_governed_relation": False,
            "qualifies_mutation_gate": False,
            "authorizes_persistence": False,
            "changes_provider_binding": False,
        },
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "strongly_connected_components": len(components),
            "cyclic_components": len(cyclic),
        },
        "relations": dict(sorted(relations.items())),
        "confidence_tags": dict(sorted(confidence.items())),
        "top_degree_nodes": top_nodes,
        "cyclic_components": [
            [{"id": node_id, "label": labels.get(node_id, node_id)} for node_id in component]
            for component in sorted(cyclic, key=lambda comp: (-len(comp), comp))[:30]
        ],
        "blast_radius_targets": target_report,
        "normalized_graph_fingerprint": _normalized_fingerprint(nodes, edges),
        "interpretation_boundary": (
            "Structural provider output only. Pantheon native mutation inventory remains authoritative "
            "for consequential-write discovery, local guards, and policy-gate verdicts."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.graph.read_text(encoding="utf-8"))
    report = summarize(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
