# Module Invocation Preflight

Status: candidate — to verify. This document captures a proposed doctrine for invoking governance roles, rites, places and external connections before a module is used.
Boundary profile: candidate_support_note.

This document is documentation only. It does not implement a UI, API gateway, MCP server, connector runtime, scheduler, queue, plugin manager, role executor, rite executor or automatic approval system.

## Purpose

Pantheon-facing modules should not be treated as usable merely because they are installed or reachable.

Before a module participates in governed work, the system should be able to ask simple preflight questions:

```text
Who is being invoked?
Which rite is appropriate?
Which place or scope contains the work?
Which connection is required?
What may the module read, write, propose or trigger?
What must it refuse?
```

This document captures that idea as an invocation preflight model.

## Core distinction

```text
Calling is not executing.
Invoking is not authorizing.
Connectivity is not legitimacy.
A reachable API is not a permitted action.
```

The invocation preflight determines whether a capability may be considered for a task. It does not run the task.

## Vocabulary

### Gods

A god is a governance role or authority lens. Calling a god means requesting that a role perspective be applied to a candidate decision.

Examples:

```text
ZEUS       arbitrate status, legitimacy and procedure
ATHENA     examine method, coherence and professional reasoning
APOLLO     examine clarity, source light and truth exposure
HERMES     carry execution outward under contract, not decide
HÉPHAÏSTOS forge a recipe candidate from declared capabilities
CHARON     mark passage, archive, supersession and non-return
MÈTIS      hold the cap: the live intention and adaptive constraint
```

A god is not a runtime agent. A role invocation produces a governance expectation or review angle, not autonomous execution.

### Rites

A rite is a governed review pattern used when a task has a recognizable tension.

Examples:

```text
CONCORDANCE_DES_SOURCES
AUTOCRITIQUE_CONTRADICTOIRE
PREMISSES_CACHEES
RITE_DIVERGENCE_CONTROLEE
REFONDATION_DE_SESSION
```

A rite may be recommended or required by a Task Contract. A rite is not a workflow graph and does not execute itself.

### Places

A place is the governed location of the work.

Examples:

```text
session
conversation
dossier
project
domain
repository
instance
organization
system
```

The place determines scope, memory eligibility, external-action limits and evidence expectations. A module authorized in one place is not automatically authorized in another.

## Invocation envelope

A module invocation preflight should use a small envelope:

```yaml
invocation_preflight:
  id:
  module_id:
  intended_use:
  place:
    level:
    id:
  god_call:
    role:
    reason:
  rite_call:
    rite:
    trigger:
  connection_requirements:
    - type:
      target:
      direction:
      required_status:
  task_contract:
    required: true
    id:
    approval_ceiling:
    evidence_required:
    memory_behavior:
  expected_outputs:
  forbidden_outputs:
  dry_run: true
```

The response should distinguish technical availability from governed usability:

```yaml
preflight_result:
  module_id:
  detected:
  configured:
  connected:
  activation_status:
  task_authorized:
  connection_status:
  allowed_uses:
  blocked_uses:
  required_gates:
  evidence_expectation:
  memory_expectation:
  refusal_tests:
  result_status:
```

## Connectivity preflight by connection type

Connectivity checks must be typed. A module can pass one connection type and fail another.

| Connection type | What to verify | What it must not imply |
|---|---|---|
| HTTP API | endpoint responds, auth valid, version known | permission to perform write actions |
| MCP | server reachable, tool list readable, tool capabilities declared | tool authorization or safe execution |
| OAuth | token present, scopes known, expiry known | permission to transmit or mutate data |
| Webhook | endpoint reachable, signature secret configured, event scope limited | acceptance of every incoming event |
| Database | connection works, schema version matches, migrations applied | memory canonization or truth validation |
| Vector store | collections exist, embedding model known, retrieval works | proof, truth or Registre Probatoire entry |
| Filesystem | path exists, permissions match declared mode | unrestricted dossier access |
| Git remote | branch readable, commit known, worktree clean | direct merge or doctrine mutation |
| Browser worker | read/screenshot/extract works | form submission or external action |
| Runtime worker | sandbox task works, candidate returned | approval, scheduling or hidden orchestration |
| Message channel | receive/send-draft possible | silent external send |

A connection preflight should record:

```text
connection_type
direction: inbound | outbound | bidirectional
mode: read_only | candidate_write | write_gated | admin_only
scope
secret_status
version
last_checked_at
risk
required_gate
```

## MCP-specific preflight

MCP tools require an explicit usability check because tool availability is often mistaken for authorization.

Minimum MCP preflight:

```text
1. server reachable
2. protocol/version known
3. tool list readable
4. each tool has declared inputs and outputs
5. each tool has forbidden outputs/effects
6. each tool maps to a Pantheon module or capability declaration
7. write-capable tools are disabled or gated by default
8. external effects require explicit approval
9. refusal test passes
```

A correct MCP preflight may say:

```text
MCP server reachable.
Tools detected.
No tool is task-authorized yet.
Write tools require gate.
```

It must not say:

```text
MCP server reachable, therefore tools may be used.
```

## Refusal tests

Every invocation preflight should include at least one negative probe.

Examples:

```text
ask Telegram to send without approval -> must refuse
ask GitHub to merge without review -> must refuse
ask memory layer to canonize without evidence -> must refuse
ask browser worker to submit a form without gate -> must refuse
ask MCP file tool to read outside scope -> must refuse
ask vector store to treat retrieval as proof -> must refuse
```

If a module cannot refuse an out-of-bounds request, it is not governed for that use.

## Relationship to preflight suites

This document complements technical preflight and memory preflight.

```text
technical preflight     can the service respond?
connection preflight    can the declared connection work?
invocation preflight    may this module be considered for this task?
task authorization      may it be used under this Task Contract?
```

## Relationship to governed composition

This candidate should be reconciled with the governed composition work around HÉPHAÏSTOS, capability registry and forged workflow manifests.

The capability registry declares what exists. The invocation preflight asks whether the relevant role, rite, place and connection are eligible for this task. The forge may then compose a candidate recipe only from eligible declarations.

```text
registry declares
invocation preflight qualifies
forge composes
Task Contract authorizes
runtime executes outside Pantheon
Evidence Pack supports review
human decides
```

## Boundary

Invocation preflight must never become:

```text
role runtime
rite executor
MCP dispatcher
automatic connector gateway
scheduler
queue
provider router
approval engine
memory promotion engine
hidden workflow runner
```

It is a governance check before use.

## Candidate questions

Open questions before promotion:

```text
Should invocation preflight be a standalone spec or part of Module Activation?
Should MCP connectivity be modeled in Connection Registry or Capability Registry?
Should gods / rites / places be exposed in the dashboard as readable calls or hidden metadata?
Which refusal tests are mandatory for each connection type?
What is the minimum result shape Pantheon Control must persist?
```

## Final rule

```text
A module may be installed and connected.
It is usable only when the right role, rite, place, connection, scope, evidence and gate all align.
```