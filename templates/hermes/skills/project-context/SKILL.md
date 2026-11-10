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

## State the basis without being asked

For every answer that relies on project or Knowledge memory, or on inspected
documents, state the basis proactively in the opening line or section:

- `De mémoire` when relying on Hindsight, Mnemosyne or conversation context
  without reopening the source; identify the remembered source and say it was
  not reopened.
- `Vérifié dans …` when the source content was directly inspected; name the
  source and locator, and bound the claim to the pages/sections actually read.
- If both were used, distinguish remembered context from directly verified
  findings. If only part of a document was inspected, say `vérifié dans les
  passages lus`, never imply a complete review.

Do this by default; do not wait for the user to ask whether a statement comes
from memory or direct verification. Keep the label brief for simple answers.

## Core route

1. Before a material recall, state the unresolved question in retrieval-ready
   terms: the decision or fact sought, its scope, relevant qualifiers and what
   would count as a useful result. Keep the user's original objective intact.
   Use Mnemosyne only when prior conversation context, terminology or decisions
   could materially sharpen that framing; skip it for a simple, self-contained
   question or when the needed context is already present.
2. Select the conversation-local project. When its designation is informal,
   partial, misspelled or otherwise not known to match the router's exact scope,
   resolve it against an admitted project candidate or governed identity first.
   Do not pass an unverified alias to a router that derives one exact scope from
   the supplied string. If several candidates remain and the distinction matters,
   preserve them or ask one targeted question.
3. For a named project or dossier, use the configured project Hindsight router
   when the exact source is not already identified within the admitted project
   scope. If that source is already known and accessible, open it directly without
   redundant recall. Form one targeted query from the request and any useful
   continuity context. Hindsight is a continuity/location lead, not authority.
   After recall, briefly distinguish what was found, its source/provenance, and
   material gaps or conflicts; then update the next step from those results.
4. For a simple orientation or continuity question, Hindsight or Mnemosyne may
   be enough when the returned memory is sufficiently complete for that narrow
   answer. Label it `de mémoire`, identify the remembered document by its
   returned title/name when available (a filename is not required), and state
   that the source was not reopened. Offer to verify the cited document or
   locator; do not imply direct inspection.
5. Exactness of the requested answer does not by itself require reopening a
   source. A simple fact, list or count may be answered from conversation
   context or Hindsight when the relevant content is complete, its document
   identity and requested locator are available, and the user has not asked to
   verify the source. Mark it `de mémoire` and say the source was not reopened.
   Inspect the exact project source when verification is requested, the memory
   is incomplete or ambiguous, versions conflict materially, or the answer
   supports a professional opinion or consequential decision. Do not infer a
   complete list or total from partial memory (for example, the highest
   numbered item observed).
6. For any question that calls for a professional, technical, contractual,
   regulatory or compliance opinion, consult the relevant transversal
   DOCUMENTAIRES/Knowledge material automatically, even if the user did not
   explicitly ask to verify a document. Also inspect the exact project source
   when the conclusion depends on project-specific facts. Do not ask whether to
   search before doing this necessary bounded work. If a needed reference or
   source cannot be resolved, give a bounded answer and name the limitation.
7. Use an admitted representation only as far as needed to support the claim.
   Prefer the least costly suitable method; do not convert, OCR, inspect images
   or transcribe media by default. Delegate a source read only when the document
   is substantial or the source work is genuinely independent and an agent can
   reduce elapsed time; otherwise read it directly. The primary agent retains
   the question, checks decisive passages and synthesizes.
8. For a request about current project status, where a project stands, the
   latest or current index of one of its drawings, models or written documents,
   or a list of projects in progress, use the configured live project-state
   source first when available, and quote the indices, dates and questions it
   returns. Hindsight scope counts and remembered documents do not establish
   that a project is active. Never infer an index, a version or a phase from a
   file name or from which files are present; when the live source gives no
   index, say so. If no live inventory is available, state that limitation
   instead of inferring activity from indexed content.

Keep the user's original question and requested outcome active through the
answer. After each useful recall or read, update the next step from the evidence
already obtained: identify which part of the question remains unanswered and
which source could answer it. Do not keep searching or reading a document merely
because it is available or has a related title. If the current route fails,
correct the specific error once or use one materially different admitted route;
then report the bounded result and blocker instead of repeating failed calls.

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

After answering, offer one concise, relevant next step: verify the cited
source, deepen the same question, or broaden the search. Do not delay or weaken
the answer by making this optional follow-up a prerequisite.
