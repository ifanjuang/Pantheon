# Pantheon Control — Intent Log

Status: candidate — to verify.
Boundary profile: candidate_support_note.

Date: 2026-06-21

Related issue:

```text
https://github.com/ifanjuang/Pantheon-Next/issues/192
```

## Purpose

The Intent Log is a cockpit-surface candidate for displaying Intent Candidates before they become tasks.

It exists because a runtime, module, skill or workflow may detect a next step, a missing capability, a workflow branch or a useful follow-up. That proposal must remain visible and bounded. It must not silently become a scoped task, a memory promotion, a truth claim, an approval or an external action.

## Status

Accepted:

```text
Expose Intent Candidates in a future governed cockpit surface.
Show admissibility status, affected truth/memory/external/canonical flags, evidence requirement and approval requirement.
Let a human inspect, reject, revise or route the candidate to a Task Contract later.
```

Refused:

```text
No runtime loop.
No self-authorized task.
No automatic approval.
No automatic memory promotion.
No external action.
No schema promotion.
No operations, platform, Docker or dependency changes.
```

To verify:

```text
whether the display remains readable once fed by real Hermes workflows;
whether the statuses align cleanly with governed_execution_handoff preflight outcomes;
whether the object belongs in the external MVP cockpit or a later OpenWebUI exposure surface.
```

To arbitrate:

```text
whether Intent Candidate later deserves a formal schema under schemas/;
whether the cockpit should support decision capture buttons;
whether rejected candidates should be retained, archived or periodically summarized.
```

## Display boundary

The cockpit may show:

```text
intent id;
origin runtime;
origin module;
observed context;
proposed intention;
proposed task;
target scope;
affected truth claims;
affected memory;
possible external effect;
possible canonical effect;
evidence required;
approval required;
admissibility status;
decision owner;
created / resolved dates;
trace refs.
```

The cockpit must not:

```text
execute the proposed task;
turn the candidate into a Task Contract by itself;
promote memory;
validate truth;
grant approval;
send, publish, file, notify or mutate an external system;
write a Registre Probatoire entry;
create a schema or runtime event without separate review.
```

## Candidate status vocabulary

Initial display statuses:

```text
candidate      — visible proposal, not yet reviewed;
to_verify      — plausible, needs evidence or compatibility check;
needs_approval — cannot proceed without a Decision Gate or approval path;
rejected       — refused and retained for traceability if useful;
blocked        — forbidden, out of scope or protected-path change without approval.
```

## Historical prototype status

The former local Pantheon Control Intent Log page and its synthetic fixture scripts were removed with the retired local dashboard.

They remain available through Git history and intervention logs, but they are no longer an active asset, an implementation claim or a fallback surface.

A future implementation belongs in the external executable cockpit or OpenWebUI exposure layer and requires its own reviewed binding. Pantheon Next retains this candidate object model and its governance boundary only.

## Future admission criteria

Before connecting an Intent Log surface to real Hermes or cockpit state, require:

```text
1. a Task Contract or workflow source that produces Intent Candidates explicitly;
2. provenance and trace refs for every candidate;
3. a visible boundary between candidate, to verify, needs approval, rejected and blocked;
4. no automatic conversion to Task Contract;
5. no automatic memory write;
6. no external effect without User Decision Gate;
7. explicit retention / deletion behavior for rejected or expired intents.
```

## Repository state

Documented non-implemented / to verify.

No current Pantheon Next page, runtime, schema, connector, database view, queue, scheduler, workflow engine, memory engine or approval engine implements this model.
