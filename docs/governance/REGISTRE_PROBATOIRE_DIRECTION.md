# Registre Probatoire — Direction note

Status: validation-only — direction record. It captures a decision and orients
Boundary profile: validation_only_trace.
the executor; it does not itself rewrite the affected doctrine or touch any
protected path.

Decision date: 2026-06-07.

## Decision captured

Two naming decisions reframe the memory model.

```text
1. "Memory" is reserved to Hermes (the execution runtime).
   Hermes owns its own runtime memory (mem0 or another system).
   It is free, self-evolving and ungoverned by Pantheon.
   Pantheon no longer uses the word "memory" for anything it governs.

2. Pantheon governs the Registre Probatoire.
   It is the rigorous, citeable record of evidence with certainty levels,
   exhibits (pièces), dates and citations.
   It replaces the former term "Canonical Memory".
```

## The model

The split is by nature, not by storage mechanism.

| | Hermès memory (mem0) | Registre Probatoire (Pantheon) |
|---|---|---|
| Nature | operational, subjective recall | probative, objective record |
| Evolution | free, self-evolving, fast | governed, dated, cited |
| Analogy | the architect's own recollection | the project's file of exhibits |
| Authority | none | the only basis one may rely on |
| Owner | Hermes / the execution runtime | Pantheon |

## The bridge rule

Free memory stays compatible with the doctrine only because of one hinge rule.
Without it, "free memory" would drift into silent authority, which the red
lines forbid (no self-learning loop, no auto-promoted memory).

```text
Hermès memory may SPEAK — propose, recall, accelerate.
Only the Registre Probatoire may be CITED and relied upon
for a consequential decision.
```

When a statement is consequential (structure, budget, urbanism, a client
commitment, professional liability), the runtime must resolve it to a Registre
Probatoire entry — with its certainty level, dates and source. This is exactly
the Answer Verification Gate posture:

```text
Memory first. Evidence when consequential. Status when deciding.
Approval when acting.
```

Pantheon never performs automatic memory promotion: nothing the runtime
remembers becomes probative on its own.

## Three orthogonal certainty axes

Renaming resolves the scale collision found across the corpus. Three different
questions get three distinct, GLOSSARY-owned scales — they are not merged.

```text
E0–E4   probative certainty   "how trustworthy is this piece?"   Registre
V0–V4   answer verification   "is this answer verified?"          Gate (#71)
C0–C5   approval ceiling      "what clearance to act?"            Approval / MCP
```

`GLOSSARY.md` becomes the single owner of all three enums.

## Registre Probatoire entry — required fields

The four maintainer requirements (certainty level, exhibits, dates, citation)
are already specified in `EVIDENCE_MEMORY_CANONICALIZATION.md`; they only need
to be promoted as the primary object:

```text
certainty_level     E0–E4 — an explainable score, absorbing the existing
                    source / date / language / context / coherence components.
exhibits (pièces)   linked_files, source_excerpt — the opposable attachment.
dates               source_date, received_date, effective_date.
citation            author_detected, page_or_location, origin_channel.
```

## Vocabulary migration (for the executor)

```text
Canonical Memory            -> Registre Probatoire entry (retained piece)
Memory Candidate (Pantheon) -> Evidence Candidate / Register Candidate
"Pantheon memory"           -> Registre Probatoire
Hermes runtime memory       -> unchanged: mem0, free, ungoverned
```

## What changes in the corpus

```text
MEMORY.md                          reframed: "memory" = Hermès runtime, free,
                                   ungoverned; Pantheon's only constraint is
                                   that it carries no authority.
EVIDENCE_MEMORY_CANONICALIZATION   becomes the central Registre Probatoire doc;
                                   the "-> Canonical Memory" endpoint renamed.
ANSWER_VERIFICATION_GATE (#71)     becomes the memory↔registre bridge rule.
EXTERNAL_RUNTIME_MEMORY_ADAPTERS   already aligned: mem0 proposes, never canonizes.
GLOSSARY.md                        owner of E0–E4 / V0–V4 / C0–C5.
AUTHORITY_INDEX / MODULES / STATUS  reindex; retire "Canonical Memory" wording.
```

## Execution checklist (for the executor)

This is the downstream work that realigns the corpus to the decision. The
executor (Hermès / ChatGPT) carries it out; this note only orders it. Nothing
below is done in this PR.

### Working rules

```text
Surgical rename, not global. Do NOT blindly replace the word "memory".
One concern per PR. Each PR: rebased on main, lint-clean, its own
CHANGELOG bump, indexes updated in that same PR only.
Append-only history: never edit past CHANGELOG entries.
Protected paths (schemas/, tests/, pyproject.toml, operations/, platform/,
Docker, .env) are deferred and need explicit approval.
Run the governance forbidden-phrase lint locally before every push.
```

### Surgical rename map — what changes vs what stays

```text
CHANGES (Pantheon-governed concept):
  "Canonical Memory"            -> "Registre Probatoire entry"
  "Memory Candidate" (Pantheon) -> "Register Candidate"
  "Pantheon memory" / governed  -> "Registre Probatoire"

STAYS UNCHANGED (these are not the governed object):
  Hermès runtime memory, mem0, external runtime memory  -> still "memory"
  Boundary phrases ("no automatic memory promotion", "never canonical")
    -> remain true and may stay as written
  Historical CHANGELOG wording -> never edited
```

### Step E1 — GLOSSARY owns the three scales (do first)

```text
File:   docs/governance/GLOSSARY.md
Do:     define once, as canonical, and let other docs link rather than redefine:
        - Registre Probatoire (the governed evidence register)
        - certainty E0–E4 (Registre)
        - answer verification V0–V4 (Gate)
        - approval ceiling C0–C5 (Approval / MCP)
        - Hermès memory (runtime, free, no authority)
Accept: each scale defined exactly once; no other doc redefines them.
```

### Step E2 — Reframe MEMORY.md

```text
File:   docs/governance/MEMORY.md  (CI-mandatory file; must stay present + lint-clean)
Do:     "memory" = Hermès runtime memory: free, self-evolving (mem0 or other),
        ungoverned, carrying NO authority. Redirect the former "Canonical Memory"
        endpoint to the Registre Probatoire. Keep the still-valid distinctions
        (Knowledge / Context / Session State / Runtime State).
Keep:   the boundary statements — Pantheon still never promotes memory; it now
        owns no governed memory at all, which makes them stronger, not weaker.
Accept: MEMORY.md no longer claims Pantheon owns a canonical memory; it points
        to the Registre Probatoire and the bridge rule.
```

### Step E3 — Promote the Registre Probatoire doc

```text
File:   docs/governance/EVIDENCE_MEMORY_CANONICALIZATION.md
Do:     retitle as the central Registre Probatoire document; rename the
        "-> Canonical Memory" endpoint to "-> Registre Probatoire entry";
        map the confidence model onto E0–E4 (link GLOSSARY).
Note:   retitle in place first (low risk). A file rename to REGISTRE_PROBATOIRE.md
        is optional and, if done, must update every inbound link in one PR.
Accept: "Canonical Memory" wording retired here; certainty uses E0–E4.
```

### Step E4 — Bridge rule in the Answer Verification Gate

```text
File:   docs/governance/ANSWER_VERIFICATION_GATE.md
Depend: this file is in PR #71 (candidate, unmerged).
Do:     if #71 lands, state the bridge rule there — "Hermès memory may speak;
        only the Registre Probatoire may be cited for a consequential decision" —
        and disambiguate its levels against the GLOSSARY (V = verification,
        C = approval), which resolves the C-scale collision.
        If #71 does not land, the bridge rule stays in this direction note until
        #71 is decided.
Accept: exactly one canonical statement of the bridge rule; V/C scales distinct.
```

### Step E5 — Reindex once

```text
Files:  docs/governance/AUTHORITY_INDEX.md, MODULES.md, STATUS.md
Do:     after E2–E4, in a single pass: retire "Canonical Memory" authority
        wording, add the Registre Probatoire, record the "memory = Hermès,
        ungoverned" boundary.
Why:    these three files are contended by almost every PR — touch them once,
        last, to avoid merge churn.
Accept: indexes consistent; no dangling "Canonical Memory" authority row.
```

### Step E6 — Schema rename (protected, deferred)

```text
Files:  schemas/register_candidate.schema.yaml (formerly memory_candidate) and its example + test
Status: PROTECTED — do NOT touch without explicit approval.
Propose: rename to register_candidate (claim, scope, certainty E0–E4, exhibits,
        dates, citation, evidence links, status, approval). Carry the example and
        the read-only test along. Present as its own approval-gated change.
```

### Whole-effort acceptance gate

```text
Governance lint green on every PR.
The three indexes are mutually consistent.
"memory" survives only where it means Hermès / external runtime memory.
The Registre Probatoire is the single governed evidence object.
The architecture proof-register vertical (#76) still reads coherently.
```

## Boundary

Direction record only. No doctrine file is rewritten here, no schema, test or
runtime is added, and no protected path is touched. The schema rename
(`schemas/register_candidate.schema.yaml`, formerly `memory_candidate`) is applied protected-path
work and stays deferred until explicitly approved. Hermès memory remaining free
does not make it authoritative; only the Registre Probatoire is probative, and
only a human gate makes a consequential entry binding.

```text
Hermès remembers freely.
Pantheon keeps the proof.
The human decides what is established.
```
