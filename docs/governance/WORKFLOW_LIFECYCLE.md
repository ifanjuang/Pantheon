# Workflow Lifecycle

Status: candidate governance support doctrine  
Scope: workflow proposal, testing, activation, deactivation and durable operation  
Runtime status: non-executable

## Purpose

This document defines how Pantheon Next should treat workflows before they are allowed to affect professional records or external communications.

It does not implement a workflow engine. It defines a governance lifecycle for future engines, Directus flows, Hermes jobs, OpenWebUI actions, scripts, queues or other automation systems.

## Core rule

```text
A workflow is never automatic by birth.
It becomes durable by proof.
```

A workflow must be describable, testable, observable, reversible where possible, and immediately disableable.

## Why this lifecycle exists

Professional workflows can affect:

- project records;
- client or contractor communications;
- financial follow-up;
- construction reports;
- contract interpretation;
- administrative forms;
- contact registers;
- document storage;
- memory and knowledge reuse.

A generated answer is not enough. A workflow must expose what it intends to do before it does it.

## Workflow modes

Pantheon-compatible workflows should support progressive authority modes.

```text
off
  The workflow exists but does nothing.

draft
  The workflow is being described. It has no operational authority.

test
  The workflow runs only on selected examples or manually supplied inputs.
  It may explain what it would do.
  It may not modify live records.

shadow
  The workflow observes real events and produces would-have-done traces.
  It may not modify live records.
  It may not move files.
  It may not send messages.

assisted
  The workflow creates action proposals and drafts.
  The user validates before any material write or external action.

active_guarded
  The workflow may execute low-risk internal writes under an approval policy.
  Higher-risk writes remain proposals.
  External commitments remain blocked.

active_durable
  The workflow is stable, monitored, versioned and disableable.
  It may execute only the actions explicitly authorized by its policy.
```

## Authority levels

Actions should be assigned a risk and authority level.

```text
0 read_only
  read documents, messages, records or sources.

1 propose_only
  classify, summarize, detect, compare or recommend without writing.

2 internal_draft_write
  create draft records or candidate records.

3 internal_controlled_write
  update internal records according to an explicit policy.

4 storage_write
  move, copy, rename or archive files in controlled storage.

5 external_draft
  prepare an outbound email, report, form or transmission package.

6 external_action
  send, submit, approve, reject, sign, transmit or otherwise bind the professional externally.
```

Default rule:

```text
Level 6 actions are not automatic by default.
```

Even durable workflows should normally keep human approval for professional commitments.

## Proposal before execution

The system must separate proposed actions from executed actions.

Candidate register:

```text
workflow_action_proposals
- workflow_run_id
- action_type
- target_type
- target_id
- proposed_payload
- human_summary
- risk_level
- authority_level
- status
```

Candidate execution log:

```text
workflow_action_executions
- proposal_id
- executed_by
- executed_at
- result_status
- result_payload
- rollback_payload
```

A workflow that cannot describe its proposed action should not be allowed to execute that action.

## Workflow definition

A workflow definition should include:

```text
name
purpose
trigger
inputs
outputs
required modules
required sources
authorized actions
authority limits
approval policy
failure behavior
rollback expectation
logging expectation
owner
status
```

A workflow version should include:

```text
version number
definition payload
human-readable description
risk assessment
change summary
test cases
activation mode
```

## Suggested tables

```text
workflow_definitions
workflow_versions
workflow_runs
workflow_steps
workflow_test_cases
workflow_action_proposals
workflow_action_executions
approval_policies
audit_events
rollback_records
```

These are candidate table families, not mandatory implementation names.

## User-created workflows

A user should be able to suggest a workflow in ordinary language.

The system should then create a workflow build request:

```text
workflow_build_requests
- user_request
- reformulated_goal
- detected_domain
- required_modules
- required_data
- proposed_steps
- identified_risks
- proposed_mode
- status
```

The first output is not an automation. It is a reviewable workflow proposal.

Example:

```text
When a contractor sends a quote by email, detect the project, classify the quote, save the file, extract the amount, compare it to the CCTP if available, and prepare comments.
```

Governed reformulation:

```text
Observe incoming email attachments.
Detect likely quote documents.
Propose project and contractor attribution.
Extract candidate quote metadata.
Compare against available CCTP articles if the project scope authorizes it.
Create action proposals only.
Do not write final records, move final files or send email until approved.
```

## Shadow mode trace

In shadow mode, a workflow should produce a trace like:

```text
I would have classified this email as a contractor quote.
I would have attributed it to project X with confidence 0.91.
I would have proposed contractor Y and lot Z.
I would have saved the file under the following path.
I would have created a candidate quote record.
I would have opened 4 CCTP coverage questions.
No live record was changed.
No file was moved to final storage.
No email was sent.
```

This mode is essential for trust calibration.

## Assisted mode trace

In assisted mode, the workflow may create proposals:

```text
create candidate document
create candidate quote
rename file
move file to project folder
create contact proposal
create CCTP gap comment
prepare outbound email draft
```

Each proposal carries a status and waits for review.

## Durable mode conditions

A workflow may be considered for durable activation only after:

- its purpose is stable;
- its trigger is bounded;
- its target objects are known;
- test cases cover expected and edge cases;
- shadow traces have been reviewed;
- failure behavior is defined;
- rollback is defined where applicable;
- external action boundaries are explicit;
- owner and deactivation procedure are known.

## Deactivation

Every workflow must be disableable without deleting its trace.

Deactivation should preserve:

- definitions;
- versions;
- runs;
- action proposals;
- executions;
- audit events;
- approvals and rejections.

The system must support disabling a workflow that behaves correctly technically but no longer fits the professional method.

## Schema evolution

Some workflows require new fields or tables. They must not mutate the schema directly.

They should create schema change proposals:

```text
schema_change_proposals
- module_id
- reason
- affected_objects
- proposed_change
- migration_candidate
- risk_level
- status
```

Schema changes must pass review before application.

## Examples

### Incoming quote workflow

Initial mode: shadow or test.

Allowed early behavior:

- detect probable quote;
- propose project attribution;
- propose contractor and lot;
- extract candidate amount;
- compare with CCTP if available;
- create comments as candidate analysis.

Blocked early behavior:

- final accounting entry;
- final archive move;
- contractor notification;
- quote approval;
- client transmission.

### Site meeting report workflow

Initial mode: test.

Allowed early behavior:

- turn notes into points;
- carry open points from previous reports;
- propose status updates;
- generate next-meeting preparation;
- draft a report.

Blocked early behavior:

- publishing the report;
- emailing participants;
- closing points without validation;
- changing contractual decisions.

### Finance follow-up workflow

Initial mode: shadow.

Allowed early behavior:

- detect invoice;
- match contractor;
- match contract or change order;
- detect amount mismatch;
- propose finance alerts.

Blocked early behavior:

- approving payment;
- rejecting invoice externally;
- applying penalties;
- notifying client or contractor.

## Operating principle

```text
The system should first learn how the user works.
Then it should explain what it would do.
Then it may propose actions.
Only after evidence of stability may selected actions become durable.
```

## Workflow adaptation (absorbed from WORKFLOW_ADAPTATION.md)

The former stub declared this intended scope; it is owned here now, still documented and not implemented until each item is reviewed:

- adaptive workflow doctrine;
- controlled workflow evolution;
- workflow revision policy;
- safe degradation behavior;
- capability-aware workflow adaptation;
- escalation conditions;
- runtime drift prevention.

These items remain candidates. None of them is implemented by this section.
