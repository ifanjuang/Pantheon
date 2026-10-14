from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "docs" / "governance" / "HERMES_INTEGRATION.md"
IMPROVEMENT = ROOT / "docs" / "architecture" / "HERMES_IMPROVEMENT_PATH.md"
NON_EQ = ROOT / "docs" / "governance" / "NON_EQUIVALENCE_RULES.md"
SURFACE = ROOT / "docs" / "governance" / "HERMES_RUNTIME_SURFACE_REVIEW.md"
ADMISSION = ROOT / "docs" / "governance" / "HERMES_EXECUTION_ADMISSION_BRIDGE.md"
RUNBOOK = ROOT / "docs" / "install" / "HERMES_EXECUTION_BRIDGE_RUNBOOK.md"


def test_consequential_effect_boundary_is_not_owned_by_hermes_hooks() -> None:
    integration = INTEGRATION.read_text(encoding="utf-8")
    improvement = IMPROVEMENT.read_text(encoding="utf-8")
    non_eq = NON_EQ.read_text(encoding="utf-8")

    assert "Pantheon effect owner / PEP -> exact consequential external effect" in integration
    assert "Pantheon-owned\nPEP / adapter outside Hermes' internal hook chain" in integration
    assert "raw consequential provider tool / credential\n-> not admitted to Hermes" in integration
    assert "pre_tool_call\n-> optional defense in depth only\n-> never the sole effect boundary" in integration
    assert "Credentials or provider\nroutes whose possession would allow bypass must remain with that owner" in integration
    assert "pre_tool_call != Pantheon PEP" in integration

    assert "Execution-strategy choice never moves the consequential-effect boundary" in improvement
    assert "raw consequential tool / credential\n-> not exposed to Hermes" in improvement
    assert "governed effect request\n-> terminates at Pantheon-owned effect owner / PEP" in improvement
    assert "pre_tool_call\n-> optional second-line runtime guard\n-> never the sole PEP" in improvement

    assert "pre_tool_call != Pantheon_PEP" in non_eq
    assert "runtime_guard_available != effect_boundary_owned" in non_eq
    assert "runtime_guard_unqualified != Pantheon_PEP_unavailable" in non_eq

    assert "Hermes Agent                -> external execution / PEP responsibility" not in integration
    assert "Pantheon does not perform the effect." not in integration
    assert "external runtime / PEP" not in integration


def test_ephemeral_sentinel_never_counts_as_deployed_route_qualification() -> None:
    non_eq = NON_EQ.read_text(encoding="utf-8")
    surface = SURFACE.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert "lab_sentinel_pass != deployed_route_guard_qualified" in non_eq
    assert "Pantheon-Next#1105 pass != deployed route guard qualified" in surface
    assert "Pantheon-Next#1105 and its generated receipts may be cited only as characterization" in surface
    assert "exact installed artifact identity/digest" in surface
    assert "Pantheon-Next#1105 lab pass != target runtime guard qualified" in runbook
    assert "If no reviewed target-local sentinel procedure is available" in runbook
    assert "do not substitute the Pantheon-Next#1105 lab receipt" in runbook


def test_effect_chokepoint_and_runtime_guard_owners_cross_reference_each_other() -> None:
    admission = ADMISSION.read_text(encoding="utf-8")
    surface = SURFACE.read_text(encoding="utf-8")

    assert "HERMES_RUNTIME_SURFACE_REVIEW.md" in admission
    assert "Hermes pre_tool_call" in admission
    assert "defense in depth for the admitted runtime/tool surface" in admission
    assert "runtime guard != effect chokepoint" in admission
    assert "raw consequential effect must\nstill remain unreachable" in admission

    assert "HERMES_EXECUTION_ADMISSION_BRIDGE.md" in surface
    assert "governed-effect request" in surface
    assert "authoritative consequential-effect chokepoint remains" in surface
    assert "secondary guard on the Hermes-side effect-request path" in surface
    assert "This document owns the release-specific guard semantics and qualification." in surface
    assert "It\ndoes not redefine the effect chokepoint." in surface
