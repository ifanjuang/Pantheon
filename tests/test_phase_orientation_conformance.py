"""The phase orientation registry stays a faithful projection of its two sources.

The registry is written in French while the domain pack phase map and the index
effect matrix are in English, so the texts cannot be compared word for word.
This test compares their structure instead: the same phase blocks, the same
number of deliverables and minimum evidence items per block, a gate per block,
and a gate risk exactly for the phases the matrix lists. It also checks that
every phase code is a declared project phase and that the two readers (the
implementation and the validation server) answer the same way.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "architecture_phase_orientation.registry.json"
SCHEMA = ROOT / "schemas" / "phase_orientation.schema.yaml"
PHASES = ROOT / "registries" / "architecture_phase_profile.registry.json"
DOMAIN_PACK = ROOT / "docs" / "domain-packs" / "architecture" / "AGENCY_DOMAIN_PACK.md"
INDEX_MATRIX = ROOT / "docs" / "domain-packs" / "architecture" / "INDEX_EFFECT_MATRIX.md"


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    following = re.search(r"^## ", text[start + len(heading):], re.M)
    return text[start: start + len(heading) + following.start()] if following else text[start:]


def _phase_map() -> dict[str, dict[str, list[str]]]:
    """Each phase map block with the lines of its three text blocks."""
    section = _section(DOMAIN_PACK.read_text(encoding="utf-8"), "## Phase map: deliverables, evidence and gates")
    blocks: dict[str, dict[str, list[str]]] = {}
    for match in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)", section, re.M | re.S):
        lists = {}
        for label, key in (("Candidate deliverables:", "deliverables"),
                           ("Minimum evidence:", "minimum_evidence"),
                           ("Gate:", "gate")):
            found = re.search(re.escape(label) + r"\s*```text\n(.*?)```", match.group(2), re.S)
            lists[key] = [line for line in (found.group(1).splitlines() if found else []) if line.strip()]
        blocks[match.group(1).strip()] = lists
    return blocks


def _matrix_risks() -> dict[str, str]:
    section = _section(INDEX_MATRIX.read_text(encoding="utf-8"), "## Phase attachment matrix")
    return dict(re.findall(r"^\| `([A-Z]+)` \|[^|]*\| ([^|]+?) \|\s*$", section, re.M))


def test_registry_validates_against_its_schema() -> None:
    validator = jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))
    validator.validate(_registry())


def test_every_phase_is_a_declared_project_phase_covered_once() -> None:
    declared = {entry["id"]: entry for entry in json.loads(PHASES.read_text(encoding="utf-8"))["entries"]}
    covered = [phase for entry in _registry()["entries"] for phase in entry["phases"]]
    assert len(covered) == len(set(covered))
    for phase in covered:
        assert phase in declared, phase
        assert declared[phase]["category"] != "non_project_scope", phase


def test_blocks_mirror_the_domain_pack_phase_map() -> None:
    phase_map = _phase_map()
    assert phase_map, "no phase map block parsed: the scan is broken"
    entries = {entry["source_section"]: entry for entry in _registry()["entries"]}
    assert set(entries) == set(phase_map)
    for heading, source in phase_map.items():
        entry = entries[heading]
        assert len(entry["deliverables"]) == len(source["deliverables"]), heading
        assert len(entry["minimum_evidence"]) == len(source["minimum_evidence"]), heading
        assert source["gate"] and entry["gate"], heading


def test_gate_risks_mirror_the_index_effect_matrix() -> None:
    risks = _matrix_risks()
    assert risks, "no matrix row parsed: the scan is broken"
    in_registry = {phase for entry in _registry()["entries"] for phase in entry["gate_risks"]}
    covered = {phase for entry in _registry()["entries"] for phase in entry["phases"]}
    assert in_registry == set(risks) & covered
    for entry in _registry()["entries"]:
        assert set(entry["gate_risks"]) <= set(entry["phases"]), entry["id"]


@pytest.fixture(scope="module")
def readers():
    sys.path.insert(0, str(ROOT / "mcp-server"))
    sys.path.insert(0, str(ROOT / "implementation"))
    from pantheon_mcp import phase_orientation as server  # type: ignore
    from mvp_vertical import phase_orientation as owner  # type: ignore

    return server, owner


@pytest.mark.parametrize("phase", ["DIAG", "ESQ", "APS", "DPC", "PRO", "DCE", "ACT", "VISA", "OPC", "AOR", "GPA", "AGENCY_LIBRARY", "FAISA"])
def test_both_readers_give_the_same_orientation(readers, phase: str) -> None:
    server, owner = readers
    served = server.phase_orientation(phase, ROOT)
    owned = owner.phase_orientation(phase)
    assert served["found"] is (owned is not None)
    assert served["advisory"] is True
    if owned is not None:
        assert owned["advisory"] is True
        for key in ("block", "label", "deliverables", "minimum_evidence", "gate", "gate_risk"):
            assert served[key] == owned[key], key


def test_a_phase_without_a_block_has_no_orientation_and_no_error(readers) -> None:
    server, owner = readers
    assert owner.phase_orientation("AGENCY_LIBRARY") is None
    assert owner.phase_orientation("") is None
    assert server.phase_orientation("FAISA", ROOT)["found"] is False


def test_every_repository_project_phase_has_a_block() -> None:
    declared = json.loads(PHASES.read_text(encoding="utf-8"))["entries"]
    project = {entry["id"] for entry in declared if entry["category"] != "non_project_scope"}
    covered = {phase for entry in _registry()["entries"] for phase in entry["phases"]}
    assert project == covered
