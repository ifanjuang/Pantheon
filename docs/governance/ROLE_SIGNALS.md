# Role Signals

Status: active doctrine — independently maintained in Pantheon Next.

Historical provenance is preserved in git history; this file has no external source dependency.

This document defines structured signals between Pantheon Roles.

A Role Signal is a governance artifact.

It is not an agent message.

It is not a runtime event.

It is not a scheduler item, queue message, bus message, tool call, hidden debate or automatic approval.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed signal, approval and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Core doctrine

Pantheon Roles may request review, transmit bounded findings, flag risk, request clarification or escalate a conflict.

They do this through structured Role Signals.

Role Signals preserve responsibility separation.

They must not create autonomous role chatter.

Canonical rule:

```text
A Role Signal may transmit a claim, uncertainty, risk, limitation or request.
A Role Signal must not increase certainty without new evidence.
A Role Signal must not execute, approve, promote memory or mutate doctrine.
```

## Canonical roles

The canonical role registry is `AGENTS.md`.

This document uses only the current Pantheon Next canonical roles:

- ATHENA;
- ARGOS;
- THEMIS;
- APOLLO;
- ZEUS;
- IRIS;
- HEPHAISTOS;
- MNEMOSYNE.

Retired historical role names not present in `AGENTS.md` are not canonical roles in this document.

Any future additional role name requires a separate governed update to `AGENTS.md`, the shared schema vocabulary and related consumers.

## Purpose

Role Signals support:

- bounded role consultation;
- source handoff;
- memory-continuity and version-review requests;
- risk warning;
- veto candidate;
- delivery stop gate;
- clarification request;
- Task Contract revision signal;
- Evidence Pack traceability;
- User Decision Gate preparation;
- candidate memory or skill gap identification.

Role Signals do not implement:

- runtime message bus;
- scheduler;
- queue;
- autonomous agent loop;
- tool execution;
- approval bypass;
- memory promotion;
- workflow execution;
- truth oracle;
- raw chain-of-thought exposure.

## Responsibility split

| Responsibility | Role or surface |
|---|---|
| Structure the method or route | ATHENA |
| Transfer source findings and evidence gaps | ARGOS |
| Escalate risk, approval boundary or veto candidate | THEMIS |
| Check completeness, coherence and final readiness | APOLLO |
| Arbitrate procedure, status and next safe action | ZEUS |
| Format the signal and user-facing wording | IRIS |
| Prepare implementation or patch candidate signals | HEPHAISTOS |
| Frame memory-oriented retrieval, continuity, supersession and retention review | MNEMOSYNE |
| Execute operational work under Task Contract | Hermes Agent |
| Expose runtime interaction when selected | Optional runtime client |
| Project governed signals, approvals and decisions | Pantheon Cockpit |
| Govern signal schema, status and limits | Pantheon Next |

Canonical split:

```text
ATHENA structures.
ARGOS qualifies sources and evidence gaps.
THEMIS blocks risk.
APOLLO checks readiness.
ZEUS arbitrates procedure.
IRIS formats and transmits.
HEPHAISTOS prepares candidates.
MNEMOSYNE governs continuity, memory-oriented retrieval framing and placement proposals.
Hermes executes externally under Task Contract.
Optional runtime clients expose interaction only.
Pantheon Cockpit projects governed signal, approval and decision state.
Pantheon governs.
```

MNEMOSYNE does not replace ARGOS for source authority. A memory may be the newest remembered state and still have weak or missing evidentiary support. ARGOS qualifies what the source supports; MNEMOSYNE qualifies which historical state is being reused and where it belongs.

## IRIS mediation

IRIS may format a Role Signal for clarity and audience fit.

IRIS may:

- choose a clearer signal type;
- reduce ambiguity;
- remove irrelevant detail;
- preserve limitations;
- preserve risk flags;
- preserve claim status;
- prepare user-facing wording after validation.

IRIS must not:

- change ARGOS factual findings;
- hide a MNEMOSYNE stale-memory or supersession warning;
- increase claim certainty;
- lower THEMIS risk;
- weaken APOLLO stop gates;
- hide unsupported-claim flags;
- choose ZEUS arbitration result;
- execute Hermes tools;
- send external messages;
- promote memory;
- activate skills.

Canonical rule:

```text
IRIS formats the signal.
The sender owns the substance.
The addressed role owns the response.
THEMIS owns risk posture.
APOLLO owns readiness review.
MNEMOSYNE owns memory-continuity review.
ZEUS owns procedural arbitration.
```

## Signal types

Allowed signal types:

```text
role_need_statement
information_transmission
clarification_request
role_consultation
risk_warning
veto_signal
brief_adherence_signal
task_contract_revision_signal
handoff_signal
stop_gate_signal
memory_candidate_signal
skill_gap_signal
asset_need_signal
source_gap_signal
evidence_gap_signal
user_decision_gate_signal
```

Existing signal types are sufficient for MNEMOSYNE. Canonizing the role does not create a second memory protocol.

Forbidden signal types:

```text
execute_tool
approve_external_action
promote_memory
activate_skill
canonize_workflow
send_external_message
mutate_file
access_secret
increase_claim_certainty_without_evidence
raw_chain_of_thought
hidden_agent_debate
```

## Base envelope

Use this envelope when structured Role Signal output is needed.

```yaml
role_signal:
  id: RS-YYYY-NNNN
  from_role: ARGOS
  to_role: THEMIS
  signal_type: risk_warning
  purpose: "Ask whether a candidate output raises approval risk."
  content_summary: "A contractor quote may be reused in client-facing wording."
  payload_ref: evidence_pack.source_inventory.v1
  certainty: E2
  claim_status: source_supported
  uncertainty_level: medium
  uncertainty_reasons:
    - mission_scope_missing
  assumptions: []
  limitations:
    - "The signed mission scope is not available."
  risk_level: C2
  evidence_refs:
    - EP-YYYY-NNNN.source_inventory
  requested_action: review
  approval_impact: possible_C4
  memory_impact: none
  external_effect: false
  status: open
```

Rules:

```text
content_summary must be short.
payload_ref must point to bounded material, not private reasoning.
limitations must be explicit below certainty E3.
risk_level must not be lowered by the sender.
claim_status must not improve without new evidence.
A signal carrying conflicting or unsupported material must request review, arbitration, source check or block.
```

## Addressing guidance

A Role Signal should be shaped for the addressed role.

| Addressed role | Emphasize | Avoid |
|---|---|---|
| ATHENA | method, structure, dependencies, route proposal | raw unstructured findings |
| ARGOS | source need, factual question, extraction target, provenance | opinion-heavy wording or memory status presented as source authority |
| THEMIS | risk, approval level, forbidden action, liability exposure | softened warnings |
| APOLLO | completeness, coherence, unsupported claims, readiness | finalization without limitations |
| ZEUS | decision needed, options, conflict, procedure | excessive detail without decision point |
| IRIS | audience, tone, wording, transmission constraints | unresolved risk without THEMIS signal |
| HEPHAISTOS | method robustness, patch scope, implementation gap, rollback | vague improvement request |
| MNEMOSYNE | memory scope, prior state, date/index/version, duplicate or supersession status, retention destination | treating recall as proof or requesting automatic promotion |

## Bounded consultation

A role may consult another role without a full workflow when the task is simple and low-risk.

Allowed:

- bounded question;
- bounded answer;
- one clarification round by default;
- visible summary if consequential;
- Evidence Pack reference when needed.

Forbidden:

- open-ended debate;
- hidden multi-agent forum;
- raw chain-of-thought;
- tool execution;
- file mutation;
- approval bypass;
- memory promotion;
- skill activation;
- workflow canonization;
- claim certainty upgrade without evidence.

Escalate to a Task Contract revision or User Decision Gate when:

- more than two or three role viewpoints become necessary;
- sources must be compared;
- risk rises to C3/C4/C5;
- external-facing output is involved;
- evidence is insufficient;
- memory or files may be impacted;
- Hermes must execute tools;
- role disagreement cannot be resolved procedurally.

## Information transmission

Use `information_transmission` when one role has produced bounded material needed by another role.

Example:

```yaml
role_signal:
  from_role: ARGOS
  to_role: APOLLO
  signal_type: information_transmission
  content_summary: "Three cited sources support the candidate chronology; one date remains unsupported."
  payload_ref: evidence_pack.source_chronology.v1
  certainty: E2
  claim_status: mixed
  uncertainty_level: medium
  limitations:
    - "The final date is inferred and not directly sourced."
  requested_action: readiness_review
```

Information transmission does not mean the receiving role must accept the information as true.

The receiving role may answer:

```text
accepted_for_review
needs_more_source
blocked_by_limitation
risk_escalation
claim_status_lowered
ready_with_limits
```

## Memory continuity and version review

MNEMOSYNE may use `role_consultation`, `information_transmission` or `memory_candidate_signal` to make memory-oriented review explicit.

Example:

```yaml
role_signal:
  from_role: MNEMOSYNE
  to_role: ARGOS
  signal_type: role_consultation
  purpose: "Check whether the newest remembered project state is supported by the applicable source."
  content_summary: "CR index 14 appears newer than the recalled index 12 and may supersede the remembered ventilation status."
  certainty: E2
  claim_status: sourced_not_verified
  uncertainty_level: medium
  limitations:
    - "The source authority of index 14 still needs review."
  requested_action: check_version
  memory_impact: memory_review_required
  external_effect: false
  status: open
```

Rules:

```text
newer remembered record does not mean stronger evidence.
retrieval order does not decide chronology.
MNEMOSYNE may propose a retention destination but not persist or promote it.
ARGOS remains responsible for source and evidence qualification.
ZEUS arbitrates material status transitions or unresolved promotion procedure.
```

## Risk warning and veto signal

THEMIS may emit a risk warning or veto signal.

Example:

```yaml
role_signal:
  from_role: THEMIS
  to_role: ZEUS
  signal_type: veto_signal
  purpose: "Block external-facing wording before approval."
  content_summary: "The draft may create a contractual commitment without C4 approval."
  claim_status: inferred_from_sources
  uncertainty_level: medium
  risk_level: C4
  requested_action: block
  approval_impact: C4_required
  next_safe_action: "Keep as internal draft or ask user for explicit validation."
```

Rules:

```text
A THEMIS veto signal cannot be overridden by role majority.
ZEUS may reroute but cannot bypass the veto.
APOLLO cannot finalize against a THEMIS veto.
IRIS cannot soften or hide the veto.
```

## Stop gate signal

APOLLO may emit a stop gate signal when finalization would overstate weak evidence, hide limitations or produce a misleading deliverable.

Allowed APOLLO decisions:

```text
ready
ready_with_limits
needs_revision
needs_user_input
blocked
```

Example:

```yaml
role_signal:
  from_role: APOLLO
  to_role: ZEUS
  signal_type: stop_gate_signal
  purpose: "Decide whether the answer can be finalized."
  content_summary: "The output is coherent but must expose missing source limitations."
  decision: ready_with_limits
  unresolved_items:
    - missing_quantity_schedule
  requested_action: finalize_with_limits
```

APOLLO must block or require visible limitations when final wording would overstate weak claims.

## Task Contract revision signal

Use `task_contract_revision_signal` when the current Task Contract no longer fits.

Typical triggers:

- scope changed;
- approval level increased;
- external effect appeared;
- memory impact appeared;
- missing source blocks finalization;
- tool execution is now needed;
- requested output changed from draft to action;
- contradiction exceeds current procedure.

Signals do not apply the change by themselves.

ZEUS arbitrates procedure.

THEMIS checks risk.

ATHENA restructures the method if a revised frame is approved.

MNEMOSYNE reviews memory scope or retention implications when the revision changes what prior context may be reused or retained.

Reference: `TASK_CONTRACT_REVISIONS.md`.

## Handoff signal

Use `handoff_signal` when the active role viewpoint changes.

Example:

```yaml
handoff_signal:
  from_role: ATHENA
  to_role: ARGOS
  task_context: "Source inventory before report drafting."
  required_inputs:
    - uploaded_files
    - selected_knowledge_sources
  expected_output:
    - source_inventory
    - missing_sources
    - usable_facts
  blockers:
    - no_files_available
```

Handoff is not delegation of authority.

The receiving role performs only its defined responsibility.

If the receiving role improves claim status, it must attach new evidence.

## Evidence Pack relationship

Consequential Role Signals should be referenced in the Evidence Pack.

An Evidence Pack may record:

- role signals;
- role consultations;
- handoffs;
- risk warnings;
- vetoes;
- stop gate decisions;
- Task Contract revision signals;
- source gaps;
- evidence gaps;
- memory-continuity, stale-recall or supersession findings;
- User Decision Gate signals.

Signal content is not proof by itself.

The signal must point to evidence when it supports a factual or consequential claim.

## Persistence

Role Signals are session artifacts by default.

They become persistent only if included in:

- an Evidence Pack;
- a Task Contract revision;
- a workflow candidate;
- a Register Candidate;
- a PR or governance document.

Persistence does not imply canonization.

Canonization follows the relevant approval and memory policy.

## Runtime-client and Cockpit boundary

Optional runtime clients may expose public summaries of Role Signals and technical interaction state. Hermes WebUI is one optional/proposed client if separately selected and qualified.

Pantheon Cockpit may project governed Role Signal summaries, approval state and linked decisions.

Allowed public summaries:

```text
ARGOS: usable sources identified; one source gap remains.
MNEMOSYNE: newer project record found; prior memory may be superseded and needs source review.
```

Forbidden public summary:

```text
raw internal reasoning, hidden prompt, private file path, secret, raw source dump
```

Neither client display nor Cockpit projection becomes signal authority, runtime governance, memory or approval.

```text
Hermes WebUI available != Hermes WebUI selected
client selected != authority transfer
projection != persistence
```

## Hermes boundary

Hermes may transport or execute work related to a Role Signal only under Task Contract.

Hermes may return:

- Result Candidates;
- Evidence Packs;
- Patch Candidates;
- Register Candidates;
- Capability Gaps;
- Risk Escalations.

Hermes must not:

- create hidden role debates;
- revise Task Contracts silently;
- approve external action;
- promote memory;
- canonize workflow;
- activate skills;
- mutate doctrine;
- treat a Role Signal as tool authorization.

A MNEMOSYNE Role Signal may tell Hermes or another admitted executor what memory scope or retrieval question is required. The signal does not itself perform the search or authorize a broader one.

## Final rule

```text
Roles may consult other roles.
They communicate through structured signals.
Signals are bounded, traceable and non-executing.
Signals may preserve claim or memory-review state but do not prove claims by themselves.
MNEMOSYNE governs continuity and memory-placement judgment.
ZEUS arbitrates procedure.
THEMIS blocks risk.
APOLLO validates readiness.
IRIS formats without changing substance.
Hermes executes externally under Task Contract.
Optional runtime clients expose interaction only.
Pantheon Cockpit projects governed signal, approval and decision state.
Pantheon governs.
```

## Signal profiles (absorbed from ROLE_SIGNAL_PROFILES.md)

The former stub declared this intended scope; it is owned here now, still documented and not implemented until each item is reviewed:

- profile-level binding between Pantheon Role signals and Hermes execution profiles;
- per-profile signal emission rules;
- per-profile signal reception rules;
- escalation signal mapping;
- capability gap signal mapping;
- approval request signal mapping;
- review request signal mapping;
- separation between governance signal doctrine and runtime signal transport.

These items remain candidates. None of them is implemented by this section.
