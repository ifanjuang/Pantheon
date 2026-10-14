# Distillation Registry

Status: active support doctrine — extracted pattern registry only.

This document records patterns that Pantheon Next has extracted from external references.

It is not a dependency list, implementation backlog or runtime plan. It does not approve integrations, tools, skills, providers, plugins, MCP servers, observability backends, GraphRAG runtimes, LangGraph runtimes, schedulers, queues or automatic memory systems.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
```

## Purpose

External references are useful only when their value is distilled into explicit Pantheon governance patterns.

This document answers:

```text
What have we actually extracted, where does it belong, and what remains forbidden?
```

It prevents vague inspiration from turning into architecture by implication.

The registry is transitional. Once a pattern is explicitly adopted by its real destination owner, rejected, superseded or no longer materially distinct, remove it from the current registry rather than preserving a duplicate rule here. Git history, issues and reference reviews retain provenance when needed.

```text
pattern learned != permanent registry entry
pattern adopted by owner -> remove duplicate registry entry
historical provenance != current authority
```

## Registry record format

Recommended fields:

```text
pattern_name
source_reference
source_class
extracted_problem
pantheon_distillation
intended_destination
allowed_use
forbidden_import
status
review_notes
```

## Status values

```text
candidate
active_support_pattern
active_governance_pattern
hermes_candidate_constraint
governed_projection_candidate
method_review_required
rejected
superseded
archived
```

A pattern is not active doctrine unless the destination governance document explicitly adopts it. A client or projection choice never promotes a pattern or transfers governance authority.

```text
client selected != governance authority
projection visible != pattern adopted
runtime support != governance requirement
```

## Current distilled patterns

| Pattern | Source reference | Pantheon distillation | Destination | Status |
|---|---|---|---|---|
| Human-owned contract boundary | contracts-skill | separate human intent from machine-maintained mapping | `TASK_CONTRACTS.md` | active_support_pattern |
| Preflight before mutation | contracts-skill, coding agent practice | check scope, constraints, protected files, evidence need and approval before changes | `EXECUTION_DISCIPLINE.md`, `EXTERNAL_TOOLS_POLICY.md` | active_support_pattern |
| Acceptance and verification trace | contracts-skill | record acceptance and verification expectations without claiming implementation | `EVIDENCE_PACK.md`, `APPROVALS.md` | active_support_pattern |
| Interruptible workflow point | LangGraph | treat human-in-the-loop as approval interruption vocabulary, not runtime graph | `TASK_CONTRACTS.md`, `USER_DECISION_GATE.md` | candidate |
| Runtime state visibility | LangGraph | summarize relevant external runtime state into evidence without owning it | `RUN_GRAPH.md`, `EVIDENCE_PACK.md` | candidate |
| Trace hierarchy summary | LangSmith, Langfuse | compress trace information into governance-relevant evidence summaries | `EVIDENCE_PACK.md`, `EXTERNAL_TOOLS_POLICY.md` | candidate |
| Evaluation score as signal | LangSmith, Langfuse | use scores as review signals only, never as approval | `APPROVALS.md`, `TENSIONS_AND_RISKS.md` | active_support_pattern |
| Measurability coverage disclosure | iFixAi | expose runtime-observed, declared, synthesized, judge-assessed, unmeasurable and insufficient-evidence coverage beside any aggregate result | `EVIDENCE_PACK.md`, `EXTERNAL_TOOL_PLACEMENT_REGISTER.md` | candidate |
| Declared governance demotion | iFixAi | treat governance supplied by fixtures or synthesized from configuration as declaration candidates, never as runtime verification, evidence sufficiency or approval | `EVIDENCE_PACK.md`, `EXTERNAL_TOOLS_POLICY.md`, `EXTERNAL_TOOL_PLACEMENT_REGISTER.md` | candidate |
| Pre-execution simulation | Future AGI | stress-test high-risk candidate actions before execution, delivery, memory or doctrine change | `PRE_EXECUTION_SIMULATION.md`, `TASK_CONTRACTS.md`, `EVIDENCE_PACK.md`, `USER_DECISION_GATE.md` | active_support_pattern |
| Trajectory evaluation | Future AGI, LangSmith, Langfuse | evaluate the path, tool-use sequence or multi-step behavior as a review signal, not approval | `PRE_EXECUTION_SIMULATION.md`, `EVIDENCE_PACK.md`, `TENSIONS_AND_RISKS.md` | candidate |
| Improvement Candidate | Future AGI | convert feedback or optimization output into reviewable candidate change rather than self-improvement | `PRE_EXECUTION_SIMULATION.md`, `MEMORY.md`, `APPROVALS.md`, `REJECTED_PATTERNS.md` | active_support_pattern |
| Prompt version as review artifact | LangSmith, Langfuse | preserve prompt/config version when it affects output legitimacy | `EVIDENCE_PACK.md`, `CONTEXT_PACKS.md` | candidate |
| Source graph candidate | GraphRAG | represent corpus structure and relationships as retrieved context, not truth | `RAG_INGESTION_PIPELINE.md`, `KNOWLEDGE_TAXONOMY.md` | candidate |
| Contradiction graph | GraphRAG, Governance College doctrine | map conflicting claims and sources without smoothing them into consensus | `GOVERNANCE_COLLEGE.md`, `EVIDENCE_PACK.md` | candidate |
| Skill anatomy card | Shokunin, Agensi | Skill/package records need trigger, scope, anti-patterns, evidence, risk and compatibility notes without creating a separate governance lifecycle | `WATCHLIST.md`, `CAPABILITY_REGISTRY.md`, `schemas/skill_manifest.schema.yaml` | active_support_pattern |
| Skill anti-pattern library | Shokunin | record when a Skill/package pattern should not be considered or activated | `WATCHLIST.md`, `REJECTED_PATTERNS.md` | active_support_pattern |
| Skill eval report | Shokunin | Skill-backed capability quality must be reviewed through evidence and task fit; evaluation is a signal, not admission | `PRE_EXECUTION_SIMULATION.md`, `EVIDENCE_PACK.md` | candidate |
| Failure-mode-first evaluation | `ai-evals-course/evals-skills` | inspect representative traces/cases and classify material failure modes before designing assertions, judges or aggregate benchmarks | `PRE_EXECUTION_SIMULATION.md`, `EVIDENCE_PACK.md`, `TENSIONS_AND_RISKS.md` | candidate |
| Evaluator calibration against human labels | `ai-evals-course/evals-skills` | before an LLM judge materially influences an evaluation, compare it against human-labelled reference samples and expose disagreement/bias as evaluation uncertainty | `PRE_EXECUTION_SIMULATION.md`, `EVIDENCE_PACK.md`, `APPROVALS.md` | candidate |
| Creator / evaluator / admission separation | Anthropic `skill-creator`, eval systems | creation, evaluation and governance admission are distinct responsibilities; self-evaluation may produce an Improvement Candidate but cannot self-admit or self-activate the Capability | `CAPABILITY_REGISTRY.md`, `PRE_EXECUTION_SIMULATION.md`, `APPROVALS.md`, `REJECTED_PATTERNS.md` | active_support_pattern |
| Marketplace signal demotion | Agensi | popularity, price, votes and installs are signals, not approval | `WATCHLIST.md`, `REFERENCE_BOUNDARIES.md` | active_governance_pattern |
| Least capability principle | external tools and connector ecosystems | use the narrowest tool and avoid write-capable surfaces for read-only tasks | `EXTERNAL_TOOLS_POLICY.md` | active_governance_pattern |
| External PEP enforcement gateway | `prabindersinghh/agent-passport` `v0.2.0` (`640b4c5`) | intercept consequential tool calls before upstream execution; bind the request to an explicit runtime principal; fail closed when the Pantheon PDP cannot validate the effect; consume one-use decisions at the PEP; derive execution traces from actual tool outcomes; keep Pantheon as the sole policy decision authority | `HERMES_INTEGRATION.md`, `HERMES_EXECUTION_ADMISSION_BRIDGE.md`, `HERMES_EXECUTION_TRACE_SUMMARY.md`, `mcp-server/docs/HTTP_API_CONTRACT.md` | active_support_pattern |
| Draft-only professional posture | professional vertical assistants | regulated or liability-sensitive outputs remain drafts until review | `USER_DECISION_GATE.md`, examples | active_support_pattern |
| Source freshness disclosure | research, RAG and professional workflows | expose date, version, staleness and source limitations | `EVIDENCE_PACK.md`, `KNOWLEDGE_TAXONOMY.md` | active_support_pattern |
| Memory candidate discipline | shared memory and persistent agent systems | every durable memory-like claim requires claim, scope, evidence, risk and approval | `MEMORY.md`, `SCOPE_ISOLATION.md` | active_governance_pattern |
| Context pack as adapter-safe bundle | assistant instruction ecosystems | bounded task context can travel, but does not become doctrine or memory | `CONTEXT_PACKS.md` | active_governance_pattern |
| Anti-collusion role separation | multi-agent frameworks as counter-models | roles must preserve distinct review pressures, not simulate a hidden agent team | `GOVERNANCE_COLLEGE.md` | active_governance_pattern |
| User Decision Gate | professional workflow risk patterns | unresolved high-impact tension must be exposed to the human | `USER_DECISION_GATE.md` | active_governance_pattern |
| Context Sufficiency Gate | contextschema-py | retrieved context should be checked for required fields, source, freshness and invalidation before action | `TASK_CONTRACTS.md`, `EVIDENCE_PACK.md`, `KNOWLEDGE_TAXONOMY.md` | candidate |
| Chunking Fitness Evaluation | chunk-norris | chunking strategies should be tested against representative questions and retrieval traces before Knowledge ingestion | `RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md`, `RAG_INGESTION_PIPELINE.md` | candidate |
| Evidence Page and Modality Mapping | MMLongBench-Doc | document answers should preserve page-level and source-type evidence metadata | `EVIDENCE_PACK.md`, `KNOWLEDGE_TAXONOMY.md`, governed Card/projection owners | candidate |
| Unanswerable Question Testing | MMLongBench-Doc | document QA systems should test refusal when available evidence is insufficient | `USER_DECISION_GATE.md`, `EVIDENCE_PACK.md`, `TENSIONS_AND_RISKS.md` | candidate |
| Memory Curation Report | agent_memory_curator_agent | memory proposals should report accepted, proposed, rejected, redacted, conflict and deprecation status | `MEMORY.md`, `EVIDENCE_PACK.md`, `SCOPE_ISOLATION.md` | candidate |
| Skill Manager Demotion | skillsgate | skill inventory and compatibility UX may inform governed projection but not installation authority | `WATCHLIST.md`, `REJECTED_PATTERNS.md`, `REFERENCE_BOUNDARIES.md` | governed_projection_candidate |
| Profile identity layer | SOUL.md, Hermes Personality & SOUL.md | stabilize Hermes execution posture without granting governance authority | `HERMES_INTEGRATION.md`, `reference_reviews/SOUL_MD_HERMES_PROFILE.md`, future `hermes/profiles` writing guidance | hermes_candidate_constraint |
| Independent framing before deliberation | `0xNyk/council-of-high-intelligence` | independently restate a hard question before multi-perspective analysis; surface material framing divergence rather than silently averaging incompatible problem definitions | `GOVERNANCE_COLLEGE.md`, Hermes Method/Skill qualification after Pantheon-Next#1093 | method_review_required |
| Anonymous adversarial cross-review | `0xNyk/council-of-high-intelligence` | separate argument quality from persona/provider prestige; require concrete objections and preserve dissent before synthesis | `GOVERNANCE_COLLEGE.md`, Hermes Method/Skill qualification after Pantheon-Next#1093 | method_review_required |
| Decision-oriented dissent summary | `0xNyk/council-of-high-intelligence` | expose convergences, unresolved disagreements, uncertainties, acceptable compromises, missing evidence and kill criteria as candidate review material without converting consensus into a Decision | `USER_DECISION_GATE.md`, existing Result/Decision Request owners | candidate |
| Deterministic external pre-vet | `0xNyk/agent-security` | run non-executing static tripwires before deeper external repository/Skill qualification; report matched patterns and coverage limits with an explicit claim ceiling | `EXTERNAL_TOOLS_POLICY.md`, existing Capability/Skill qualification tests | method_review_required |

## Distillation rules

A distilled pattern must:

- name the external source;
- identify the governance problem it helps solve;
- define the Pantheon destination;
- preserve forbidden imports;
- avoid vendor or framework lock-in;
- stay compatible with Task Contracts, Evidence Packs, approvals and memory policy;
- preserve the separation between runtime interaction, external execution, governed projection and Pantheon authority;
- leave this registry when the destination owner has absorbed the rule and no distinct cross-cutting review purpose remains.

## What does not count as distillation

The following are not valid distillation:

- copying a framework architecture;
- importing code because the pattern is useful;
- treating a popular repository as authority;
- treating a runtime capability as governance requirement;
- adding a dependency without a governance decision;
- converting external documentation into Pantheon doctrine without review;
- creating a skill because a marketplace lists one;
- creating memory because a system stores user history.

## Relationship to rejected patterns

When a pattern is useful but dangerous, split it:

```text
useful part -> DISTILLATION_REGISTRY.md
forbidden part -> REJECTED_PATTERNS.md
```

Example:

```text
Shokunin SKILL.md anatomy -> distill.
Shokunin persistent memory / MCP / auto-save / scheduler -> reject as Pantheon core pattern.
```

## Relationship to approvals

Adding a support pattern to this registry is not the same as modifying canonical doctrine.

Changing active governance documents may require stronger approval, especially when it affects:

- memory promotion;
- approval thresholds;
- protected files;
- Task Contract semantics;
- external tool authorization;
- runtime interaction or Hermes execution boundaries;
- governed Cockpit/Card projection boundaries;
- professional liability posture.

## Forbidden drift

The registry must never become:

- implementation backlog;
- dependency manifest;
- vendor ranking;
- plugin catalog;
- skill marketplace;
- runtime roadmap;
- automatic adoption queue;
- authority substitute;
- proof of safety.

If a registry entry is treated as permission to implement runtime behavior, the boundary has failed.

## Final rule

```text
Distillation records what Pantheon is still evaluating or transferring into its owners.
Adopted rules live with their owners, not here.
```
