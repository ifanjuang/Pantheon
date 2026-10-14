# Mobile Knowledge A/B proposal review

Date: 2026-08-05
Status: implementation candidate; real-device and production-Hermes acceptance not established.

## Objective

Extend the existing mobile Markdown editor so one exact selection may receive one or two immutable proposal variants, be compared by a human, and only then be explicitly applied through the existing optimistic Knowledge revision path.

This replaces the obsolete direct-Hermes proposal path from draft PR Pantheon-Next#235. Hermes returns the canonical `Execution Result` type `knowledge_edit_variant`, defined in Pantheon-Next at commit `63f9769161cec395caef9625a37f8053388036fc`.

## Existing owners reused

```text
Knowledge source and revision          knowledge_items
bounded edit request                   knowledge_edit_requests
runtime return                         execution_results / execution_result_items
proposal projection                    knowledge_edit_variants
human review trace                     knowledge_edit_review_events
Knowledge application                  knowledge.apply_edit_request
mobile local request queue             existing Knowledge PWA
```

No universal Information branch, workflow engine or second result envelope is introduced.

## Lifecycle

```text
exact selection request queued
-> admitted Hermes execution returns an Execution Result
-> editor-controlled deterministic projection validates the exact request scope
-> A, and B when requested, become immutable local candidates
-> human selects or rejects
-> explicit apply rechecks the current Knowledge version and selection digest
-> existing Knowledge revision transaction applies the selected replacement
```

```text
Execution Result stored != variant projected
variant projected != variant selected
variant selected != edit applied
edit applied != Knowledge professionally validated
Knowledge revised != Evidence
```

## Exact scope

The request and each candidate share:

```text
request_ref
request_scope_digest
knowledge_ref
base_version
selection_start / selection_end
selected_text_digest
```

A candidate with another scope, revision, selection digest or replacement digest is refused. It is never silently rebased or adapted.

## API split

Editor-key routes:

```text
POST /knowledge/{knowledge_id}/variant-edit-requests
POST /execution-results/{execution_result_id}/results/{result_ref}/project-knowledge-edit-variant
GET  /knowledge/{knowledge_id}/edit-reviews
GET  /edit-requests/{request_id}/review
POST /edit-requests/{request_id}/select-variant
POST /edit-requests/{request_id}/reject
POST /edit-requests/{request_id}/apply-selected
```

Hermes stores its output through the existing Execution Result API. There is no direct Hermes route for inserting a Knowledge variant.

Human identity is required for selection, rejection and application. Deterministic projection does not claim a human decision.

## Persistence

`knowledge_edit_variants` stores immutable projected candidates with their source Execution Result and item references. `knowledge_edit_review_events` is append-only.

The edit-request row stores only current projection fields needed for review and application. It does not replace the historical event trace.

Relevant dependency order is explicit in `cockpit_composed.initialize_composed_schema`:

```text
Source Intake owner
-> Information projection owner
-> Execution Result owner
-> Knowledge edit variants
```

The corresponding files are currently:

```text
009_source_intake_admission.sql
013_information_card_projection.sql
010_execution_results.sql
014_knowledge_edit_variants.sql
```

The numeric filename prefixes are not treated as a global migration scheduler. The composed initializer declares the actual dependency order. Migration `014` also upgrades the pre-existing result-kind constraint for already initialized databases.

## Mobile behavior

The separate `variant_review.js` adapter:

- preserves one local queue for request creation;
- retains version, range and selected text in each queued request;
- adds an explicit A/B action;
- loads only reviews for the open Knowledge item;
- displays one diff per projected candidate;
- separates selection, rejection and application;
- uses explicit refresh and online replay without polling;
- does not expose the server-side Execution Result projection operation;
- leaves authenticated APIs outside the service-worker cache.

## Boundaries

```text
queued offline request != overwrite permission
provider result stored != displayed proposal
source_ref attached != Evidence admitted
editor key != professional validation
UI action != task authorization
runtime success != Knowledge acceptance
```

No scheduler, queue server, automatic retry, provider router, memory promotion, Evidence admission, automatic approval or autonomous rewriting is added.

## Integration with Source Intake and Information

Source Intake PR Pantheon-Next#242 and Information projection PR Pantheon-Next#243 are merged. The composed Cockpit initializer replays both owner migrations before the A/B review persistence, while the Information routes remain owned by `cockpit_shell`.

```text
Information displayed != Knowledge edit candidate
Document backing != Knowledge source authority transferred
Source linked != variant authorized
```

No Information relation, Information variant or second content graph is introduced by this tranche.

## Remaining issue Pantheon-Next#165 scope

```text
structured revision request for Knowledge proposal variants
whole-document coherence report candidate
summary/introduction/TOC/conclusion adaptation candidates
conflict-safe offline replay for review decisions
real-device accessibility and offline recovery acceptance
```
