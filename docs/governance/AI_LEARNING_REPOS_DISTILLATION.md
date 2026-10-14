# AI Learning Repositories Distillation

Status: support review — draft support note, pending governance index reconciliation.

Date: 2026-05-29

This document records five public AI learning repositories as external learning references for Pantheon Next.

It does not add dependencies, authorize implementation, approve a provider/runtime/plugin/skill/MCP server/tool gateway/workflow engine/evaluation engine/memory system or select a client.

```text
compatible clients may expose learning/runtime interaction
Pantheon Cockpit/Card owners may expose governed review projections
Hermes Agent may execute admitted external capabilities
Pantheon Next governs consequential status
```

## Purpose

The repositories reviewed here expose recurring AI work patterns:

- prompt framing;
- context and retrieval discipline;
- tool use;
- evaluations;
- application lifecycle;
- model internals;
- deployment and security concerns.

Pantheon Next should learn from these patterns without copying their runtimes, examples or product assumptions into its governance core.

```text
Popularity != approval
course != doctrine
notebook != runtime authority
prompt persona != Pantheon Role
eval pass != governed approval
client display != authority
```

## Source set

| Repository | Primary learning value | Pantheon relevance | Execution relevance | Interaction/projection relevance | Boundary |
|---|---|---|---|---|---|
| `f/prompts.chat` | Prompt persona and framing examples | Anti-confusion material between prompt persona, Pantheon Role, runtime profile and Task Contract | May inspire bounded prompt templates under contract only | May be browsed as non-canonical reference material | Must not become a role registry, skill marketplace or internal MCP layer |
| `dair-ai/Prompt-Engineering-Guide` | Prompt, context, RAG, agent and adversarial prompting taxonomy | Prompt/context risk vocabulary, adversarial review and method distillation | May inform execution prompts/checklists under Task Contract | May be exposed as a learning Knowledge Item | Must not import agentic RAG or LLM-as-judge authority into Pantheon |
| `anthropics/courses` | First-party notebook courses for API use, prompting, evaluations and tool use | Evidence Pack expectations, evaluation discipline and tool-use boundaries | May inform external tool-use/evaluation candidates | Governed surfaces may expose eval results, approval gaps and review notes | Provider-specific reference, not a provider-routing decision |
| `microsoft/generative-ai-for-beginners` | Broad generative-AI application curriculum, including responsible AI, UX, lifecycle and security | Product lifecycle, safety, security and professional onboarding vocabulary | May inform a broad capability map, not a runtime plan | May inspire Cockpit explanation and training surfaces | Microsoft ecosystem bias must not become Pantheon architecture |
| `mlabonne/llm-course` | LLM internals, fine-tuning, quantization, RAG, agents, deployment and security | Skill Watchlist, tool-risk classification and external capability boundaries | Strong relevance to optional technical capability candidates | Governed surfaces may display candidate outputs and references only | Must not make Pantheon a training, fine-tuning or quantization runtime |

## Pantheon reading order

For Pantheon Next, the priority remains:

1. `anthropics/courses` — evaluation and tool-use discipline.
2. `dair-ai/Prompt-Engineering-Guide` — prompt, context, RAG and adversarial taxonomy.
3. `microsoft/generative-ai-for-beginners` — lifecycle, UX, security and responsible-AI framing.
4. `mlabonne/llm-course` — capability and skill-watch vocabulary.
5. `f/prompts.chat` — persona examples and anti-confusion material.

Reason:

```text
strengthen proof, boundaries and approvals first
absorb broader curricula and technical patterns second
```

## Prompt framing

Relevant references:

- `f/prompts.chat`;
- `dair-ai/Prompt-Engineering-Guide`;
- `anthropics/courses`;
- `microsoft/generative-ai-for-beginners`.

```text
Prompt framing can change output behavior.
It does not create governance authority.
```

A prompt persona must not be confused with a Pantheon Role, runtime profile, Task Contract, Evidence Pack, approval or Registre Probatoire entry.

## Context, RAG and retrieval

Relevant references:

- `dair-ai/Prompt-Engineering-Guide`;
- `microsoft/generative-ai-for-beginners`;
- `mlabonne/llm-course`.

```text
Retrieval improves access.
Retrieval does not validate.
Retrieved Knowledge may become Evidence only when selected, scoped and recorded.
```

This supports `KNOWLEDGE_TAXONOMY.md`, `SCOPE_ISOLATION.md`, `CONTEXT_PACKS.md` and current retrieval/Evidence-boundary doctrine.

## Tool use and agents

Relevant references:

- `anthropics/courses`;
- `dair-ai/Prompt-Engineering-Guide`;
- `microsoft/generative-ai-for-beginners`;
- `mlabonne/llm-course`.

```text
Tool use is a capability surface.
It is not authorization.
```

Tool patterns may inform external execution candidates, but tool use remains governed by Task Contract scope, External Tools Policy, Evidence expectations, approval level and memory rules.

## Evaluations, safety and security

Relevant references:

- `anthropics/courses`;
- `microsoft/generative-ai-for-beginners`;
- `dair-ai/Prompt-Engineering-Guide`;
- `mlabonne/llm-course`.

```text
An evaluation can reveal quality or failure modes.
It does not replace approval.
```

Useful distillation targets include evaluation checklists, model-graded-output cautions, adversarial-prompt risk patterns, tool-use risk classification and delivery-readiness versus correctness distinctions.

## Model internals and deployment

Relevant reference:

- `mlabonne/llm-course`.

```text
Model internals help classify capability and risk.
They do not require Pantheon to own model training or deployment.
```

Fine-tuning, quantization, inference optimization and model deployment remain external technical capabilities if ever used.

## Product lifecycle and UX

Relevant reference:

- `microsoft/generative-ai-for-beginners`.

```text
A governed AI workflow is not only prompting.
It also needs user-action clarity, lifecycle discipline, safety posture and delivery-state vocabulary.
```

This is useful for Pantheon Cockpit/Card projection, compatible runtime-client explanation, approval visibility and professional onboarding. A client choice remains replaceable and does not become governance doctrine.

## Candidate distillations

The following are documentation candidates, not implementation tasks.

| Candidate | Source inspiration | Possible Pantheon location | Status |
|---|---|---|---|
| Evaluation checklist for candidate outputs | `anthropics/courses` | `EXTERNAL_TOOLS_POLICY.md` or a non-executable checklist | candidate |
| Prompt persona versus Pantheon Role clarification | `f/prompts.chat` | `REJECTED_PATTERNS.md` or pattern card | candidate |
| Adversarial prompt and prompt-injection review note | `dair-ai/Prompt-Engineering-Guide` | `EXTERNAL_TOOLS_POLICY.md`, `TENSIONS_AND_RISKS.md` | candidate |
| Tool-use boundary checklist | `anthropics/courses`, `mlabonne/llm-course` | `EXTERNAL_TOOLS_POLICY.md` support note | candidate |
| AI application lifecycle vocabulary | `microsoft/generative-ai-for-beginners` | `EDITORIAL_LANGUAGE.md`, `PANTHEON_COCKPIT_UX_SPEC.md` | candidate |
| External technical skill-watch records | `mlabonne/llm-course` | `SKILL_WATCHLIST.md` | candidate, separate review required |

No candidate becomes active doctrine merely by being listed here.

## Rejected patterns

| Pattern | Why rejected |
|---|---|
| Star count as adoption signal | Popularity is visibility, not Evidence or approval |
| Prompt persona as Pantheon Role | A persona changes style; a Role carries governed responsibility |
| Course notebook as Pantheon runtime | Learning material must not become execution architecture |
| Eval pass as approval | Evaluation is Evidence input, not governance decision |
| RAG demo as proof | Retrieval demonstrates access, not truth |
| Agent lesson as architecture commitment | Agentic examples must not import a hidden runtime |
| Tool-use tutorial as tool authorization | Availability never bypasses Task Contract and approval |
| Fine-tuning guide as Pantheon capability | Training/quantization are external technical capabilities, not governance core |
| LLM-as-judge as human decision replacement | Automated judgment may assist review but cannot replace governed approval |
| MCP example as internal connector policy | MCP remains an external capability/policy surface, not a universal internal layer |
| Learning client as governance owner | Display or interaction does not transfer authority |

## Placement

### Pantheon Next

Pantheon may keep these repositories as external references, Knowledge Items, method-review sources, candidate-distillation sources and rejected-pattern sources.

Pantheon must not use them as dependencies, runtime engines, approval authorities, memory authorities, role registries, plugin catalogs or provider-routing sources.

### External execution

Hermes or another admitted runtime may later use selected patterns as execution support under Task Contract.

Potential relevance includes evaluation candidates, tool-use workflows, technical skill candidates, capability-gap vocabulary and implementation checklists.

External runtimes must not install skills automatically, promote memory, approve their own outputs, broaden scope silently or import a course as standing runtime behavior.

### Runtime clients and Pantheon Cockpit

Compatible runtime clients may expose learning/reference interaction or runtime-facing results.

Pantheon Cockpit/Card owners may expose governed Knowledge, Evidence, approval and decision projections.

Neither surface may:

- turn learning material into a Registre Probatoire entry by display;
- treat retrieved course content as proof;
- silently authorize broader runtime access;
- convert prompt examples into hidden standing behavior;
- approve or transmit based only on UI selection.

```text
client selected != governance authority
projection visible != approval
retrieved reference != Evidence
```

## Governance decision rule

Before promoting a pattern from these repositories into Pantheon doctrine, ask:

```text
What exact pattern is useful?
Which confusion does it reduce?
Does it preserve source -> Evidence -> approval -> memory separation?
Does it require runtime ownership?
Does it affect external transmission or memory?
Can it remain optional and replaceable?
What Evidence/review supports it?
Which approval level is required?
```

If a pattern blurs proof, approval, memory or runtime boundaries, reject or quarantine it.

If it is useful but execution-facing, route it to an admitted external capability candidate under Task Contract.

If it is Pantheon-facing, project it through existing Cockpit/Card/decision owners without creating a client-specific governance subsystem.

## Indexing rule

This note remains draft until the main governance indexes explicitly reconcile it. It must not be treated as active doctrine merely because it exists.

## Status

Research and support note only.

No dependency, runtime, client plugin, Hermes skill, MCP layer, provider routing, evaluation engine, schema, test, operations tooling or memory promotion is authorized by this document.
