# Run Trace View

Status: active doctrine — conceptual stabilization.

This file keeps the historical name `RUN_GRAPH.md` for repository compatibility.

The canonical concept is `Run Trace View`.

A Run Trace View is a human-readable representation of governed activity.

It is not a runtime graph.

It is not a graph executor.

It is not workflow state.

It is not an observability backend.

It is not a mechanism to resume execution.

```text
Optional Hermes WebUI or other compatible clients may expose runtime interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed trace/review state.
Pantheon Next governs.
```

## Purpose

A Run Trace View helps a human reviewer understand what happened around a governed task.

It may summarize:

- the user request;
- linked Task Contract;
- linked Evidence Pack;
- role viewpoints;
- source references;
- outputs;
- review notes;
- approval state;
- risks and limitations;
- Register Candidates.

It exists for visibility, review and audit.

It does not make Pantheon Next run anything.

## Naming and compatibility

The term `Run Graph` is legacy vocabulary.

It may appear in historical references, but it must not be interpreted as an executable graph.

Pantheon Next should prefer:

```text
Run Trace View
Trace Summary
Review Timeline
Evidence Timeline
```

The file name may remain until repository references are reconciled.

## Core principle

Trace is not state.

A trace helps humans review a task.

A state allows a runtime to continue a task.

Pantheon Next may govern traces.

Pantheon Next must not own runtime state.

## Allowed content

A Run Trace View may contain:

```text
Request summary
Task Contract reference
Evidence Pack reference
Major review milestones
Role viewpoint summaries
Source references
Assumption summaries
Risk summaries
Output references
Approval references
Register Candidate references
Redaction notes
Limitations
```

These are review artifacts.

They are not runtime control artifacts.

## Forbidden content

A Run Trace View must not contain:

```text
hidden chain-of-thought
raw scratchpad
secret values
credentials
private provider traces
worker state
queue state
scheduler state
provider routing state
retry internals
runtime graph state
agent handoff internals
```

Sensitive information must be redacted or excluded.

## Graph language

Nodes and edges may be used visually.

They are display conventions only.

A node is not executable.

An edge is not a dispatch rule.

A path is not a scheduler plan.

A graph is not a source of truth.

The source of truth remains the relevant governance artifacts:

- Task Contract;
- Evidence Pack;
- Approval record;
- Memory governance record when applicable.

## Relationship to Evidence Packs

A Run Trace View may summarize an Evidence Pack.

It must not replace the Evidence Pack.

It must not add unsupported claims.

It must not hide evidence gaps.

If the Evidence Pack is incomplete, the trace view must show the limitation.

## Relationship to Task Contracts

A Run Trace View may show how an activity related to a Task Contract.

It must not expand the Task Contract scope.

It must not authorize activity that the Task Contract did not authorize.

## Relationship to Approvals

A Run Trace View may display approval state.

It must not grant approval.

It must not trigger execution from approval state.

It must not turn a visual timeline into a governance decision.

## Relationship to Memory

A Run Trace View may show Register Candidates.

It must not promote memory.

It must not treat repeated trace visibility as a Registre Probatoire entry.

## Relationship to Hermes Agent

Hermes Agent may produce runtime traces or summaries externally.

Pantheon Next may receive a governed summary.

Pantheon Next does not store Hermes internal runtime state.

Pantheon Next does not replay Hermes execution.

Pantheon Next does not resume Hermes tasks from a trace view.

## Relationship to runtime clients and Cockpit

`nesquena/hermes-webui`, if selected, or another compatible client may expose runtime interaction and technical run information. Hermes WebUI is an optional/proposed external surface, not a required Pantheon component.

Pantheon Cockpit may project a governed Run Trace View, review status and linked decision state.

Client or Cockpit display does not canonize a trace, make it complete, grant approval, resume execution or transfer authority.

```text
runtime display != governed trace
trace projected != trace persisted
projection != approval
projection != authority
optional client selected != authority transfer
```

## Relationship to schemas

A future schema may validate the structure of a Run Trace View.

It may validate:

- identifiers;
- linked artifacts;
- visible milestones;
- redaction status;
- source references;
- risk notes;
- approval references.

It must not validate runtime graph behavior.

It must not define execution order, worker state, queue state, scheduler state, provider routing or retry behavior.

## Final rule

A Run Trace View exists to make work understandable.

Not to make work run.
