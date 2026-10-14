# Hermes Profile Constitution Adapter

Status: adapter candidate — runtime-profile constitution for Hermes execution.
Boundary profile: candidate_support_note.

This file is not canonical Pantheon doctrine.

It is not a Hermes configuration file, gateway routing file, Kanban board,
dispatcher, scheduler, queue, approval mechanism, memory mechanism, profile
installer or runtime manifest.

It does not create, install, start, route or authorize any Hermes profile.

## Purpose

This adapter note translates Pantheon governance boundaries into one practical
runtime question:

```text
When does external Hermes execution need a distinct profile rather than a posture,
Method, Skill, Capability or bounded delegation inside the governed default?
```

Read it with:

```text
docs/governance/AGENTS.md
docs/governance/HERMES_INTEGRATION.md
hermes/profiles/README.md
hermes/profiles/_base/README.md
hermes/profiles/_base/base-soul-rules.md
```

## Non-authority rule

A Hermes profile is an execution identity only.

```text
profile name != Pantheon Role
profile memory != Registre Probatoire entry
profile done != approval
profile comment != Evidence Pack
profile output != deliverable
profile routing != authorization
runtime tool choice != governance decision
```

If a profile produces anything consequential, the output remains candidate-only
until the relevant Pantheon gate classifies it.

## Profile admission rule

The normal governed path uses the `pantheon-governed` runtime envelope.

A separate profile is exceptional. It is justified only by a demonstrated runtime
boundary that cannot be represented safely inside the governed default, such as:

```text
materially different model or provider exposure
materially different memory / context-injection posture
different credentials or secret boundary
different capability / tool surface
different private-data exposure
different execution isolation requirement
different host or deployment trust boundary
```

The following are not sufficient reasons by themselves:

```text
different cognitive function
different Pantheon Role
different work posture
different Method or Skill
different source family
different tool chosen inside the same admitted boundary
different subtask delegated with delegate_task
```

Therefore:

```text
Pantheon Role != Hermes Profile
Role selected != profile selected
posture changed != profile changed
cognitive function != runtime boundary
delegate_task child != profile
```

A profile proposal must state the runtime boundary it adds and why the existing
governed envelope cannot represent that boundary. Without that demonstration,
prefer convergence on the existing profile plus Methods, Skills, Capabilities and
bounded delegation.

## Shared output envelope

Every governed runtime route reduces useful work to the same envelope:

```text
Task Contract in
-> bounded Hermes execution
-> Result Candidate + Evidence Pack Candidate + Capability Gap out
-> Pantheon status / proof / approval / memory gate
-> human decision
```

A runtime may report runtime status. It must not declare governance status.

## Governed runtime mode

The normal professional governed route uses:

```yaml
runtime_mode: pantheon-governed
task_contract_use: required
external_memory_provider: off
built_in_memory_injection: off
built_in_user_profile_injection: off
memory_tool: off
session_memory_key: forbidden
automatic_runtime_recall: forbidden
automatic_runtime_memory_write: forbidden
OpenWebUI_memory_injection: forbidden
OpenWebUI_automatic_RAG: forbidden
private_reasoning_projection: forbidden
reasoning_stream_to_user_surface: forbidden
commentary_projection: preferred_when_supported
interim_progress_projection: preferred_when_supported
profile_route: explicit_when_required
runtime_capability_surface: observable_and_qualified
runtime_tool_selection: adaptive_within_admitted_boundary
provider_and_model_override_in_run_payload: omitted_unless_separately_admitted
output_status: candidate_only
```

These fields describe an expected governed posture, not proof that a deployed
surface behaves that way. Configuration supports qualification; observed runtime
behavior remains the acceptance boundary.

The governed profile may retain `MEMORY.md` and `USER.md` as files inside its
isolated Hermes home, but baseline governed execution does not inject or expose
them. A memory provider, retrieval path or memory tool may be admitted only through
an explicit qualified task/deployment boundary.

`hermes memory off` disables the external provider only. It does not prove that
built-in memory injection, user-profile injection or the memory tool are disabled.

A named route such as `/p/<profile>/` proves only that the route answered. It does
not prove memory is inert, the capability surface is safe or the task authorized.

```text
profile route reachable != profile safe
hermes memory off != built-in memory injection off
external provider absent from tool list != external memory proven off
memory tool absent != memory injection disabled
stored memory != admitted memory
runtime mode configured != task authorized
show_reasoning false != private reasoning proven hidden
commentary unavailable != governed task unsafe
provider selected != memory admitted
memory recalled != truth
```

If the exact runtime mode, material memory posture, active capability surface or
user-visible reasoning posture cannot be observed sufficiently for the task, the
route remains `not_qualified` and must return a Capability Gap.

## Personal runtime boundary

The personal-assistant posture remains separate:

```yaml
runtime_mode: assistant-personal
task_contract_use: forbidden
external_memory_provider: optional_one_only
built_in_memory_posture: user_selected
runtime_recall_and_write: user_scoped_convenience
Pantheon_authority: none
professional_task_authorization: none
canonical_memory_promotion: none
```

This is a runtime boundary, not a Pantheon Role and not an additional governance
identity.

A `pantheon-governed` task must not silently fall back or delegate into this
memory-enriched posture.

## Work shape versus runtime identity

Work shape belongs primarily to the governed method.

Named work functions such as coordination, investigation, production,
contradiction review, evidence review, repository maintenance, document intake,
observability review or external-action preparation should normally be expressed
through:

```text
posture
Method
Skill
Capability / connector
bounded delegate_task
```

They do not become profiles merely because the work is distinct.

The preferred strategy is the smallest sufficient mechanism:

```text
same governed context
    -> default

bounded delegate_task + output_schema
    -> when a child task, fresh conversation or strict output contract adds value

separate profile
    -> only when the runtime boundary itself materially changes
```

A delegated worker remains transient and anonymous from Pantheon's point of view.

```text
subagent_id != Mortel
Mortel != runtime identity
fresh child conversation != fully isolated reviewer
delegate_task available != delegation required
```

## Historical Role-aligned profiles

Historical Role-aligned profile candidates under `hermes/profiles/` are
compatibility debt, not target topology.

Their removal must preserve useful capability rather than deleting it with the
profile shell.

Before deleting one, inspect whether it contains a material difference in:

```text
model / provider
memory or context injection
credentials
tool / capability surface
data exposure
execution isolation
deployment boundary
```

If no such difference exists, migrate useful prompt/method/tool knowledge to the
appropriate Method, Skill or Capability owner and retire the profile.

If a real runtime difference exists, retain or redesign a profile named for that
runtime boundary rather than for the Pantheon Role it happened to support.

```text
historical Role alignment != current runtime architecture
profile folder exists != profile required
deleting profile shell != deleting useful capability
```

## Adaptive runtime selection

Pantheon constrains legitimacy. Hermes chooses execution means.

A Task Contract may constrain objective, scope, source/data exposure, effect
ceiling, required reviews, approvals, Evidence expectations, allowed outputs and
forbidden effects. It need not name every concrete runtime tool when several
qualified mechanisms can satisfy the same boundary.

Inside that boundary Hermes may select, combine, sequence, replace or stop using:

```text
native tools
skills
plugins
MCP capabilities
retrieval providers
models
subagents / delegation
background or durable runtime mechanisms
```

```text
tool available != effect authorized
plugin installed != plugin adopted
MCP reachable != capability admitted
provider/model available != data exposure authorized
delegate_task available != delegation required
runtime success != Evidence
```

Changing a mechanism does not require a new Pantheon concept when objective,
scope, data exposure, memory posture, effect ceiling and approval posture remain
unchanged.

If a candidate mechanism requires broader source access, new private-data
disclosure, stronger permissions, consequential mutation/transmission, protected
path access, memory persistence or a higher approval ceiling, Hermes must not
silently select it. Return a Capability Gap or request the applicable gate.

## Routing principles

### Intake before consequential synthesis

If incoming material has unclear scope, version, authority, source status or
sensitivity, resolve that uncertainty before consequential synthesis.

Document intake is a method/work shape, not a mandatory profile hop.

### Evidence before consequential conclusion

If material sources matter to a consequential answer, decision brief,
professional position, repository change or external message, preserve source
traceability and contradiction review.

Evidence review is a method/work shape, not a mandatory profile hop.

### Domain work remains candidate work

Architecture-domain execution may apply professional methods only after scope and
evidence expectation are sufficiently bounded. The runtime applies a method. It
does not become the professional.

### Repository work remains gated by effect

Repository changes remain subject to applicable repository and protected-path
rules. A concrete runtime tool is not authorized merely because it can write.

Protected paths remain blocked without explicit approval:

```text
schemas/
tests/
pyproject.toml
operations/
platform/
Docker
.env
CLAUDE.md
```

A commit is an external repository effect. Runtime success never canonizes the
change.

### Governance review is not Zeus

A runtime may prepare governance-review material. It may not decide Zeus status by
itself.

### External effects are approval-bound

Any action that sends, publishes, files, commits to a third party, mutates an
external system or changes recipient-visible state must satisfy the applicable
approval/effect gate before execution.

## Kanban handoff convention

When Hermes uses Kanban or another durable runtime mechanism for governed work, a
bounded handoff should preserve at least:

```yaml
pantheon_handoff:
  task_contract:
  context_pack:
  evidence_expectation:
  requested_effect:
  approval_ceiling:
  runtime_profile:
  runtime_mode: pantheon-governed
  allowed_outputs:
  forbidden_outputs:
  idempotency_key:
  return_expected:
    - runtime_task_status
    - runtime_mode_observation
    - memory_posture_observation
    - produced_candidates
    - evidence_refs
    - approval_gap
    - memory_impact
    - unchanged_objects
```

Kanban is optional and is not a second source of truth.

Runtime comments and progress notes remain runtime notes only. They may support an
Evidence Pack Candidate when summarized, scoped and linked.

## delegate_task convention

The governed runtime may use short-lived delegation for bounded work.

Allowed examples include parallel source scan, contradiction review, short
code/document review, red-team critique and option comparison.

Delegation is not required merely because a task has several subquestions.

Delegated work inherits the parent runtime boundary unless a distinct boundary has
been separately admitted. A `pantheon-governed` task must not delegate into
`assistant-personal` or another memory-enriched route silently.

A delegation request must preserve material scope, source refs when relevant,
exclusions, expected output status, forbidden effects and return expectations.
Runtime-specific prompt syntax remains Hermes-owned.

## Channel routing convention

Gateway or messaging channel routing may map a topic, bot token or channel to a
profile. That is transport only.

```text
message received != task authorized
profile mentioned != approval granted
agent reply != external delivery unless it reaches a third party
agent-to-agent discussion != governance review
private reasoning != user-visible activity
```

A governed client must not silently fall back to a personal/memory-enriched route.
`profile route fell back to default` is a Capability Gap when that fallback changes
the admitted execution posture.

The governed client must not send `X-Hermes-Session-Key` unless separately
admitted; session continuity must not silently reintroduce runtime memory.

For a governed user-facing surface, model scratchpad, chain-of-thought blocks and
reasoning deltas remain hidden. Safe commentary may be projected when supported.

## Failure behavior

When the governed runtime cannot safely proceed, it must emit a Capability Gap
instead of improvising.

Common gaps include:

```text
missing Task Contract
missing Context Pack or source version
missing approval
ambiguous requested effect
runtime mode not observed
memory posture not sufficiently observed
active capability surface not qualified
private reasoning visible on governed user surface
reasoning visibility posture not sufficiently observed
profile route fell back to default
candidate mechanism requires broader source or data exposure
candidate mechanism requires stronger permission or higher effect ceiling
protected path requested
external target unconfirmed
evidence expectation unmet
memory impact unclear
channel routing unsafe
```

## Local verification checklist

Before binding a governed runtime profile locally, verify what is material:

```text
Hermes version and exact profile route
runtime boundary / isolation
memory provider/injection/tool/session posture
active capability/tool surface
provider/model data-exposure posture
selected plugin/MCP/provider behavior when used
delegation/durable-work behavior when used
idempotency and external-effect gates when applicable
workspace/source isolation
private reasoning absent from the governed user-visible surface
reasoning deltas not projected to the governed user-visible surface
commentary/interim progress capability recorded when available
trace visibility
no automatic memory promotion
no automatic external action
no protected-path mutation without gate
```

Configuration supports this verification but does not replace it.

```text
display.show_reasoning = false -> expected configuration signal, not behavioral proof
plugins.stream_reasoning_deltas = false -> preferred baseline when supported, not proof of channel behavior
show_commentary/interim messages unavailable -> UX degradation, not automatic safety failure
observed reasoning disclosure -> not_qualified regardless of nominal config
```

Qualification should observe capabilities, not freeze a historical tool list
unless a narrow high-risk binding requires that exact restriction.

## Status decisions

```text
Accepted:
Profiles as execution identities for real runtime boundaries.
pantheon-governed as the normal governed runtime envelope.
Work functions expressed through postures, Methods, Skills and Capabilities.
Adaptive Hermes selection among qualified means inside an admitted Task Contract.
Stored profile memory remaining inert by default.
Private reasoning remaining hidden on governed user-visible surfaces.
Safe commentary and interim progress as preferred observability when supported.
Profile constitution as adapter note outside the kernel.
Kanban and delegate_task as optional runtime mechanisms, not Pantheon requirements.

Refused:
Profiles as Pantheon Roles.
One profile per Pantheon Role.
Profiles created only to represent cognitive functions.
Parallel governed copies of every work function.
Profile constitution as doctrine source.
Runtime memory as Registre Probatoire.
Tool availability as task authorization.
Nominal show_reasoning false treated as proof that reasoning is hidden.
Private chain-of-thought or reasoning deltas projected as Pantheon activity.
Commentary availability treated as a safety authority.
A fixed global tool allowlist as the normal expression of Pantheon governance.
A personal memory-enriched profile receiving a Pantheon Task Contract without separate admission.
Kanban comments as Evidence Pack by themselves.
Self-authorized external action.
Self-organizing agent team as governance.

To verify:
Exact installed Hermes runtime/profile/capability behavior.
Complete memory status observation.
Governed user-visible reasoning posture on each admitted surface.
Selected plugin/MCP/provider behavior when used.
Loop guardrails and durable/delegation semantics when used.

To arbitrate:
Whether Pantheon Control may trigger a durable Hermes runtime task directly.
Whether nightly reviews may update dashboard status or only propose status changes.
Whether a shared context bus is admissible, and under which scope and memory rules.
```

## Final rule

```text
The governed method chooses the work shape.
The runtime profile expresses a real execution boundary.
The admitted Task Contract constrains consequence, scope and exposure.
Hermes chooses qualified runtime means inside that boundary.
Private reasoning stays private; safe observable commentary may be projected.
Stored runtime memory remains inert unless separately admitted.
None creates authority.
Pantheon governs the consequence.
```
