"""Governance invariants for proposal-only effect previews.

The matcher may expose user hints and lexical candidates. This seam guarantees
that the public cockpit response cannot imply an owner mutation without a target
and cannot expose an application route.
"""

from __future__ import annotations

from copy import deepcopy


def enforce_preview(payload: dict) -> dict:
    """Return a guarded copy of a deterministic preview payload."""
    guarded = deepcopy(payload)
    for proposal in guarded.get("proposals") or []:
        proposal["requires_human_confirmation"] = True
        proposal["apply_route"] = None
        if proposal.get("target") is None and proposal.get("effect") != "CREATE":
            requested = str(proposal.get("effect") or "unknown")
            proposal["effect"] = "CREATE"
            proposal["effect_source"] = f"target_required:overrode_{requested.lower()}"
            proposal["candidate_object_type"] = "unclassified"
            reasons = list(proposal.get("reasons") or [])
            reasons.insert(
                0,
                f"L’effet {requested} nécessite une cible existante ; aucune cible n’a été rapprochée.",
            )
            proposal["reasons"] = reasons
    return guarded
