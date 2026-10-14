# Tensions and Risks

Status: active support doctrine — persistent governance tensions.

This document records the recurring tensions Pantheon Next must preserve, qualify or escalate.

It does not add runtime behavior.

It does not add agents.

It does not define automatic enforcement.

It does not create a scheduler, queue, message bus, hidden workflow runner, decision engine, approval engine or memory engine.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work, Pantheon Cockpit projects governed tensions and decision state, and Pantheon retains governance authority.

## Purpose

Pantheon Next is not designed to eliminate tension.

It is designed to keep important tension visible until evidence, approval or human decision resolves it.

This document answers:

```text
Which conflicts must remain visible because they protect professional responsibility?
```

## Core rule

```text
A tension is not a defect.
A hidden tension is a governance failure.
```

## Permanent tensions

| Tension | What it means | Main risk if hidden | Preferred governance response |
|---|---|---|---|
| Speed vs proof | fast output may outrun source discipline | confident unsupported answer | Evidence Pack or source reserve |
| Convenience vs governance | easy automation may bypass review | hidden external effect | approval gate and tool risk class |
| Autonomy vs approval | agent initiative may look efficient | self-approval or unauthorized action | Task Contract boundary |
| Continuity vs scope isolation | memory helps but may leak between contexts | cross-project contamination | scoped Register Candidate discipline |
| Retrieval vs evidence | found content may look authoritative | retrieved equals true fallacy | Evidence Item conversion |
| Trace vs proof | logs show activity but not legitimacy | activity mistaken for evidence | governance-relevant evidence summary |
| Score vs judgment | eval scores can help compare outputs | LLM judge or metric becomes authority | score as signal only |
| Simulation vs approval | simulation can reveal failure modes | simulation pass treated as permission to deliver, transmit, merge or remember | Pre-execution simulation plus approval review |
| Optimization vs doctrine mutation | feedback loops can improve candidates | prompt, skill, workflow or doctrine changes mutate automatically | Improvement Candidate with explicit approval |
| Feedback loop vs self-evolution | production feedback can expose real defects | system starts improving itself without governance | candidate change, evidence, rollback and human decision |
| Graph structure vs truth | graph relations reveal corpus structure | graph centrality treated as proof | graph as retrieved context |
| Repository radiography vs graph authority | graph tools can clarify repository topology | clear visual structure treated as validated architecture | structural graph as candidate evidence under Task Contract |
| Production vs delivery | artifact exists before it is safe to use | premature external transmission | delivery status and approval |
| Clarity vs precision | smooth language may hide uncertainty | polished but unsafe output | APOLLO clarity plus ARGOS/THEMIS checks |
| Synthesis vs contradiction | synthesis may erase conflict | false consensus | contradiction ledger |
| Generalization vs dossier specificity | reusable pattern may overreach | project fact becomes doctrine | scope review |
| Local-first vs governance | self-hosting helps privacy | local data treated as safe by default | same evidence and memory rules |
| Tool richness vs attack surface | more tools increase capability | uncontrolled execution surface | least capability principle |
| Cockpit display vs authority | visible artifact feels official | runtime client or Cockpit projection becomes source of truth | projection is not authority |
| Runtime completion vs validation | successful execution may look final | Hermes done equals approved | candidate status preserved |
| Professional judgment vs automation | AI can draft expert-like output | professional responsibility outsourced | User Decision Gate |
| Pattern distillation vs architecture import | references are useful | framework copied into Pantheon | Reference Boundary review |
| Memory usefulness vs privacy | durable memory improves continuity | sensitive retention | approval and scope |
| Dissent vs smoothness | disagreement slows output | hidden risks | governed tension preserved |
| Chunking fitness vs evidence authority | better chunks may improve retrieval | retrieval score mistaken for proof | ingestion evidence only |
| Long-document confidence vs evidence locality | a model may answer from broad document context | fluent answer without auditable page/source grounding | evidence pages and source modalities |
| Unanswerable question vs forced answer | not every dossier supports an answer | refusal failure or invented answer | User Decision Gate and insufficiency status |
| RAG architecture promise vs measured reliability | architecture claims can sound definitive | near-zero hallucination claim treated as proof | benchmark, abstention and audit required |
| Skill inventory vs capability authorization | seeing available skills creates pressure to install | marketplace or installer drift | Skill Watchlist and explicit approval |
| Memory hygiene vs memory authority | curation improves memory quality | curator becomes a Registre Probatoire entry authority | Register Candidate plus approval |

## Risk taxonomy

Recommended risk labels:

```text
runtime_drift
memory_drift
evidence_drift
approval_drift
scope_drift
authority_drift
external_effect_drift
privacy_drift
professional_liability_drift
source_freshness_risk
contradiction_suppression
skill_sprawl
connector_overreach
observability_overreach
method_overreach
retrieval_score_overreach
benchmark_overreach
unanswerable_failure
modality_loss
graph_authority_overreach
repository_radiography_overreach
simulation_overreach
optimization_overreach
self_evolution_drift
```

## Risk severity

Severity may be classified as:

```text
low
medium
high
critical
```

Severity should rise when the tension affects:

- external transmission;
- protected files;
- memory promotion;
- doctrine change;
- professional liability;
- client, patient, legal, financial or contractual effect;
- sensitive data;
- irreversible action;
- cross-scope reuse;
- unverified source reliance.

## Role responsibility

| Tension family | Primary role pressure |
|---|---|
| scope, sequence, decomposition | ATHENA |
| source, provenance, freshness | ARGOS |
| policy, liability, approval | THEMIS |
| clarity, completeness, readiness | APOLLO |
| fabrication, patch, deliverable feasibility | HEPHAISTOS |
| recipient, exposure, transmission | IRIS |
| status conflict, next procedure | ZEUS |

Roles do not solve tension automatically.

They reveal, preserve or escalate it.

## Tension record format

When a tension affects a task, record the minimum useful information:

```text
tension_id
tension_type
affected_claim_or_output
roles_detecting_it
severity
source_or_evidence_status
approval_implication
memory_implication
external_effect_implication
recommended_next_action
resolution_status
```

## Resolution statuses

```text
noted
accepted_with_reserve
needs_source
needs_scope_decision
needs_approval
blocked_for_delivery
blocked_for_transmission
blocked_for_memory
escalated_to_user
resolved
superseded
revoked
```

## Next action vocabulary

Useful actions:

```text
find_source
check_freshness
narrow_scope
split_task
mark_assumption
preserve_contradiction
request_user_clarification
escalate_approval
block_delivery
block_transmission
reject_memory_candidate
create_memory_candidate_only
move_to_watchlist
move_to_rejected_patterns
run_context_sufficiency_check
run_chunking_fitness_check
run_pre_execution_simulation
create_improvement_candidate
mark_unanswerable
preserve_evidence_page
preserve_source_modality
mark_graph_as_candidate_evidence
```

## Relationship to Governance College

`GOVERNANCE_COLLEGE.md` defines why roles exist and how useful disagreement is preserved.

This document lists the tensions those roles should keep visible over time.

If a role cannot reveal, preserve or escalate a useful tension, it should not be activated for that task.

## Relationship to User Decision Gate

A tension should escalate to `USER_DECISION_GATE.md` when it exceeds safe procedural arbitration.

Examples:

```text
source conflict affects external advice
scope conflict changes dossier boundary
memory proposal is useful but sensitive
clear draft may imply contractual approval
runtime candidate requires protected mutation
question appears unanswerable from available evidence
external API would receive private documents
retrieval score is being treated as approval
simulation pass is being treated as approval
optimization output is being treated as doctrine mutation
feedback loop is being treated as self-evolution authority
generated repository graph is being treated as architecture truth
```

## Relationship to Evidence Packs

Evidence Packs should preserve tensions when they affect output legitimacy.

An Evidence Pack should not smooth serious risk into neutral prose.

It should mark:

- unresolved source conflict;
- unsupported assumption;
- stale source;
- approval gap;
- delivery limitation;
- memory risk;
- external effect risk;
- capability gap;
- insufficient evidence;
- unanswerable question;
- retrieval limitation;
- missing page reference;
- uncertain table, chart or image extraction;
- benchmark limitation;
- simulation limitation;
- optimization candidate risk;
- graph authority risk;
- generated graph scope limitation.

## Relationship to Watchlist and References

External references often create tensions.

For example:

| Reference pressure | Tension created |
|---|---|
| LangGraph durable execution | runtime continuity vs Pantheon non-runtime boundary |
| Langfuse traces | trace usefulness vs trace-as-proof fallacy |
| Future AGI simulation and optimization loops | simulation vs approval, optimization vs doctrine mutation and feedback loop vs self-evolution |
| GraphRAG summaries | synthesis power vs graph-as-truth fallacy |
| Understand-Anything repository graphs | repository radiography vs graph authority |
| Shokunin skills | skill discipline vs marketplace/installer drift |
| Glia-like shared memory | continuity vs scope isolation |
| LLM-as-judge | evaluation speed vs approval sovereignty |
| OpenWebUI Knowledge | retrieval convenience vs evidence discipline |
| contextschema-py | context sufficiency vs approval authority |
| chunk-norris | chunking fitness vs evidence authority |
| MMLongBench-Doc | benchmark usefulness vs professional validation |
| Medium RAG 10M+ claims | architecture promise vs measured reliability |
| skillsgate | skill inventory vs automatic installation pressure |
| agent_memory_curator_agent | memory hygiene vs memory authority |

These tensions should feed `REFERENCE_BOUNDARIES.md`, `DISTILLATION_REGISTRY.md` or `REJECTED_PATTERNS.md` when they become stable.

## Anti-patterns

Avoid:

```text
resolving tension by hiding it
turning all tensions into generic cautions
using ZEUS to erase dissent
using APOLLO to make risk sound smooth
using ARGOS to drown output in irrelevant sources
using THEMIS to block without next procedure
using HEPHAISTOS to produce before legitimacy
using IRIS to transmit before approval
```

Prefer:

```text
specific tension
specific affected output
specific evidence gap
specific risk
specific next action
specific approval implication
```

## Forbidden drift

This document must never become:

- automatic risk engine;
- hidden policy executor;
- autonomous blocker;
- runtime monitor;
- scoring backend;
- observability backend;
- approval engine;
- memory engine;
- substitute for human decision.

It names risks.

It does not execute risk controls.

## Final rule

```text
Pantheon does not remove friction.
Pantheon makes the right friction reviewable.
```
