# Terminology Boundaries

Status: active support doctrine — controlled vocabulary, reserved terms and migration guidance.

This document defines the preferred Pantheon Next vocabulary for future development and progressive cleanup of existing documents.

It does not rename schemas, tests, runtime objects, APIs, tool contracts, database fields, files, folders or external product concepts by itself.

It does not implement a runtime, workflow engine, scheduler, approval engine, memory engine, connector gateway, plugin manager, schema migration, automatic terminology linter, competence engine, skill generator or documentation-ingestion pipeline.

```text
Optional compatible runtime client       -> runtime interaction
Hermes Agent                             -> external execution runtime
Runtime adapter / Hermes                 -> PEP for consequential effects
Pantheon Cockpit                         -> governed Cards, status, Evidence gaps and decisions
Pantheon policy service                  -> bounded deterministic PDP interface
Pantheon Next                            -> governance, authority and PDP semantics
Human                                    -> consequential decision when required
```

## Purpose

Pantheon Next must avoid terms that make governance look like execution, runtime state, automatic validation or generic memory.

A term is acceptable only if its layer is clear:

```text
Pantheon governs status, scope, evidence, approval, memory and external-action legitimacy.
The execution runtime executes workflows, skills, tools, jobs and actions.
The exposure surface exposes, captures and displays.
The professional decides.
```

This document is a vocabulary boundary. It is not a dictionary of every word in the repository.

## Canonical grammar

Use short object names plus explicit status rather than long compound nouns.

Preferred shape:

```text
Object · status
```

Examples:

```text
Assertion · proposed
Assertion · sourced
Evidence · candidate
Evidence · contradicted
Register · validated
Recall · stale
Capability · suspended
Competence · candidate
```

Avoid silently changing the noun to imply authority.

```text
candidate output ≠ deliverable
retrieved source ≠ evidence
runtime memory ≠ Register
workflow run ≠ approval
trace ≠ proof
competence available ≠ action authorized
skill executed ≠ Pantheon validated
```

## Core Pantheon vocabulary

| Term | French | Layer | Meaning | Must not become |
|---|---|---|---|---|
| Case | Affaire | professional unit | The professional unit under review. In architecture, a Project is a subtype of Case. | folder, corpus, file directory |
| Project | Projet | professional subtype | Architecture or construction case subtype. | generic system project |
| Situation | Situation | professional trigger | A concrete question, tension, event or request inside a Case. | workflow, action |
| Method | Méthode | professional frame | The governed professional method for a domain. | runtime workflow, professional authority by itself |
| Approach | Démarche | governed reusable path | A reusable governed way to handle a recurring Situation. | executable workflow |
| Contract | Contrat | governance boundary | The bounded mission frame for a request: intent, scope, allowed outputs, forbidden effects and approval expectations. | legal client contract, runtime task |
| Scope | Périmètre | boundary | What is in, out, uncertain or forbidden. | broad context |
| Corpus | Corpus | document set | The document set mobilized for a Situation. | Case, Register, folder |
| Source | Source | input material | A document, excerpt, email, rule, plan, image, record or retrieved item. | evidence by itself |
| Connaissance | Knowledge | métier / dossier content | Professional, regulatory, contractual, project or dossier knowledge that informs a decision or supplies what to use. | skill, guide, tool, template, proof by itself |
| Context | Contexte | minimized transmission | The minimum necessary material sent to an AI/runtime for a task. | complete Corpus, memory |
| Capability | Capacité | abstract governable function | A governable effect class such as read, extract, classify, compare, draft, annotate or transmit. | Hermes Skill, host Plugin, approved Competence |
| Competence | Compétence | governed reusable ability | A bounded reusable ability to do something using guides, resources, templates, tools and task constraints. | runtime skill, professional authority, approval |
| Guide | Guide de compétence | competence method support | A method document explaining how a Competence is learned or applied. | Connaissance, Evidence, runtime instruction by itself |
| Resource | Ressource de compétence | competence support material | A file, link, wiki, manual, dataset, snapshot, example or documentation used by a Competence. | Connaissance métier, Evidence, approval |
| Template | Template | output form | A reusable form for a candidate output, card, report, table, graph, mail, gate or mapping. | validation, source, proof |
| Assertion | Assertion | truth-status object | A statement that must be qualified, supported, contradicted, validated, rejected or superseded. | expression, final truth |
| Expression | Expression | wording | The formulation of content. IRIS may work on Expression without changing substance. | Assertion |
| Manifestation | Manifestation | observed trigger | A sign, event or observable fact that triggers a Situation. | Assertion, Evidence |
| Evidence | Preuve | review support | Material that supports or contradicts an Assertion. Always status-qualified. | final proof by itself |
| Gate | Seuil | decision exposure | The visible point where a decision, escalation or approval is required. | automatic approval engine |
| Approval | Approbation | legitimacy | Explicit validation of a status, output, external action, Register entry or scope change. | execution, display, click-only UI state |
| Register | Registre | validated memory | What remains after validation. Use Registre Probatoire when the probative register is meant. | runtime memory, database dump |
| Recall | Rappel | memory candidate | What a runtime memory, search or adapter brings back from the past. | Register |
| Record | Enregistrement | stored data | Stored data without probative authority by itself. | Register |
| Archive | Archive | inactive past | Preserved material that should no longer actively guide current work. | active memory |
| Trace | Trace | observation trail | A reviewable history of execution, consultation, change or discussion. | Evidence by itself |
| Handoff | Relais | governed crossing | A controlled transfer from governance to external execution. | queue, workflow, scheduler |
| Surface | Surface | exposure | The layer that displays, captures, labels, warns or exposes a decision. | runtime, authority |
| Cockpit | Cockpit | administration | A configuration and oversight interface. | governance authority |

## Reserved runtime vocabulary

The following words belong to execution and infrastructure unless explicitly qualified as candidates or references.

| Term | French | Reserved for | Rule |
|---|---|---|---|
| Runtime | Runtime | Hermes, LangGraph or another execution environment | Executes outside Pantheon. |
| Workflow | Workflow | executable process, runtime graph, CI flow, automation | Pantheon may govern a Workflow Candidate, but does not run workflows. |
| Skill | Skill | Hermes or runtime-executable ability | Pantheon governs Capability and Competence status; Hermes executes Skill. |
| Tool | Outil | runtime or host callable tool | Availability is not authorization. |
| Plugin | Plugin | host-system extension | Plugin presence is not governed permission. |
| Job | Job | technical execution unit | Not a governance task. |
| Action | Action | operational effect | External action needs approval if consequential. |
| State | État | runtime state | Not memory, not Register. |
| Run | Run | runtime execution instance | Run success is not approval. |
| Node | Nœud | graph/runtime function | Not a Role. |
| Edge | Arête | graph transition | Not a governance path. |
| Checkpoint | Checkpoint | runtime snapshot | Not Evidence. |
| Thread | Thread | runtime or conversation continuity | Not Case. |
| Queue | File | infrastructure queue | Not Pantheon scheduling. |
| Scheduler | Planificateur | infrastructure timing | Not Pantheon governance. |
| Worker | Worker | executor process | Not a Pantheon Role. |

## Capability, competence, skill, plugin and capacity

These words must not collapse.

```text
Capability is the abstract governable effect class.
Competence is a bounded reusable ability governed by Pantheon.
Skill is the execution-side projection, typically Hermes.
Plugin is a host-system extension.
Capacity means volume, load or limit.
```

French:

```text
La Capacité est la classe abstraite d'effet gouvernable.
La Compétence est une capacité réutilisable, bornée et gouvernée par Pantheon.
Le Skill est la projection exécutable, typiquement côté Hermes.
Le Plugin est une extension d'un hôte.
Capacity signifie jauge, volume, charge ou limite.
```

Rules:

```text
Use Capability for the abstract kernel-level placement test.
Use Competence for governed reusable abilities such as filling a PDF, querying an API, calculating a surface, producing a diagram or doing sourced web research.
Use Skill only for execution-side ability.
Use Plugin only for host-system extension.
Use Capacity only when the meaning is quantity or load.
Professional judgement remains with the professional; a system Competence is not professional authority.
```

See `COMPETENCE_MODEL.md` for the governed competence vocabulary.

## Connaissance, guide, resource and template

These words also must not collapse.

```text
Connaissance = what the profession, project, contract or rule says.
Guide de compétence = method document explaining how to do something.
Ressource de compétence = material used by a competence.
Template = reusable form of an output.
```

Examples:

| Situation | Connaissance | Guide / Resource | Competence | Template |
|---|---|---|---|---|
| Fill a PDF | values to enter: client, address, parcel, surfaces | PDF/OCR/AcroForm docs | PDF filling | field mapping |
| Surface taxable | tax and project rules, plans, measured areas | calculation guide, official notes, examples | calculate taxable surface | calculation table |
| API query | address, parcel, SIRET or professional input | API docs, examples, wiki | query an API | API result sheet |
| d3.js diagram | project/cards/status data | d3.js docs, snippets | produce a diagram | graph template |

A documentation API, d3.js guide, OCR manual, PDF library guide or wiki about how to operate a tool is a Guide or Ressource de compétence.

It is not a Connaissance métier unless it directly states professional, regulatory, contractual or project content.

A Template structures output. It never validates content.

## Case, folder, corpus and dossier

`Dossier` is useful in public French prose, but dangerous as a canonical system word because it can mean professional matter, file folder or document bundle.

Preferred distinctions:

| Term | French | Meaning |
|---|---|---|
| Case | Affaire | professional unit followed by Pantheon |
| Project | Projet | architecture/construction subtype of Case |
| Situation | Situation | concrete question or tension inside a Case |
| Corpus | Corpus | mobilized document set |
| Folder | Dossier | file-storage directory only |

Use `Affaire` for the governed professional unit. Reserve `Dossier` for public language or storage/folder contexts unless the surrounding text makes the meaning explicit.

## Method, approach and workflow

These three words mark three different layers.

| Term | French | Layer | Example |
|---|---|---|---|
| Method | Méthode | professional domain | architecture method, legal method, medical method |
| Approach | Démarche | reusable governed handling of a Situation | PLU response approach, CCTP review approach |
| Workflow | Workflow | executable runtime process | Hermes workflow, LangGraph graph, CI workflow |

Rules:

```text
Method frames the profession.
Approach handles a recurring Situation.
Workflow executes in the runtime.
```

French:

```text
La Méthode cadre le métier.
La Démarche traite une Situation récurrente.
Le Workflow s'exécute dans le runtime.
```

Avoid `meta-workflow` as a canonical term. Use `Approach` or `governance lifecycle` depending on whether the subject is reusable professional handling or status progression.

## Assertion, expression, manifestation and finding

Use `Assertion` for truth-status work.

| Term | French | Meaning | Rule |
|---|---|---|---|
| Assertion | Assertion | statement to qualify | central truth-status object |
| Expression | Expression | wording or formulation | IRIS may modify without changing substance |
| Manifestation | Manifestation | observed trigger or sign | may create a Situation |
| Finding | Constat | validated Assertion | use only after review/approval |
| Conclusion | Conclusion | final reasoning output | avoid before validation |

Example:

```text
Manifestation: the city asks for a permeable-ground justification.
Situation: possible planning-compliance risk.
Approach: regulated response review.
Assertion: delivery areas may be excluded from the relevant surface calculation.
Evidence: PLU excerpt, massing plan and surface table.
Gate: architect approval before city reply.
Approval: professional validates the response.
Register: decision preserved for the Case.
```

## Assertion lifecycle

Assertions may evolve, but not silently.

```text
Draft assertions may be edited.
Sourced assertions must be revised.
Validated assertions must be superseded, not overwritten.
Registered assertions must be linked, not erased.
```

French:

```text
Les assertions brouillon peuvent être modifiées.
Les assertions sourcées doivent être révisées.
Les assertions validées doivent être remplacées, pas écrasées.
Les assertions inscrites au Registre doivent être liées, jamais effacées silencieusement.
```

Recommended statuses:

```text
proposed
unsupported
sourced
contradicted
to_verify
validated
rejected
superseded
archived
```

## Memory, recall, register, archive and trace

Avoid unqualified `Memory` in governance text.

| Term | French | Meaning |
|---|---|---|
| Recall | Rappel | candidate material returned by runtime memory, search, graph recall or adapter |
| Record | Enregistrement | stored data without validation by itself |
| Register | Registre | validated, scoped and durable memory |
| Archive | Archive | preserved but inactive past |
| Trace | Trace | reviewable history, not proof by itself |

Rules:

```text
Runtime memory is Recall.
Stored data is Record.
Validated memory is Register.
Inactive past is Archive.
Execution history is Trace.
```

French:

```text
La mémoire runtime est du Rappel.
La donnée stockée est un Enregistrement.
La mémoire validée est le Registre.
Le passé inactif est l'Archive.
L'historique d'exécution est une Trace.
```

## Role vocabulary

A Pantheon Role is not an agent.

| Term | French | Meaning |
|---|---|---|
| Role | Rôle | governance authority viewpoint |
| Charter | Charte | canonical definition of a Role |
| Mandate | Mandat | what the Role must examine |
| Lens | Regard | useful review angle |
| Power | Pouvoir | authorized governance effect |
| Limit | Limite | what the Role must not do |
| Signal | Signal | structured inter-role message |
| Activation | Activation | when the Role is active, mandatory, suspended or blocked |
| Attribute | Attribut | descriptive metadata only |

Rules:

```text
A Role has a Charter, Mandate, Lens, Powers, Limits, Signals, Activation and Attributes.
An Attribute describes.
A Mandate obliges.
A Limit blocks.
A Power authorizes.
A Signal transmits.
Activation conditions.
```

French:

```text
Un Rôle a une Charte, un Mandat, un Regard, des Pouvoirs, des Limites, des Signaux, une Activation et des Attributs.
Un Attribut décrit.
Un Mandat oblige.
Une Limite bloque.
Un Pouvoir autorise.
Un Signal transmet.
Une Activation conditionne.
```

Do not use `Role Profile` as a canonical term. Use `Hermes profile aligned with a Pantheon Role` when referring to execution-side profiles.

## External system boundary vocabulary

### Optional runtime clients

| External term | Pantheon classification | Rule |
|---|---|---|
| Client | optional, replaceable runtime interaction surface | availability or selection does not transfer governance authority |
| Approval control | runtime interaction control | not Pantheon human approval |
| Session | runtime continuity | not Case or governed identity |
| Attachment | runtime input material | not Evidence by itself |
| Memory | Recall | not Register |

### OpenWebUI — historical/refused integration vocabulary

OpenWebUI is not a selected architecture component, target client or governance owner. The mappings below preserve the interpretation of terms found in historical integration material; they do not define current ownership or reinstate the product.

| External term | Pantheon classification | Rule |
|---|---|---|
| Function | Surface extension | not Pantheon runtime |
| Pipe | Surface/runtime adapter | not Method |
| Filter | Surface interception | may support minimization, not approval |
| Action | UI-triggered operation | may create external-effect risk |
| Tool | host tool | not authorized merely by availability |
| Knowledge / RAG | retrieval support | not Evidence by itself; not automatically Connaissance métier |
| Memory | Recall | not Register |

### Hermes

| External term | Pantheon classification | Rule |
|---|---|---|
| Profile | execution profile | may align with Role, never becomes Role |
| Skill | executable implementation | may project a governed Competence or Capability |
| Tool | runtime tool | must respect Contract and Handoff |
| Run | runtime execution | creates Trace, not Approval |
| Patch | Patch Candidate | not merge, not doctrine |
| Memory | Recall | not Register |

### LangGraph

| External term | Pantheon classification | Rule |
|---|---|---|
| Graph | Workflow | executable runtime graph |
| State | Runtime State | not memory, not Register |
| Node | Runtime function | not Role |
| Edge | Runtime transition | not Approach |
| Checkpoint | Runtime snapshot | not Evidence |
| Thread | Runtime continuity | not Case |
| Interrupt | Runtime pause | not Approval |

### Langflow

| External term | Pantheon classification | Rule |
|---|---|---|
| Flow | Workflow/preparation flow | not Approach |
| Component | technical block | not canonical Capability by itself |
| Template | technical template | not Method |
| Output | runtime output | candidate until reviewed |

### MCP

| External term | Pantheon classification | Rule |
|---|---|---|
| Server | connector/tool gateway | not governance layer |
| Client | connector-side consumer | not Approval authority |
| Tool | callable external function | not Capability validated by default |
| Resource | accessible material | Source candidate, Guide/Ressource de compétence or Connaissance candidate depending on scope; not Evidence |
| Prompt | template | not Method |
| Authorization | technical permission | not Pantheon Approval |
| Capability negotiation | technical discovery | not governed authorization |

### Observability

| External term | Pantheon classification | Rule |
|---|---|---|
| Trace | Trace | supports review, does not prove by itself |
| Observation | observation record | not Evidence unless selected and qualified |
| Span | trace segment | not Assertion |
| Generation | model call | not professional output |
| Session | trace grouping | not Case |
| Score | evaluation metric | not Approval |

### Memory systems and graph retrieval

| External term | Pantheon classification | Rule |
|---|---|---|
| Memory | Recall | candidate only |
| Search result | Recall | not Register |
| Embedding | technical index | not Evidence |
| Vector store | record/retrieval store | not memory authority |
| Entity | extracted candidate | not Case |
| Relationship | extracted relation | not probative link by itself |
| Claim | Assertion candidate | not validated Assertion |
| Finding | candidate summary | not Constat unless approved |

## Existing vocabulary migration rules

Existing documents may continue using historical terms until they are revised. New work should follow this mapping.

| Existing / risky term | Preferred term | Rule |
|---|---|---|
| Matter | Case | Use Case as English canonical term. |
| Dossier as system unit | Case / Affaire | Reserve dossier for public prose or Folder. |
| Path | Approach | Use when the sequence is reusable across Cases. |
| Meta-workflow | Approach / governance lifecycle | Do not use as canonical term. |
| Workflow in Pantheon doctrine | Approach unless executable | Keep Workflow only for Workflow Candidate or runtime. |
| Claim | Assertion | Claim becomes a deprecated English alias. |
| Affirmation | Assertion | French public alias only if needed. |
| Expression as truth object | Assertion | Expression is wording only. |
| Finding as candidate | Assertion / candidate | Finding is validated only. |
| Memory | Recall or Register | Always distinguish candidate recall from validated register. |
| Skill in Pantheon | Competence or Capability | Skill is execution-side. |
| Plugin | Capability / host plugin | Plugin remains host-system language. |
| Competence as runtime skill | Competence / Skill | Competence is governed reusable ability; Skill is runtime projection. |
| Knowledge as generic file pile | Connaissance / Source / Guide / Ressource | Distinguish métier knowledge from competence documentation and retrieval material. |
| Agent | Role | Agent reserved for runtime/external products. |
| Multi-agent | College | No hidden agent debate. |
| Orchestrator | Arbiter / coordinator | Avoid runtime implication. |

## Public aliases

Public-facing language may remain less technical, but must not create false authority.

| Canonical | Public-friendly |
|---|---|
| Case | affaire, dossier when no folder confusion exists |
| Approach | démarche |
| Contract | contrat de mission IA, cadrage de mission |
| Context | contexte minimal nécessaire |
| Capability | capacité |
| Competence | compétence |
| Connaissance | connaissance métier, connaissance projet, règle métier |
| Guide | guide de compétence, méthode d'application |
| Resource | ressource de compétence, documentation technique, ressource |
| Template | modèle, gabarit, trame |
| Assertion | point à vérifier, énoncé, assertion |
| Evidence | support de preuve, élément probatoire |
| Gate | seuil de décision |
| Approval | validation explicite, approbation |
| Register | mémoire validée, Registre probatoire |
| Recall | rappel candidat, élément retrouvé |

## Final boundary formula

```text
Pantheon governs Approaches, Competences, Assertions, Evidence, Gates, Approvals and Registers.
Runtimes execute Workflows, Skills, Tools, Jobs and Actions.
Optional runtime clients expose runtime interaction.
Pantheon Cockpit projects governed Cards, status, Evidence gaps and decisions.
Connectors produce Records and Recall.
Memory systems produce Recall, not Register.
Observability produces Trace, not Evidence.
Graphs reveal relations, not truth.
Databases store Records, not Decisions.
The professional decides.
```

French:

```text
Pantheon gouverne les Démarches, Compétences, Assertions, Preuves, Seuils, Approbations et Registres.
Les runtimes exécutent les Workflows, Skills, Outils, Jobs et Actions.
Les clients runtime optionnels exposent l'interaction avec le runtime.
Le Pantheon Cockpit projette les Cards, statuts, lacunes de preuve et décisions gouvernés.
Les connecteurs produisent des Enregistrements et du Rappel.
Les systèmes de mémoire produisent du Rappel, pas du Registre.
L'observabilité produit des Traces, pas des Preuves.
Les graphes révèlent des relations, pas la vérité.
Les bases stockent des Enregistrements, pas des Décisions.
Le professionnel décide.
```
