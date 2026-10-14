# Architecture Target Workflows

Status: candidate support document — target workflow synthesis, documented non-implemented.
Boundary profile: candidate_support_note.

This document consolidates the architecture-agency workflow examples into one target model.

It does not implement a runtime, connector, OpenWebUI action, Hermes skill, Gmail sender, Telegram listener, WhatsApp integration, form filler, image analyzer, document generator, PDF exporter or memory engine.

## Purpose

The examples show the same target pattern in professional architecture-agency situations:

1. prequalifying a transmitted document or corpus before detailed analysis;
2. preparing an authorization dossier and Cerfa;
3. analyzing an invoice or situation against CCTP and site reports;
4. reviewing a site photo before adding a point to a site report or escalating.

The common point is not automation. The common point is a governed workflow:

```text
source intake -> source qualification -> scoped context -> candidate production -> quality gates -> user questions -> human decision -> trace decision
```

## Target goals

The target workflows should serve concrete agency goals before they serve automation goals.

| Goal | What it improves | What must remain governed |
|---|---|---|
| Structure dossiers | project sources, versions, decisions, open questions | source status and memory promotion |
| Reduce avoidable errors | missing pieces, outdated documents, wrong references, inconsistent surfaces | confidence, verification and user questions |
| Make work reviewable | citations, assumptions, contradictions, candidate outputs | evidence expectations and output statuses |
| Shorten preparation time | forms, notices, drafts, comparison tables, meeting notes | external actions and final approval |
| Preserve professional responsibility | signature, visa, formal notice, deposit, transmission | human decision gate |
| Build reusable practice | templates, recurring gates, trace formats, improvement reports | candidate-only learning until validated |

The first target is not a perfect autonomous workflow. The first target is a repeatable professional path that stops at the right moments.

## Milestones

The workflow target should be developed through visible milestones. Each milestone must remain useful by itself and must not depend on hidden autonomy.

| Milestone | Name | Expected capability | Boundary |
|---|---|---|---|
| M0 | Documentation baseline | examples, D3 diagrams, target model, terms and gates | documented, non-implemented |
| M1 | Read-only dossier cockpit | display dossier sources, statuses, missing information and questions | no connector write, no sending |
| M2 | Source intake and RAG candidate | retrieve relevant chunks from selected project sources and show citations | retrieval is not proof |
| M3 | Quality gates | verify objective, source date, citation, context, mandate and confidence | stops or asks, does not decide |
| M4 | Draft candidates | prepare Cerfa, notice, CR entry, email text, visa note, photo annotation candidate | drafts only, no transmission |
| M5 | Trace decision | ask what to delete, keep, record or promote as Register Candidate | no automatic memory promotion |
| M6 | Controlled connector actions | create a draft, update a tracking row, export a PDF candidate when explicitly approved | bounded action, visible approval |
| M7 | Composed workflows | combine reusable blocks into Cerfa, invoice-visa, site-photo and future agency workflows | composition by contract, not hidden automation |

A milestone is complete only when its boundary is as visible as its capability.

## Workflow atoms

Workflows should be decomposed into small reusable atoms. A rich workflow is then a composition of atoms, not a single monolithic agent.

| Atom | Input | Output candidate | Typical reuse |
|---|---|---|---|
| Source intake | selected dossier, uploaded file, message, photo, connector item | source list with origin and scope | all workflows |
| Source qualification | source list | status, date, version, authority, contradiction | RAG, evidence, QA |
| Document intake scan | document or corpus candidate | identity, structure, authority, applicability, risk and proposed next step | document review, RAG, form filling, proof register |
| RAG retrieval | qualified sources + task | relevant excerpts with citations | Cerfa, invoice, CR, photo review |
| Context minimization | task + excerpts + sensitivity | scoped context, masked fields, exclusion list | external model calls |
| Engine routing proposal | task + sensitivity + volume | local/internal or external route candidate | confidential or large tasks |
| Candidate analysis | context pack | analysis candidate with assumptions | plan, photo, invoice, PLU, CCTP |
| Candidate generation | analysis + template | draft output | Cerfa, notice, email, CR, letter |
| Quality gate | candidate + criteria | pass, fail, questions, retry route | all consequential outputs |
| User question | failed gate or uncertainty | explicit question with options | surfaces, mandate, missing info |
| Visual recheck | PDF, plan, photo, annotated output | visual review candidate | plan review, photo, export |
| Delivery gate | candidate output + recipient/action | approval prompt and delivery status | draft, send, deposit, export |
| Trace decision | task result + user choice | no trace, short trace, register entry, Register Candidate | all workflows |
| Improvement report | failures, retries, corrections | improvement candidate | future pack refinement |

Each atom should be independently testable as a candidate behavior before being composed into longer workflows.

## Primitive workflows

Atoms become useful when they are grouped into small primitive workflows. These are still reusable and bounded, but they already express a professional behavior.

### 1. Document intake scan

A document must not move directly from transmitted to trusted. Before detailed analysis or adaptation, the system performs a short prequalification pass.

```text
document or corpus received
-> identify document type
-> read title, author, date, version and declared scope
-> inspect table of contents, headings, annexes and visible exclusions
-> classify authority and source status
-> check applicability to the dossier and task
-> flag risk of use
-> propose next step
```

Minimum output:

```text
document_id or temporary reference
document type
author / issuer
date / version / index
project or dossier scope
structure visible: title / headings / table of contents / annexes
authority class: contract / project source / official reference / technical reference / commercial / example / unknown
applicability: applicable / partial / context only / out of scope / to confirm
risk: low / medium / high
recommended next step: analyze / compare / request newer source / exclude / ask user
```

Architecture examples:

| Document | Intake question | Typical risk |
|---|---|---|
| CCTP example | Is it a project piece or a reusable example? | treating an example as contractual |
| Signed quote | Is it the latest signed version and does it match the lot? | validating a situation against the wrong amount |
| Site report | Is it the latest report and were points closed later? | reopening a resolved point or ignoring a repeated reserve |
| PLU extract | Is the source current and applicable to the parcel? | relying on an obsolete rule |
| Cerfa | Is this the correct form version for the procedure? | filling an outdated or wrong form |
| Manufacturer notice | Is this technical support or a regulatory proof? | over-weighting commercial material |
| Photo | Does metadata, date and project context fit the claimed site event? | inferring a finding from a weak visual index |

Document intake scan is an admission decision, not a full analysis. It decides whether and how the document may enter the working perimeter.

### 2. Information collection workflow

The system should not search every source blindly. It should first identify what kind of information is requested, then choose the relevant source families.

```text
user asks for information
-> classify information type
-> select source families
-> retrieve candidates
-> qualify source status
-> detect conflict or missing value
-> ask user if needed
-> return information candidate with source and confidence
```

| Information type | Preferred source families | Typical question if uncertain |
|---|---|---|
| Client identity / contact | contacts, signed documents, project register, emails | two addresses found — which one is authoritative for this form? |
| Project address / parcel | project folder, cadastre, Géoportail, existing forms | parcel reference missing or inconsistent — confirm before use? |
| Regulatory rule | PLU, official portal, saved regulation, dated web citation | source date uncertain — check latest rule before relying on it? |
| Surface / quantity | plans, schedules, prior calculations, measured candidate | plan label and calculation differ — which value should be retained? |
| Contractual amount | contract, signed quote, invoice, amendment, situation | invoice amount differs from signed quote — is there an amendment? |
| Site progress | latest CR, photos, site notes, schedule | photo suggests progress but CR says pending — request confirmation? |
| Decision / approval | emails, CR decisions, signed documents, validated memory | found as draft only — should not be treated as approved? |
| Transmission date | email, register, Notion, spreadsheet, agenda | should this date be recorded as prepared, sent or received? |

Output should be explicit:

```text
value candidate
source used
source status
confidence
contradictions
question if needed
allowed reuse scope
```

### 3. Form filling workflow

Form filling is not one operation. It is a controlled sequence of field classification, source mapping, candidate fill and review comments.

```text
select form
-> identify form version and required fields
-> classify each field
-> map each field to possible sources
-> retrieve value candidates
-> fill certain fields
-> comment uncertain fields
-> list missing information
-> visual recheck
-> user review gate
```

| Field status | What the system may do | What must remain visible |
|---|---|---|
| Certain | fill the field and cite source | source and date |
| Likely | fill with comment or warning | confidence and assumption |
| Conflicting | do not choose silently | competing values and user question |
| Missing | leave blank or placeholder | requested information |
| Consequential | require explicit review | approval level and risk |
| External-action field | prepare only | no filing or submission without gate |

A form candidate should contain comments, not only values.

Examples:

```text
Field: applicant address
Value candidate: [address]
Source: Google Contacts / signed mission letter
Status: conflicting values found
Comment: confirm whether personal address or billing address must be used.
```

```text
Field: surface created
Value candidate: 52 m²
Source: measured from plan A102
Status: to verify
Comment: plan title block indicates 48 m². Difference may come from wall thickness or outdated label.
```

### 4. Comment and annotation workflow

When the output is a plan, form, PDF or photo, comments should be treated as first-class outputs.

```text
candidate output
-> identify uncertain zones
-> attach comments to fields, pages, plan zones or photo areas
-> classify comments by severity
-> ask targeted questions
-> update candidate after user response
```

| Comment type | Example | Target |
|---|---|---|
| Missing | no notice found | dossier checklist |
| Contradiction | CR says done, photo shows unresolved | CR / photo / lot |
| Measurement doubt | image-based measure uncertain | plan or photo annotation |
| Source warning | PLU date uncertain | source list |
| Legal / contractual caution | visa may engage agency | email / note / form |
| Style / method | wording not aligned with agency | draft text |

Comments are not noise. They are the review interface.

## Composition rules

Composable workflows need strict composition rules.

```text
A workflow atom may consume only the candidate output of the previous atom.
A workflow atom may not silently promote a candidate to proof, memory or action.
A workflow atom may call another atom only through the shared envelope.
A workflow atom must expose its failure state and retry target.
A workflow composition must show every consequential gate.
```

The composition model is therefore:

```text
Task Contract
-> atom
-> Result Candidate + Evidence Pack Candidate
-> gate or next atom
```

A workflow may be long, but every step must remain inspectable.

## Target pattern

A workflow is not a single prompt. It is a dossier path.

```text
User request
-> intake of authorized sources
-> document intake scan / source qualification
-> RAG / source retrieval and qualification
-> pre-transmission minimization
-> engine routing: local/internal or external
-> candidate analysis
-> candidate production
-> quality gate
-> feedback / user questions / retry
-> reintegration inside the agency perimeter
-> deliverable preparation through templates
-> final visual and contextual review
-> user decision gate
-> trace / memory decision
```

## Placement

| Layer | Role in the workflow | Must not become |
|---|---|---|
| OpenWebUI | Interface, cockpit, selection, warning, status display, decision capture, review surface | source of truth, autonomous approval surface, hidden workflow runner |
| Hermes Agent | Execution runtime, source retrieval, extraction, analysis, conversion, drafting, image review, candidate production | approval authority, canonical memory, professional decision-maker |
| Pantheon Next | Rules, statuses, gates, evidence expectations, memory boundaries, scope and responsibility | runtime, scheduler, queue, provider router, connector platform |

## OpenWebUI as cockpit

OpenWebUI is the visible workbench.

It may expose:

- the current dossier;
- the selected project;
- the active task contract;
- source lists;
- status labels;
- missing information;
- questions to the user;
- candidate outputs;
- evidence packs;
- approval gates;
- memory decisions;
- action buttons such as prepare draft, request more evidence, revise, approve, reject.

It should not hide consequential decisions inside a chat flow.

## Hermes Agent as execution workshop

Hermes Agent is the place where work happens.

It may execute or delegate:

- document search;
- document intake scan;
- RAG retrieval;
- source audit;
- OCR or document extraction;
- form prefilling;
- text drafting;
- email draft preparation;
- PDF preparation;
- image analysis;
- photo annotation;
- transcription;
- meeting note preparation;
- plan review assistance;
- data export;
- connector calls;
- evidence pack candidate preparation.

Hermes returns candidates. It does not approve, sign, send, deposit, canonize or decide.

## Candidate connectors and surfaces

These are candidate connection surfaces, not commitments and not implemented by this document.

| Family | Examples | Typical use |
|---|---|---|
| Documents | Google Docs, Word, PDF, Markdown, templates | notices, letters, forms, reports, relecture |
| Spreadsheets | Google Sheets, Excel | project registers, dates, follow-up tables, quantities |
| Messaging | Gmail, Telegram, WhatsApp | incoming photos, email drafts, project exchanges |
| Project knowledge | Notion, project-platform, project folders, memory candidates | dossier context, project notes, validated traces |
| Calendar | Google Calendar, agenda tools | meetings, site visits, transmission dates |
| Visual and media | Canvas, image generation, ComfyUI, image analysis | annotated photos, diagrams, visual explanations |
| Audio | recording, transcription, meeting minutes | site meeting transcription, CR preparation |
| External references | cadastre, PLU, Géoportail, official forms, APIs, web sources | regulatory context, source verification, Cerfa versioning |

A connector being technically available does not make it authorized. Authorization depends on scope, source policy, risk, approval level and memory rule.

## Candidate skills and tools

Candidate skills and tools should be declared through the module envelope, not hardcoded as doctrine.

Examples:

- source intake;
- document intake scan;
- source audit;
- RAG retrieval;
- citation verification;
- pre-transmission minimization;
- anonymization and pseudonymization;
- local/external engine routing proposal;
- image description;
- plan reading and annotation;
- surface calculation candidate;
- photo risk review;
- CCTP / CR / invoice comparison;
- form prefilling;
- notice drafting;
- email draft preparation;
- PDF export;
- visual recheck;
- trace registration candidate;
- memory candidate preparation.

Every skill returns:

```text
Task Contract in
-> execution
-> Result Candidate + Evidence Pack Candidate out
```

## Quality gates

A target workflow must stop or loop back if one of these checks fails:

- objective not reached;
- source missing;
- citation not verified;
- source date or version uncertain;
- source intake scan missing for a transmitted corpus;
- document authority or applicability unresolved;
- RAG context incomplete;
- legal, contractual or regulatory consistency uncertain;
- calculation confidence too low;
- image measurement uncertain;
- plan legend inconsistent;
- project context mismatch;
- scope or mandate unclear;
- output vocabulary not aligned with the agency method;
- deliverable status unclear;
- external action not approved;
- memory destination not decided.

## Feedback loops

The target model requires visible return paths:

```text
quality gate -> source intake scan
quality gate -> RAG / source retrieval
quality gate -> analysis
quality gate -> generation
quality gate -> user question
confidence too low -> source request
citation failed -> source verification
document applicability unclear -> user question or source exclusion
image uncertainty -> site verification or photo request
mandate unclear -> user decision gate
external action requested -> approval gate
memory unclear -> trace decision gate
```

A retry is not failure. In a professional workflow, looping back is part of dossier discipline.

## Trace and memory decision

At the end of a task, the system must ask what remains.

Options:

- delete or do not retain the discussion;
- keep a short trace only;
- record a date of transmission;
- register the action in Notion;
- register the action in a spreadsheet;
- create a note in the selected project tool;
- create a Register Candidate scoped to the dossier;
- create an improvement report candidate.

Nothing becomes canonical memory without validation.

## Example workflows

| Example | Document | D3 prototype | Main lesson |
|---|---|---|---|
| Cerfa and authorization dossier | `docs/examples/architecture_cerfa_workflow/README.md` | planned, not included in this PR | RAG, minimization, local/external engine choice, QA, templates and trace |
| Invoice / situation and visa risk | `docs/examples/architecture_invoice_visa_workflow/README.md` | `docs/assets/pantheon-workflows/architecture_invoice_visa_spine_d3.html` | Distinguish simple transmission, advice, visa and signature |
| Site photo review and escalation | `docs/examples/architecture_site_photo_review_workflow/README.md` | `docs/assets/pantheon-workflows/architecture_site_photo_review_spine_d3.html` | An image is an index, not an automatic finding |

## Boundary

These workflows describe a target operating model. They are not implemented.

They may guide future OpenWebUI templates, Hermes skills, connector manifests, example task contracts and D3 visualizations.

They do not authorize any tool to send, sign, file, deposit, approve, remember or act externally without explicit user decision.

```text
The database records.
The workflow proposes.
The evidence supports.
The approval validates.
The human decides.
```