# Vertical slice — `architecture_devis_reprise` (governed, fictional)

Status: validation-only / governed vertical slice — a schema-valid, machine-checked
end-to-end dossier proving the governance loop is coherent. Fictional (Maison Lierre
extension, a complementary quote). It **executes nothing**; Hermes and OpenWebUI run
outside the repo (see `RUNBOOK.md`).
Boundary profile: validation_only_trace.

## What this proves (and what it does not)

It proves the **governance spine holds end to end** — every artifact validates against
the real schemas and the coherence invariants (checked read-only by the mcp-server
doctor, `check_vertical_slice`, and in CI). It does **not** prove the runtime works:
no capability is executed, nothing is sent, approved or promoted. `forged != authorized`,
`completed != approved`, `returned != a Registre Probatoire entry`.

## The loop, as files

```text
task_contract.devis-reprise.yaml        the bounded Task Contract (scope: project)
workflow_manifest.devis-reprise.yaml    forged manifest: signed capability_steps + two gates
policy_decision.gate1.yaml              gate 1 (pre-execution eligibility) as data (allow_with_gate)
   → [ Hermes executes the bounded steps OUTSIDE the repo — see RUNBOOK.md ]
evidence_pack.devis-reprise.yaml        Evidence Pack Candidate (scope: project)
answer_status.devis-reprise.yaml        answer status: V2 / E2 / K3, references the pack and the register candidate
register_candidate.devis-reprise.yaml   Registre Probatoire candidate (scope: project) — a point to verify, not approved
   → [ User Decision Gate + human decision ]
```

## Coherence invariants (enforced read-only)

- the register candidate (the evidence-log entry) is scoped to a **project**;
- because the post-execution evidence gate is `required`, the answer status carries
  both verification **V** and certainty **E**;
- the answer status references the dossier's evidence pack and register candidate.

## Scenario

A complementary quote (*devis complémentaire*) adds a plus-value that is not
reconcilable with the prior signed amendment. The governed output is a **candidate
opinion + a draft MOA email**, with the quote **not approved** and **nothing sent** —
the discrepancy is returned as a point to verify at the gate.
