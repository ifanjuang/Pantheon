# Pantheon Cockpit — co-located candidate

Status: implemented and tested candidate surface — not adopted, not activated, not production-authorized.

This directory is the current Cockpit frontend and projection layer in the co-located `implementation/` candidate. It exposes bounded views over existing owners; it does not become a database, governance authority, runtime, scheduler, memory engine, approval engine or source of professional truth.

```text
Pantheon Next governs.
Hermes executes bounded external work.
The Cockpit exposes projections and captures bounded intent.
The human decides consequential effects.
```

## Current boot chain

`index.html` is the current shell. It loads `cockpit_bootstrap.js`, which delegates to `live_bootstrap.js`.

`live_bootstrap.js` owns the shared live/demo boot sequence:

1. select live or `?mode=demo` data posture;
2. load tag icon registries;
3. load and validate the Navigation Registry;
4. load card projection definitions;
5. load Swiper when available, otherwise expose fallback controls;
6. load the classic projection, interaction, handoff, editor and map modules in one declared order;
7. start demo fixtures only after production modules are loaded.

Demo mode substitutes data. It is not a second Cockpit application and cannot establish runtime health, adoption or authorization.

## Navigation and Card contracts

The current navigation configuration is owned by:

```text
registries/navigation_registry.json
projection/navigation_registry_loader.js
projection/navigation_registry_adapter.js
projection/child_collection_assembler.js
```

The canonical validation contract remains repository-root `schemas/navigation_registry.schema.yaml`.

Root identities/order are defined by the Navigation Registry. The current registered sequence is:

```text
Pantheon → Affaires → Connaissances → Workspace → Outils → Décisions
```

The header menu is derived from that registry and the Card projection definitions; static HTML must not carry a competing root list.

Card presentation definitions are owned by:

```text
registries/card_projection_definitions.json
projection/card_projection_definition_loader.js
structured_interface.js
```

The registries describe projection identity, ordering, source names and presentation. They do not own endpoint routing, business identity, authorization, Evidence qualification or runtime execution.

```text
Card != source of truth
projection != persistence
rendered status != authorization
runtime success != Evidence
```

## Current owner projections

The Cockpit composes existing bounded sources including:

- Agency Data / Project projections;
- Information, Document, Knowledge and Work Issue projections;
- Decision Request projections;
- Category/CategoryAssignment-backed Knowledge navigation;
- runtime/tool observations;
- read-only filesystem Workspace collections;
- project anatomy and context projections;
- bounded handoff and candidate-action surfaces.

The Cockpit must reuse those owners rather than create parallel records merely to render a Card.

## Workspace boundary

`workspace_collection_read.py` and its API expose explicitly configured filesystem roots as ephemeral read-only `workspace_entry` Cards.

```text
filesystem path != Project
folder name != Category
folder location != Knowledge
retrieved file != Evidence
workspace projection != governed identity
```

Physical configured roots stay server-side. The projection rejects path traversal and symlink traversal and does not infer domain identity from directory structure.

Direct collection reads now add cheap reconstructible metadata to file Cards: filename, extension, MIME type, byte size, filesystem modification timestamp, file kind and adjacent `document.yaml` presence. The sidecar is only observed; this seam does not parse or validate it, resolve identity from it, ingest file contents or use Hindsight.

```text
filesystem appearance / drop
→ next Workspace collection read exposes the file Card + local metadata
→ no watcher, cache or persistence required

adjacent document.yaml observed
!= manifest valid
!= identity mapping resolved

PDF metadata observed
!= PDF content understood
```

The Workspace navigation path deliberately does not compute a SHA-256 for every listed file. Exact content digests belong to the bounded operation that actually needs an exact byte basis, such as qualification, derivation or admission; ordinary folder navigation remains inexpensive and reconstructible.

Workspace currently occupies a primary root because a bounded source and projection already exist. That root placement remains reversible product navigation; it does not promote folders into governed identities.

## Competence / Capability boundary

Cockpit product doctrine is owned by `docs/governance/PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md`. Competence composition semantics are owned by `docs/governance/COMPETENCE_MODEL.md`; technical facts remain with the existing Capability owners.

The current implementation must not manufacture a `Compétences` root by relabelling runtime tools, filesystem workspaces or Skills.

```text
Compétence != Workspace
Compétence != runtime Skill
Tool != Compétence
Capability candidate != admitted capability
installed != approved
available != task-authorized
```

The Context Resolver defines a `#` capability namespace, but no live capability provider is currently attached. A future competence/capability projection must compose existing governed owners rather than introduce a new Cockpit registry solely for navigation.

## Decisions and execution

Decision Requests remain separate governed objects. Their presence may block continuation, but a Cockpit interaction does not automatically resume work.

Hermes handoffs and runtime observations are technical/execution projections only:

```text
handoff prepared != execution authorized
run launched != result approved
run succeeded != Work Issue resolved
technical receipt != Evidence
Decision recorded != external effect executed
```

## Development constraints

When extending this directory:

- keep one boot chain for live and demo;
- keep the Navigation Registry as the executable owner of root identities/order;
- prefer registries and generic projection machinery over hard-coded parallel navigation;
- keep owner records outside the Cockpit renderer;
- preserve stable entity identity across projections;
- keep lazy collection reads read-only unless a separately governed owner action exists;
- do not infer Case, Knowledge, Evidence, Decision or authorization from folders, UI placement or runtime state;
- update the relevant contract tests when a root, source, Card definition or route boundary changes.

## Validation

The current implementation is covered by Cockpit navigation, Card projection, Workspace collection, Decision Request, Category navigation, Tool Card and composed-route tests under `implementation/tests/`, plus repository CI.

CI success is test evidence only:

```text
test pass != adoption
CI green != production authorization
implementation present != activated
```

Do not pin this README to a historical validation commit. Current `main`, current tests and current workflow results are the authority for implementation state.
