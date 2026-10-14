# Reasoning Modes Library

Status: candidate support doctrine — governance frame for a candidate Guide de compétence on reasoning modes.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a reasoning engine, mode selector, router, agent runtime, orchestrator, scheduler, queue, approval engine or memory engine.

It classifies and bounds the reasoning-mode library held at
`templates/competence/reasoning_modes_guide_candidate.json`.

## What the library is

A catalog of reasoning modes (deduction, razors, oblique techniques, structured
methods), each with a trigger description, an injection snippet to paste into a
prompt, an optional mini-process, guard-rails and a fidelity check.

In `COMPETENCE_MODEL.md` terms this is a **Guide de compétence**: it explains a
method for applying or learning a competence. It is not a Connaissance métier,
not an Evidence item, not a Template and — despite an earlier misnamed
`$schema` key — **not a JSON Schema**.

## Placement and status

```text
Authority class: candidate support doctrine (this note);
                 candidate Guide de compétence (the JSON resource).
Repo state: documented non-implemented.
Location: templates/competence/reasoning_modes_guide_candidate.json
          (moved out of schemas/, which is a protected implementation path and
           the wrong zone for a content resource).
```

The JSON is a governed candidate resource, not canon. Nothing in it is promoted,
validated or canonized by its mere presence.

## Boundary

The library describes a `selector` (a Métis logic that diagnoses a task,
prescribes a reasoning structure and attaches guard-rails) and `controls`
(fidelity and justesse checks). These are described as **consultative**: the
advisor prescribes, it never resolves the task itself.

In Pantheon this distinction is binding:

```text
The selector here is an advisory DESCRIPTION, not a router, agent or executor.
There is no automatic selection and no automatic execution in the governance core.
If a runnable selector is ever built, it runs Hermes-side, outside the core,
  under the existing placement doctrine, and remains a candidate until reviewed.
A prescribed reasoning mode is a suggestion injected into a prompt; it does not
  validate, approve, send, canonize memory or replace professional judgement.
```

The "Zeus avale Métis" framing (orchestrator consults Métis, then executes via a
separate agent) is an Hermes-side orchestration idea. Pantheon governs the
library; it does not host the orchestrator.

## Relationship with existing documents

```text
COMPETENCE_MODEL.md            — names Guide de compétence / Ressource / Connaissance.
REQUEST_LIFECYCLE.md           — MÈTIS as conditional cap-keeper; gates remain decisive.
ROLE_ACTIVATION_MODEL.md — facets express, they do not self-authorize.
AUTHORITY_INDEX.md             — records this note and the resource's status.
```

## To verify / to arbitrate

```text
whether the library stays generic or is split per domain;
whether any reasoning mode warrants a Hermes skill later (separate candidate);
whether a small JSON shape check belongs in tests/ later (not now);
the malformed $schema key has been removed; confirm no consumer relied on it
  (the resource was orphaned, so none is known).
```

## Boundary reminder

```text
This is a governance frame plus a candidate Guide de compétence.
It is consultative reasoning support, not an engine.
It selects nothing by itself, executes nothing, approves nothing.
Any runtime selector lives Hermes-side, outside the governance core.
```
