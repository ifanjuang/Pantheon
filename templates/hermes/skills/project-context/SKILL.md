---
name: project-context
description: "Use for agency project or professional-document questions requiring local context, source routing or a governed boundary. Use Hindsight to locate missing sources, then inspect only the exact source needed; creates no truth, approval, persistence or authorization."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/HERMES_INTEGRATION.md
  related_skills: [pantheon-governed-method, pantheon-activity-projection, pantheon-request-intake, source-research]
---

# Agency project context

Use one document-neutral route for project material: retain the project selected
by the conversation, resolve an informal designation to an exact project
candidate before calling a strict project-scoped router, then use Hindsight to
locate candidates. Open an admitted exact source only to the level the request
needs. Source format does not establish the method or authority of the result.

For a multi-source, long-document or version-sensitive agency task, read
[references/task-context-selection.md](references/task-context-selection.md)
**after scope and policy preflight** to select the smallest source subset and
relevant specialist Skill. Skip this additional reference for simple orientation;
do not load a full project corpus or the entire conversation by default.

## Conversation projection

For non-trivial agency work, when `pantheon-activity-projection` is available,
load and apply it before substantial execution. It does not prescribe the runtime tool sequence.
If unavailable, report a presentation capability gap
without inventing an equivalent governance layer.

```text
projection plan != runtime dispatch plan
visible milestone != MCP-prescribed tool sequence
```

## Core route

1. Select the conversation-local project. When its designation is informal,
   partial, misspelled or otherwise not known to match the router's exact scope,
   resolve it against an admitted project candidate or governed identity first.
   Do not pass an unverified alias to a router that derives one exact scope from
   the supplied string. If several candidates remain and the distinction matters,
   preserve them or ask one targeted question.
2. When the exact project scope is known and the source is not, use the configured
   project Hindsight router as a continuity/location lead. If an exact source is
   already known and accessible, open it directly without redundant recall.
3. For simple recall, Hindsight may be sufficient when it returns the answer,
   source locator and relevant version/limitations. Label it
   `orientation mémoire — non confirmée`; do not open a PDF by default.
4. Inspect the exact source when the user requests verification, the answer will
   support a consequential decision or external communication, candidate versions
   conflict in a way that changes the result, or Hindsight lacks enough context
   to answer. Keep the source inspection bounded to the relevant passage/pages.
5. For a request about current project status or a list of projects in progress,
   use the configured live project-state source when available. Hindsight scope
   counts and remembered documents do not establish that a project is active.
   If no live inventory is available, state that limitation instead of inferring
   activity from indexed content.
6. Use an admitted representation only when needed for the source question.
   Prefer the least costly suitable method; do not convert, OCR, inspect images
   or transcribe media by default.
7. For technical, legal, regulatory, contractual or professional-rule testing,
   consult the relevant DOCUMENTAIRES or authoritative source separately from
   the project source.

When an answer depends on project values not given, read
[references/project-frame.md](references/project-frame.md) for the frame
factors, the ways to narrow them and the likely task.

Read [references/professional-source-routing.md](references/professional-source-routing.md)
before a material professional review. Read
[references/project-resolution.md](references/project-resolution.md) for an
ambiguous project identity, and
[references/document-inspection.md](references/document-inspection.md) when a
source or derived representation must support a claim.

## Boundaries

Do not hard-code workspace paths, Hindsight bank IDs or providers. Do not turn
a memory lead, filename, search hit, representation or parser success into a
source claim. Use `source-research` only when the local sources cannot answer a
material current or external question. Route consequential decisions through
the selected Pantheon binding.

```text
Hindsight recall != source authority
representation != source replaced
retrieved != truth
project source != external rule
memory answer != Evidence
```
