"""The workflow that runs the pin guard must be triggered by everything it reads.

`test_external_qualification_pins.py` scans four roots, only two of which sit
under `implementation/`. `implementation-ci.yml` — the workflow whose "Run
remaining test suite" step actually executes it — was filtered to
`implementation/**` and `schemas/**`.

The consequence was not hypothetical. PR Pantheon-Next#1073 touched only
`deployment/ubuntu/observe-hermes-runtime` and
`tests/test_hermes_runtime_observation_script.py`; neither matched the filter,
the workflow never ran, and the guard stayed red on `main` across five
subsequent merges before anyone looked.

A guard whose reach exceeds its trigger is a control that cannot fire. This test
holds the two together: widen what the guard reads and the filter must follow.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

import yaml

from test_external_qualification_pins import QUALIFICATION_SOURCE_ROOTS

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "implementation-ci.yml"

# The step that runs the whole suite, and therefore the guard.
FULL_SUITE_STEP = "Run remaining test suite"


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    # `on` is the YAML 1.1 boolean True once parsed, unless quoted.
    return workflow.get("on") or workflow.get(True)


def _covers(patterns: list[str], root: str) -> bool:
    """Would any path filter match a file somewhere under `root`?"""
    probe = f"{root}/probe.py"
    return any(fnmatch.fnmatch(probe, pattern) for pattern in patterns)


def test_the_workflow_still_runs_the_whole_suite() -> None:
    """If this step is gone, the guard is no longer run and this file is moot."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert FULL_SUITE_STEP in text, (
        f"{WORKFLOW} no longer has a '{FULL_SUITE_STEP}' step; the pin guard may "
        "not be executed by CI at all."
    )


def test_path_filters_cover_every_root_the_pin_guard_reads() -> None:
    triggers = _triggers(_workflow())
    assert triggers, f"{WORKFLOW} declares no triggers"

    for event in ("push", "pull_request"):
        config = triggers.get(event)
        assert config, f"{WORKFLOW} has no `{event}` trigger"
        patterns = config.get("paths")
        # No `paths` key means the event fires on every change, which trivially
        # covers every root.
        if patterns is None:
            continue
        uncovered = [
            root for root in QUALIFICATION_SOURCE_ROOTS if not _covers(patterns, root)
        ]
        assert not uncovered, (
            f"{WORKFLOW} `{event}.paths` does not cover {uncovered}, which "
            "test_external_qualification_pins.py reads. A change under those "
            "roots would skip this workflow and the guard would not run. Add a "
            "matching glob, or narrow QUALIFICATION_SOURCE_ROOTS."
        )
