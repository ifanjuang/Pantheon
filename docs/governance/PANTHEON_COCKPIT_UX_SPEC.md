# Pantheon Cockpit UX Specification

Status: candidate — to verify.
Boundary profile: candidate_support_note.

This document is a product and governance UX candidate for the future Pantheon-facing cockpit, discussion surface and drafting surface.

It does not implement a UI, runtime, chat engine, editor, plugin, bridge, provider router, scheduler, queue, approval engine, memory engine, OpenWebUI Function, Hermes skill, Google Apps Script, Office add-in or external connector.

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

This specification defines what a professional user should see, decide and understand at consequential decision points. It does not decide, execute, approve, send, remember or validate by itself.

## Purpose

Pantheon needs a daily professional cockpit that can be used by non-technical practitioners without hiding governance-critical boundaries.

The cockpit should make common professional work easy:

```text
answer a sensitive email;
review a contractor document;
prepare a regulated response;
work on a project dossier;
edit a draft;
ask for more evidence;
accept, revise or refuse a proposed workflow;
record what was decided and why.
```

The cockpit must not become a clone of a generic chat UI. It should keep the convenience of hierarchical conversation and drafting assistance while making source status, mission limits, evidence expectations and human decisions visible.

## Boundary

The cockpit is an exposure and decision-capture surface.

Allowed posture:

```text
show;
select;
warn;
label;
compare;
request revision;
request more evidence;
display source state;
display Evidence Pack Candidate state;
display Workflow Proposal state;
capture explicit human decision;
prepare a governed handoff for an external execution runtime.
```

Forbidden posture:

```text
approve automatically;
validate a professional conclusion;
turn a draft into a deliverable without a human gate;
promote memory automatically;
create a Registre Probatoire entry by itself;
send or file externally by itself;
execute tools by itself;
become the runtime or provider router;
hide missing evidence behind a fluent answer.
```

The cockpit may display buttons that request execution, but those buttons must be framed as decision capture or handoff preparation, not as Pantheon-owned execution.

## User modes

The cockpit should expose two levels.

### Cabinet mode

Default mode for practitioners and collaborators.

Visible concepts:

```text
project;
request;
mail;
document;
workflow proposal;
risk;
mission scope;
sources;
missing evidence;
decision;
draft;
proof trail;
cost;
system health.
```

Hidden unless needed:

```text
runtime;
provider;
API key;
vector database;
logs;
model route;
module manifest;
plugin type;
healthcheck details.
```

### Technical administration mode

Restricted mode for administrators or developers.

Visible concepts:

```text
services;
modules;
connectors;
providers;
local models;
external models;
logs;
configuration;
healthchecks;
capability gaps;
usage metrics.
```

Technical mode must not bypass governance. A configured connector is not an authorized action. An installed module is not an approved capability.

## Main navigation

Recommended primary navigation:

```text
Home
Projects
Requests to process
Discussion
Assisted drafting
Documents
Workflows
Proofs and sources
AI costs
System health
Technical administration
```

Avoid making the main navigation tool-first:

```text
Models
Providers
Runtime
Database
Plugins
Logs
```

Tools are implementation details. The professional user should begin from a situation, not from a module.

## Professional request lifecycle

A request should move through visible states.

```text
received
intake required
workflow proposed
sources pending
human decision required
accepted
revision requested
refused
candidate produced
deliverable prepared
external action pending
archived
```

A consequential request must not jump directly from received to deliverable.

## Workflow Proposal

Before sensitive work, the cockpit should display a Workflow Proposal.

Minimum fields:

```text
request summary;
project or dossier scope;
professional domain;
mission phase or scope signal;
consequence level;
risk triggers;
documents used;
documents absent;
source tensions;
proposed steps;
expected Result Candidate;
expected Evidence Pack Candidate;
required human decision;
forbidden effects;
external action status;
memory status.
```

The proposal is not execution. It is the reviewable plan a human can accept, revise, expand or refuse.

Recommended decision buttons, left to right:

```text
View sources
Research further
Edit / comment
Request change
Refuse
Accept
```

Recommended colors:

```text
gray   = view / neutral / archive;
blue   = research further / develop;
orange = edit / comment / reorganize;
yellow = request change;
red    = refuse;
green  = accept.
```

The green button is the most consequential. It should appear after source review and revision options, not before them.

## Hierarchical discussion

Pantheon should support a hierarchical discussion surface inspired by branching chat interfaces, but governed by project, mission, evidence and decision status.

A conversation is not only a transcript. It is a tree of professional alternatives.

Example:

```text
Project conversation
├─ Branch A: cautious client response
│  ├─ shorter version
│  ├─ firmer version
│  └─ version with mission-limit reservation
├─ Branch B: proposed additional service / amendment
└─ Branch C: regulatory research before response
```

Visible branch actions:

```text
create a variant;
compare versions;
return here;
mark as retained;
set aside;
archive;
create proof trail;
link to draft;
link to sources.
```

A branch should expose at least:

```text
branch title;
created from;
current status;
risk level;
project scope;
mission scope;
source status;
retained output, if any;
linked Evidence Pack Candidate, if any.
```

A discarded branch must remain distinguishable from a retained branch. The system must not silently blend refused hypotheses into later answers.

## Drafting surface

Pantheon should include an assisted drafting surface distinct from the discussion surface.

The drafting surface supports professional editing over a selected passage, paragraph, section or full document.

Typical user actions:

```text
clarify;
shorten;
develop;
rephrase;
make firmer;
make more diplomatic;
add a reservation;
secure liability wording;
add sources;
turn into an email;
turn into a CCTP clause;
turn into a client-facing explanation;
turn into an insurer-facing chronology;
create proof trail.
```

The drafting surface must show the scope of the edit:

```text
whole document;
section;
paragraph;
sentence;
selected term.
```

It must avoid unrequested full rewrites when the user selected only a narrow passage.

## Draft Anchor

A Draft Anchor links a selected text fragment to the discussion, sources and decision state that produced or modified it.

Candidate shape:

```text
draft_anchor:
  anchor_id:
  document_ref:
  selected_text:
  selection_scope: document | section | paragraph | sentence | term
  linked_project:
  linked_conversation_node:
  linked_branch:
  linked_workflow_proposal:
  linked_evidence_pack_candidate:
  proposed_replacement:
  user_decision: accepted | revised | refused | pending
  created_at:
```

The Draft Anchor is a traceable relation. It is not memory promotion and not proof by itself.

## Proofs and sources

The user-facing label should be:

```text
Proofs and sources
```

French UI label:

```text
Preuves & sources
```

Avoid using `Evidences` as the French interface label. It is ambiguous in French. The technical object may remain `Evidence Pack Candidate`.

The panel should show:

```text
documents used;
documents referenced but absent;
source type;
authority class;
date;
version;
validity signal;
precise excerpts;
citations;
assumptions;
unknowns;
contradictions;
confidence signal;
review angles;
missing evidence;
required human decision.
```

The panel must separate retrieved material from validated evidence. A retrieved source remains a candidate until reviewed.

## Capability Gap

When the cockpit cannot safely prepare a workflow, answer or handoff, it should display a Capability Gap instead of improvising.

Typical gaps:

```text
source absent;
recipient unconfirmed;
approval missing;
runtime unavailable;
connector not authorized;
write scope forbidden;
mission scope unknown;
evidence expectation unmet;
external action ambiguous;
idempotency key missing.
```

Minimum displayed fields:

```text
what is missing;
why it matters;
what would go wrong if ignored;
safe fallback;
required user or admin action;
status: blocked | degraded | to configure.
```

A gap is preferable to a fabricated answer, silent downgrade or unauthorized action.

## System health

Cabinet mode should show health in professional terms:

```text
Everything works;
Some functions are limited;
Action required.
```

Detailed technical health can appear on expansion:

```text
Document analysis: OK;
Web research: OK;
Local AI: limited;
External AI: OK;
Proof trail: OK;
Notion connector: reconnect required;
execution runtime: degraded.
```

Core services should not expose destructive actions in cabinet mode.

Allowed cabinet actions:

```text
open UI;
configure;
check health;
view logs;
repair;
install when missing.
```

Avoid:

```text
delete;
force enable;
trust source;
auto-approve;
promote memory.
```

## Local AI and external AI

The cockpit may group AI capacity into professional categories.

```text
Local AI
├─ office workstation
├─ server or NAS
├─ collaborator workstation
├─ local models
└─ hardware availability

External AI
├─ provider status
├─ daily tokens
├─ monthly tokens
├─ daily cost
├─ monthly cost
├─ project cost
└─ quota / limit state
```

Cabinet mode should prioritize costs by project and function. Tokens may remain a detail view.

Example:

```text
Today: 3.42 EUR;
Project ROSERAIE: 0.84 EUR;
PDF analysis: 0.62 EUR;
email drafting: 0.18 EUR;
regulatory research: 0.31 EUR.
```

## Google Docs, Google Sheets and Office projections

Future document integrations should be projections of the same governed drafting model.

For a Google Docs or Google Sheets projection, the tool may:

```text
read the user-selected text or range;
ask Pantheon for a Workflow Proposal or drafting candidate;
show the proposed replacement;
insert only after explicit user acceptance;
record a Draft Anchor candidate;
link back to sources and project scope.
```

It must not:

```text
rewrite a document silently;
insert consequential wording without user acceptance;
send a document externally;
promote the selected content to memory;
turn a draft into proof.
```

Office add-ins should follow the same model later. They should not define separate governance rules.

## Suggested implementation phases

This section is planning guidance, not implementation authorization.

### Phase 0 — doctrine and mockups

Allowed:

```text
UX specification;
non-executable HTML mockups;
fictional examples;
AI logs;
Notion tracking.
```

### Phase 1 — discussion and decision mock

Candidate surface:

```text
conversation tree mock;
branch status mock;
Workflow Proposal card;
Proofs and sources panel;
manual decision buttons.
```

### Phase 2 — assisted drafting mock

Candidate surface:

```text
selected text panel;
Draft Anchor candidate;
replacement proposal;
accept / revise / refuse;
version comparison.
```

### Phase 3 — external projections

Candidate integrations:

```text
Google Docs Apps Script;
Google Sheets Apps Script;
Office add-in;
connector bridge.
```

Each projection must remain bounded by the same decision, source, approval, memory and external-action rules.

## UX microcopy rules

Avoid labels that imply automatic truth or approval:

```text
validated;
approved;
trusted;
proof created;
memory saved;
sent;
executed;
source accepted.
```

Prefer:

```text
candidate;
to verify;
prepared;
proposed;
retained draft;
human decision required;
source cited;
source missing;
proof trail candidate;
ready for review.
```

Dangerous professional wording should trigger warnings, especially in architecture, construction and regulated contexts:

```text
I validate;
this is compliant;
you may execute;
we guarantee;
our fault;
we should have;
at our charge;
confirmed technically;
approved for execution.
```

Suggested safe pattern:

```text
Our review concerns only the architectural coherence of the proposed principle, subject to the technical justifications to be produced by the contractor or its qualified technical advisor.
```

## Decision summary

Accepted as candidate orientation:

```text
Pantheon should expose a governed professional discussion surface;
Pantheon should support conversation branching;
Pantheon should support assisted drafting over selected text;
Proofs and sources should be visible and distinct from final proof;
workflow proposals should precede sensitive action;
human decisions should be explicit and captured.
```

Rejected:

```text
Pantheon as OpenWebUI clone;
Pantheon as runtime;
Pantheon as automatic approval engine;
Pantheon as automatic memory engine;
Pantheon as source-of-truth for retrieved but unreviewed material.
```

To verify:

```text
exact placement of the cockpit surface;
relationship to OpenWebUI once the cockpit matures;
choice of internal editor;
Google Docs / Sheets projection scope;
Office projection scope;
Notion tracking shape;
UI wording in French and English.
```

## Final rule

```text
The cockpit helps the professional see, branch, draft, verify and decide.
The runtime carries the work.
The validated remains.
```
