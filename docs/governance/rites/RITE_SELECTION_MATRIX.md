# Rite Selection Matrix

Status: active doctrine - rite selection support.

This document helps choose which rite may be useful for a given governance symptom.

It is an ergonomic selection aid.

It is not a trigger engine.

It is not a runtime policy.

It is not an automatic classifier.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed rite, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

A rite should answer a specific governance symptom.

A rite should not be invoked because it is available, elegant or intellectually attractive.

This matrix helps map symptoms to candidate rites, anti-risks and required outputs.

The invocation rules remain governed by `RITE_INVOCATION_POLICY.md`.

## Core rule

```text
A symptom may suggest a rite.
It does not trigger the rite.
ZEUS decides whether the rite is allowed.
```

## Selection matrix

| Governance symptom | Candidate rite | Main anti-risk | Required output |
|---|---|---|---|
| Too many plausible options | `RITE_DIVERGENCE_CONTROLEE.md` | proliferation | shortlist, block reason, task split or User Decision Gate |
| Premature convergence | `RITE_DIVERGENCE_CONTROLEE.md` | obvious but weak answer | option clusters and non-obvious defensible option when relevant |
| Seductive but fragile idea | `RITE_DIVERGENCE_CONTROLEE.md` plus possible `AUTOCRITIQUE_CONTRADICTOIRE.md` | false good idea | traps detected and ZEUS status |
| Candidate output looks too convincing | `AUTOCRITIQUE_CONTRADICTOIRE.md` | smooth unsafe conclusion | claim separation, unsupported claims, correction actions or block |
| Professional delivery risk | `AUTOCRITIQUE_CONTRADICTOIRE.md` | premature delivery | delivery status, risks and next allowed action |
| Source disagreement | `CONCORDANCE_DES_SOURCES.md` | proof theater | claim-to-source map and contradiction ledger |
| Source freshness matters | `CONCORDANCE_DES_SOURCES.md` | stale authority | freshness note and claim status |
| Retrieved knowledge is being treated as proof | `CONCORDANCE_DES_SOURCES.md` | retrieval mistaken for evidence | unsupported claims and blocked claims |
| Problem seems obvious but unstable | `PREMISSES_CACHEES.md` | hidden premise | hidden assumptions and assumption statuses |
| Scope keeps expanding silently | `PREMISSES_CACHEES.md` | scope drift | revised problem statement and Task Contract impact |
| User intent is inferred but unconfirmed | `PREMISSES_CACHEES.md` | invented user preference | assumptions marked as inferred or requiring confirmation |
| Session has too many contradictory iterations | `REFONDATION_DE_SESSION.md` | polluted context | preserved invariants, discarded noise and unresolved tensions |
| Corrections improve locally but degrade globally | `REFONDATION_DE_SESSION.md` | Hydre-like proliferation | new Task Contract draft and preserved tensions |
| Old context contaminates current decision | `REFONDATION_DE_SESSION.md` | hidden memory or stale frame | source preservation note and reset boundary |

## No rite needed conditions

A rite should usually be rejected when:

- the task is low risk;
- the answer is simple and bounded;
- no external delivery is involved;
- no memory impact exists;
- no source contradiction affects the output;
- no hidden premise changes scope, evidence, approval or memory;
- direct drafting, editing or clarification is cheaper and safer.

Useful status:

```text
rite_not_needed
```

This is a positive governance decision, not an omission.

## Escalation signals

A User Decision Gate should be considered when:

- two candidate rites suggest different procedures;
- a rite exposes a conflict of value;
- options imply materially different professional risks;
- evidence remains insufficient but the user wants to proceed;
- refoundation would discard a direction the user may value;
- memory, delivery or external transmission depends on unresolved judgment.

## Selection mistakes

Common wrong selections:

| Mistake | Why it fails | Better response |
|---|---|---|
| Using divergence for a simple factual question | creates noise | answer directly or request source if needed |
| Using autocritique for style-only work | creates bureaucracy | edit directly unless style affects meaning or risk |
| Using source concordance for unsourced brainstorming | creates false proof posture | mark as exploratory |
| Using hidden-premise review for every missing preference | blocks harmless work | proceed with explicit reserve |
| Using refoundation for normal revision | deletes continuity | revise within current frame |

## Relationship to rite modes

After a rite is selected, use `RITE_MODES.md` to decide intensity:

```text
mode_light
mode_standard
mode_full
```

A correct rite with excessive intensity can still create governance drag.

## Final rule

Choose a rite only when the symptom justifies the governance cost.
