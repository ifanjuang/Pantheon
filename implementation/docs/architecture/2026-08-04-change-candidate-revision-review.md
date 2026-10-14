# ChangeCandidate structured revision review

Date: 2026-08-04
Status: implemented candidate in this repository; deployment and real-device acceptance not established.

## Objective

Add the first missing review action from issue Pantheon-Next#165: a human may request revision of an exact Project ChangeCandidate with structured annotations, while preserving the current server-owned diff, base revision, proposal digest and append-only decision history.

## Reused owners

```text
Project attributes and revision     agency_data
proposal envelope and exact diff    agency_change_candidates
structured review                   agency_change_candidate_review
human HTTP gates                    agency_change_candidate_review_api
Cockpit projection                  existing decision card + review adapter
technical history                   agency_change_candidate_events
```

No parallel editor model, workflow engine or Hermes task lifecycle is introduced.

## Review decision

A pending proposal may now receive one terminal human decision:

```text
apply
reject
request revision
```

`request revision` stores:

```text
status = revision_requested
exact base_revision already carried by the proposal
proposal_digest already carried by the proposal
structured annotations
optional decision note
human actor
idempotency key
append-only event and timestamp
```

Supported annotation types are deliberately small:

```text
source_required
question
hypothesis
contradiction
needs_deeper_review
```

Each annotation may target one changed field or the whole proposal and may cite source references. A source reference remains a reference; it is not Evidence admission.

## Cockpit behavior

The existing Project ChangeCandidate card remains the surface. It already displays the exact field-level diff. A separate adapter adds:

- a human `Demander une révision` action only while the proposal is pending;
- a mobile dialog for one or more structured annotations;
- optional source references and a global note;
- read-only projection of stored annotations and ordered review history;
- focus restoration, live status messaging, safe-area handling and reduced-motion behavior.

The adapter does not create a new candidate or start Hermes. A revised proposal must be produced later through the normal admitted proposal path with a new idempotency identity.

## Boundaries

```text
revision requested != Project mutated
revision requested != new Hermes task
annotation source_ref != Evidence
proposal history != business truth
mobile dialog submitted != offline replay implemented
review status != Project status
```

The API response keeps the following facts explicit:

```text
project_mutated = false
execution_authorized = false
task_authorized = false
evidence_admitted = false
new_candidate_created = false
```

## Verification

The slice includes tests for:

- structured annotation validation;
- Project revision and attributes unchanged;
- idempotent replay;
- refusal of apply, reject or second revision decision after closure;
- append-only event persistence;
- composed migration order;
- stable human-only routes;
- Cockpit load order and history projection;
- mobile/accessibility guards;
- JavaScript syntax.

## Remaining issue Pantheon-Next#165 scope

This slice does not close Pantheon-Next#165. Remaining independent tranches are:

```text
A/B proposal variants
candidate global-coherence report
candidate adaptations for summary/introduction/TOC/conclusion
real offline queue and conflict-safe replay
real-device accessibility and offline acceptance
extension beyond Project attributes when an owner contract exists
```

These must reuse the same proposal, provenance, revision and human-review boundaries rather than extending this module into a general workflow engine.
