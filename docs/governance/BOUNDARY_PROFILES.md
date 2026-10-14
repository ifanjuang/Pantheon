# Boundary Profiles

Status: active support doctrine — boundary profile vocabulary and deduplication rule.

This document defines reusable boundary profiles for Pantheon Next documents and templates.

It does not create a runtime, schema, test, CI workflow, operation, platform component, Docker configuration, environment setting, approval engine, memory engine, scheduler, queue, provider router, plugin manager, installer, updater or external action.

## Purpose

Many repository documents need to say that they do not execute, approve, remember, send, schedule, route providers or install tools.

Repeating that whole disclaimer in every document creates noise.

Use a `Boundary profile` line when a document can inherit a standard boundary.

## Rule

A boundary profile reduces repeated boilerplate.

It does not reduce responsibility.

If a document touches a protected path, proposes an external action, changes execution status, changes memory behavior, changes approval behavior or changes a runtime surface, the specific boundary must still be explicit.

## A profile classifies the document, not its subject

Choose the profile from what the document **is and does**, never from what it is about.

A policy governing external tools is active support doctrine. A review of one external runtime is an external reference review. Both are "about external things"; only the second one is one.

This is the distinction that failed in practice. Where the vocabulary offered no term for what a document *is*, authors reached for a label describing its *subject*:

```text
external runtime adapter
architecture source adapter specialization
architecture_project_understanding_projection
projection_definition
```

Each of those is a vocabulary of one, useful to no other document. A subject belongs in the title and in the `Status:` line, not in this slot.

## Inherited role separation

`docs/governance/ARCHITECTURE.md` (active doctrine) owns the role separation, and every profile inherits it:

```text
Hermes-compatible clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides.
```

A document that declares a `Boundary profile` therefore does not need to restate it, and should not.

Restating it is not false. It is duplication, and duplication is what makes a change to the separation expensive: retiring one named client required sweeping the same sentence out of documents one by one, because each held its own copy instead of inheriting the owner's.

Inheritance covers the generic separation only. A document that names a specific exposure, execution, governance or approval surface is making a concrete claim about that surface and must state it with the fields below.

## Boundary fields

For concrete capabilities, repos, skills, connectors, workflows or runtime changes, prefer explicit fields:

```text
exposed_by
executed_by
governed_by
approved_by
forbidden
```

Use these fields when the answer must classify who displays, who executes, who governs, who approves and what remains forbidden.

## Profiles

### `documentation_only`

Use for explanatory Markdown that states or explains an idea without proposing implementation.

Means:

```text
runtime: false
schema: false
test: false
ci: false
external_action: false
memory_promotion: false
approval_change: false
```

### `candidate_support_note`

Use for notes that propose, explore or frame a candidate direction.

Means:

```text
binding_doctrine: false
implementation: false
runtime: false
external_action: false
memory_promotion: false
automatic_approval: false
```

Candidate support can inform a later decision. It cannot promote itself.

### `active_support_doctrine`

Use for documents that clarify, coordinate or operationalize already accepted doctrine.

Means:

```text
canonical_override: false
runtime: false
implementation: false
external_action: false
memory_promotion: false
automatic_approval: false
```

Active support doctrine must remain compatible with canonical doctrine and `AUTHORITY_INDEX.md`.

### `active_governance_doctrine`

Use for a document that **is** accepted doctrine — canonical or active — rather than one that supports it.

Means:

```text
doctrine: true
runtime: false
implementation: false
external_action: false
memory_promotion: false
automatic_approval: false
```

Authority comes from the `Status:` header and `AUTHORITY_INDEX.md`, never from this line. Declaring the profile does not promote a document to doctrine.

### `external_reference_review`

Use for a review of an external specification, runtime, tool or capability that Pantheon has not adopted.

Means:

```text
installed: false
adopted: false
activated: false
task_authorized: false
runtime: false
external_action: false
memory_promotion: false
```

Reviewing something is not selecting it. A recorded external fact is provenance rather than a commitment, and its currentness decays, so a review names the version it read.

### `bounded_implementation_change`

Use for a change under `implementation/` that runs — code, persistence, projections, adapters and their tests.

Means:

```text
implementation: true
runtime: candidate
approval: false
authorization: false
evidence_admission: false
memory_promotion: false
external_action: false
canonical_override: false
```

This is the only profile that admits executable behavior, so it is exactly where `implementation success != authorization` has to be said out loud. Passing tests are implementation evidence; they approve no effect, admit no Evidence and move no doctrine.

### `validation_only_trace`

Use for reconciliation notes, local reports or audit traces.

Means:

```text
doctrine_creation: false
runtime: false
approval: false
external_action: false
memory_promotion: false
```

A trace may support a later review. It is not doctrine by itself.

### `non_executable_template`

Use for prompt, handoff, return, form, profile, flow, trace or policy templates that are not deployed.

Means:

```text
installed: false
deployed: false
executed: false
runtime_config: false
skill_installation: false
external_action: false
memory_promotion: false
automatic_approval: false
```

A template may frame future use. It does not prove that the tool, skill, flow or action exists.

### `schema_contract`

Use for declarative schema files or schema notes.

Means:

```text
validation_contract: true
runtime: false
approval: false
truth_validation: false
external_action: false
memory_promotion: false
```

Schema validity is structural only.

### `read_only_verification_surface`

Use for bounded checkers or status surfaces that report but do not act.

Means:

```text
read_only: true
runtime_execution: false
write_action: false
approval: false
external_action: false
memory_promotion: false
```

A read-only pass is not approval, truth, memory admission or runtime safety.

## Minimal usage

Recommended header pattern:

```text
Status: candidate support note — documented non-implemented.
Boundary profile: candidate_support_note.
```

or:

```text
Status: candidate support note — non-executable prompt template — documented non-implemented.
Boundary profile: non_executable_template.
```

## Required local override

Add a local boundary section when the document introduces any of these:

```text
protected path change
schema or test change
CI or workflow change
runtime status claim
external tool or connector adoption
installation proposal
update proposal
health status
rollback status
external send or write action
memory admission
approval behavior
```

## Non-equivalence reminders

Boundary profiles preserve non-equivalence rules.

Use `docs/governance/NON_EQUIVALENCE_RULES.md` as the canonical reference for recurring distinctions such as:

```text
template != implementation
schema_valid != approved
runtime_success != evidence
installed != approved
trace != doctrine
```

Do not copy the full non-equivalence list into every document. Repeat only the distinctions that are locally material.

## Forbidden use

Do not use a boundary profile to hide a consequential change.

If the change has an operational effect, name the effect.

If the effect is not approved, state that it is not approved.
