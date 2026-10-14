# Architecture convergence closure

Date: 2026-08-04

Status: closure record — implementation repository; Pantheon-Next remains the semantic authority.

## Audited references

```text
pantheon-mvp main: b82d6f797816200ffde415de29e9675d518acd1d
Pantheon-Next main: 93f1420e47c1b5b3fe5132722ec332a00f0b5dd3
open pull requests at closure preparation: 0 in both repositories
```

The CI reruns both inventories on the actual PR merge head and the current Pantheon-Next `main`. These references record the starting point of the final closure review, not a permanently pinned authority snapshot.

## A–O closure

| Stage | Result |
|---|---|
| A | Current-main architecture audit rerun and corrected |
| B | CI guard against new generation-named active identities |
| C | Stable materials, document and active-test identities |
| D | Professional duty-of-care material absorbed by the existing governance owner |
| E | Internal MCP HTTP routes stabilized |
| F | Agency and Work routes stabilized |
| G | Cockpit routes stabilized |
| H | Documents and Resources routes stabilized |
| I | Hermes routes stabilized |
| J | Usage evidence added; the only proven dead implementation contract removed |
| K | Shared primitives introduced only after compatible repeated use |
| L | Hermes Handoff, admission, envelope, launch and scoped-context seams consolidated |
| M | Common factual Observation envelope shared without a universal status ontology |
| N | Cockpit and PostgreSQL/API reads optimized from measured baselines |
| O | Final cross-repository audit and removal of the temporary decreasing-debt baseline |

## Permanent closure invariants

The architecture workflow now fails when either repository introduces:

```text
a generation-named active artifact
an internal versioned route
a Python parse error
an implementation module classified candidate_unreferenced
```

The guard also fails when either expected repository is absent from an inventory, preventing a false green result produced from a partial audit.

The former `ARCHITECTURE_DEBT_BASELINE.json` and its decreasing-debt checker are removed because their reviewed allowance is already zero. A permanent zero invariant replaces the temporary allowance list.

## Measured optimization results

### Cockpit Project schema reads

Representative loader scenario:

```text
total requests: 9 -> 7 (-22.2%)
Project schema reads: 3 -> 1 (-66.7%)
Project bundle reads: unchanged at 5
```

The cache remains per loader instance and exact read token, supports explicit refresh and evicts failed requests.

### Work Issue Cockpit projection

Three Work Issues for one exact `case_ref`:

```text
SQL executions: 16 -> 5 (-68.75%)
previous formula: 1 + 5N
current non-empty strategy: 5 constant bounded queries
```

Every aggregate remains schema-validated. Ordering, Work Card metadata, Work Activity projection and the single-item `get_issue` path remain unchanged.

## Retained boundaries

```text
stable identity != semantic authority
zero debt finding != proof that all architecture questions are solved
CI success != human approval
usage evidence != deletion authorization
client cache != source of truth
batched read != broader scope
runtime success != Evidence
Observation != truth
installed != approved
activated != task_authorized
```

Pantheon remains governance. Hermes remains external execution. Cockpit and OpenWebUI remain projection and decision surfaces. Consequential changes remain human-reviewed.

## Follow-up posture

The A–O convergence program is closed. Further work should enter normal feature or maintenance flow and must not reopen temporary generation identities, versioned internal routes or broad abstraction layers without new evidence.
