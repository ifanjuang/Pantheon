# Architecture Document Review

Status: candidate support doctrine — first architecture-domain document review slice.
Boundary profile: candidate_support_note.

This document applies `DOMAIN_PACK_SPEC.md` and `DOCUMENT_INTELLIGENCE.md` to architecture practice.

It is documentation only.

It does not implement a professional authority, document processor, OCR pipeline, vector index, graph runtime, database schema, OpenWebUI template, Hermes skill, approval system, memory engine or automatic action.

## Purpose

Architecture practice is document-heavy and liability-sensitive.

The useful first slice is not a generic architecture assistant. It is a governed review method for comparing professional documents, surfacing risks and keeping responsibility explicit.

The first concrete use case:

```text
CCTP / quote comparison in ACT or pre-contract review.
```

The method may later extend to site reports, reservations, service orders, contracts, insurance certificates, planning documents, official notices and client instructions.

## 1. Scope and audience

Covered:

```text
architects
architecture agencies
maître d'oeuvre workflows
private or public project dossiers
ACT / DET / AOR-oriented document review
```

Typical dossiers:

```text
CCTP
CCAP
AE
DPGF
contractor quote
service order
site report
reservation list
contractor response
technical note
planning exchange
insurance or qualification document
```

Out of scope:

```text
legal advice by the system
urban-planning compliance verdict by the system
structural engineering validation by the system
thermal or fluid engineering validation by the system
accounting validation
insurance advice
automatic contractor selection
automatic contractual action
automatic client or contractor transmission
```

The architect remains responsible for review, judgement, coordination and transmission.

## 2. Vocabulary

Core terms:

```text
source document: received or referenced document
fragment: bounded source excerpt
claim: interpretation derived from fragments
risk: possible professional consequence requiring review
contradiction: conflict between documents or fragments
missing item: expected item not found in the compared source
Evidence Pack Candidate: review bundle, not proof by itself
approval: explicit human decision at the required level
```

Terms that must not be confused:

```text
retrieved fragment != evidence
comparison candidate != conformity verdict
confidence score != validation
contractor quote line != accepted scope
agency habit != professional rule
site report draft != transmitted instruction
memory candidate != Registre Probatoire entry
```

## 3. Source policy

Acceptable sources for this slice:

```text
project-specific documents selected by the user
dated versions of CCTP / CCAP / AE / DPGF / quote / OS / site report / reservations
professional reference material explicitly selected for the task
prior agency checklists when approved and scoped
```

Sources that are reference, not proof by themselves:

```text
generic model documents
prior project documents
contractor marketing material
web search excerpts
non-current standards or guidance
agency memory not approved for the current task
```

Version-sensitive sources:

```text
CCTP revisions
quote revisions
signed vs unsigned documents
site report revisions
reservation updates
contractor insurance certificates
planning documents
regulatory or professional guidance
```

If the source version is uncertain, the result status cannot exceed:

```text
requires_human_review
```

## 4. Evidence expectations

A reviewable result must carry:

```text
source document references
version or date when known
fragment references
claim type
claim text
affected lot or actor when known
phase
severity or consequence estimate
contradictions and missing evidence
recommended status
```

For CCTP / quote comparison, every material claim must show at least one CCTP fragment and one quote or DPGF fragment, or explicitly state that the matching quote fragment was not found.

The system must not smooth over contradictions.

Acceptable claim types:

```text
missing_item
contradiction
ambiguity
variant_detected
exclusion_detected
scope_shift
quantity_mismatch
deadline_or_phase_risk
approval_needed
contractor_question_needed
client_arbitration_needed
```

## 5. Risk triggers

The following triggers require stricter gates:

```text
claim that a quote is compliant or non-compliant
claim that a contractor is selected or rejected
claim that a cost, delay or penalty is contractually established
claim that a task is included, excluded or owed
claim that a reservation is lifted
claim that a service order may be sent
claim that a document is safe to transmit
claim based on missing or uncertain source versions
claim touching liability, insurance, safety, structure, fire, accessibility or public procurement
```

The default result for such items is:

```text
requires_human_review
```

If the item may commit the architect externally, the result must escalate to a User Decision Gate.

## 6. Pre-transmission minimization

Before sending material to an external model or runtime, minimize:

```text
client names
addresses
financial details not necessary for the task
private correspondence not necessary for the claim
third-party personal data
unrelated project material
```

The default is minimum necessary context.

For CCTP / quote comparison, the preferred task scope is:

```text
one project
one phase
one lot or controlled set of lots
specific document versions
specific comparison objective
```

Cross-project examples may be used only as approved agency checklists or patterns, not as raw precedent.

## 7. Output statuses and delivery gates

Recommended output statuses:

```text
draft_candidate
source_incomplete
requires_more_evidence
requires_human_review
requires_contractor_question
requires_client_arbitration
approved_for_internal_use
approved_for_meeting_preparation
approved_for_transmission_draft
approved_for_contractual_action
rejected
obsolete
```

Delivery gate examples:

```text
internal note: approved_for_internal_use
meeting preparation: approved_for_meeting_preparation
email draft to contractor: approved_for_transmission_draft
service order or contractual position: approved_for_contractual_action
```

Preparing a transmission draft is not sending it.

## 8. Answering / acting boundary

The system may:

```text
summarize selected documents
compare selected documents
extract candidate obligations
surface missing items
surface contradictions
prepare questions for contractor review
prepare a meeting checklist
prepare an email draft with visible status
build an Evidence Pack Candidate
```

The system must not:

```text
declare a quote compliant
select or reject a contractor
approve a quote
send an email
issue a service order
lift a reservation
validate an insurance position
approve a payment
file or transmit an official document
promote agency memory automatically
```

Bounded and traced actions may exist later only if explicitly approved under Pantheon gates. This document does not authorize them.

## 9. Memory rules

Architecture review may propose Register Candidates such as:

```text
agency checklist candidate
lot-specific vigilance point
project-scoped factual memory
rejected pattern
source mapping pattern
```

Examples:

```text
Check roof technical penetrations when comparing roofing quote against CCTP.
Check whether quote exclusions contradict CCAP or CCTP obligations.
Check whether site report reservations are linked to dated contractor responses.
```

A Register Candidate must remain scoped until approved.

It must not become a Registre Probatoire entry because it was frequent, high-confidence, retrieved, embedded or accepted once on a project.

## 10. Review angles and decision gates

Mandatory review angles for consequential architecture review:

```text
source completeness
version consistency
scope isolation
claim-to-fragment traceability
contractual consequence
professional liability consequence
client or contractor transmission consequence
memory consequence
```

Escalate to a User Decision Gate when:

```text
the result may be transmitted externally
the result affects contractor scope or cost
the result affects client arbitration
the result affects contractual action
the result proposes Registre Probatoire entry
the evidence is contradictory but action is requested
```

Relevant Pantheon roles and rites may be activated according to the task risk, but activation does not validate the result.

## 11. Templates

### CCTP / quote comparison candidate

```text
project:
phase:
lot:
source_documents:
comparison_objective:

finding:
claim_type:
affected_actor:
affected_lot:
severity:

cctp_fragment:
quote_fragment:
missing_or_contradicting_evidence:

interpretation_candidate:
recommended_action:
recommended_status:
approval_needed:
```

### Contractor question draft candidate

```text
project:
lot:
recipient:
status: draft_candidate

question:
source_basis:
requested_clarification:
deadline_or_phase_context:
not_to_send_before:
approval_needed:
```

### Meeting preparation checklist candidate

```text
project:
meeting:
phase:
status: approved_for_meeting_preparation only after review

items_to_discuss:
evidence_refs:
open_questions:
client_arbitrations:
contractor_questions:
risks_not_to_decide_in_meeting_without evidence:
```

## First MVP use case

```text
Compare a CCTP and a contractor quote for one lot.
Detect missing, ambiguous, excluded or contradictory items.
Return only candidates with source fragments and a recommended status.
Require human validation before external use.
```

Inputs:

```text
project scope
phase
lot
CCTP version
quote or DPGF version
comparison objective
```

Outputs:

```text
finding candidates
source fragments
missing evidence
severity estimate
recommended question or action
recommended status
approval requirement
```

Forbidden output:

```text
quote compliant
quote non-compliant
contractor selected
service order ready to send
client decision made
memory promoted
```

## Example

```text
Finding candidate:
CCTP appears to require a roof penetration for ventilation, but no matching quote line was found.

Claim type:
missing_item

Evidence:
CCTP fragment: selected page / section reference.
Quote fragment: no matching item found in selected quote scope.

Risk:
Potential unpriced scope or coordination gap.

Recommended action:
Ask the contractor for written clarification before contract finalization.

Status:
requires_human_review
```

This is not a non-conformity verdict. It is a review item.

## Boundary phrase

```text
The architecture pack frames professional review.
It does not replace the architect's judgement.
The tools surface candidates.
The architect decides what may leave the agency.
```
