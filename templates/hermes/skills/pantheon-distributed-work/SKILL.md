---
name: pantheon-distributed-work
description: "Choose and coordinate bounded Hermes work across direct execution, delegated subagents, persistent Bot profiles, and Kanban tasks while preserving the original user objective, source boundaries, and Pantheon authority limits."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/GOVERNED_METHOD_STANDARD.md
  related_skills: [pantheon-governed-method, project-context, pantheon-request-intake, pantheon-activity-projection]
  runtime: external-hermes
  upstream: "Hermes delegation, profiles/Bot Mode and Kanban; exact installed features require runtime qualification"
---

# Pantheon distributed work

Use when a material task may benefit from multiple bounded workstreams or a
durable task graph. The primary Hermes agent retains the user's question,
coordinates the work, verifies decisive evidence and writes the final answer.

```text
Pantheon Role != worker identity
Mortel posture != Hermes profile
subagent != persistent Bot
Bot != Pantheon authority
Kanban != source of truth
worker report != Evidence
```

## Choose the smallest sufficient work shape

Start with direct execution. A simple, bounded question or one long document
normally needs no child agent. Distribute only when independent work can reduce
elapsed time or a resumable workflow materially helps; use the fewest workers
that cover those tasks.

| Work shape | Use when | Return path |
|---|---|---|
| Direct | One source, one bounded question, or steps depend on each other | Primary agent checks and answers |
| `delegate_task` | One-off bounded subtask needing fresh context, or independent source reads when observed concurrency can reduce elapsed time | Child returns a compact structured report to the parent |
| Hermes Bot | Reusable named specialist with a persistent profile/chat and a real capability or model boundary | Bot returns a candidate through its chat/peer surface; parent verifies it |
| Kanban | Work must persist across turns/processes, has dependencies, retries, assignments or visible status | Assigned worker returns task status and candidate artifacts; parent reviews them |

Do not create a new profile merely to express a work posture, Pantheon Role,
source family or temporary subtask. A Bot is a persistent Hermes profile; cloning
copies settings rather than creating a live shared base. If a distinct Bot is
proposed, name the concrete difference in model/provider, credentials, memory,
capability surface, data exposure or execution isolation. Keep governed tasks
inside their admitted `pantheon-governed` boundary.

Do not select a mechanism from prose alone. Confirm the active toolset, profile,
MCP bindings, effective worker limit and child timeout when the runtime exposes
them. If concurrency is unknown, assume one worker and do not claim parallel
execution. If a worker's timeout exceeds the remaining user budget, do not
delegate work required for the answer. Report the capability gap and perform the
supported portion directly.

## Plan before dispatch

Preserve the exact user request and its purpose before decomposing it. Record the
project or referent, exact source paths and versions, scope, exclusions,
completion criteria, output language and any corrections already established.
Treat a later clarification as additive unless the user changes the objective.

Split by independent evidence or expertise, not by arbitrary page count. For a
comparison, give each reader one bounded source or question. Do not ask one
child to judge another child's result. Keep one dispatch wave active by default:
check the current task ledger before dispatching, and never duplicate an
in-flight assignment. Limit the wave to the observed concurrent-worker cap. If
the task payload is rejected, correct it once against the exposed tool schema;
an error is not a dispatch. Start a later wave only after current workers return
and only for a material unresolved task that can still affect the answer. Do
not launch new work after synthesis has begun just to repeat work already
completed or pending.

Give each child the smallest sufficient toolsets and skills. Ask the child to
load relevant skills itself only when the skills tool is exposed; never claim a
skill was used without an observed load or runtime record. Do not grant broader
tools, memory, source access or authority for convenience. Do not include
private reasoning; transmit only the task frame and needed source references.

Resolve the project and source route once in the parent whenever possible. A
fuzzy project candidate with `identity_confirmed: false` is not a confirmed
project binding. Before source-specific dispatch, confirm the project against
the user context and the permitted project catalogue, then take each exact
`source_path` from that project's Vault source inventory (or an exact successful
read). Do not reconstruct a filename from memory, a document title, or a
Hindsight chunk. If the project or source is not confirmed, resolve it in the
parent or ask; do not dispatch guessed bindings.

When the parent has confirmed the project and exact source files, include the
resolver's canonical `project_ref`, each exact `source_path`, observed
title/version/date, relevant pages, and any known route constraints in the child
assignment. Tell the child to use that binding directly and skip project/source
rediscovery unless discovery itself is its assigned task. Never use a document
number, filename or display title as `project_ref` unless the resolver returned
that exact value as the project reference. If the supplied route fails, return
the exact tool error and stop source retries; do not guess a new project
reference, widen the search, or silently switch sources. The parent corrects a
failed binding and redispatches only if needed.

Bind the assignment to the relevant **internal section**, not just the file.
When a source file combines documents, sections, appendices or forms, use
Hindsight's document-structure information as a navigation lead and confirm the
boundaries from the source's own contents, headings or labels. Pass the child
the exact section and page range when known; do not ask it to read the whole
file because of the filename or container title. If the boundary is not
established, have the parent resolve it before dispatch or explicitly bound
discovery to the structural pages.

Each source-reading child returns:

```yaml
observed_facts: []
exact_sources_and_locators: []
contradictions: []
missing_or_unreadable_material: []
limits: []
```

Require no global verdict from source readers. Do not treat a Bot message, Kanban
comment, Hindsight recall, skill name or child summary as source verification.

## Keep the parent in charge of synthesis

The parent must:

1. retain the original question, requested outcome and user corrections across
   waiting, retries and context compaction;
2. wait for required work and report truthful progress without inventing a
   completion state;
3. reconcile source versions, scopes, coverage and disagreements;
4. reopen exact primary-source passages for decisive claims;
5. separate observed facts, inference, unresolved questions and missing evidence;
6. answer the original question first, then offer optional deeper work.

Do not reread every child step-by-step by default. Verify decisive passages,
unexpected claims, contradictions, calculations and items that materially change
the conclusion. If a worker failed, timed out, used the wrong source or returned
no locator, mark that contribution unverified and continue only where safe.

Treat a user deadline as a work budget: reserve time to verify and synthesize;
do not start or wait for required work that cannot reasonably return within the
remaining budget. If the runtime timeout or cancellation behavior is unknown,
do not rely on it to meet a hard deadline. If a worker is still pending at the
limit, return the supported partial result and say what remains pending. A
deadline in the prompt does not itself cancel a Hermes task. Stop a worker only
through a documented runtime action
using its exact observed identifier; if stopping fails or the identifier is
unavailable, do not guess or retry with a fabricated ID—report the worker as
still pending or stop status as unconfirmed.

## Make delegation observable without inventing activity

When the user asks to follow agents, or trace mode is active, use the display
contract in `pantheon-activity-projection` and add a compact worker ledger. For
each worker, show only details exposed by Hermes:

```text
Worker: <task label from the dispatched assignment> (<runtime ID, if shown>)
Assignment: <bounded source/task scope>
State: <exact state currently exposed by Hermes>
Last observed event: <timestamp and tool/event, only if exposed>
Return: <not yet received / received / failed, only as observed>
```

Use a task label such as `Étude de sol` and preserve the worker identifier only
when Hermes exposes it. Do not invent personal names, claim a worker is active
from elapsed time alone, or infer progress from an unchanged `last tool` field.
A plan is not a dispatch; a dispatch error is not a launched worker. Show failed
attempts and retries when they affect the user's understanding. On a long wait,
report the last visible state and say when no newer event is observable; do not
fabricate a heartbeat or ETA.

`pantheon-activity-projection` already defines opt-in trace mode and the labels
Ulysse, Nestor, Dédale and Cassandre as optional work postures. They are not
worker identities: never rename a child `Ulysse` or `Cassandre` merely to make
the agent list memorable. Show a posture only when the governed method selected
it. Show a Pantheon Role/God only when a governed result explicitly returns
that viewpoint; show a Rite only when its method was actually applied and the
runtime/owner contract supports that observation. A skill load, Hindsight
recall or tool call by itself does not prove a God or Rite was activated.

The parent remains visible as the coordinator. Keep its ledger separate from
child rows and state which decisive source checks it performed itself. Treat
worker-reported reads as reports until the parent verifies material passages.
Do not expose hidden reasoning or unbounded raw tool logs; summarize observable
events, errors, source locators and returned results.

## Verify Pantheon and Hermes capabilities by observation

Pantheon concepts are not runtime agents. Gods/Roles are standing governance
responsibilities, Mortels are work postures, Rites structure bounded review, and
governed Spaces distinguish durable activity. Hermes executes; Pantheon policy
consultation returns bounded decisions as data. A name in a prompt or answer is
not proof of activation or operation.

| Surface | What can be verified | What is not proved by that check |
|---|---|---|
| Role / “god” viewpoint | An observed route/tool call returns the exact owner/doctrine locator, and that source's responsibility/limits are reflected in the candidate with citations | A runtime agent named after the Role, authority transfer, or approval |
| Rite | The owner catalogue reports the implementation state; exercise only an implemented behavior with expected results defined by its owner contract or existing acceptance tests | That every prose Rite is executable, automatically triggered, approved or complete |
| Governed Space / “place” | Exact project/place resolution, source family, version/path, authorized read route and source locator are observed; wrong-project/missing-source cases fail closed | A new data store, project truth, evidence admission or authority from the place label |
| Skill / MCP / tool | Active profile tool inventory, skill load or authenticated catalog, and a bounded task call are observed in a fresh session | Successful professional outcome, truth, authorization, or capability beyond the tested call |
| Bot / subagent / Kanban | Actual dispatch/assignment, worker identity or profile, tool calls, completion/failure event and returned report are observed | Bot identity as a Pantheon Role, a subagent as a persistent profile, or worker agreement as proof |

Before claiming “works”, record the exact installed Hermes/profile and the
observable trace. Derive expected outputs and positive, negative or failure
controls only from the capability owner's contract, schema or existing
acceptance tests. Never invent an expected result from a narrative description.
If no observable test and expected result are defined, report `not_qualified`
or `documented_non_implemented`; do not simulate success. Check forbidden
effects only where an owner-defined observation can establish them. Use
`get_consultation_catalog` for its documented implementation-state map and the
Hermes runtime inventory for actually exposed tools. `get_capability_status`
qualifies caller-provided observations; it is not a live runtime probe.

The repository's Rite Trigger Catalogue identifies only the explicit
`tests_pass_completion` attention question as implemented in its first slice;
it says this returns attention data and does not execute a Rite. Other catalogue
signals remain candidates until separately qualified. Confirm the live
consultation/catalogue status and owner-defined test before claiming runtime
behavior. Governed Spaces are semantic distinctions, not Hermes workspaces or
automatic storage/authority domains. A source lookup/read can qualify that
specific source route; it cannot prove that every Space lifecycle works.

## Return and stop conditions

Return a concise status:

- work shapes actually used, with observed dispatch and completion state;
- each source/capability actually opened or invoked, with exact locator;
- findings, disagreements and unresolved coverage;
- elapsed time and call counts only when measured by the runtime;
- runtime or authorization gaps and the smallest next action.

Stop distributing when there are no remaining independent tasks, when
coordination cost exceeds the likely benefit, or when the task would require a
broader data/authority boundary. Never create, activate, approve, persist or
route a Bot, Role, Rite, Space or Kanban workflow merely because this Skill is
loaded.
