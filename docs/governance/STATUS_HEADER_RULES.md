# Status Header Rules

Status: active support doctrine — status header vocabulary and deduplication rule.
Boundary profile: active_support_doctrine.

This document defines how Markdown `Status:` headers should be written in Pantheon Next.

It does not create a runtime, schema, test, CI workflow, approval engine, memory engine, scheduler, queue, provider router, installer, updater or external action.

## Purpose

`Status:` headers are useful because they make the state of a file visible near the top of the file.

They become harmful when every document invents a slightly different wording.

Use this file to keep status headers readable, stable and compatible with repository guards.

## Required form

Use one line near the top of the file:

```text
Status: <authority family> — <local qualifier> — <repo state>.
```

The local qualifier may be omitted when unnecessary:

```text
Status: active support doctrine — implemented as documentation.
```

## Authority families

Prefer one of these families:

```text
canonical doctrine
active support doctrine
active support note
candidate support doctrine
candidate support note
candidate support specification
candidate support map
candidate orientation
validation-only trace
validation-only proposal
reference
implementation artifact
external reference
obsolete
refused
not applicable
```

Do not invent a new family if one of these fits.

## Repo states

Prefer one of these repo states:

```text
implemented as documentation
documented non-implemented
to verify
implemented as schemas
implemented as static asset
implemented as local script
implemented as test
implemented as CI
voluntarily absent
obsolete
refused
not applicable
```

A repo state must not imply runtime behavior unless runtime code, operations or deployment material actually exists.

## Common patterns

### Canonical or active doctrine

```text
Status: canonical doctrine — implemented as documentation.
Status: active support doctrine — implemented as documentation.
Status: active support doctrine — documented non-implemented.
```

### Candidate material

```text
Status: candidate support doctrine — documented non-implemented.
Status: candidate support note — documented non-implemented.
Status: candidate support specification — documented non-implemented.
Status: candidate orientation — documented non-implemented.
```

### Trace and logs

```text
Status: validation-only trace — documented non-implemented.
Boundary profile: validation_only_trace.
```

### Templates

```text
Status: candidate support note — non-executable template — documented non-implemented.
Boundary profile: non_executable_template.
```

### Indexes and maps

```text
Status: candidate support map — populated; awaiting review.
Status: active support index — implemented as documentation.
```

## Boundary profile line

When the document repeats a known boundary, add a separate line:

```text
Boundary profile: <profile_name>.
```

Examples:

```text
Boundary profile: candidate_support_note.
Boundary profile: active_support_doctrine.
Boundary profile: validation_only_trace.
Boundary profile: non_executable_template.
```

Use `docs/governance/BOUNDARY_PROFILES.md` for profile meanings.

## Forbidden status shortcuts

Avoid statuses that imply authority, safety or implementation without proof:

```text
approved
accepted
safe
trusted
canonicalized
active runtime
installed
healthy
ready for execution
authorized
memory admitted
```

Use a precise phrase instead:

```text
reviewable
implemented as documentation
documented non-implemented
candidate support note
validation-only trace
pending human decision
```

## Relation to non-equivalence rules

Status headers must respect `docs/governance/NON_EQUIVALENCE_RULES.md`.

In particular:

```text
status_header != implementation
implemented_as_documentation != runtime
validation_only_trace != doctrine
candidate_support != approval
```

## Local override

If a document touches runtime, protected paths, schemas, tests, CI, memory, approval, installation, update, rollback or external action, do not rely only on the header.

Add a local boundary section that names the effect directly.

## Review rule

When adding or editing a `Status:` header:

```text
1. choose an existing authority family;
2. choose an existing repo state;
3. add a boundary profile if it removes boilerplate;
4. repeat local distinctions only when material;
5. do not imply implementation through wording.
```
