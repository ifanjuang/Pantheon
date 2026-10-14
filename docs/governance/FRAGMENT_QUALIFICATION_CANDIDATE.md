# Fragment Qualification Candidate

Status: candidate governance contract.

## Purpose

A `fragment_qualification_candidate` records Hermes' proposed semantic reading of
fragments already present in a governed `document_structure`.

It may propose:

- topic;
- discipline;
- representation kind;
- project state;
- variant identity;
- project coverage references;
- certainty, rationale and a discriminating question.

It does not rewrite the extracted structure and does not create Architecture
Project Understanding objects.

```text
document fragment detected != project fact
qualification candidate != reviewed classification
certainty band != probability of truth
supporting fragment != Evidence admitted
Hermes result != professional validation
```

## Required flow

```text
Document Structure read
→ Hermes analyzes selected fragments
→ Fragment Qualification Candidate
→ schema and reference validation
→ human review or downstream governed alignment
→ optional APU candidate in a later, separate operation
```

The candidate must reference existing fragments from one exact structure. A
consumer must reject unknown fragment references, cross-document references and
empty semantic proposals.

## Review behavior

Use `generated_unreviewed` when no ambiguity requiring attention was identified.
Use `needs_review` when the result contains an explicit question, weak certainty,
conflicting fragments or a consequential interpretation such as demolition,
contractual applicability or executed state.

These statuses are review dispositions only. Neither status approves an APU
write.

## Minimality

This contract deliberately does not introduce:

- a second document tree;
- a canonical discipline registry;
- an AEC compliance conclusion;
- automatic entity creation;
- a new memory or Evidence store;
- provider or model routing.

Canonical vocabularies may replace free-text discipline/topic values later when
an existing registry is verified to cover the need.

## Authority

Pantheon Next defines the candidate contract. Hermes produces candidates. The
MVP may validate and transport them. A later APU alignment step may consume a
reviewed candidate but must preserve the original fragment provenance and review
status.
