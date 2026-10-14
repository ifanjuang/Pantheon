# Uniform Capability Governance

Status: active support doctrine — the keystone that unifies how Pantheon governs every added capability. It coordinates existing canonical doctrine (capability passport, the two gates, the placement test); it does not replace it.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: compatible runtime clients are optional interaction surfaces, Hermes/the external runtime executes admitted work and enforces consequential effects as PEP, Pantheon Cockpit projects governed state, and Pantheon retains governance/PDP authority.

## The principle

Pantheon does not write a rulebook per module, per skill, per function or per plugin.

It writes **one rulebook** and applies it to every capability through **one passport per capability**.

```text
One law      — the universal envelope and the gate.
One passport — a declaration (data) carried by each capability.
No per-module rules.
```

A capability's specifics live in its passport (data). The governance logic stays universal. Adding a new module, skill, function or plugin adds a passport, never a new rule.

## The universal envelope

Whatever a capability is, and whatever external surface hosts or exposes it (Hermes, an observability layer, an optional runtime client, an MCP server), every consequential use passes through the same envelope:

```text
Task Contract
  -> the capability runs in the execution runtime
  -> Result Candidate + Evidence Pack Candidate
  -> gate: passport check, evidence, scope, approval ceiling
  -> the human decides
```

This is the same path the two gates in `WORKFLOW_SCHEMA.md` describe. The current capability-passport shape lives in `schemas/capability_passport.schema.yaml`, with its non-executable template in `templates/mcp_capability_passport.yaml`, and governed capability declarations remain registered through `CAPABILITY_REGISTRY.md`.

## One law, many passports

The passport classifies each capability uniformly:

```text
reads private data? writes external state? can change the register? can send externally?
allowed scope / forbidden scope · risk level · approval ceiling (C0–C5) ·
evidence required · required_envelope: task_contract_in -> candidate_out -> evidence_pack_out
```

Two capabilities differ by their passport values, not by bespoke governance code. The rule that reads a passport is the same for all.

## The chokepoint — what makes Pantheon master

Pantheon is master not because it executes, but because **every consequential effect passes through its gate**.

```text
Non-consequential effect (display, format, help, draft)  -> free; no gate needed.
Consequential effect (asserted truth, external action,
  a Registre Probatoire entry, an approval)              -> must pass the gate.
```

The invariant — and the one real architectural requirement:

```text
The execution runtime must route consequential effects through Pantheon's policy check.
A consequential effect that reaches the world without passing the gate is a bypass.
A bypassable gate makes Pantheon master only in advice, not in fact.
```

So "Pantheon remains master" is a property of the runtime honouring the gate, not of where code lives. The implemented Pantheon policy boundary is described by `mcp-server/docs/HTTP_API_CONTRACT.md`; enforcement remains on the runtime/PEP side as governed by `HERMES_INTEGRATION.md`. A capability may be installed or exposed by Hermes, another external runtime, an observability surface or an optional runtime client; the moment it would produce a consequential effect, it resolves through Pantheon.

## Named architecture (PDP / PEP)

This is a known, validated pattern. In Policy Decision Point / Policy Enforcement Point terms:

```text
Pantheon policy service = bounded Policy Decision Point (PDP) interface.
Hermes / external runtime = Policy Enforcement Point (PEP) for consequential effects.
Optional runtime client   = replaceable runtime interaction surface.
Pantheon Cockpit          = governed projection of decisions, Evidence gaps and status.
Pantheon Next             = governance and authority semantics.
Human                     = consequential decision when required.
Pantheon Control          = bounded operational eyes and hands; it does not decide legitimacy.
```

External grounding (distilled, not imported): the PDP/PEP separation (XACML), policy-as-data decision engines (Open Policy Agent and admission control such as Gatekeeper), signed provenance/attestation (in-toto, SLSA) for the evidence side, and software-catalog + golden-path templates (Backstage) for Control. Pantheon adopts the *vocabulary and the chokepoint pattern*; it imports no runtime.

## What this means for modules, skills, functions and domains

Activation, review and placement owners project this single law onto their area; they must not invent competing per-capability rules:

```text
MODULE_ACTIVATION / ROLE_ACTIVATION  -> status and task-authorization axes; defer to the passport.
CAPABILITY_REGISTRY                  -> declaration/admission metadata; a Skill is only one Capability primitive.
WATCHLIST / REFERENCE_BOUNDARIES     -> external Skill/package observation and interpretation, without adoption.
EXTERNAL_TOOLS_POLICY / placement    -> an external tool is a capability with a passport.
CAPABILITY_PLACEMENT (placement test) -> decides whether an effect is consequential, hence gated.
DOMAIN_PACK_SPEC                     -> projects the method; the envelope stays the same.
```

Skill discovery, package installation, runtime loading and execution remain operational/runtime concerns. They do not create a parallel Pantheon Skill lifecycle.

The placement test (`AUTHORITY_INDEX.md`, `CAPABILITY_PLACEMENT.md`) decides the one thing that matters: is the effect consequential? If yes, the gate applies; if no, it is a feature of the runtime.

## Pantheon Control under this law

Control needs no per-module rules either. It **applies the universal passport** and **displays gate state**; it decides nothing.

```text
Control may: install / update repos, deploy presets, preflight states, test MCP,
             show the database and the evidence logs, show installed / connected /
             authorized / validated, show passport and gate status.
Control may not: canonize, approve, promote a register entry, or admit a capability
             by display alone. installed != connected != authorized != validated.
```

## Boundary

This document is the governance contract for capability uniformity. It adds no runtime, scheduler, queue, provider router, policy engine, installer or MCP host inside Pantheon Next. Enforcement lives in the execution runtime honouring the gate; Pantheon owns the law, the passport shape and the decision, not the execution.

```text
One law, one passport per capability, an unbypassable gate for consequential effects.
Pantheon decides. The runtime enforces. The governed projection exposes status. The human engages.
```
