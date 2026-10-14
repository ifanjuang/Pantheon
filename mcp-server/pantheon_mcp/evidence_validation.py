"""Fail-closed validation for read-only verification evidence.

The verification classifiers deliberately accept incomplete evidence and turn
missing signals into capability gaps. Evidence that is present, however, must
match its governance schema exactly: coercing strings, numbers or containers to
booleans can manufacture a positive assurance verdict.
"""

from __future__ import annotations

import jsonschema
import yaml

from .repo import RepoNotFound, find_repo_root


def _display_path(path) -> str:
    rendered = "$"
    for part in path:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def validate_evidence(evidence, schema_path: str) -> list[str]:
    """Return deterministic validation problems for one evidence payload.

    Missing optional evidence remains valid and is handled by each classifier
    as a capability gap. A missing or invalid schema is itself a blocking
    validation problem so verification never falls back to permissive logic.
    """
    if not isinstance(evidence, dict):
        return ["$: evidence must be a mapping"]

    try:
        root = find_repo_root()
        path = (root / schema_path).resolve()
        if root != path and root not in path.parents:
            raise PermissionError(f"schema path escapes repository root: {schema_path}")
        schema = yaml.safe_load(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    except (
        OSError,
        PermissionError,
        RepoNotFound,
        yaml.YAMLError,
        jsonschema.SchemaError,
    ) as exc:
        return [f"evidence schema unavailable or invalid ({schema_path}): {exc}"]

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(evidence),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message),
    )
    return [f"{_display_path(error.absolute_path)}: {error.message}" for error in errors]


def invalid_evidence_report(problems: list[str]) -> dict:
    """Build the common non-positive result returned for malformed evidence."""
    return {
        "result": "error",
        "verdict": "invalid",
        "problems": [f"invalid evidence: {problem}" for problem in problems],
        "capability_gaps": [],
        "posture": "read-only",
        "decides": False,
    }


def verdict_report(
    evidence: dict,
    *,
    axes: dict,
    verdict: str,
    gaps: list[str],
    note: str,
) -> dict:
    """Build the positive result envelope shared by every ``verify_*`` classifier.

    Each verification owns its own axes and its own verdict ladder — what
    "degraded" means for a backup is not what it means for an exposure surface.
    What they must never diverge on is the envelope around that verdict: the
    same keys, in the same order, always reporting a read-only posture that
    decides nothing. Five hand-written copies could drift on any of those, and a
    consumer reading ``decides`` or ``posture`` would have no way to notice.

    ``axes`` is inserted verbatim between the component and the verdict, so each
    classifier keeps its own vocabulary without owning the envelope.
    """
    return {
        "result": "ok",
        "component": str(evidence.get("component") or "unknown"),
        **axes,
        "verdict": verdict,
        "capability_gaps": gaps,
        "posture": "read-only",
        "decides": False,
        "note": note,
    }
