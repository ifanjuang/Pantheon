# Rejected Patterns

Status: active support doctrine — rejection memory only.

This document records patterns that Pantheon Next explicitly rejects, usually because they would collapse governance into runtime, memory into retrieval, evidence into logs, or approval into automation.

It does not add implementation.

It does not define runtime behavior.

It does not create an enforcement engine.

It does not authorize automatic blocking, scheduling, routing, tool execution or memory mutation.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: compatible runtime clients may expose runtime interaction only, Hermes/the external runtime executes admitted work, Pantheon Cockpit projects governed state, and rejected-product examples do not become current architecture owners.

## Purpose

Rejected patterns matter because architectural drift often returns under new names.

This document answers:

```text
What have we already refused, and why?
```

It prevents repeated debate from eroding doctrine.

## Rejection record format

Recommended fields:

```text
pattern_name
source_or_family
rejection_reason
violated_boundary
related_governance_docs
safe_alternative
status
review_notes
```

## Status values

```text
rejected
rejected_as_pantheon_core
hermes_only_possible_under_contract
runtime_client_exposure_only_possible
method_review_required
archived
superseded
```

## Current rejected patterns

| Pattern | Source or family | Why rejected | Safe alternative |
|---|---|---|---|
| Pantheon execution engine | agent frameworks, legacy predecessor runtime drift | Pantheon must govern, not execute | Hermes executes under Task Contract |
| Central LangGraph runtime | LangGraph-style orchestration | would turn governance manifests into executable graphs | use as external runtime reference only |
| Hidden workflow runner | workflow automation systems | execution would become invisible to governance review | Task Contracts plus Evidence Packs |
| Scheduler or queue inside Pantheon | agents, jobs, automation systems | creates autonomous timing and runtime state | external runtime reports capability gaps and evidence |
| Provider router inside Pantheon | model gateways, provider routers | collapses governance into provider selection | external provider/runtime policy governed by Task Contract |
| MCP server layer inside Pantheon | MCP ecosystems | creates plugin/runtime surface inside governance repo | treat MCP as external capability surface under tool policy |
| Plugin marketplace | skill ecosystems, MCP marketplaces | capability availability becomes authorization | governed watchlist and separate review |
| Automatic skill installer | skill ecosystems | bypasses approval, scope and evidence review | Skill Candidate review, Hermes-only if approved |
| Skill auto-updater | self-updating skill systems | creates self-evolution and supply-chain risk | explicit review and versioned candidate updates |
| Auto-promoted memory | persistent agent memory systems | violates candidate versus canonical memory | Register Candidate plus approval path |
| Shared flat memory | shared memory layers | breaks scope isolation and project boundaries | scoped a Registre Probatoire entry only |
| Runtime state as memory | agents, LangGraph, observability systems | execution traces are not durable governed truth | summarize only relevant evidence |
| Trace store as Evidence Pack | observability platforms | activity log is not governed proof | Evidence Pack with selected sources, risks and outputs |
| Eval pass as approval | eval systems, LLM-as-judge | score is not human/governance approval | evaluation signal plus approval review |
| Simulation pass as approval | Future AGI, simulation/eval systems | simulation success can reveal confidence but cannot authorize delivery, transmission, memory or doctrine | Pre-execution simulation as Evidence Pack signal plus approval review |
| Eval pass as automatic optimization | Future AGI, optimization loops | a score must not mutate prompts, policies, skills, workflows or doctrine | Improvement Candidate plus explicit approval |
| LLM judge as final authority | automated evaluation methods | replaces user/professional decision | judge output as signal or dissent only |
| Multi-model consensus as proof or authorization | second-opinion and model-panel systems | agreement between models is correlated generated output, not independent source corroboration, professional truth or authorization | preserve individual opinions/dissent as review signals, verify material claims against applicable sources, and keep the human/governance gate |
| Hidden multi-agent debate | multi-agent frameworks | creates opaque authority and possible role collusion | Governance College as visible review roles |
| Autonomous role agents | agent teams mapped to Greek roles | Pantheon Roles are review viewpoints, not workers | Hermes profiles may produce candidates |
| ZEUS truth engine | over-centralized arbitration | ZEUS arbitrates status and procedure, not truth | User Decision Gate when procedure is insufficient |
| Graph as truth | GraphRAG and knowledge graph systems | extracted relationships are generated and scoped | graph as retrieved context or Evidence Candidate |
| Generated graph as architecture truth | Understand-Anything, GraphRAG, repository maps | visual clarity can be mistaken for validated architecture | structural graph as candidate evidence with Task Contract and Evidence Pack review |
| Graph as a Registre Probatoire entry | graph memory systems | breaks approval and scope requirements | Register Candidate from graph only with review |
| OpenWebUI as source of truth | cockpit and KB surfaces | display and upload do not canonize | Pantheon Cockpit projects governed artifacts; compatible clients expose runtime interaction only |
| OpenWebUI global knowledge bridge | direct KB/vector access | grants Hermes unbounded data access | scoped Context Pack or read-only governed gateway |
| Hermes free browsing of OpenWebUI storage | integration shortcuts | bypasses Task Contract scope | authorized knowledge IDs and selected excerpts |
| Automatic external action | email, calendar, publishing, deployment agents | creates third-party effect without approval | draft first, approval before send/write |
| Working while user sleeps | autonomous background-agent patterns | creates unsupervised execution and timing loops | explicit task execution outside Pantheon under contract |
| Self-evolution loop | self-updating agents | governance mutates without review | proposed changes as candidates plus approval |
| Self-improving loop as governance authority | Future AGI, self-improving agent systems | feedback loops can improve candidates but must not become doctrine, memory, skill or workflow authority | Improvement Candidate with scope, evidence, risk and approval |
| Tool factory inside Pantheon | tool-generation repositories | creates tool runtime and supply-chain risk | external tool candidates governed by policy |
| Automatic repository mutation | coding agents | commits are not doctrine validation | patch candidate, diff review, ai_log |
| Professional agent as authority | legal, medical, architecture assistants | professional responsibility cannot be delegated to AI | draft-only posture and human review gate |
| Connector access by convenience | MCP/connectors/app integrations | available access becomes authorization | least-capability authorization under Task Contract |
| Parallel runtime policy authority | agent passport and security-gateway systems | a second policy engine that may independently allow consequential effects creates competing PDPs, divergent authorization semantics and authority drift | Pantheon remains the sole PDP; a runtime PEP may enforce Pantheon decisions and apply local deny-only hardening that can narrow but never widen authority |
| Popularity-based approval | skill marketplaces | market signal replaces governance review | popularity can only trigger watch status |
| Context validation as approval | contextschema-py misuse | context sufficiency is not C0-C5 governance approval | use as evidence/status signal only |
| Chunking score as evidence authority | RAG evaluation tools | retrieval fitness does not prove source truth or answer correctness | use as ingestion evidence only |
| Global chunker by convenience | RAG pipelines | one document's best chunker must not become global KB policy | scope chunking by document, dossier, corpus or project |
| Benchmark score as delivery approval | document QA benchmarks | benchmark performance does not validate a professional livrable | use as evaluation evidence only |
| Near-zero hallucination claim as proof | RAG architecture articles | reliability claims without benchmark, abstention and evidence audit are not governance evidence | treat as weak signal only |
| Direct skill manager adoption | SkillsGate-style managers | turns skill discovery into capability mutation | watch and review skills; never auto-install |
| Working plan or handoff as current governed state | Scoville Plan/Handoff, planning-with-files | durable continuity files can be stale and do not become project identity, current truth, Evidence, approval or authorization | use Work Issue/Context Pack-style continuity and re-read current authoritative state before resuming |
| Memory curator as canonical authority | memory curator systems | curation output must not promote a Registre Probatoire entry without approval | Register Candidate plus explicit approval |

## Rejection categories

### Runtime drift

Rejected when the pattern makes Pantheon execute, schedule, route, dispatch, retry, install, run tools or manage workers.

### Memory drift

Rejected when the pattern turns retrieval, logs, traces, embeddings, shared memory, user history or repeated observations into a Registre Probatoire entry.

### Evidence drift

Rejected when the pattern treats logs, scores, traces, graph centrality, citations or confident output as proof without governed selection and review.

### Approval drift

Rejected when the pattern makes a click, score, model judgment, successful run, user silence, repeated use or tool availability equivalent to approval.

### Scope drift

Rejected when the pattern allows cross-project, cross-dossier, cross-user or global reuse without explicit scope review.

### External effect drift

Rejected when the pattern sends, publishes, writes, deletes, deploys, files, notifies, installs, configures or mutates without explicit user intent and approval.

### Authority drift

Rejected when a tool, UI, runtime, agent, score, graph, marketplace or vendor becomes a source of truth.

## Safe replacement patterns

| Rejected impulse | Replacement |
|---|---|
| execute inside Pantheon | delegate externally under Task Contract |
| keep all traces | summarize governance-relevant evidence |
| remember automatically | propose Register Candidate |
| install useful skill | record watch item and review |
| trust retrieved source | convert to Evidence Item with claim scope |
| let agent decide | expose User Decision Gate |
| let roles talk in background | preserve visible role statuses and dissent |
| adopt framework architecture | distill governance vocabulary only |
| trust repository graph | treat structural graph as candidate evidence only |
| trust simulation pass | treat simulation as candidate evidence and require approval |
| trust optimization loop | produce Improvement Candidate only |
| trust RAG score | keep retrieval score as limited Evidence Candidate metadata |
| trust benchmark score | record benchmark as method evidence, not delivery approval |
| trust long-context answer | require page/source grounding and insufficiency handling |
| trust model consensus | keep dissent visible and verify material claims against applicable sources |
| trust persisted plan/handoff | re-read current governed state and owner documents before resuming |

## Relationship to Distillation Registry

A rejected source may still contain a useful pattern.

The useful part belongs in `DISTILLATION_REGISTRY.md`.

The unsafe part belongs here.

This split is mandatory when a reference is both valuable and dangerous.

## Relationship to Governance College

Rejected patterns often look like helpful agents.

Pantheon rejects hidden agency and preserves visible tension instead.

Roles organize review.

They do not run a secret committee.

## Relationship to Watchlist

A watch item should be moved here when review shows that its main pattern conflicts with Pantheon doctrine.

A rejected item may still be archived as a historical caution.

## Reconsideration rule

Rejected does not mean impossible forever.

It means forbidden under current doctrine unless a future governed decision explicitly revises the boundary.

Such revision would require:

- explicit rationale;
- evidence or review note;
- risk analysis;
- affected governance document updates;
- approval level appropriate to the risk;
- ai_log entry.

## Forbidden drift

This document must never become:

- automatic enforcement engine;
- security policy implementation;
- runtime blocklist;
- scheduler or monitor;
- hidden validator;
- unreviewable veto authority.

It records doctrine.

It does not execute doctrine.

## Final rule

```text
A rejected pattern stays visible so it does not return disguised as convenience.
```
