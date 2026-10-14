# Markdown Dossier Workflow

Status: to verify — active governance proposal, documented, not implemented.
Boundary profile: candidate_support_note.

This document defines a governed workflow for producing professional dossiers progressively in Markdown.

It does not define a Pantheon editor runtime, hidden workflow runner, scheduler, queue, provider router, automatic memory system, OpenWebUI plugin implementation or Hermes tool implementation.

## Purpose

Professional dossier production is not a one-shot AI answer.

A professional often needs to build a document over time:

- draft a section;
- add source notes;
- mark unsupported claims;
- ask questions inside the document;
- request variants for one paragraph;
- deepen a specific point;
- verify that a local change remains coherent with the whole dossier;
- update the table of contents, introduction, diagrams, conclusion and source list;
- preserve versions and review history.

The purpose of this workflow is to make that process governable.

The target is not a smarter chat response.

The target is a professional document that can be reviewed, sourced, corrected, versioned, validated and, when appropriate, linked to memory candidates.

## Product promise

```text
Work on a professional document progressively.
Select a paragraph, section, table or diagram.
Ask for a variant, source check, deeper explanation or rewrite.
Keep comments, questions, assumptions and missing evidence visible.
After each meaningful modification, verify coherence across the whole dossier.
Version the update.
Validate what may be delivered.
Decide separately what may remain as memory.
```

## User-facing vocabulary

The user-facing layer should avoid technical platform vocabulary where possible.

Preferred public vocabulary:

```text
Dossier
Source
Question
Hypothèse
Contradiction
Preuve
Variante
Livrable
Validation
Mémoire
Version
```

Technical vocabulary may remain in governance documentation:

```text
Task Contract
Evidence Pack
Register Candidate
Registre Probatoire entry
Context Pack
Run Trace View
Approval Level
```

## Scope

This workflow applies to professional Markdown dossiers such as:

- notes;
- reports;
- summaries;
- correspondence drafts;
- technical memoranda;
- legal or administrative notes;
- contradiction reports;
- quote analyses;
- meeting synthesis;
- source-backed research notes;
- deliverable preparation files.

The Markdown dossier is a working surface.

It is not a Registre Probatoire entry by itself.

It is not an Evidence Pack by itself.

It may contain Evidence Pack references, source notes, open questions, assumptions, contradictions, validation markers and memory proposals.

## Non-goals

This document must not be interpreted as authorizing:

- a Pantheon Markdown editor runtime;
- hidden autonomous document rewriting;
- automatic document updates without review;
- automatic source validation;
- automatic memory promotion;
- automatic skill installation;
- provider routing;
- scheduler or queue;
- hidden multi-agent orchestration;
- OpenWebUI becoming a Registre Probatoire entry;
- Hermes approving its own work;
- Pantheon becoming the execution layer.

## Dossier structure

A governed Markdown dossier may include:

```md
# Dossier title

## Status

## Summary

## User request

## Scope

## Sources

## Open questions

## Assumptions

## Contradictions

## Analysis

## Proposed deliverable

## Evidence notes

## Validation checklist

## Version history

## Memory proposals
```

The exact structure may vary by dossier type.

The governing principle is stable: the document should distinguish the content being produced from its sources, assumptions, uncertainties, evidence, validation state and memory proposals.

## Inline governance comments

Inline comments may be used to keep governance information close to the relevant passage.

These comments are annotations.

They are not executable instructions.

Possible marker style:

```md
<!-- pantheon:source-needed claim="..." -->
<!-- pantheon:citation-needed -->
<!-- pantheon:question target="user" -->Quel niveau de détail faut-il pour cette partie ?<!-- /pantheon:question -->
<!-- pantheon:assumption -->Hypothèse à vérifier avant livraison.<!-- /pantheon:assumption -->
<!-- pantheon:contradiction source_a="..." source_b="..." -->
<!-- pantheon:variant request="more concise" scope="section" -->
<!-- pantheon:coherence-risk -->Cette section peut contredire l'introduction.<!-- /pantheon:coherence-risk -->
<!-- pantheon:validation-required level="C2" -->
<!-- pantheon:memory-candidate scope="project" -->
```

Alternative syntaxes may be considered later:

- YAML front matter;
- blockquote callouts;
- footnote-style markers;
- sidecar JSON/YAML files;
- OpenWebUI note metadata;
- Evidence Pack references.

Any syntax must preserve readability and avoid turning comments into hidden execution commands.

## Annotation vocabulary

Recommended annotation types:

| Annotation | Meaning |
|---|---|
| `source-needed` | A claim requires a source before delivery. |
| `citation-needed` | A source exists or is expected, but the citation must be added. |
| `unsupported-claim` | A claim currently lacks support. |
| `assumption` | A working hypothesis, not validated fact. |
| `contradiction` | Two sources, passages or claims conflict. |
| `question` | A question to the user, source, reviewer or future workflow. |
| `deepen` | A point should be expanded or explained. |
| `variant` | A localized alternative is requested. |
| `coherence-risk` | A local change may affect the global document. |
| `validation-required` | The passage requires an approval threshold before use. |
| `memory-candidate` | A possible durable fact is proposed for later review. |
| `rejected` | A passage or claim was considered but rejected. |
| `resolved` | A previous issue was addressed. |

## Selected-zone operation model

The user should be able to work on a selected zone rather than regenerate the whole document.

Allowed selection scopes:

- sentence;
- paragraph;
- heading block;
- section;
- table;
- list;
- diagram description;
- annex;
- introduction;
- conclusion;
- full dossier.

Candidate operations:

| Operation | Expected result |
|---|---|
| Rewrite | Revised text candidate. |
| Simplify | More accessible wording. |
| Professionalize | More formal or métier-appropriate language. |
| Expand | More developed explanation. |
| Shorten | More concise version. |
| Add citations | Citation or source-note candidate. |
| Explain | Clarification without necessarily rewriting. |
| Variant A/B | Multiple alternatives with trade-offs. |
| Deepen | Focused development of one point. |
| Extract missing information | List of missing facts or documents. |
| List contradictions | Contradiction candidates. |
| Transform into table | Table candidate. |
| Prepare diagram | Diagram structure or Mermaid/text candidate. |
| Align tone | Adapt to recipient, use case or dossier style. |
| Coherence review | Impact analysis against the rest of the dossier. |

Each operation should return a candidate, not silently overwrite validated content.

## Coherence review

After a meaningful edit, a coherence review should verify whether the local change affects the whole dossier.

The review may be performed by an external execution layer under Pantheon governance.

It should check:

- table of contents;
- introduction;
- section order;
- definitions;
- repeated claims;
- contradictions;
- unsupported claims;
- citation consistency;
- source status;
- diagram consistency;
- conclusion alignment;
- terminology consistency;
- scope drift;
- tone drift;
- deliverable readiness;
- whether the edited zone contradicts another part of the dossier.

The coherence review should produce a candidate report.

It must not approve the dossier by itself.

## Update proposal model

The system may propose related updates after a local edit.

Possible update candidates:

- summary update;
- introduction update;
- table of contents update;
- section title update;
- cross-reference update;
- diagram update;
- conclusion update;
- source list update;
- evidence note update;
- open question update;
- validation checklist update;
- memory proposal update.

These updates remain candidates until accepted where approval is required.

## Versioning expectations

Every meaningful dossier update should be versionable.

A version record should preserve:

- previous version reference;
- edited scope;
- requested action;
- source changes;
- assumptions added or removed;
- contradictions added, preserved or resolved;
- validation status;
- reviewer notes;
- reason for update;
- whether memory was proposed;
- whether any delivery-relevant output changed.

Possible statuses:

```text
draft
candidate_update
under_review
accepted
rejected
superseded
validated
archived
```

A minimal Markdown version record may look like:

```md
## Version history

### v0.3 — candidate_update

- Edited scope: `## Analysis / Ventilation`
- Requested action: deepen and add source notes
- Sources changed: added `source_ref: dtu-ventilation-note`
- Assumptions added: one
- Contradictions resolved: none
- Coherence review: introduction and conclusion may need update
- Validation: pending
```

## Evidence linkage

When a passage relies on sources, the document should distinguish:

```text
source cited
source missing
source weak
source contradicted
claim unsupported
assumption only
validated evidence
```

A source note may point to:

- a source reference;
- an Evidence Pack item;
- a document section;
- a quote excerpt;
- a page or paragraph;
- an external URL reference;
- a user-provided file;
- a retrieved source candidate.

A source note does not automatically validate the claim.

Evidence remains selected support for a claim or output, not generic context.

## OpenWebUI mapping

OpenWebUI may expose the cockpit for this workflow.

Potential OpenWebUI responsibilities:

- Markdown or rich text document view;
- selected text or section;
- note-focused chat sidebar;
- action buttons such as `Variant`, `Source check`, `Deepen`, `Coherence review`;
- inline comments or visible annotations;
- user questions;
- proposed edits;
- diff preview;
- approval prompts;
- source and Evidence Pack display;
- export to `.md`, `.txt` or `.pdf`.

OpenWebUI may already provide useful surfaces such as Notes, selected-text enhancement, note-context injection, action functions and native tools.

These surfaces remain cockpit capabilities.

OpenWebUI does not become:

- a Registre Probatoire entry;
- source of truth;
- approval authority;
- execution doctrine;
- hidden runtime.

## Hermes Agent mapping

Hermes Agent may execute technical operations under Task Contract.

Potential Hermes responsibilities:

- selected-zone rewrite;
- variant generation;
- source retrieval;
- citation audit;
- contradiction extraction;
- coherence review;
- Markdown patch candidate;
- diagram candidate;
- version note candidate;
- source list update candidate;
- memory candidate proposal when allowed.

Hermes returns candidates and evidence.

Hermes does not:

- approve the dossier;
- canonize memory;
- silently update validated content;
- bypass approvals;
- become Pantheon doctrine.

## Pantheon responsibility

Pantheon governs:

- allowed annotation vocabulary;
- source and citation discipline;
- claim status vocabulary;
- selected-zone scope rules;
- coherence review requirements;
- approval thresholds;
- versioning expectations;
- memory proposal rules;
- evidence linkage rules;
- non-goals and anti-runtime guardrails.

Pantheon does not execute the edit.

Pantheon defines what makes the edit governable.

## Candidate workflow

```text
1. User opens or creates a Markdown dossier.
2. User selects a zone.
3. User requests rewrite, variant, source check, expansion, diagram or explanation.
4. The task is framed with scope and constraints.
5. External execution proposes a modification.
6. Coherence review checks impact on the whole dossier.
7. The system proposes related updates: summary, intro, diagram, TOC, conclusion, source list.
8. User accepts, rejects or asks for revision.
9. Version record is created.
10. Register Candidate is proposed only if explicitly allowed.
```

## Approval guidance

Approval mapping must remain consistent with `APPROVALS.md`.

General guidance:

| Situation | Expected posture |
|---|---|
| Local wording improvement | Low approval threshold if no meaning changes. |
| Source or citation addition | Review source quality and relevance. |
| New claim | Mark unsupported until sourced or accepted as assumption. |
| Contradiction resolution | Require explicit review. |
| Deliverable-ready section | Require user-facing validation. |
| External transmission | Requires higher approval. |
| Memory proposal | Requires memory-specific review and scope. |
| a Registre Probatoire entry | Requires explicit approval and evidence linkage. |

## First prototype acceptance criteria

A first proof of concept should demonstrate:

- one Markdown dossier;
- selected-zone edit;
- inline governance comment;
- source-needed marker;
- question-to-user marker;
- variant generation for one section;
- coherence review against the whole document;
- update proposal for summary or introduction;
- version record;
- no automatic Registre Probatoire promotion;
- no hidden autonomous workflow.

## Risks

| Risk | Guardrail |
|---|---|
| The editor becomes a runtime. | Keep execution in OpenWebUI/Hermes or external tools, not Pantheon. |
| Comments become hidden instructions. | Treat annotations as governance metadata, not commands. |
| AI overwrites validated content. | Require diff preview and approval where needed. |
| Memory is silently updated. | Use Register Candidate workflow only. |
| Source notes are mistaken for proof. | Keep source, evidence and validation distinct. |
| Coherence review is mistaken for approval. | Review output remains candidate until human validation. |
| OpenWebUI Notes become source of truth. | Notes are cockpit/workspace content, not a Registre Probatoire entry. |
| Hermes self-approves edits. | Hermes returns candidates only. |

## Status

Documented governance proposal.

Implementation not started.

Runtime integration not implemented.

OpenWebUI mapping to verify before implementation.

Hermes mapping to verify before implementation.

Schema impact not assessed.

Tests not implemented.
