"""Read-only reader/projector for a per-module verification preset.

A verification preset (``schemas/verification_preset.schema.yaml``) declares, per
module, which read-only verifications apply and the thresholds the evidence should
meet. This loads a provided preset, validates it against that schema, and projects
it into a *plan as data*: for each active verification, its thresholds and the
evidence fields a producer should gather. It runs no verification, gathers no
evidence, probes nothing and decides nothing — it only tells a producer (Hermes,
an operator, the cockpit) what to gather and against which bar. The verify_* tools
still classify the gathered evidence and return verdicts. The gate and the human
decide.
"""

from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

from .repo import find_repo_root, read_repo_text

SCHEMA_PATH = "schemas/verification_preset.schema.yaml"

# The evidence fields a producer should gather for each verification, so the plan
# tells a producer exactly what each verify_* tool expects. Mirrors the evidence
# schemas (install / observability / backup / exposure / update).
EVIDENCE_FIELDS = {
    "install": ["installed", "installed_markers", "install_success_markers", "logs", "health", "checks", "expected_checks"],
    "observability": ["signals", "expected_signals", "freshness", "errors"],
    "backup": ["present", "backup_markers", "freshness", "restore"],
    "exposure": ["reach", "auth", "scope"],
    "update": ["current_version", "available_version", "channel"],
}


def _load_schema(root: Path) -> dict:
    return yaml.safe_load(read_repo_text(SCHEMA_PATH, root))


def load_verification_preset(preset: dict) -> dict:
    """Validate a verification preset and project it into a verification plan as
    data. Read-only: it runs no verification and decides nothing."""
    if not isinstance(preset, dict):
        return {
            "result": "error",
            "problems": ["preset must be a mapping (a verification_preset object)"],
            "posture": "read-only",
            "decides": False,
        }

    root = find_repo_root()
    schema = _load_schema(root)
    validator = jsonschema.Draft202012Validator(schema)
    problems = []
    for e in sorted(validator.iter_errors(preset), key=lambda x: list(x.path)):
        path = ".".join(str(p) for p in e.path) or "<root>"
        problems.append(f"{path}: {e.message}")
    if problems:
        return {
            "result": "error",
            "module_id": str(preset.get("module_id") or "unknown"),
            "problems": problems,
            "posture": "read-only",
            "decides": False,
        }

    verifications = preset.get("verifications") or {}
    active = []
    inactive = []
    for name in EVIDENCE_FIELDS:  # deterministic, known order
        block = verifications.get(name)
        if not isinstance(block, dict):
            inactive.append(name)
            continue
        if block.get("applies") is False:
            inactive.append(name)
            continue
        thresholds = {k: v for k, v in block.items() if k != "applies"}
        active.append(
            {
                "verification": name,
                "thresholds": thresholds,
                "evidence_fields": EVIDENCE_FIELDS[name],
            }
        )

    gaps = []
    if not active:
        gaps.append("no verification applies in this preset")

    return {
        "result": "ok",
        "module_id": str(preset.get("module_id") or "unknown"),
        "active": active,
        "inactive": inactive,
        "capability_gaps": gaps,
        "posture": "read-only",
        "decides": False,
        "note": (
            "Projects a validated preset into a plan as data; runs no verification, "
            "gathers no evidence and decides nothing. A producer gathers the "
            "evidence; the verify_* tools classify it; the gate and the human decide."
        ),
    }
