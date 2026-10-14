# External Reference Reviews

Status: support doctrine index — reference review navigation only.

This directory contains detailed reviews of external systems before any Pantheon distillation, external-runtime binding, client selection or governed Cockpit projection is considered.

It does not approve dependencies.
It does not approve integrations.
It does not define runtime behavior.

Current responsibility split:

```text
Compatible runtime clients -> optional runtime interaction surfaces
Hermes Agent               -> external execution candidate/binding where useful
Pantheon Cockpit           -> governed projection where useful
Pantheon Next              -> governance distillation and authority boundaries
Human                      -> consequential decision when required
```

A reference may concern only one of these layers. Reviewing a product does not create a missing layer merely to give that product somewhere to live.

## Review rule

Every external reference should be reviewed against the smallest existing responsibility it could improve:

```text
Pantheon governance -> useful governance pattern, forbidden imports and existing destination owner
Hermes/runtime       -> executable capability candidate only when the capability is demonstrated and bounded
Runtime client       -> replaceable interaction surface only when a distinct interaction need exists
Pantheon Cockpit     -> governed projection pattern only when a distinct projection need exists
```

If the useful pattern already has an owner, distill into that owner rather than creating a product-specific path. If no demonstrated capability gap remains, keep the reference historical or refuse it.

```text
reviewed != adopted
compatible != selected
selected != dependency adopted
projected != authoritative
```

## Reviews

The detailed one-shot reviews formerly stored in this directory were removed on 2026-07-07 (governance cleanup, audit follow-up). Each full text remains in the private Pantheon-Next archive history. The strategic memory of each tool is kept below.

New reviews follow the review rule above, are distilled promptly, and the one-shot review file is removed once its distillate lands here — a review is a working document, not doctrine.

Historical rows below preserve the vocabulary and product relationships that were reviewed at the time. Those mentions are provenance, not current architecture assignments.

## Removal index — strategic memory of reviewed tools (2026-07-07)

One row per removed review. Status vocabulary: **distilled** (the useful pattern already lives in the target document), **to review** (candidate value, never distilled — re-open from git history before use), **superseded** (covered by a newer review or document). All rows: removed; git history.

| Tool / repo | Abstract capability | Hermes binding candidate | Status | Target doctrine document | Potential interest | Main risk |
|---|---|---|---|---|---|---|
| Pantheon MVP Vertical bundle | bounded Block 1 governed task loop: Task Contract ingestion, SQL-scoped retrieval, candidate return | historical executable-binding review; former `ifanjuang/pantheon-mvp` topology is superseded | superseded / historical provenance | `NEXT_MVP_REPOSITORY_PLACEMENT.md`, current Document/Knowledge owners and `implementation/` tests | historical source of the first bounded executable vertical slice | treating a superseded external-repository review as current implementation placement or adoption readiness |
| TrueMemory | evidence-first memory: admission gate, evidence atoms, scoped retrieval, dependency graph | local-first memory adapter behind the Registre Probatoire | distilled | `EVIDENCE_MEMORY_CANONICALIZATION.md`, `MEMORY.md` | richest memory-pattern source reviewed (9 patterns, data model) | opaque memory injection replacing governed evidence |
| AgentCanvas | agent trace visualization | trace-view adapter for run inspection | to review | `PANTHEON_CONTROL_BOUNDARY.md` | visual run evidence for review surfaces | trace display mistaken for validation |
| AgentOS | dynamic runtime capability vocabulary, memory quality signals | none (vocabulary only) | distilled | `CAPABILITY_REGISTRY.md` | naming for runtime-generated capability candidates | importing an autonomous generated-capability runtime |
| AgentVision | visual evidence capture of rendered artifacts | screenshot/visual-diff evidence producer | to review | `PANTHEON_CONTROL_BOUNDARY.md` | visual proof for UI/document rendering claims | screenshots treated as ground truth |
| ASSERT | spec-driven evaluation, executable regression checks | governance-regression eval runner | distilled | `HERMES_INTEGRATION.md` (absorbed evaluation layer) | spec → executable check discipline | judge-as-approval authority |
| Autotelic Agency | self-generated goals as reviewable Intent Candidates | intent-candidate emitter under Task Contract | to review | `TASK_CONTRACTS.md` | names the intent-before-action object | self-set goals executing without a gate |
| BFL OpenAI Image Proxy | OpenAI-compatible image generation proxy (FLUX) | image-generation adapter behind passport | to review | `EXTERNAL_TOOLS_POLICY.md` | image generation without modifying OpenWebUI | external send of prompts/assets without approval |
| CogniCore | runtime failure memory, reflection cards, adaptive-runtime passport fields | Hermes-side operational-mistake memory | to review | `EXTERNAL_TOOLS_POLICY.md` | staged distillation plan already written (levels 0–3) | alpha project; runtime learning drifting into Pantheon memory |
| Crawlberg | web crawl as source-intake candidate | web evidence intake skill | to review | `RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md` | URL→candidate-source pipeline shape | crawl output treated as truth; antibot bypass liability |
| dcode-agent-kit | agent/skill scaffolding conventions | Hermes skill scaffolding templates | to review | `SKILL_LIFECYCLE.md` | phase sequence and approval-gate lesson | scaffolds installing skills by implication |
| Dify / Langflow | visual agentic app builders, workflow labs | workflow-lab sandbox outside Pantheon | to review | `EXTERNAL_TOOLS_POLICY.md` | app-surface candidates for agency use cases | builder workflows bypassing the chokepoint |
| directory-mcp | entity/identity graph (Entities/Anchors/Edges/Observations) | identity-resolution helper under MCP passport | distilled | `EVIDENCE_MEMORY_CANONICALIZATION.md` | actor-layer schema for the Registre Probatoire | external directory becoming the entity registry |
| dltHub Text-to-SQL | definitions-first canonical data access | none (pattern only) | distilled | `DATA_PLATFORM_ARCHITECTURE.md` | definitions-before-queries discipline | importing Text-to-SQL as a feature |
| ELT (Epistemic Lattice Tethering) | earned-confidence gating, context management protocol | none (method inspiration) | to review | `ANSWER_VERIFICATION_GATE.md` | confidence earned by verification, not fluency | ontology-anchor-as-oracle; unverifiable claims |
| Flexible GraphRAG | document intelligence, hybrid retrieval, GraphRAG ingestion | document-intelligence adapter | to review | `DOCUMENT_INTELLIGENCE.md` | strongest retrieval-architecture candidate reviewed | ingestion pipeline becoming an ungoverned truth source |
| Forever AI Components | card affordance UX (governed affordance) | none (UX pattern) | distilled | `CARD_STACK_MODEL.md` | gesture discipline for decision cards | polished affordance implying granted capability |
| Future AGI | AI reliability suite: eval, simulation, guardrails | pre-execution simulation + eval runner | distilled | `PRE_EXECUTION_SIMULATION.md`, `HERMES_INTEGRATION.md` | simulation-before-high-risk-task pattern | self-improvement loop; platform as runtime |
| Hermes Agent v0.18 (release) | completion contracts, MoA, /learn, /journey | direct adapter mapping (it is the execution runtime) | to review | `HERMES_INTEGRATION.md` | keeps Pantheon aligned with the real Hermes surface | release features absorbed without boundary review |
| Hermes Agent beginner setup guide (2026-07-08) | runtime setup/status surface: install path, setup portal, models, tools, gateway, profiles, doctor, updates | direct Hermes runtime Capability Slot and cockpit card candidate | distilled | `HERMES_RUNTIME_GOVERNANCE.md` | turns field setup pitfalls into status fields, gates and non-equivalence warnings | install recipe imported as Pantheon procedure or auto-install path |
| Hermes Agent v0.18 (cards) | card projections of runtime objects | cockpit card adapters | to review | `CARD_STACK_MODEL.md` | ready-made card set for the cockpit | runtime state displayed as validated status |
| Hermes MoA | mixture-of-agents divergence benchmark | MoA run under internal benchmark protocol | distilled | `HERMES_INTEGRATION.md` | divergence as review signal, not truth | consensus mistaken for verification |
| Langfuse (dashboard card) | trace-dashboard link exposure | read-only dashboard link card | to review | `PANTHEON_CONTROL_BOUNDARY.md` | first observability exposure pattern | health display implying approval authority |
| Langfuse (install package) | bounded observability installation beside Hermes | trace metadata contract (task_contract_id…) | distilled | `operations/langfuse-hermes-first-test-runbook.md` | the one package that reached an operational runbook | installation drift beyond the bounded package |
| LangGraph | graph-structured agent runtime | optional runtime candidate under Task Contract | distilled | `EXTERNAL_TOOLS_POLICY.md` | boundary stress-test vocabulary (drift taxonomy) | central-runtime import; highest runtime-drift risk reviewed |
| Nango | connector gateway, OAuth/token custody | connector gateway candidate | distilled | `EXTERNAL_TOOLS_POLICY.md` | centralized credential custody pattern | connector functions becoming a workflow runtime |
| Odysseus | self-hosted AI workspace threat model | none (threat-model source) | distilled | `EXTERNAL_TOOLS_POLICY.md` (absorbed threat-model review), `MODEL_CAPABILITY_PASSPORT.md` | 8 distillations incl. untrusted-context admission rule | privileged local access without host-control classification |
| Plano | AI dataplane: gateway, routing, filter chains | gateway/observability adapter | to review | `EXTERNAL_TOOLS_POLICY.md` | infrastructure-level policy enforcement point | provider routing imported into Pantheon |
| Pythia | machine-readable governance state view | `governance_state_view` emitter | to review | `PANTHEON_CONTROL_BOUNDARY.md` | compact situational state for other systems | state view mistaken for authority |
| Quarkdown | documentary publication / dossier rendering | rendering skill candidate | to review | `SKILL_LIFECYCLE.md` | professional dossier/presentation export | polished render mistaken for validated document |
| RAG Made Simple | minimal RAG pipeline pedagogy | none (pedagogy) | distilled | `RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md` | plain-language RAG framing (used by README) | simple RAG answering consequentially without status |
| Row-Bot 4.2.0 | delegated child-agent runs, tool allowlists, write-locks | delegated-run pattern narrower than parent contract | to review | `EXTERNAL_TOOLS_POLICY.md` | single-writer and delegation-narrowing rules | delegated runs widening beyond the parent contract |
| self-inspect-mcp | deterministic metacognition prompts (signal → question) | mode_light rite prompter | distilled | `rites/README.md` | operationalizes rites without LLM judgment | imported as an internal runtime/MCP server |
| Voyager / DSPy (Skill Forge) | forged recipes, per-step signatures | forge mechanics stay Hermes-side | distilled | `CAPABILITY_REGISTRY.md`, governed composition (`schemas/workflow_manifest.schema.yaml`) | signature-as-contract vocabulary (landed in 0.1.60) | self-improving skill-writing loop |
| EviBound / SkillsVote / GovernSpec / MedSkillAudit | convergent skill-governance gates | none (vocabulary) | distilled | `CAPABILITY_REGISTRY.md`, `SKILL_LIFECYCLE.md` | two-gate lifecycle confirmed by four independent sources | autonomous approval/promotion engines |
| SOUL.md | profile identity layer for execution agents | Hermes profile identity (`hermes/profiles/*/soul.md`) | distilled | `hermes/profiles/PROFILE_CONSTITUTION.md`, `DISTILLATION_REGISTRY.md` | already implemented in the seven profiles | persona treated as governance authority |
| Sub-Agent-MCP | bounded sub-agent delegation over MCP | sub-agent caller under Task Contract | distilled | `EXTERNAL_TOOLS_POLICY.md` | delegation envelope vocabulary | YAML agent registry becoming doctrine |
| Understand-Anything | repository radiography, structural graph analysis | structural-analysis skill candidate | distilled | `docs/examples/understand_anything_structural_analysis/` | graph analysis framed as candidate evidence | self-updating graph treated as truth |

## Non-adoption rule

A review may recommend:

- watch;
- distill into an existing owner;
- reject;
- keep as a bounded Hermes/runtime capability candidate;
- keep as a replaceable runtime-client candidate;
- keep as a governed Cockpit projection pattern;
- archive as historical provenance.

A review must not be treated as:

- dependency approval;
- implementation approval;
- runtime migration;
- skill installation;
- provider choice;
- memory promotion;
- approval shortcut.

## Final rule

```text
Review first.
Distill only what survives the boundary.
Reuse an existing owner before adding a product path.
Install nothing by implication.
```
