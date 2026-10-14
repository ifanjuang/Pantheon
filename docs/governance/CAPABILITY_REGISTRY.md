# Capability Registry

Status: candidate / to verify — governance declaration of capabilities, organized as a dependency graph for governed composition.
Boundary profile: candidate_support_note.

A capability registry is a governance declaration of *what capabilities exist*, *what each may and may not do*, and *which other capabilities each one depends on*. It is the index from which HEPHAISTOS forges a Workflow Manifest candidate (`WORKFLOW_SCHEMA.md`).

It is not a runtime. It is not a skill installer. It is not a plugin manager. It is not a tool dispatch table. It does not execute, schedule, queue or route anything.

## Candidate posture

This document is useful, but it remains `candidate / to verify` until explicitly promoted in `AUTHORITY_INDEX.md`.

A capability declaration inside this registry is also a candidate until reviewed.

Candidate status is intentional: the registry introduces a new organizing surface and must remain visibly non-canonical until its interactions with Workflow Manifests, Capability Passports, HEPHAISTOS, Registre Probatoire and module preflight are reconciled.

## Core principle

Pantheon applies one governance law to capabilities through the Capability Passport defined by active support doctrine and `schemas/capability_passport.schema.yaml`.

A Capability is a governed unit that may be represented by a runtime primitive such as a Skill, Tool, Prompt or Resource. A runtime primitive does not become admitted, safe, activated or task-authorized merely because it exists.

A **Capability Slot** is different: it is an abstract, replaceable function or binding target used to classify which capability or external binding may satisfy a need.

```text
Capability Slot != Capability
Capability Passport != runtime binding
Skill discovered != Skill admitted
installed != approved
activated != task-authorized
```

The runtime owns execution and implementation mechanics. Pantheon owns governance classification, eligibility, scope, evidence expectations and approval boundaries.

```text
The registry declares governed capabilities and dependencies.
The Capability Passport classifies each capability uniformly.
Capability Slots organize replaceable binding choices where needed.
The forge composes eligible capabilities.
The runtime executes.
Pantheon governs eligibility, evidence support and status.
```

A capability declaration is a candidate until reviewed. Availability is not authorization. Installability is not capability approval.

## Capability declaration

A capability declaration should remain structurally small. Canonical concerns:

```text
Identity        stable governance identifier and clear title
Primitive       Skill / Tool / Prompt / Resource or another passport-supported form
Purpose         the professional outcome it serves
Inputs          expected inputs
Outputs         allowed outputs
Forbidden       forbidden outputs and forbidden effects
Risk class      consequence if it goes wrong
Authority       what it may decide; what it must escalate
Dependencies    other capabilities it relies on
Domain scope    where it applies (domain pack, dossier, scope_id)
Evidence        expected Evidence Pack Candidate shape and probative support
Provenance      where the declaration came from, and when
Status          candidate / reviewed / suspended / rejected or the applicable governed lifecycle state
```

A declaration describes governance. It does not describe scheduling, retries, provider routing or tool dispatch.

Runtime implementation and release provenance, and binding selection, remain separate concerns. A passport does not install or bind anything by itself.

## Skill admission guard

A Skill may itself be a Capability primitive under the uniform Capability Passport. This does not collapse Skill discovery, installation, validation, admission and task authorization into one state.

External skill catalogues, public repositories and package installers may expose or distribute Skills. They do not approve them.

A Skill may be easy to install, recommended by a catalogue, popular, discoverable, synced across agents or already present in a runtime. None of those states makes it eligible for a Pantheon-governed task.

```text
visible       != admitted
available     != authorized
installed     != approved
synced        != reviewed
discoverable  != trusted
recommended   != safe
popular       != safe
MCP available != task-authorized
```

Before a runtime Skill may be admitted for governed use, its admission material must record at least:

```text
Source          repository, package, catalogue entry or local origin
Version         pinned version, commit hash, content hash or immutable release reference
Author          upstream author, maintainer or internal owner
Installer       how the runtime obtains it, if relevant
Permissions     requested file, network, command, connector or write perimeter
Scope           allowed dossier, project, domain, user or organization scope
Forbidden       forbidden effects, forbidden outputs and forbidden persistence
Risk class      consequence if it fails or exceeds its declared boundary
Approval ceiling maximum approval level it may reach without human decision
Evidence        required Evidence Pack Candidate shape
Owner           person accountable for admission review
Reviewed by     reviewer and review date
Status          applicable Skill / Capability lifecycle state
```

A Skill with unknown source, floating version, broad command access, hidden network access, write access to doctrine, free access to private material or external side effects is not eligible by default.

The safe default is project-scoped admission, pinned version, minimum permissions and explicit review. Global skill installation, multi-agent installation, remote synchronization and automatic skill update are governance risks unless separately reviewed and bounded.

The registry may declare that a Skill capability exists. It must not install it. It must not update it. It must not treat an external catalogue as a source of authority.

### MCP write-capable skill managers

A SkillsGate-like tool is a skill manager, not a governance authority. It may expose skill inventory, discovery, preview, installation, removal, update and synchronization through CLI, TUI, desktop UI or MCP tools.

Pantheon may use that operational model to define admission metadata. It must not import the manager as Pantheon machinery.

Read-only skill inventory is low-risk only when it remains inventory:

```text
list installed skills
show source and installed path
show target agents
show installedAt / updatedAt metadata
show lockfile or hash metadata
show catalogue source
```

Preview-before-install is also only a candidate step:

```text
list discovered skills without installing
read SKILL.md metadata
surface declared tools and permissions
prepare Skill Admission Candidate
```

Write-capable operations are external actions and must be gated:

```text
install skill into one agent
install skill into several agents
remove skill
update skill
sync skills from packages or remote servers
edit local skill content
```

Those operations may be available through MCP, but MCP availability is not authorization. A write-capable MCP tool may prepare a candidate review or ask for a User Decision Gate. It must not silently install, update, remove or sync skills for governed work.

Suggested refusal tests for any SkillsGate-like admission path:

```text
refuse public-skill global install without review
refuse multi-agent install without explicit target scope
refuse package sync without inventory review
refuse unpinned source or floating branch for governed work
refuse broad filesystem, shell, network or connector access without permission mapping
refuse catalogue ranking as a safety signal
refuse local skill edits that preserve reviewed status without re-review
refuse use on client or project data before project-scoped admission
refuse skill output as proof, approval or Registre Probatoire material without evidence review
```

The useful pattern to keep is the admission gap:

```text
The catalogue discovers.
The manager installs.
The runtime exposes.
Pantheon classifies and admits or blocks governed eligibility.
Capability Slot binding, when relevant, remains a separate selection.
Task Contract / Execution Admission separately authorizes one runtime opportunity.
The human approves consequential use.
```

## Why a graph, not a list

Capabilities are declared with their dependencies, so the registry forms a graph, not a flat list. This lets the forge retrieve a capability *and the capabilities it structurally needs*, instead of matching free text.

```text
high-level capability   "prepare the project form"
  depends on
mid-level capabilities  "fetch form template", "resolve known field", "verify entity"
  depends on
low-level capabilities  "read scoped source", "render annotated document"
```

Retrieval starts from a small seed selected by declared purpose, then follows declared dependencies to recover what is structurally required. The graph is a governance map of dependency, not an execution graph.

## Metadata-first selection

Only governance declarations are read during composition. Execution is invoked only after the forged manifest is found eligible and the task is separately authorized, outside Pantheon.

```text
read declarations to compose
resolve required admission / binding references
invoke only when separately task-authorized, outside Pantheon
```

## Enrichment is governed

The registry may be enriched over time — new capabilities, new domain sources, new declarations. Enrichment is a governed step.

```text
a new capability declaration enters as candidate
review may promote it
a superseded declaration is archived, not deleted (CHARON)
```

No capability self-registers as authority. No enrichment auto-promotes. The registry must not become a marketplace, an automatic installer or a capability runtime.

## Relationship to the forge

HEPHAISTOS reads this registry to assemble a Workflow Manifest candidate. The registry supplies eligible capabilities and their dependencies; the forge supplies topology and per-step signatures; Pantheon supplies the cap, gates and status.

```text
registry         -> what governed capabilities exist and what they may do
Capability Slot  -> replaceable function / binding target where applicable
forge            -> how capabilities are composed for this cap
Pantheon         -> whether the recipe is eligible, evidence-supported and approved
runtime          -> execution, outside Pantheon
```

## Relationship to Skills, Passports and modules

The active uniform rule is:

```text
one governance law
one Capability Passport per governed capability unit
no per-module governance engine
```

A Skill can be a Capability primitive. `schemas/skill_manifest.schema.yaml` supplies Skill-oriented declaration/admission metadata; `schemas/capability_passport.schema.yaml` supplies the uniform governance classification.

For a Skill-backed workflow step, the current workflow schema may carry:

```text
capability_step.capability_id
capability_step.skill_manifest_ref -> skill_manifest.skill_id
```

`skill_manifest_ref` proves an explicit admission/reference relationship. Its presence does not create a second abstract Capability layer above every Skill, and identifier equality does not by itself grant admission or authorization.

The important non-equivalences are lifecycle and authority boundaries:

```text
Skill discovered != Skill validated
Skill validated != Capability admitted
Capability admitted != Capability Slot selected
Capability Slot selected != dependency adopted
Capability admitted != task-authorized
runtime success != Evidence
```

Risk uses the shared `low / medium / high / critical` scale where the schemas require it.

## Relationship to scope and memory

A capability declares its governed scope (`SCOPE_ISOLATION.md`, `CORE_RECORDS_MODEL.md`). A capability that crosses scopes must say so and is governed accordingly. The registry records declarations; it does not promote memory and it is not a Registre Probatoire entry.

## Bonus tool candidate map

Bonus tools are optional adapters or references that may enrich the execution surface, but are not required for Pantheon governance.

A Tool may be a Capability primitive once governed through the Passport and applicable admission path. Documentation or reachability alone does not do that.

```text
bonus tool visible       != admitted capability
bonus tool documented    != installed tool
bonus adapter reachable  != task authorization
bonus output generated   != evidence, proof, approval or memory
```

### `bfl_openai_image_proxy`

```text
id: bfl_openai_image_proxy
label: BFL OpenAI Image Proxy
source_review: BFL_OPENAI_IMAGE_PROXY_REVIEW.md
cartography_class: bonus_tool_candidate
primary_layer: adapter / binding
exposure_surface: OpenWebUI
execution_provider: Black Forest Labs FLUX
purpose: expose FLUX text-to-image generation through an OpenAI-compatible image endpoint for OpenWebUI
allowed_outputs:
  - Image Candidate
  - Result Candidate
  - Trace Reference
  - Evidence Pack Candidate only if separately reviewed
forbidden_outputs:
  - proof
  - professional validation
  - approved client deliverable
  - Registre Probatoire entry
  - memory promotion
  - provider routing authority
risk_class: medium when client-facing or project-decision support is possible
approval_ceiling: candidate-only unless a User Decision Gate approves narrow use
memory_behavior: none by default
status: optional_bonus_candidate / documented_non_implemented
```

Placement phrase:

```text
OpenWebUI exposes image generation.
The proxy adapts the OpenAI-compatible request.
BFL executes image generation.
Pantheon governs status, scope, evidence, delivery and memory.
```

This entry only adds the tool to the cartography. It does not install, configure, admit or authorize the proxy.

## Boundary

Documentation only. This registry is a governance declaration. It does not implement a runtime, installer, scheduler, queue, provider router, tool dispatch, external catalogue integration, automatic skill update, automatic skill promotion or automatic memory promotion. Execution remains external.

```text
The registry declares governed capabilities and dependencies.
The Capability Passport classifies them under one law.
Capability Slots keep replaceable binding targets distinct.
The forge composes them for a cap.
Pantheon governs eligibility, evidence support and status.
Task Contract / Execution Admission governs task/run legitimacy.
The execution runtime executes outside.
The human engages.
```
