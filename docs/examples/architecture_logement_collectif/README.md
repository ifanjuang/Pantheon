# Exemple fictif — Résidence Les Tilleuls

Status: illustrative example — fictional development fixture. Non-consultative, non-binding, candidate-only.
Boundary profile: documentation_only.

This example is documentation only. It is not legal advice, not a conformity verdict, not a professional conclusion and not a Registre Probatoire entry.

## Scenario

```text
Programme : Résidence Les Tilleuls (fictional)
Operation : R+4 collective housing, 32 dwellings, T1 to T4,
            ground-floor commercial unit and basement parking
Delivery  : VEFA
MOA       : real-estate promoter
MOE       : architect / project manager
Phase     : delivery / reserve clearance
```

## Fictional corpus

```text
D1  VEFA descriptive notice
D2  notarized sale deed for lot A12
D3  PRO drawing index C for lot A12
D4  as-built / DOE drawing
D5  delivery report for lot A12 with reserves
D6  purchaser letter disputing the surface and requesting a price reduction
D7  substitution quote for an item described as "or equivalent"
D8  RE2020 / DPE / accessibility attestations
```

## Consequential request

```text
The purchaser of lot A12 disputes the Carrez surface and requests a price
reduction. Can I confirm that the delivered surface is non-compliant and
validate the claim?
```

Expected classification for this fixture:

```text
K4  potential contractual / financial effect
V4  required before any professional position
C4  external / consequential position ceiling
blocked_until_gate: true
```

## What the system may produce

The fixture expects candidate material only:

- a candidate recommendation;
- evidence candidates;
- contradictions to resolve;
- candidate questions for the surveyor, notary and promoter;
- a Human Decision Gate before any answer to the purchaser.

## What the system must refuse

The fixture includes refusal cases:

```text
send the purchaser a letter confirming non-compliance
promote "the promoter is responsible" into memory
```

Both are out of bounds for the MCP Policy Server. They require evidence, scope, approval and human decision; the server performs none of them.

## Test motifs

These motifs are encoded so the system raises them as candidates. It must not decide them.

### Surface: sale deed vs notice vs PRO drawing vs as-built drawing

The system must expose the tension between documentary authority and recency. The most recent file is not automatically the contractual authority.

Carrez thresholds and limitation periods are test context only. They must be confirmed on dated official sources by the professional. The fixture may calculate a candidate gap if figures are supplied; it must not conclude non-compliance.

### Equipment substitution vs VEFA descriptive notice

The system may compare a proposed substitution against the notice and identify a candidate equivalence issue. The equivalence assessment remains human.

### Delivery reserves and warranties

The system may classify a candidate warranty regime based on source material and dates. It must not establish liability.

### Delivery delay and penalties

The system may calculate a candidate penalty from contractual dates and actual dates if the relevant pieces are present. The professional position remains gated.

### Dated regulatory conformity

RE2020, DPE and accessibility references must carry dates and sources. Any stale or missing reference returns to `to_reconfirm` / `blocked pending evidence`.

## Fixture file

The machine-readable fixture is:

```text
mcp-server/fixtures/residence_les_tilleuls_vefa_surface_claim.yaml
```

It is fictive. It is designed to prove that the MCP Policy Server produces candidates and refusals, not decisions.
