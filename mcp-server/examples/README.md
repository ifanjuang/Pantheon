# mcp-server examples

Status: example — conformance demonstration, candidate-only.

## `hermes_vertical_runner.py` — the proven vertical (step 4 of TARGET_ARCHITECTURE)

Plays the **Hermes side** of the Phase 5 integration contract over the real MCP protocol (stdio) on one fixture (default: Résidence Les Tilleuls, VEFA surface claim — fictional), and **stops at the User Decision Gate**:

```text
classify_request                 -> K4 / V4 / C4, blocked_until_gate
prepare_task_contract_skeleton   -> candidate (constrained status vocabulary)
SIMULATED execution              -> outside Pantheon, fictional, computes nothing real
prepare_evidence_pack_skeleton   -> filled into an Evidence Pack candidate
schema validation                -> evidence_pack + register_candidate (E6 baseline)
refusal probes (FR + EN)         -> send / promote refused over the wire
check_external_action            -> blocked_by_default
HERMES OUTPUT ENVELOPE           -> printed for human review; the run ends at the gate
```

Run it:

```bash
cd mcp-server
pip install -e .            # mcp SDK + PyYAML (jsonschema required for validation)
python3 examples/hermes_vertical_runner.py [path/to/fixture.yaml]
```

Exit code 0 = every conformance expectation held and the run ended at the gate. Any deviation (wrong axis, forbidden language, unrefused effect, non-validating candidate) exits 1.

`tests/test_vertical_e2e.py` keeps this green as a regression (skips when the SDK is absent, e.g. in the governance CI).

## Boundary

This runner is **not Hermes and not a runtime**: a deterministic, read-only script. The execution step is explicitly simulated and fictional; every produced object is a candidate; nothing is sent, written, approved, promoted or scheduled. In a real deployment, Hermes performs the execution step under the reviewed Task Contract and returns the same envelope; the gate and the human decide.
