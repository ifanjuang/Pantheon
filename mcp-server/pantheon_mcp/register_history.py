"""Read-only coherence checks for Register Candidate history.

This module extends the existing Registre Probatoire validation seam without
creating a new record type or authority. It only evaluates already-declared
RegisterCandidate history:

- rejected candidates must not silently reappear as unrelated later candidates
  with the same exact scope and normalized claim;
- supersession references must preserve a coherent append-only history.

The check never rejects, approves, supersedes or mutates a candidate itself.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .repo import find_repo_root


TERMINAL_PREDECESSOR_STATUSES = {"superseded", "rejected", "revoked", "archived"}


def _scope_key(candidate: dict[str, Any]) -> tuple[str, str]:
    scope = candidate.get("scope")
    if not isinstance(scope, dict):
        return ("", "")
    return (str(scope.get("scope_type") or ""), str(scope.get("scope_id") or ""))


def _claim_key(candidate: dict[str, Any]) -> str:
    """Return a bounded exact-text key; this is deliberately not semantic matching."""

    return " ".join(str(candidate.get("claim") or "").casefold().split())


def _created_at(candidate: dict[str, Any]) -> datetime | None:
    value = candidate.get("created_at")
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _chain_reaches(
    candidate_id: str,
    target_id: str,
    by_id: dict[str, dict[str, Any]],
) -> bool:
    """Return whether the declared supersession chain reaches target_id."""

    seen: set[str] = set()
    current_id = candidate_id
    while current_id and current_id not in seen:
        seen.add(current_id)
        current = by_id.get(current_id)
        if current is None:
            return False
        predecessor_id = current.get("supersedes_candidate_id")
        if not isinstance(predecessor_id, str) or not predecessor_id:
            return False
        if predecessor_id == target_id:
            return True
        current_id = predecessor_id
    return False


def evaluate_register_history(candidates: list[dict[str, Any]]) -> list[str]:
    """Evaluate bounded non-resurrection and supersession invariants.

    Inputs are expected to have already passed ``register_candidate.schema.yaml``.
    The function remains defensive because tests may call it directly with small
    synthetic candidates.
    """

    violations: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            violations.append("candidate without candidate_id cannot participate in history")
            continue
        if candidate_id in by_id:
            violations.append(f"duplicate candidate_id in history: {candidate_id}")
            continue
        by_id[candidate_id] = candidate

    successors: dict[str, list[dict[str, Any]]] = {}

    for candidate_id, candidate in by_id.items():
        predecessor_id = candidate.get("supersedes_candidate_id")
        if predecessor_id in (None, ""):
            continue
        if not isinstance(predecessor_id, str):
            violations.append(f"{candidate_id} has a non-string supersedes_candidate_id")
            continue
        if predecessor_id == candidate_id:
            violations.append(f"{candidate_id} cannot supersede itself")
            continue

        predecessor = by_id.get(predecessor_id)
        if predecessor is None:
            violations.append(
                f"{candidate_id} supersedes unknown candidate '{predecessor_id}'"
            )
            continue

        successors.setdefault(predecessor_id, []).append(candidate)

        if _scope_key(candidate) != _scope_key(predecessor):
            violations.append(
                f"{candidate_id} supersedes {predecessor_id} across different scopes"
            )

        successor_time = _created_at(candidate)
        predecessor_time = _created_at(predecessor)
        if (
            successor_time is not None
            and predecessor_time is not None
            and successor_time <= predecessor_time
        ):
            violations.append(
                f"{candidate_id} must be created after superseded candidate {predecessor_id}"
            )

        if (
            candidate.get("status") == "approved"
            and predecessor.get("status") not in TERMINAL_PREDECESSOR_STATUSES
        ):
            violations.append(
                f"approved successor {candidate_id} cannot leave predecessor "
                f"{predecessor_id} in active status '{predecessor.get('status')}'"
            )

    # Explicitly catch longer cycles, not only direct self-supersession.
    for candidate_id in by_id:
        seen: set[str] = set()
        current_id = candidate_id
        while current_id in by_id:
            if current_id in seen:
                violations.append(
                    f"supersession cycle detected from candidate {candidate_id}"
                )
                break
            seen.add(current_id)
            predecessor_id = by_id[current_id].get("supersedes_candidate_id")
            if not isinstance(predecessor_id, str) or not predecessor_id:
                break
            current_id = predecessor_id

    # A candidate marked superseded is no longer current; the dossier must show
    # the approved successor that replaced it rather than only the terminal flag.
    for candidate_id, candidate in by_id.items():
        if candidate.get("status") != "superseded":
            continue
        approved_successors = [
            item for item in successors.get(candidate_id, []) if item.get("status") == "approved"
        ]
        if not approved_successors:
            violations.append(
                f"superseded candidate {candidate_id} has no approved successor in the dossier"
            )

    # Tombstone-like behavior without a Tombstone object: exact-scope + normalized
    # claim reappearance must preserve the rejected candidate in the explicit
    # supersession chain. This intentionally does not attempt semantic paraphrase
    # detection; retrieved text is not a truth engine.
    rejected = [item for item in by_id.values() if item.get("status") == "rejected"]
    for prior in rejected:
        prior_id = str(prior.get("candidate_id"))
        prior_time = _created_at(prior)
        prior_key = (_scope_key(prior), _claim_key(prior))
        if not prior_key[1]:
            continue
        for later_id, later in by_id.items():
            if later_id == prior_id:
                continue
            later_time = _created_at(later)
            if prior_time is not None and later_time is not None and later_time <= prior_time:
                continue
            if (_scope_key(later), _claim_key(later)) != prior_key:
                continue
            if not _chain_reaches(later_id, prior_id, by_id):
                violations.append(
                    f"{later_id} silently resurrects rejected candidate {prior_id}; "
                    "explicit supersession history is required"
                )

    return violations


def check_register_history(root: Path | None = None) -> dict[str, Any]:
    """Evaluate candidate history in the existing cascade-register corpus."""

    root = root or find_repo_root()
    instances_dir = root / "docs" / "examples" / "cascade_register"
    if not instances_dir.is_dir():
        return {
            "ok": False,
            "status": "not_run",
            "message": "Required cascade-register instance directory is missing.",
            "candidates_checked": 0,
            "violations": [],
        }

    candidates: list[dict[str, Any]] = []
    violations: list[dict[str, str]] = []
    for path in sorted(instances_dir.rglob("*.y*ml")):
        rel = str(path.relative_to(root))
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            violations.append({"file": rel, "message": f"YAML parse failed: {exc}"})
            continue
        if isinstance(data, dict) and "candidate_id" in data:
            candidates.append(data)

    if not candidates:
        return {
            "ok": False,
            "status": "not_run",
            "message": "No Register Candidate was discovered in the required corpus.",
            "candidates_checked": 0,
            "violations": violations,
        }

    for message in evaluate_register_history(candidates):
        violations.append({"file": str(instances_dir.relative_to(root)), "message": message})

    return {
        "ok": not violations,
        "status": "pass" if not violations else "fail",
        "message": (
            f"{len(candidates)} Register Candidate(s) passed history coherence validation."
            if not violations
            else "Register Candidate history contains resurrection or supersession violations."
        ),
        "candidates_checked": len(candidates),
        "violations": violations,
    }
