# Answer Verification Gate

Status: candidate / to verify — central doctrine proposal for memory-first answers, evidence escalation and consequential response status.
Boundary profile: candidate_support_note.

This document is doctrine candidate only.

It does not implement a runtime, retrieval layer, checker, approval engine, evidence store, memory engine, scheduler, queue, MCP server, OpenWebUI extension, Hermes skill, database rule or automatic decision system.

## Purpose

Pantheon Next must not turn every remembered statement into a governed record.

Professional work needs a living memory layer. It should be able to recall context, propose associations, detect tensions and answer lightweight questions without forcing every thought through a proof procedure.

The risk is different: memory-based answers can become dangerous when they are presented as verified truth, validated choice, canonical memory, delivery-ready output or authorized action.

This document defines the gate between:

```text
memory may speak
```

and:

```text
evidence is required before assertion, decision or action
```

## Core doctrine

```text
Free memory is allowed to speak.
Knowledge may be consulted.
Retrieval may suggest.
Verified evidence is required to assert.
Governed status is required to decide.
Approval is required to act.
Logs may audit.
Delivery may commit.
```

French operational phrasing:

```text
La memoire peut parler.
La connaissance peut etre consultee.
La recherche peut suggerer.
La preuve permet d'affirmer.
Le statut permet de decider.
L'approbation permet d'agir.
Le log permet d'auditer.
La livraison peut engager.
```

No layer may silently replace another.

## Architectural shift

The simple flow is insufficient:

```text
Question -> memory -> answer
```

A fully proof-first flow is also too heavy:

```text
Question -> evidence required for everything -> answer
```

The governed flow is:

```text
Question
-> memory-based answer candidate
-> consequence qualification
-> verification when required
-> explicit answer status
-> status or approval gate when consequential
```

Pantheon does not govern every answer.

Pantheon governs answers that become consequential.

## Layer separation

The COP, administration cockpit or exposure surface may display these layers together, but they must remain separate.

| Layer | Role | Authority |
|---|---|---|
| Knowledge Layer | Holds consultable material: files, emails, sources, uploaded documents, knowledge bases, official references | No authority by default |
| Free Memory | Recalls, associates, hypothesizes, detects tensions | No canonical authority |
| Retrieval / Candidate Discovery | Finds possibly relevant material, chunks, records or prior context | Candidate signal only |
| Evidence Layer | Structures sources, excerpts, versions, assumptions and proof references | Probative authority, subject to status |
| Status / Choice Registry | Records the evolution of choices, claims, dependencies, versions and statuses | Procedural authority |
| Approval Layer | Authorizes promotion, delivery or external action | Legitimacy authority |
| Logs / Observability | Records runtime activity, errors, tool calls, traces and health | Audit support only |
| Delivery / External Action | Records what left the system or affected the outside world | External effect record |

The memory may suggest.

The knowledge layer may be consulted.

Retrieval may propose candidates.

The evidence may support.

The status may qualify.

The approval may authorize.

The log may audit.

The delivery record may prove that something was transmitted.

None of these proves the others by default.

## Forbidden equivalences

The following collapses are forbidden:

```text
Knowledge != Memory
Memory != Evidence
Evidence != Status
Status != Approval
Approval != Truth
Logs != Evidence by default
Delivery != Validation
Retrieval != Proof
Score != Confidence
Confidence != Validity
Repeated use != Registre Probatoire entry
Embedding match != Source
Runtime state != Governed status
Draft != Sent
Sent != True
```

A remembered claim is not proof.

A retrieved source is not a decision.

A runtime log is not evidence by default.

A status is not an approval.

An approval is not truth.

A delivery record is not validation of the delivered content.

## Verification levels

Every consequential response should be able to declare its verification level.

| Level | Name | Source posture | Allowed use |
|---|---|---|---|
| V0 | free | memory, session context or reasoning only | brainstorming, informal orientation |
| V1 | memory-based | memory recalls a prior context but no evidence is attached | low-risk reminder with explicit caution |
| V2 | to verify | memory or retrieved context suggests an answer but evidence is missing, incomplete, stale or conflicted | working hypothesis, not decision-ready |
| V3 | evidence-verified | answer is supported by identified evidence references and scope is clear enough for review | reviewable assertion, subject to status |
| V4 | approved | evidence, status and required approval are present | delivery, promotion or external action within scope |

The gate does not forbid V0 or V1 answers.

It forbids presenting V0, V1 or V2 as V3 or V4.

## Consequence levels

The verification requirement depends on possible consequence.

This document uses `K0` to `K4` for consequence levels to avoid collision with approval levels owned by `APPROVALS.md`.

| Consequence level | Description | Minimum posture |
|---|---|---|
| K0 | casual thought, ideation, style, non-binding wording | V0 allowed |
| K1 | low-risk reminder or orientation | V1 allowed with visible qualifier |
| K2 | useful claim that could affect work but does not yet commit the dossier | V2 minimum; evidence recommended |
| K3 | claim that affects truth, cost, scope, compliance, status, coordination or responsibility | V3 required |
| K4 | decision, memory promotion, delivery, instruction or external action | V4 required |

Approval level names remain owned by `APPROVALS.md`; this document only defines the answer-verification posture.

## Gate questions

Before a memory-based response is treated as reliable, the gate asks:

```text
1. Is the answer merely conversational or exploratory?
2. Could it create a false project truth?
3. Could it change a choice, status, cost, scope, deadline or responsibility?
4. Could it reactivate an obsolete or superseded memory?
5. Could it contradict a validated status?
6. Could it rely on stale, superseded, cross-dossier or weak evidence?
7. Could it trigger or justify an external action?
8. Could it cause sensitive or private information to be retained improperly?
9. Could a professional rely on it in a way that creates liability?
10. Is a runtime log being mistaken for professional proof?
```

If the answer to all consequence questions is no, memory may answer freely.

If any answer is yes, the response must escalate to evidence, status and possibly approval.

## Answer status object

The cockpit or runtime may represent the result with a reviewable status object.

Specification only. This is not an executable schema.

```yaml
answer_status:
  source_mode: memory_based | knowledge_context | retrieved_context | evidence_pack | approved_record | runtime_log | delivery_record
  verification_level: V0_free | V1_memory_based | V2_to_verify | V3_evidence_verified | V4_approved
  consequence_level: K0 | K1 | K2 | K3 | K4
  evidence_required: true | false
  evidence_refs: []
  status_refs: []
  approval_required: true | false
  approval_ref: null
  log_refs: []
  delivery_refs: []
  confidence_note: "Memory suggests this, but no evidence has been attached yet."
  allowed_use: brainstorming | informal_orientation | working_hypothesis | reviewable_assertion | approved_action
  missing_evidence: []
  contradictions: []
  stale_or_superseded_refs: []
```

The shape above is a documentary contract candidate. Any executable schema must be proposed separately under the protected `schemas/` path and requires explicit approval.

## Claim record candidate

When a statement becomes consequential, a simple answer status may not be enough. The COP or an external runtime may need to represent the claim and its transitions.

Specification only. This is not an executable schema.

```yaml
claim_record:
  id:
  claim_text:
  scope:
    level: session | dossier | project | domain | organization
    id:
  source_mode:
    - memory
    - knowledge
    - retrieved_context
    - evidence_pack
    - approved_record
    - runtime_log
    - delivery_record
  current_status:
    value: free | remembered | candidate | to_verify | evidence_candidate | evidence_verified | contradicted | to_arbitrate | validated | approved | delivered | superseded | obsolete | revoked | rejected | blocked | archived
    updated_at:
    updated_by:
  verification:
    level: V0_free | V1_memory_based | V2_to_verify | V3_evidence_verified | V4_approved
    evidence_required: true
    evidence_refs: []
  consequence:
    level: K0 | K1 | K2 | K3 | K4
    triggers:
      - cost
      - scope
      - compliance
      - client_commitment
      - memory_promotion
      - external_action
  approval:
    required: true
    approval_ref:
    approval_level:
  memory:
    candidate_allowed: true
    canonical_allowed: false
    scope_locked: true
    retention:
  delivery:
    allowed: false
    delivery_refs: []
  logs:
    runtime_trace_refs: []
    log_as_evidence: false
  uncertainty:
    assumptions: []
    contradictions: []
    missing_evidence: []
  next_action:
```

A claim record is not a memory record, proof registry entry, runtime log or delivery receipt. It is a governance-facing status shape for consequential statements.

## Evidence item, Evidence Pack and Evidence Registry

This document uses three terms that must not be merged.

| Term | Meaning | Boundary |
|---|---|---|
| Evidence Item | A specific source, excerpt, file, dated document, command output or trace selected for review | Does not decide status alone |
| Evidence Pack | A human-auditable proof package linked to a Task Contract and output | Not a runtime log or chain-of-thought |
| Evidence Registry | A possible index of evidence items and packs | Must not become runtime, memory engine or approval engine |

A retrieved chunk may become an Evidence Item only after it is selected, scoped, versioned and represented as reviewable evidence.

A runtime log may become an Evidence Item only when the technical activity itself is governance-relevant and has been summarized for review.

## Status transitions

A status must not erase the previous status.

It creates a transition.

Example:

```yaml
choice_record:
  id: pool_dossier_example
  object: pool
  current_status: abandoned
  previous_status: candidate
  scope: dossier_example
  evidence_refs:
    - meeting_report_2024_02_02
    - client_email_2024_02_05
  decision_ref: user_validation_2024_02_05
  supersedes:
    - pool_candidate_2024_01_12
  consequences:
    - pool_heat_pump_obsolete
    - terrace_layout_to_verify
    - rainwater_design_to_review
```

History is not deleted.

The transition is qualified.

Contradiction does not erase memory; it opens a transition to qualify.

## Case catalogue

### Lightweight memory answer

```text
The client seemed interested in a continuous terrace.
```

Allowed posture:

```text
V1 memory-based.
K1 orientation.
Use: low-risk reminder.
Qualifier: d'apres memoire / to verify before design decision.
```

### Consequential assertion

```text
The continuous terrace is validated in the project.
```

Required posture:

```text
V3 evidence-verified minimum.
K3 truth / scope impact.
Evidence: client email, meeting report, validated plan or decision record.
```

### External action

```text
Send the modified plan to the contractor.
```

Required posture:

```text
V4 approved.
K4 external action.
Evidence: current drawing, recipient scope, delivery status, approval reference.
```

### Source found but not decisive

```text
We like the idea of a continuous terrace.
```

This may support a preference.

It does not prove validation.

Allowed posture:

```text
Evidence candidate.
Claim supported: preference.
Claim not supported: validated decision.
Next action: seek stronger evidence or open User Decision Gate.
```

### Source probative but scope ambiguous

A client may validate a terrace in an early design phase without validating its technical, financial or contractual consequences.

Allowed posture:

```text
V2 or V3 depending on scope clarity.
Scope status: to verify.
Delivery status: not delivery-ready.
```

### Strong source but obsolete

A plan, email or report may be true historically and false operationally.

Allowed posture:

```text
Evidence status: superseded.
Current use: historical context only.
Requires current source before assertion.
```

### Contradictory sources

If an email says the pool is abandoned and a later report says it is retained, the system must not smooth the conflict.

Allowed posture:

```text
Claim status: contradicted.
Decision status: to_arbitrate.
Required gate: User Decision Gate.
Memory behavior: do not promote.
```

### Oral decision

A meeting or site conversation may be relevant, but it is usually weaker than a written confirmation.

Allowed posture:

```text
Evidence type: oral_decision_note.
Probative strength: weak_to_medium.
Requires confirmation before delivery or contractor instruction.
```

### Draft prepared but not sent

```text
Draft != sent.
```

Allowed posture:

```text
Delivery status: draft.
External effect: false.
Approval required to send if consequential.
```

### Sent but not true

```text
Sent != true.
```

A sent message proves transmission. It does not prove the content was correct.

Allowed posture:

```text
Delivery status: sent.
Truth status: disputed or to verify when challenged.
Corrective action possible: true.
```

### Runtime log as proof

A log may prove that a technical event occurred.

It does not prove that the professional claim is true.

Allowed posture:

```text
Log status: technical_trace.
Evidence status: not evidence by default.
Can become evidence if selected, scoped and summarized.
```

### OCR or extraction output

OCR text is not the document.

It is an extraction candidate.

Allowed posture:

```text
Source type: ocr_extract.
Reliability: degraded unless checked.
Requires visual check for consequential use.
Allowed use: evidence_candidate_only.
```

### RAG retrieved the wrong version

A chunk from a superseded version can be semantically relevant and operationally wrong.

Allowed posture:

```text
Retrieval status: candidate.
Version check required: true.
Evidence status: blocked until version resolved.
```

### Repeated claim

Repetition is not validation.

Allowed posture:

```text
Claim repeated: true.
Canonical memory: false.
Requires evidence link and approval for promotion.
```

### Cross-dossier memory

A memory from one dossier may suggest an analogy, but it must not become a rule for another dossier.

Allowed posture:

```text
Scope: other_dossier.
Cross-scope reuse: forbidden without review.
Allowed use: analogy_only.
```

### Sensitive but useful information

Some information may be useful but unsafe to retain.

Examples include health, family, financial, conflict, credential or private client information.

Allowed posture:

```text
Memory candidate: forbidden or minimized.
Evidence storage: restricted.
Retention: limited.
```

### External rule or reference may be stale

Regulatory, legal, product, standard, pricing and public-office information can expire.

Allowed posture:

```text
Source status: stale_or_to_refresh.
Claim status: to_verify.
Requires current source before consequential assertion.
```

### Professional high-risk triggers

Architecture domain triggers include:

```text
surface
budget
height
setback
parking
fire safety
accessibility
structure
insurance
permit status
client validation
contractor instruction
payment approval
scope commitment
```

Minimum posture:

```text
K3 or K4 depending on action.
V3 required for assertion.
V4 required for delivery, instruction, approval, promotion or external action.
```

### Role or agent output

A Pantheon role, Hermes profile, LangGraph node or DeepAgents subagent may propose a review note.

It does not approve.

Allowed posture:

```text
Role output status: review_note_candidate.
Approval status: not_approved.
```

### Runtime state from LangGraph or other orchestration

A runtime checkpoint is not memory.

A runtime state is not evidence by default.

Allowed posture:

```text
Runtime state: external.
Canonical memory: forbidden.
Evidence possible: summary only if relevant to review.
```

### Correction, revocation and supersession

A validated statement may later be revoked by stronger evidence.

Allowed posture:

```yaml
status_transition:
  from: validated
  to: revoked
  reason: stronger_evidence
  evidence_ref: new_document
  previous_memory_behavior: superseded_not_deleted
```

The validated remains historically.

The current status changes.

## Memory, evidence, status, logs and delivery are not interchangeable

A memory can remember that a client mentioned abandoning a pool.

That memory is not proof.

The Evidence Registry may contain a dated email or meeting report confirming the abandonment.

The Status / Choice Registry may then record:

```text
pool: validated -> abandoned
pool heat pump: candidate -> obsolete
terrace compatibility: candidate -> to verify
foundation assumption linked to pool: to verify -> to arbitrate
```

The log may record that a tool extracted this information.

The delivery record may record that a note was sent.

Neither the log nor the delivery record proves the professional claim by default.

The memory may keep the whole history.

The status registry records the transition.

A contradiction does not erase history; it opens a transition to qualify.

## Relationship to existing doctrine

### Relationship to `MEMORY.md`

`MEMORY.md` governs the boundary between Hermes free memory and the Registre Probatoire (Register Candidates and Registre Probatoire entries).

This document adds a response-level gate before memory is used as an assertion.

Free memory may support V0 and V1 answers. The Registre Probatoire remains governed by `MEMORY.md` and `EVIDENCE_MEMORY_CANONICALIZATION.md`.

No automatic memory promotion is introduced.

### Relationship to `EVIDENCE_PACK.md`

`EVIDENCE_PACK.md` governs the proof package produced after external execution.

This document defines when an answer must escalate from memory-based response to evidence-supported assertion.

Evidence remains governed justification, not runtime activity.

### Relationship to logs and observability

Logs, traces, execution metadata, checkpoints, health checks and runtime states may support audit.

They are not Evidence Packs.

They are not Registre Probatoire entries.

They are not approval records.

They may be cited as Evidence Items only when the technical fact itself is governance-relevant and has been selected, scoped and summarized for human review.

### Relationship to delivery and external action

A delivery record proves that something left the system or affected the outside world.

It does not prove the content was true, current, approved or complete unless those references are attached.

Consequential delivery requires V4 posture.

### Relationship to `CAPABILITY_PLACEMENT.md`

The gate follows the placement rule:

```text
If this goes wrong, can it produce a false truth,
an unapproved external effect,
a wrong memory,
an invalid approval,
an illegitimate scope expansion,
or an unauthorized action?
```

When yes, Pantheon governs the decision.

The execution still belongs outside Pantheon.

### Relationship to domain packs

Domain packs should define professional triggers that raise the required verification level.

Examples:

```text
architecture: budget, surface, regulatory compliance, client validation, contractor instruction
law: deadline, jurisdiction, legal position, filing, client advice
medicine: diagnosis, medication, urgent symptom, patient instruction
accounting: tax treatment, filing obligation, financial statement claim
```

A domain pack may adjust risk triggers and delivery gates, but it must not lower the general rule that consequential assertions require evidence.

## COP display rule

The COP must not collapse memory, knowledge, retrieval, evidence, status, approval, logs and delivery into one object.

It may display them together only if their authority remains visible.

Minimum display posture:

```text
answer text
verification level
consequence level
source mode
memory signals used
knowledge or retrieval refs
attached evidence refs
current status refs
approval state
runtime log refs when relevant
delivery refs when relevant
allowed use
remaining uncertainty
next action
```

The COP is a cockpit of qualification.

It is not the memory itself.

It is not the Evidence Registry.

It is not the Status / Choice Registry.

It is not the approval authority.

It is not the runtime log.

It is not the delivery authority.

## Forbidden drift

This doctrine must not become:

- a universal proof requirement for every answer;
- a hidden runtime classifier;
- an automatic approval engine;
- an automatic memory promotion engine;
- a replacement for `MEMORY.md`;
- a replacement for `EVIDENCE_PACK.md`;
- a database schema by implication;
- a COP implementation spec;
- an observability implementation spec;
- a delivery engine;
- a reason to store hidden chain-of-thought;
- a way to treat memory as proof;
- a way to treat logs as evidence by default;
- a way to treat delivery as validation.

## Review decision proposal

```text
Accepted:
- memory may answer lightweight questions;
- consequential answers must escalate to evidence, status and approval;
- knowledge, memory, retrieval, evidence, status, approval, logs and delivery must remain separate.

To verify:
- whether this remains a standalone candidate doctrine;
- whether parts should later be reconciled into MEMORY.md, EVIDENCE_PACK.md or REQUEST_LIFECYCLE.md;
- whether the claim_record shape should ever become a schema.

To arbitrate:
- exact naming of consequence levels;
- minimum COP display fields;
- which domain triggers force V3 or V4.

Refused:
- treating retrieval, score, repeated use, runtime state, log or delivery as proof;
- automatic approval;
- automatic memory promotion;
- hidden runtime classification inside Pantheon.
```

## Final rule

```text
Memory first.
Evidence when consequential.
Status when deciding.
Approval when acting.
Logs when auditing.
Delivery when committing.
```

The validated remains.
