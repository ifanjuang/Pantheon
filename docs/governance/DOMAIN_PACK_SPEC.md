# Domain Pack Specification — General

Status: active support doctrine — general specification for professional domain packs.

This document defines the general requirements a professional domain pack must satisfy, before any profession-specific pack (architecture, law, medicine, accounting, engineering) is written.

It is a specification, not an implementation.

It does not create a runtime, an agent, a professional authority or an automatic action.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
```

## Purpose

A practitioner does not want generic AI behavior. They want AI use that respects the conduct and method of their profession.

A domain pack is how Pantheon Next encodes that respect, per profession, as a governed configuration — not as a profession-specific autonomous worker.

This general specification answers one question:

```text
What must every domain pack define, whatever the profession?
```

Profession-specific packs fill the same slots with their own rules.

## What a domain pack is

A domain pack is a governed configuration of:

```text
vocabulary
source policy
pre-analysis intake discipline
evidence expectations
risk triggers
pre-transmission minimization rules
output statuses and delivery gates
answering / acting boundary
memory rules
review angles and decision gates
templates
```

It is a frame the professional fills, reviews and signs behind — not advice the pack gives on its own.

## What a domain pack is not

A domain pack does not provide professional advice.

A domain pack does not hold legal, medical, architectural, financial or engineering authority.

A domain pack does not validate a source by itself.

A domain pack does not approve, transmit, send or execute by itself.

A domain pack does not promote memory by itself.

A domain pack is not a profession-specific agent, a runtime, a scheduler or a router. Pantheon must never run, route or automate the domain pack; it only governs status.

## Required sections of any domain pack

Every domain pack, whatever the profession, must define the following sections. Profession-specific packs reuse these headings.

### Pre-analysis intake discipline

Before a domain pack supports detailed analysis, drafting, memory proposal or external-action preparation, it must define how incoming material is admitted into the working perimeter.

Minimum pre-analysis output:

```text
corpus inventory
documents received
documents referenced but absent
source type and authority class
date / version / validity signal
reviewable scope
non-reviewable scope
unknowns
contradictions or source tensions
required review angles
user questions or stop conditions
```

This step is not analysis. It is admission control.

A document, corpus, photo, message, table, retrieved excerpt or connector item must not move directly from received to trusted. The domain pack defines how it is classified, bounded and qualified before any conclusion, draft, Register Candidate or external action can rely on it.

The discipline is expressed through the existing sections below: source policy, evidence expectations, risk triggers, review angles and delivery gates. It is not a separate runtime step and does not authorize execution.

### 1. Scope and audience

```text
profession or sub-domain covered
typical dossiers in scope
explicitly out of scope
the responsibility the practitioner carries
```

The scope must state what the pack does not cover, so the practitioner is never misled about coverage.

### 2. Vocabulary

```text
domain terms used in plain language
terms that must not be confused
status words specific to the domain
```

Vocabulary aligns with `EDITORIAL_LANGUAGE.md`: plain, situation-first, no overpromise.

### 3. Source policy

What may enter the working perimeter, and under which caution:

```text
acceptable source types for the domain
sources that are reference, not proof
sources that expire or get superseded
sources that must be checked against a more recent rule
```

A found source stays a candidate. The policy never turns a source into proof by itself.

### 4. Evidence expectations

What a reviewable result must carry in this domain:

```text
what an Evidence Pack must contain for this work
which claims need a source link
which assumptions must be stated
which contradictions must be surfaced, not smoothed over
```

See `EVIDENCE_PACK.md`. A retrieved excerpt is a candidate, not proof.

### 5. Risk triggers

The situations that raise the stakes and must change behavior:

```text
phrases or acts that commit the practitioner externally
figures or limits that carry liability if wrong
material that is private, client, patient, contractual or regulated
a new external rule that may touch an active dossier
```

Each trigger maps to a status, a stricter gate or a User Decision Gate.

### 6. Pre-transmission minimization

What is masked or reduced before anything is sent to an AI engine:

```text
identifiers to mask (names, addresses, client or case references)
sensitive excerpts to minimize or exclude
the minimum necessary context for the task
what must never leave the practitioner's perimeter
```

The default is minimum necessary context, not the whole dossier. See `CONTEXT_PACKS.md` and `SCOPE_ISOLATION.md`.

### 7. Output statuses and delivery gates

How a result is qualified before it can leave:

```text
the status an output carries (draft, to verify, candidate, deliverable)
who the recipient may be at each status
which approval level (C0-C5) a delivery requires
```

Approval levels follow `APPROVALS.md`. Nothing leaves without a status.

### 8. Answering / acting boundary

The boundary the practitioner asked to be explicit:

```text
what the AI may answer (propose, draft, summarize)
what counts as acting (sending, filing, committing externally)
what stays a visible human decision
what, if the practitioner explicitly decides so, may be a bounded and traced action
```

Answering is not acting. Preparing a message is not sending it.

### 9. Memory rules

What may remain after the task, and how it is bounded:

```text
what may become a Register Candidate
the scope it stays attached to
the approval it needs to become a Registre Probatoire entry
what must never be remembered (secrets, raw private payloads)
```

See `MEMORY.md`. Nothing remains without validation, and memory stays scoped.

### 10. Review angles and decision gates

How tensions are exposed before the human decides:

```text
which Pantheon Roles are mandatory for this domain
which rites coordinate recurring tensions
which situations escalate to a User Decision Gate
```

See `GOVERNANCE_COLLEGE.md`, `rites/README.md` and `USER_DECISION_GATE.md`. Roles judge, the human decides.

### 11. Templates

```text
recurring dossier or message shapes for the domain
the fields each template makes explicit
the status each template starts in
```

A template is a preparation or projection pattern, not runtime authority. Runtime-facing templates remain with the applicable Hermes/external-client owners; governed visual composition remains with `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md`, `CARD_STACK_MODEL.md` and existing Card projection owners. A domain pack does not create a client-specific template subsystem.

## Minimum fields a domain pack declares

A domain pack declares, at minimum:

```text
domain_name
scope
out_of_scope
vocabulary
source_policy
pre_analysis_intake_rule
evidence_expectations
risk_triggers
minimization_rules
output_statuses
delivery_approval_levels
answering_acting_boundary
memory_rules
mandatory_roles
decision_gate_triggers
templates
status: draft-only until reviewed
```

A domain pack is draft-only until reviewed. Activation reveals tensions and constrains context; it does not grant professional authority.

## Boundary phrase

```text
A domain pack frames professional AI use.
It does not advise, validate, send, execute or remember by itself.
The professional decides. Only the validated remains.
```

## Next

Profession-specific packs reuse these eleven sections. The first worked pack is architecture, drafted from this general specification and from the architecture examples under `docs/examples/`.
