# MCP Pantheon Minimal Profile

Status: active support doctrine — bounded read-only Pantheon MCP profile.

The implemented `mcp-server/` is a read-only policy, consultation and validation surface. This document defines its minimum architectural boundary; implementation status remains described by `WHAT_RUNS.md` and the executable module/tests.

```text
Hermes Web/dashboard or another compatible replaceable client handles runtime interaction.
Hermes Agent executes externally.
Pantheon MCP projects governance and validation data read-only.
Pantheon Cockpit may project governed status, Cards, navigation, review and decisions.
Pantheon governs consequential status.
The human decides.
```

No client, runtime result, MCP response or displayed state transfers governance authority.

## Purpose

The minimal profile gives Hermes and other bounded clients a traceable way to consult Pantheon doctrine and request side-effect-free validation without turning Pantheon into an execution runtime, gateway, scheduler, provider router, memory engine or approval engine.

## Implemented boundary

The existing `mcp-server/` owns the executable read-only service. Its current consultation surface includes repository-source discovery, doctrine reads, governance-structure explanation, architecture explanation and caller-provided capability-status qualification. Additional validators exist under the same bounded implementation.

```text
MCP resource listed != source adopted
validation pass != authorization
runtime success != Evidence
projection != persistence
retrieved != truth
```

## Allowed behavior

Pantheon MCP may:

- expose traced governance sources and their declared status;
- return validation/classification reports as data;
- qualify caller-provided observations without pretending to have probed a runtime;
- prepare bounded candidate structures where an existing contract owns them;
- report missing evidence, scope, authorization or capability as explicit gaps.

Responses must remain attributable to their repository owners and must not silently create doctrine.

## Forbidden behavior

Pantheon MCP must not:

- execute a task or external effect;
- send, file, merge, install, schedule or route providers;
- become an unrestricted connector or data gateway;
- approve its own result or convert runtime success into authorization;
- promote runtime/workspace memory into the Registre Probatoire;
- turn retrieval, health, reachability, CI status or a model result into truth/Evidence;
- make a client, provider or folder/path authoritative by selection alone.

## Client and Cockpit boundary

Runtime interaction and governed projection are separate responsibilities.

```text
Hermes Web/dashboard
-> chat, sessions, attachments and runtime controls

compatible Hermes Web/PWA/mobile clients
-> optional replaceable interaction clients

Pantheon Cockpit
-> governed Cards/navigation/status/review/decision projections
-> not a second general-purpose chat frontend
```

Pantheon MCP may supply read-only governed data to those surfaces. It does not own their session/runtime persistence and does not authorize an effect because a client displayed or requested it.

## Generic exposure verification

The existing exposure verifier classifies provided evidence about a surface's reach, authentication and scope. It is client-agnostic and may be used for `hermes_web`, `runtime_client` or another bounded surface.

```text
exposure verification != client ownership
reachable != authorized
public + authenticated != approved
safe-looking surface != professional authority
```

The verifier performs no network probe and grants no authority.

## External runtime relationship

Hermes Agent may consume Pantheon policy/validation outputs only within the applicable Task Contract and gates.

```text
Task Contract / governed context in
-> authorized Hermes execution
-> Result Candidate / observations / Evidence material out
-> Pantheon validation and governed status
-> human decision where required
```

Hermes must not treat Pantheon MCP as a hidden planner, provider selector, scheduler, permission oracle or replacement for human/professional approval.

## Capability admission

An externally available MCP/tool capability remains subject to the existing capability placement, binding, activation and Task Contract owners.

```text
listed != installed
installed != approved
binding selected != dependency adopted
activated != task authorized
```

Do not create a second MCP registry or installer inside this profile.

## Evidence, memory and Register

MCP outputs are reports/candidates, not Evidence by themselves. Runtime memory, workspace notes, retrieved context and the Registre Probatoire remain separate.

```text
memory != Evidence
source capture != Evidence
retrieval != promotion
validation report != professional truth
```

Durable governed assertions continue through the existing Register Candidate and approval path.

## Minimum refusal posture

Any requested side effect that is not explicitly owned by a separately authorized external execution path must fail closed. A refusal should identify the missing Task Contract, approval, Evidence or capability boundary rather than silently performing the effect.

## Current owners

```text
runtime interaction     -> Hermes Web/dashboard + compatible replaceable clients
external execution      -> Hermes Agent
policy/validation MCP   -> mcp-server/
governed projection     -> Pantheon Cockpit / Card projection owners
governance authority    -> Pantheon doctrine/contracts/decisions
human consequence       -> explicit human/professional decision where required
```

## Final rule

Pantheon MCP is a bounded governance interface, not a runtime. Keep clients replaceable, execution external, projections non-persistent by implication, and authority with the existing governed owners.
