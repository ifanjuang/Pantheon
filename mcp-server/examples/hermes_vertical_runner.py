#!/usr/bin/env python3
"""Vertical conformance runner — plays the Hermes side of the Phase 5
integration contract over the real MCP protocol (stdio) and stops at the
User Decision Gate.

This is NOT Hermes and NOT a runtime: it is a deterministic, read-only
demonstration that the contract holds end to end on one fixture. The
"execution" step is an explicitly simulated, fictional computation; every
produced object is a candidate validated against the repository schemas;
nothing is sent, written, approved or promoted. The run always ends at
the gate with the human decision options.

Usage:
    python3 examples/hermes_vertical_runner.py [fixture.yaml]
(defaults to the Résidence Les Tilleuls VEFA fixture)
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
import os
import sys
from pathlib import Path

import yaml

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
DEFAULT_FIXTURE = MODULE_DIR / "fixtures" / "residence_les_tilleuls_vefa_surface_claim.yaml"

FORBIDDEN_LANGUAGE = ["approved", "validated truth", "authorized action", "safe to execute"]


class ConformanceError(AssertionError):
    pass


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise ConformanceError(msg)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Step C — SIMULATED execution outside Pantheon (fictional, deterministic).
# A real deployment runs this inside Hermes under the Task Contract; the
# policy server is never involved in producing the professional content.
# ---------------------------------------------------------------------------
def simulated_execution(fixture: dict) -> dict:
    return {
        "label": "SIMULATED_EXECUTION (fictional, outside Pantheon)",
        "comparison": {
            "claimed_basis": "D2 acte de vente notarié (surface privative annoncée)",
            "observed_basis": "D4 plan de récolement / DOE (surface telle que construite)",
            "surface_gap_candidate": "to be computed by a géomètre; this run computes nothing real",
            "threshold_note": "the 1/20 threshold and the one-year delay are domain-pack material, to verify on dated official sources",
        },
        "contradictions_found": fixture["request"].get("contradictions_to_resolve", []),
        "questions_raised": [
            "Quelle surface fait autorité : acte notarié, plan PRO ou DOE ?",
            "Le délai d'action (1 an depuis l'acte) court-il encore ?",
            "Un géomètre a-t-il mesuré la surface livrée ?",
        ],
        "status": "candidate",
    }


def build_evidence_pack_candidate(fixture: dict, skeleton: dict, simulated: dict) -> dict:
    scope = fixture["request"]["scope"]
    return {
        "evidence_pack_id": "vertical.tilleuls.evidence-pack",
        "task_contract_id": "vertical.tilleuls.task-contract-candidate",
        "created_at": _now(),
        "summary": (
            "Fictional vertical run: VEFA surface claim on lot A12. Candidates, "
            "contradictions and questions prepared; no position taken."
        ),
        "scope": {"scope_type": scope["scope_type"], "scope_id": scope["scope_id"]},
        "sources": [
            {"type": "source_reference", "reference": ref, "status": "unverified"}
            for ref in fixture["request"].get("sources_expected", [])
        ],
        "assumptions": list(skeleton.get("assumptions_to_state", [])),
        "actions": [
            "classified the request through the policy server (K/V/C)",
            "prepared Task Contract and Evidence Pack candidate skeletons",
            "ran a SIMULATED comparison outside Pantheon (fictional)",
            "stopped at the User Decision Gate",
        ],
        "risks": [
            {
                "description": "confirming non-conformity without a measured surface and dated legal basis",
                "severity": "high",
                "mitigation": "géomètre measurement + dated official sources before any position",
            }
        ],
        "outputs": [
            {
                "output_id": "result-candidate-1",
                "output_type": "analysis",
                "status": "candidate",
                "reference": "RESULT_CANDIDATE in the run envelope",
            }
        ],
        "reviews": [{"reviewer": "human-maintainer", "status": "pending"}],
        "approval_state": {"level": "C4", "status": "required"},
        "user_decision_gate": {
            "status": "decision_required",
            "decision_effects": [
                "professional position with contractual and financial effect",
            ],
        },
        "governance_refs": [
            "docs/governance/EVIDENCE_PACK.md",
            "docs/governance/USER_DECISION_GATE.md",
        ],
    }


def build_register_candidate(fixture: dict) -> dict:
    scope = fixture["request"]["scope"]
    return {
        "candidate_id": "vertical.tilleuls.register-candidate",
        "created_at": _now(),
        "proposed_by": "vertical-runner (simulated Hermes)",
        "claim": (
            "A surface contestation exists on lot A12 (loi Carrez); the authoritative "
            "surface and the action deadline are unresolved."
        ),
        "scope": {"scope_type": "project", "scope_id": scope["scope_id"]},
        "source": "D6 courrier acquéreur (fictional fixture)",
        "evidence_link": "vertical.tilleuls.evidence-pack",
        "evidence_pack_id": "vertical.tilleuls.evidence-pack",
        "certainty": "E1",
        "risk": {
            "level": "high",
            "notes": "claim records the existence of a contestation only; it asserts no non-conformity",
        },
        "proposed_durability": "project",
        "required_approval": "C4",
        "status": "candidate",
        "governance_refs": [
            "docs/governance/EVIDENCE_MEMORY_CANONICALIZATION.md",
            "docs/governance/GLOSSARY.md",
        ],
    }


def validate_against(schema_rel: str, instance: dict, label: str) -> None:
    import jsonschema

    schema = yaml.safe_load((REPO_ROOT / schema_rel).read_text(encoding="utf-8"))
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(instance),
        key=lambda e: list(e.path),
    )
    _check(not errors, f"{label} does not validate against {schema_rel}: "
           + "; ".join(f"{'/'.join(map(str, e.path))}: {e.message[:80]}" for e in errors[:5]))
    print(f"  [schema] {label} validates against {schema_rel}")


async def run(fixture_path: Path) -> dict:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    fixture = yaml.safe_load(fixture_path.read_text(encoding="utf-8"))
    request = fixture["request"]
    expected = fixture.get("expected_outputs", {})

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pantheon_mcp"],
        cwd=str(MODULE_DIR),
        env={**os.environ, "PANTHEON_REPO_PATH": str(REPO_ROOT)},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(tool: str, **kwargs) -> dict:
                result = await session.call_tool(tool, kwargs)
                return json.loads(result.content[0].text)

            print(f"== Vertical run: {fixture['fixture_id']} (fictional) ==")

            # 3. classify
            classification = await call("classify_request", request_yaml=yaml.safe_dump(request))
            want = expected.get("classification", {})
            for key, exp in (("consequence_level", want.get("consequence_level")),
                             ("required_verification", want.get("required_verification")),
                             ("required_approval_ceiling", want.get("approval_level")),
                             ("blocked_until_gate", want.get("blocked_until_gate"))):
                if exp is not None:
                    _check(classification.get(key) == exp,
                           f"classification.{key}: got {classification.get(key)!r}, want {exp!r}")
            print(f"  [classify] {classification['consequence_level']}/"
                  f"{classification['required_verification']}/"
                  f"{classification['required_approval_ceiling']} blocked_until_gate="
                  f"{classification['blocked_until_gate']}")

            # 4. task contract candidate
            tc = await call("prepare_task_contract_skeleton", request_yaml=yaml.safe_dump(request))
            _check(tc["object"] == "TASK_CONTRACT_CANDIDATE_SKELETON", "wrong skeleton object")
            _check(tc["status"] in tc["allowed_status_terms"], "skeleton status outside allowed terms")
            dumped = json.dumps(tc).lower()
            for phrase in FORBIDDEN_LANGUAGE:
                _check(phrase not in dumped, f"forbidden language in skeleton: {phrase}")
            print(f"  [contract] candidate skeleton status={tc['status']!r}")

            # 5. SIMULATED execution outside Pantheon
            result_candidate = simulated_execution(fixture)
            print("  [execute] simulated outside Pantheon (fictional comparison, no real computation)")

            # 6. evidence pack candidate, validated against the E6 baseline
            skel = await call("prepare_evidence_pack_skeleton", request_yaml=yaml.safe_dump(request))
            _check(skel["object"] == "EVIDENCE_PACK_CANDIDATE_SKELETON", "wrong pack skeleton")
            pack = build_evidence_pack_candidate(fixture, skel, result_candidate)
            validate_against("schemas/evidence_pack.schema.yaml", pack, "Evidence Pack candidate")
            register = build_register_candidate(fixture)
            validate_against("schemas/register_candidate.schema.yaml", register, "Register candidate")

            # Refusal probes over the wire
            for case in fixture.get("refusal_cases", []):
                report = await call("classify_request",
                                    request_yaml=yaml.safe_dump({"perform": [case["request"]]}))
                _check(report.get("result") == "refused",
                       f"refusal probe not refused: {case['request']!r}")
                print(f"  [refusal] refused: {case['request'][:60]!r}")
            gate = await call("check_external_action",
                              description="send the reply letter to the purchaser of lot A12")
            _check(gate["status"] == "blocked_by_default", "external action not blocked")
            print("  [external] blocked_by_default confirmed")

            # 7-8. envelope, then STOP at the gate
            envelope = {
                "RESULT_CANDIDATE": result_candidate,
                "EVIDENCE_PACK_CANDIDATE": pack,
                "STATUS": "candidate — blocked until gate",
                "SCOPE_USED": request["scope"],
                "APPROVAL_NEEDED": classification["required_approval_ceiling"],
                "REGISTER_CANDIDATE_PROPOSAL": register,
                "LIMITS_AND_UNCERTAINTIES": [
                    "fictional fixture; no real dossier was read",
                    "surface gap not measured; thresholds/delays to verify on dated sources",
                    "nothing was sent, written, approved or promoted by this run",
                ],
                "USER_DECISION_GATE": {
                    "stopped_here": True,
                    "options": expected.get("authorized_output", []),
                    "forbidden": expected.get("forbidden_output", []),
                },
            }
            print("  [gate] STOPPED at the User Decision Gate — the human decides.")
            return envelope


def main() -> int:
    fixture = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    try:
        envelope = asyncio.run(run(fixture))
    except ConformanceError as exc:
        print(f"CONFORMANCE FAILURE: {exc}", file=sys.stderr)
        return 1
    print("\n== HERMES OUTPUT ENVELOPE (candidate, for human review) ==")
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    print("\nVERTICAL CONFORMANCE: PASS (ended at the gate; no effect performed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
