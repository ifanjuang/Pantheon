# Template Model

Status: candidate support note — template discipline — documented non-implemented.

This document defines the common structure for Pantheon / Hermes prompt and execution templates.

It is not a runtime configuration.
It does not install, execute, deploy, approve, send, schedule, route providers, promote memory or create an autonomous workflow.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally under Task Contract.
Pantheon Cockpit may expose governed template-derived projections.
Pantheon Next governs consequential status.
The human validates consequential output.
```

## Purpose

A template is a reusable candidate contract or preparation pattern.

It may frame how an assistant, external runtime, governed projection or human reviewer should read, qualify, transform, compare, draft or return information.

A template may standardize:

- role framing;
- required inputs;
- source hierarchy;
- allowed outputs;
- forbidden outputs;
- uncertainty discipline;
- Evidence expectations;
- human validation points;
- final answer or return format.

A template must not be treated as implementation, adoption or authority.

## Authority boundary

Templates instantiate existing doctrine. They do not create doctrine by themselves.

A template must remain compatible with:

- repository status rules;
- authority classes;
- Task Contracts;
- Evidence rules;
- approval rules;
- memory/Register rules;
- external-action boundaries;
- runtime and projection placement boundaries.

If a template conflicts with active doctrine, the template is wrong.

## Template anatomy

Each reusable template should define:

```text
name
status
owner_layer
surface
intent
target_user
phase_or_context
required_inputs
optional_inputs
source_hierarchy
operating_rules
forbidden_behaviors
output_structure
uncertainty_handling
evidence_requirements
approval_or_human_validation_points
memory_behavior
external_action_behavior
examples_or_notes
```

`surface` describes where a template may be consumed or projected. It does not create that surface as an architecture dependency.

## Required distinctions

Every template that handles consequential professional work must distinguish:

```text
fact
assumption
interpretation
recommendation
uncertainty
missing_information
decision_required
```

A template must not convert an assumption into a fact, hide uncertainty or fabricate a source that was not actually consulted.

## Source hierarchy

A template should state the source hierarchy expected by its domain/task owner.

A typical professional-project ordering may include:

```text
1. governed project/source records applicable to the task
2. latest applicable drawings or written documents
3. contract / mission scope
4. applicable regulations or professional references
5. meeting minutes and correspondence
6. qualified domain knowledge
7. model inference
```

Model inference is never Evidence by itself. Retrieval does not change source authority.

## Output status

Template output should be labelled when appropriate:

```text
candidate
partial / to verify
documented non-implemented
ready for human review
requires source check
requires approval
refused / out of scope
```

## Forbidden pattern

A template must not:

- claim implementation or installation;
- self-approve;
- promote memory;
- authorize an external action;
- create hidden workflow/runtime behavior;
- create a scheduler, queue or provider router;
- turn runtime success into Evidence;
- treat a tool or retrieval response as validated truth;
- bypass a human decision gate;
- import raw prompt leaks, proprietary prompts or unqualified third-party instructions into Pantheon doctrine.

## External inspiration rule

External prompt collections, tool prompts, leaked system prompts, public examples and third-party assistants may inspire abstract structure only.

Allowed:

- prompt architecture patterns;
- input/output contract patterns;
- uncertainty discipline;
- source hierarchy patterns;
- refusal and stop-condition patterns;
- trace and Evidence framing patterns.

Forbidden:

- raw ingestion;
- verbatim reuse;
- vectorization as knowledge authority;
- skill derivation from proprietary prompts;
- dependency adoption;
- automatic update;
- treating external prompts as authority.

## Placement

```text
Pantheon governs template status, boundary and consequence.
Hermes Agent may execute from a template only under the applicable Task Contract.
Hermes Web/dashboard or another compatible replaceable client may present runtime-facing forms/prompts.
Pantheon Cockpit and existing Card owners may project governed template-derived status/review surfaces.
The human validates consequential output where required.
```

A selected client, template, renderer or runtime does not receive governance authority from placement.

```text
projection != persistence
runtime success != authorization
provider selected != authority transfer
```

A template is useful only when its boundary is visible.
