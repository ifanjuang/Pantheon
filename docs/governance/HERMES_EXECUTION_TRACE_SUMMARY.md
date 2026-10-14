# Hermes Execution Trace Summary

Status: implementation artifact — implemented subordinate technical contract; optional during migration.

Issue: Pantheon-Next#563.

The contract is attached to the existing Hermes Runtime Return. It does not create a new execution object, graph authority, runtime, scheduler, queue, persistence owner, Evidence object, Decision, Knowledge object or Work Issue state owner.

```text
Launch Context Snapshot
→ Hermes executes externally
→ Runtime Return
  └─ optional execution_trace_summary
      └─ existing Cockpit Work Activity read projection
```

## Purpose

The summary answers one narrow technical question:

> What execution facts were observed or reported between the immutable launch snapshot and the candidate return?

It does not decide whether the result is true, professionally valid, approved, admissible as Evidence or sufficient to resolve the Work Issue.

```text
execution_trace_summary != Evidence
execution_trace_summary != Decision
execution_trace_summary != Knowledge
runtime success != Work Issue resolution
trace complete != result true
tool success != professional validation
runtime_reported != independently_observed
```

## Existing owners

The summary remains subordinate to existing authorities only:

- `HERMES_EXECUTION_ADMISSION_BRIDGE.md` owns execution admission and return doctrine;
- `HERMES_RUN_LAUNCH_JUNCTION.md` owns reservation and run correlation;
- `schemas/work_issue_slice.schema.yaml` owns the persisted Work Issue/HermesRun slice;
- `implementation/mvp_vertical/hermes_execution_trace.py` validates the optional technical receipt against the persisted run;
- the existing Runtime Return path persists the receipt inside `normalized_return`;
- the external Hermes binding builds the receipt from observed or runtime-reported facts;
- `implementation/mvp_vertical/work_activity_projection.py` exposes the already admitted receipt as read-only Cockpit data;
- the existing Work Card renderer presents that data as technical detail only.

No intermediate execution-plan owner is required. Cockpit projection is not persistence, scheduling, execution or authorization.

## Minimal first slice

The bounded contract can contain only:

```text
correlation
runtime identity
terminal execution counters
tool usage summary
observed limits
structured refusals
trace references
provenance groups
```

It excludes prompts, hidden reasoning, full tool payloads, arbitrary logs, source binaries, conversation history, a universal DAG, replay state, checkpoint state and provider/model routing decisions.

Missing information is omitted rather than invented. A missing counter differs from zero.

## Shape

```yaml
execution_trace_summary:
  schema_version: hermes-execution-trace-summary-v1
  correlation:
    admission_id: admission-...
    launch_reservation_id: launch-reservation-...
    snapshot_id: launch-snapshot-...
    snapshot_digest: sha256:...
    run_id: run-...
  runtime:
    implementation: hermes-agent
    version: observed-version
    profile: qualified-profile
  execution:
    started_at: 2026-08-25T18:00:00Z
    ended_at: 2026-08-25T18:00:05Z
    terminal_status: completed
    step_count: 3
    tool_call_count: 2
    retry_count: 0
    repair_count: 0
  tools:
    - tool_id: pantheon_context_manifest
      call_count: 1
      terminal_status: completed
  limits:
    max_steps: 12
    observed_steps: 3
    timeout_seconds: 180
    timed_out: false
  refusals:
    - code: context_entity_not_admitted
      count: 1
  trace_refs:
    - hermes://runs/run-...
  provenance:
    pantheon_observed:
      - correlation.admission_id
      - correlation.launch_reservation_id
      - correlation.snapshot_id
      - correlation.snapshot_digest
      - correlation.run_id
    binding_observed:
      - execution.started_at
      - execution.ended_at
      - execution.retry_count
    runtime_reported:
      - execution.step_count
      - execution.tool_call_count
      - tools
```

The example values are illustrative. Active runtime qualification names are registry-driven; this contract does not pin a current Hermes version or profile. Historical qualification fixtures remain historical evidence of those runs and do not define active naming.

## Correlation rules

`pantheon-mvp` verifies authoritative identities against persisted launch state:

```text
body admission_id == route admission_id
body run_id == route run_id
launch_reservation_id belongs to admission_id
snapshot_id belongs to launch_reservation_id
snapshot_digest equals persisted digest
run_id belongs to the consumed admission
```

A foreign or mismatched identity is refused atomically. The binding locks these values from launch receipts and bridge responses; the model must not generate or rewrite them.

## Runtime identity

The optional runtime block records technical identity only when it is available from a qualified observation path. It does not select, approve or adopt that runtime.

```text
runtime observed != runtime approved
profile qualified != task authorized
implementation available != dependency adopted
```

No current Runtime Lab version literal is part of this contract.

## Counters, tools and limits

Counters are non-negative and bounded. Tool usage is a summary, not a complete trace. Full arguments and outputs remain external.

A tool identifier outside the surface qualified before reservation must be refused or recorded as an explicit trace inconsistency by the authoritative executable path.

```text
tool called != effect authorized
tool completed != result valid
tool available != capability adopted
```

Token or cost fields still require a demonstrated stable source and unit before addition.

## Refusals

Refusals are bounded technical denials, not Evidence or automatic proof of malicious intent. The first admitted code is:

```text
context_entity_not_admitted
```

Any new refusal code requires a corresponding executable path and test.

## Trace references

`trace_refs` points to detailed external traces without embedding them.

```text
trace ref != trace content
trace content != Evidence
trace availability != result truth
```

The optional summary does not replace the existing normalized-return `trace_refs`.

## Provenance

Provenance is mandatory whenever the summary is present. Included field paths are grouped by source:

```text
pantheon_observed
binding_observed
runtime_reported
```

A path must not appear in more than one group in the first slice.

- `pantheon_observed`: verified from authoritative Pantheon state or bridge events;
- `binding_observed`: directly observed by the external binding;
- `runtime_reported`: supplied by Hermes about its internal execution.

No field becomes `pantheon_observed` merely because it arrived through a Pantheon endpoint.

## Partial summaries

The summary remains optional and may be partial. Exact correlation and provenance remain required whenever a summary is present.

```text
summary absent != run invalid
summary partial != run failed
summary complete != result accepted
```

The existing binding currently emits only facts it can justify. Phase E demonstrated that `retry_count: 0` is emitted only when the launch receipt explicitly observes that no automatic retry occurred; missing observation remains missing data.

## Bounds

The executable validator defines explicit ceilings, including:

```text
tools: 100
refusals: 100
trace_refs: 100
provenance paths per group: 200
serialized summary: 64 KiB
bounded identifiers and counters
```

The executable validator remains authoritative for exact bounds.

## Persistence

The summary is persisted through the existing Hermes Runtime Return/HermesRun `normalized_return` payload. There is no separate trace table or aggregate.

```text
new field != new aggregate
projection != persistence
```

## Cockpit projection

The Cockpit reuses the existing `Work Issue → Work Activity → Work Card` read path. It does not fetch a second trace source and does not reconstruct missing runtime facts in the browser.

When `execution_trace_summary` is present, the Work Card detail can show bounded technical information such as terminal status, counters, runtime identity, exact correlation, tool/refusal summaries, technical limits and provenance counts. The Work Card status continues to come from the governed Work Issue projection.

```text
runtime completed != Work Issue done
runtime success != Evidence admitted
runtime success != Decision created
runtime success != Knowledge created
technical detail visible != authorization
```

An absent summary remains a valid migration state and produces no invented technical detail.

## Implementation sequence

The original staged plan has converged onto existing owners:

1. contract/doctrine introduced under Pantheon-Next#563;
2. Runtime Return validation and persistence merged in Pantheon-Next#723;
3. existing one-shot binding production merged in Pantheon-Next#724;
4. governed synthetic Phase E acceptance merged in Pantheon-Next#733 at `d04c7785`;
5. Phase F reuses the existing Cockpit Work Activity read projection and Work Card detail renderer, without a new owner.

No retry scheduler, replay/checkpoint engine, trace aggregate, Langfuse/OTel requirement or automatic governance promotion is introduced by this sequence.

## Required invariants and tests

```text
foreign admission_id -> refused
foreign run_id -> refused
foreign launch reservation -> refused
foreign snapshot id or digest -> refused
negative counter -> refused
oversized collection -> refused
unqualified tool id -> refused or explicit inconsistency
false Pantheon-observed provenance -> refused
valid partial summary -> accepted
summary absent during migration -> accepted
valid summary -> persisted by existing Runtime Return path
runtime success -> no Work Issue closure
runtime success -> no Evidence, Decision or Knowledge creation
Cockpit projection -> read-only technical detail
```

## Final rule

```text
Pantheon qualifies the technical receipt.
Pantheon does not become the runtime.
Hermes reports or exposes execution facts.
The binding distinguishes observation from report.
The Cockpit projects those facts without promoting them.
The human decides consequential meaning.
```
