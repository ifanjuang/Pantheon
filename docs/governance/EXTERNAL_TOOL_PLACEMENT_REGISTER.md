# External Tool Placement Register

Status: active support register — lightweight placement decisions for external tools, skills and products.

This register records placement decisions for external repositories and tools reviewed during Pantheon Next governance work.

It is a support register, not doctrine by itself.

It does not install dependencies, create a runtime, create a connector, create a Hermes skill, create a runtime-client component, approve a tool for production use or promote any output to proof or memory.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work as PEP, Pantheon Cockpit projects governed state, and Pantheon policy/governance remains the bounded PDP authority.

## Purpose

External tools are useful, but they must not blur Pantheon's boundary.

This register answers one narrow question:

```text
Where does this external capability belong, and what must Pantheon govern if it is used?
```

Canonical placement remains governed by:

- `CAPABILITY_PLACEMENT.md`;
- `MODULAR_DOMAIN_REORIENTATION.md`;
- `DOMAIN_PACK_SPEC.md`;
- `EXTERNAL_TOOLS_POLICY.md`;
- `ADAPTERS_AND_BINDINGS.md`.

If this register contradicts those documents, the canonical governance documents win.

## Placement rule

For every external tool, skill, connector, workflow, module or product, ask:

```text
If this goes wrong, can it produce a false truth,
an unapproved external effect,
a wrong memory,
or an unauthorized action?
```

- No — it is a feature. Place it in the tool layer that is best at using it.
- Yes — Pantheon governs the decision, status, proof, approval, scope or memory. Execution still remains outside Pantheon.

Governing a capability is not implementing it.

## Reviewed external tools

| Tool / repository | Nature | Placement | Status | Risk | Decision Zeus | Repo state | Next action |
|---|---|---|---|---|---|---|---|
| `greensock/gsap-skills` | Official GSAP AI coding skill set for animation, timelines, ScrollTrigger and framework integration. | Hermes skill candidate, frontend / motion. | Candidate / to verify | Low | Accepté | Documented non implemented | Verify license, integration target and accessibility rules before use. |
| `sujan1-3/browser-eyes-mcp` | MCP browser inspection and control layer using Chromium / CDP operations such as screenshots, DOM, network, storage and interaction. | Hermes MCP skill candidate with privileged modes. | Candidate / to verify | Medium to high | Accepté with constraints | Documented non implemented | Define read-only, interactive and mutation modes; require scope and approval for mutation, interception, cookies, storage and sensitive sessions. |
| `rowboatlabs/rowboat` | Local-first AI coworker / external product with long-lived context, knowledge graph, local notes and tool integrations. | External reference, possible future adapter; not a Hermes skill and not Pantheon core. | Candidate / to verify | High if absorbed directly | À vérifier / À arbitrer | Documented non implemented | Study only as external reference for inspectable working memory and graph context; never import its memory as a Registre Probatoire entry without governed promotion. |
| `Dyalwayshappy/Spice` | Decision-layer runtime above agents, with Decision Cards, read-only perception, decision guidance, approval checkpoints, executor handoff, outcomes and decision memory. | External reference only. May inspire Pantheon Cockpit decision surfaces and governed handoff vocabulary. Not a Hermes default runtime and not Pantheon core. | Reference / to verify | Critical if absorbed as decision authority | Refusé dans le core; à vérifier as UX/method reference | Documented non implemented | Distill compatible patterns only: Decision Card, sources/why/details/json inspection, unsupported-semantics reporting, read-only perception and approval-gated handoff. Do not install as governance runtime. |
| `PaddlePaddle/PaddleOCR` | OCR and document parsing toolkit for PDFs, images, layout, tables and structured extraction. | Hermes document-extraction capability candidate. Dashboard may expose install, configure, health and logs; Hermes owns installation and execution; Pantheon has no dependency. | Candidate / to verify | Medium to high if OCR output is treated as truth | Accepté with constraints | Documented non implemented | Add as dashboard-installable Hermes-managed capability only. Benchmark on CERFA, mairie arrêté, devis, chantier CR and surface tables. Outputs remain Extraction Candidates / Evidence Pack Candidates. |
| `12britz/awesome-free-models` | Curated list of free AI models, API tiers, local inference tools, chatbot UIs, RAG/vector databases, agentic frameworks, fine-tuning tools, datasets, hosting platforms and learning resources. | External tooling watchlist source only. It may seed dashboard watchlist cards or Hermes capability review candidates, but it is not a catalogue of approved models, tools or providers. | External reference / candidate-only | Medium; high if free-tier, license, privacy, benchmark or availability claims are trusted without review | Accepté as watchlist only | Documented non implemented | Use only to discover candidates. Verify license, commercial terms, data policy, retention, local/cloud boundary, version/date, quota, stability and agency benchmark before any admission or configuration. |
| `comet-ml/opik` | Open-source LLM observability, tracing, evaluation, datasets, online scoring and optimization platform. | External observability and evaluation layer; possible Hermes-side binding through a reviewed adapter or OpenTelemetry path if compatibility is proven. Pantheon Cockpit may project governed summaries; optional runtime clients may expose runtime interaction only. Pantheon has no dependency. | Candidate / to verify | High if professional data is captured without minimization, traces are treated as proof, scores become approval or optimizers mutate prompts/tools automatically | Accepté with constraints as evaluation lab candidate; not selected as default observability binding | Documented non implemented; not installed; not approved; inactive | Compare with Langfuse on five governed Task Contracts after verifying Hermes instrumentation, data minimization, retention, access control, self-host footprint and rollback. |
| `ifixai-ai/iFixAi` | Open-source AI operational-misalignment diagnostic with provider adapters, structural and judge-based inspections, scorecards and content-addressed run manifests. | External evaluation-method reference and watchlist item only; possible bounded Hermes-side lab runner against fictional fixtures after separate review. Not a Pantheon approval, certification or production gate. | External reference / watchlist | High if full model I/O, multi-provider judging, persistent telemetry, public test corpora or aggregate grades are treated as safe evidence | Accepté as method reference only; installation and operational use not approved | Documented decision; not installed; not approved; inactive | Distill coverage-disclosure and declared-versus-observed patterns. Do not run on client or production data; revisit only through a separate data-handling, telemetry, provider, cost and reproducibility review. |
| `Brescou/langgraph-agent-stack` | Deployable LangGraph and FastAPI multi-agent template with typed domain packs, version routing, memory, providers, connectors, evaluation, observability and deployment scaffolding. | External runtime reference only; possible specialized Hermes-side orchestration binding if a proven capability gap requires stateful graph execution. Not Pantheon core and not a default Hermes runtime. | External reference / watchlist | Critical if its control plane, memory, review queue, plugins or routing become Pantheon authority or duplicate Hermes | Refusé as Pantheon runtime; accepté as design reference only | Documented decision; not installed; not approved; inactive | Distill bounded pack-contract, evaluation, canary, budget, supply-chain and interrupt/resume patterns only. Revisit a binding only after an explicit Hermes capability gap and separate governed review. |
| `mr-september/hermes-uplink` | Third-party mobile PWA / thin client that proxies Hermes sessions and capabilities through a loopback proxy and Tailscale Funnel. | External UX reference only. It may inspire mobile session-resume patterns, but it is not a Pantheon Cockpit, selected/default Hermes client or governed action surface. | Reference only / refused for current architecture | Critical if it creates a direct Hermes bypass, exposes full sessions/capabilities through one shared credential or adds an ungoverned public endpoint | Refusé as integration; accepté as UX reference only | Documented decision; not installed; not approved; inactive | Do not adopt. Distill only bounded mobile and resumable-session UX patterns if they remain useful after comparison with official Hermes surfaces. |

## Tool notes

### GSAP Skills

Accepted as a lightweight Hermes skill candidate.

It may help produce frontend animation code, UI micro-interactions, educational interfaces, dashboard motion, scroll-driven explanations and visual prototypes.

It must return code candidates and integration notes. It must not decide UX acceptance, publish to production, bypass accessibility constraints or make candidate status look validated.

Governance trigger: animation becomes consequential if it hides a warning, changes the interpretation of a status, pushes a user toward an approval or visually confuses candidate and validated states.

### Browser Eyes MCP

Accepted as a privileged Hermes MCP skill candidate.

Recommended modes:

1. read-only audit — screenshots, DOM inspection, accessibility tree, console logs, network read, HAR export;
2. interactive test — click, type, scroll, navigation and device emulation within declared scope;
3. mutation / interception — DOM edit, JS edit, cookie and storage mutation, request interception, header injection or environment falsification.

The third mode requires explicit approval and a bounded scope.

All outputs are Evidence Pack Candidates until Pantheon qualifies their status.

### Rowboat

Not accepted as a skill.

Rowboat is a product / runtime / workspace pattern, not a bounded execution capability.

Its useful pattern is inspectable working memory and graph-based context accumulation.

Pantheon boundary:

```text
Rowboat records and organizes working context.
Hermes may execute bounded tasks.
Pantheon governs promotion, status, proof, memory and approval.
```

Rowboat memory, notes, summaries or graph relations are not a Registre Probatoire entry or proof by default. They may only enter Pantheon as Register Candidates or Evidence Pack Candidates under a governed promotion rule.

### Spice

Not accepted as Pantheon core, Hermes default runtime or approval authority.

Spice is valuable because it makes the pre-execution decision visible: candidate options, selected option, rejected trade-offs, sources, why, simulation metadata, approval checkpoints and executor handoff.

The compatible pattern is not the Spice runtime. The compatible pattern is a displayable and reviewable decision surface:

```text
Governed decision surface in Pantheon Cockpit
-> governed Task Contract / Context Pack / Evidence Pack Candidate
-> Pantheon policy disposition / human gate when required
-> Hermes bounded execution through the external runtime/PEP when admitted
-> Outcome Observation Candidate
-> Pantheon status review
```

Patterns to distill:

- Decision Card as a compact decision review surface;
- `/sources` as Evidence Pack display;
- `/why` as structured decision rationale and objection view;
- `/details` as expanded audit card;
- `/json` as raw artifact inspection for developers;
- `decision.md` as inspiration for bounded decision guidance, not as runtime policy owner;
- explicit support contract for what the active adapter can actually evaluate;
- unsupported semantics reporting instead of guessing;
- read-only perception before any execution request;
- approval-gated executor handoff;
- outcome observation separated from governance validation.

Patterns to refuse:

- Spice as decision authority above Pantheon;
- Spice memory as canonical memory;
- Spice approvals as Pantheon approvals;
- Spice Decision Card as Evidence Pack or Registre Probatoire entry;
- Spice executor handoff as authorized execution by itself;
- Spice runtime state as governance state;
- automatic reflection or decision evolution as memory promotion.

Boundary:

```text
Spice may inspire Pantheon decision surfaces.
Spice must not become Pantheon's decision authority.
```

### PaddleOCR

Accepted only as a Hermes-managed document extraction capability candidate.

The dashboard may expose user and admin controls:

```text
install via Hermes;
configure;
check health;
view logs;
run benchmark;
show capability gap when unavailable.
```

The dashboard must not become the installer, OCR runtime, document authority or proof engine. It can request or display Hermes-managed capability state.

Hermes may install and run PaddleOCR as an OCR / document parsing tool, but it must return candidates only:

```text
Document Source
-> Extraction Candidate
-> Fragment Candidate
-> Evidence Pack Candidate
```

PaddleOCR output must carry at least:

```text
source_id;
source_version;
page_or_location;
extraction_method;
model_or_tool_version;
extraction_confidence;
layout/table confidence when available;
produced_at;
scope_id;
known_limits;
```

Pantheon governs the status, evidence rule, approval rule, memory rule and promotion path. It must not depend on PaddleOCR and must not treat OCR success as proof.

Minimum benchmark before operational use:

```text
CERFA;
mairie arrêté;
devis;
chantier compte rendu;
tableau de surfaces.
```

Benchmark result remains `Candidate / to verify` until reviewed.

### Awesome Free Models

Accepted only as an external tooling watchlist source.

`12britz/awesome-free-models` is useful as a radar for candidate models, local inference tools, API tiers, chatbot UIs, RAG/vector tools, agentic frameworks, fine-tuning tools, datasets and hosting platforms.

It must not be treated as:

```text
approved model catalogue;
approved provider list;
approved install source;
license authority;
privacy authority;
benchmark authority;
production readiness signal;
Pantheon capability registry;
Hermes skill registry.
```

The dashboard may expose a `Tooling Watchlist` view derived from reviews, but the view remains display and qualification only:

```text
watchlist item;
category;
source URL;
local_or_cloud;
data_sensitivity_fit;
license_status;
commercial_terms_status;
privacy_status;
quota_status;
benchmark_status;
Pantheon placement;
Decision Zeus;
repo_state;
next_action.
```

A listed model, API, framework or tool may become eligible only through a separate review. Each candidate must record at least:

```text
exact upstream source;
pinned version or retrieval date;
license and commercial-use status;
data retention and training policy;
local / cloud processing boundary;
required permissions;
quota or free-tier volatility;
professional-domain benchmark result;
forbidden outputs and effects;
owner and review date.
```

Free availability is not authorization.

Catalogue visibility is not admission.

A model that answers well in a benchmark still returns candidates, not truth.

### Opik

Reviewed source: [`comet-ml/opik`](https://github.com/comet-ml/opik), retrieved 2026-07-14.

Accepted only as an external observability and evaluation candidate.

Capability Slot:

```text
abstract_capability: AI runtime observability and evaluation
candidate_binding: comet-ml/opik
installation_status: not installed
health_status: unknown / not checked
update_status: upstream active / update not authorized
activation_status: inactive
approval_status: not approved
rollback_status: not applicable before a bounded lab
```

Placement:

- Pantheon governs trace eligibility, purpose, scope, data class, redaction, sampling, retention, evaluation status, export status, activation, update and rollback gates.
- Hermes may emit minimized traces through a reviewed adapter and may run bounded evaluation campaigns under Task Contract.
- Pantheon Cockpit may project governed trace summaries, comparison results, limitations and links. Optional runtime clients may expose runtime interaction state only; neither surface installs the binding or silently intercepts content.
- Human approval is required before installation, activation, cloud transfer, raw-content capture, online evaluation, optimizer use or any prompt/tool mutation.
- No native Hermes binding was verified during this review. Generic OpenTelemetry support or an SDK wrapper is a candidate path only, not an implemented integration.

Required non-equivalences:

```text
trace_recorded != evidence
evaluation_score != approval
LLM_judge_pass != professional_validation
prompt_optimized != prompt_authorized
runtime_healthy != safe_for_professional_data
```

Forbidden placement:

```text
Opik as Pantheon runtime
Opik trace store as Evidence Pack
Opik score as approval gate
automatic optimizer activation
automatic prompt or tool mutation
automatic trace-to-register promotion
raw professional trace export without governed minimization
OpenWebUI filter installation without separate review
```

Bounded comparison target against Langfuse:

1. instrument the same five fictional governed Task Contracts;
2. compare trace completeness without hidden reasoning capture;
3. compare redaction, sampling, retention and export controls;
4. compare deployment footprint, access control, backup and rollback;
5. compare regression reports for scope, source, evidence and approval violations;
6. return an Evaluation Report Candidate, never an adoption decision.

The comparison itself remains non-implemented. No Opik Cloud transfer or self-hosted deployment is authorized by this record.

### iFixAi

Reviewed source: [`ifixai-ai/iFixAi`](https://github.com/ifixai-ai/iFixAi), commit [`b911e25fcdf9d49e0e025162f2650253072449e5`](https://github.com/ifixai-ai/iFixAi/commit/b911e25fcdf9d49e0e025162f2650253072449e5), observed 2026-07-15.

Accepted only as an external evaluation-method reference and watchlist item.

Observed scope at the pinned commit:

```text
Python package version 3.2.0 under Apache-2.0
up to 45 inspections: 32 core and 13 extended
structural checks plus LLM-judge evaluation paths
self-judge, independent-judge and multi-judge modes
OpenAI-compatible HTTP and provider-specific adapters
JSON and Markdown scorecards
content-addressed run manifests with fixture and rubric hashes
optional local resume checkpoints
Claude Code and Codex plugin surfaces plus generated agent skills
pseudonymous PostHog telemetry
```

Verification status:

```text
source review: performed against the pinned commit
README, LICENSE, pyproject, SECURITY and selected implementation paths: inspected
local installation: not performed
local test execution: not performed
live provider run: not performed
exact upstream CI result for the pinned commit: not established by this review
production suitability: not established
professional-data suitability: not established
```

Capability Slot:

```text
abstract_capability: bounded AI-system evaluation and regression diagnostics
candidate_binding: ifixai-ai/iFixAi
execution_owner: Hermes-side external lab runner only
installation_status: not installed
health_status: unknown / not checked in the target environment
update_status: upstream version 3.2.0 observed / update not authorized
activation_status: inactive
approval_status: not approved
rollback_status: not applicable before a bounded lab
```

Direct observations:

- The upstream README explicitly says the diagnostic is not a certification or safety guarantee.
- The package can evaluate a model or agent through provider SDKs or an OpenAI-compatible endpoint and may use a different provider, or several providers, as judges.
- Missing capability surfaces may produce `insufficient_evidence`; those results are reported but excluded from the aggregate score.
- Run manifests record versions, rubric hashes, fixture digests, judge configuration and other metadata in a content-addressed structure. The upstream reproducibility document states that live-provider scores are not reproducible because LLM outputs remain non-deterministic.
- At the pinned commit, the upstream `reproducibility.md` guide describes manifest schema version 2 while the upstream `manifest.py` implementation defines version 3; documentation/code alignment is therefore not established.
- Scorecards and resume checkpoints may contain full model inputs and outputs. The security policy says checkpoints are written mode `0600`, removed after successful completion and intentionally remain after an interrupted resumable run.
- Pseudonymous telemetry sends a persistent random installation identifier, version, operating system, surface and timestamps to PostHog in the United States. It is opt-out, disabled automatically in CI and documented as retained indefinitely.
- The upstream methodology recognizes that public inspection corpora can be memorized and warns against treating some passing results as deployment gates.
- Configuration stores the API-key environment-variable name rather than the secret, and the project includes provider-specific secret redaction for recognized error-log paths. This does not sanitize scorecards or checkpoints.

Reviewer inferences:

- A high grade may combine structural observations, declared fixture content, synthesized governance surfaces and LLM-judge verdicts. Pantheon must keep those evidence origins separate.
- An `insufficient_evidence` exclusion can improve the apparent aggregate while reducing measured coverage; coverage disclosure is therefore required beside every score.
- Independent judging reduces self-judging bias but increases external-provider disclosure, cost and data-handling surface.
- Content-addressed manifests strengthen traceability of declared inputs; they do not make live LLM judgments deterministic, professionally valid or sufficient evidence.

Unknown or unverified in this review:

```text
target-environment installation and dependency compatibility
real cost and latency for representative governed Task Contracts
provider-side retention and training behavior for transmitted evaluation content
access control, backup and deletion behavior around local scorecards and checkpoints
false-positive and false-negative rates on private agency fixtures
stability of grades across repeated live-provider runs
fitness for confidential, personal, contractual or regulated professional data
```

Useful patterns that may be distilled without adopting the runner:

```text
measurability coverage disclosed beside every aggregate score
declared governance demoted below runtime-observed behavior
insufficient evidence reported explicitly rather than converted to pass
self-judged and independent-judged results visibly separated
fixture, rubric, judge and version identity retained with the result
reproducibility claims bounded to deterministic replay conditions
```

Forbidden placement:

```text
iFixAi as Pantheon runtime or approval authority
letter grade as certification, proof, adoption decision or production gate
automatic installation through a Pantheon plugin or skill manager
automatic score-to-evidence, score-to-register or score-to-memory promotion
client or production data use before separate data-handling approval
silent multi-provider transmission of professional content
telemetry activation without visible status and governed opt-out
scorecard or checkpoint storage treated as safe merely because runtime succeeded
```

Required non-equivalences:

```text
evaluation_completed != evidence_sufficient
grade_A != approved
independent_judge != professional_validation
manifest_verified != live_result_reproducible
insufficient_evidence_excluded != coverage_sufficient
installed != approved
telemetry_disclosed != telemetry_authorized
```

Current decision:

```text
retain as an external evaluation-method reference
distill method patterns only
do not install
do not activate
do not run against client or production data
do not create a Pantheon dependency
revisit only through a separate bounded Hermes lab proposal
```

### LangGraph Agent Stack

Reviewed source: [`Brescou/langgraph-agent-stack`](https://github.com/Brescou/langgraph-agent-stack), commit [`f18b04ee78aae78abe61b694c22f1e8156dc9950`](https://github.com/Brescou/langgraph-agent-stack/commit/f18b04ee78aae78abe61b694c22f1e8156dc9950), retrieved 2026-07-14.

Accepted only as an external runtime and industrialization reference.

Observed scope:

```text
FastAPI API and SSE streaming
LangGraph agents and typed domain packs
pack registry, versions and traffic weights
provider, memory and connector abstractions
cost limits, metrics and output guards
human-review queue for regulated packs
standalone interrupt/resume example
Docker, Helm, Terraform, SBOM and image-signing workflows
```

Verification status at the pinned commit:

```text
source review: performed
local dependency sync: performed with uv --frozen
local pytest: 801 passed, 33 skipped, 1 failed
failure cause: optional anthropic dependency absent from the minimal sync
local lint and format: passed
local type check: 0 errors, 29 optional-dependency warnings
upstream CI result for exact SHA: not established by this review
production suitability: not established
```

The local checks qualify the observed repository state. They do not prove production readiness, professional-data suitability or integration safety.

Capability Slot:

```text
abstract_capability: stateful multi-agent workflow orchestration
candidate_binding: Brescou/langgraph-agent-stack
execution_owner: Hermes-side external runtime only
installation_status: not installed
health_status: unknown / not checked in the target environment
update_status: upstream active / update not authorized
activation_status: inactive
approval_status: not approved
rollback_status: not applicable before a bounded lab
```

Placement:

- Pantheon governs binding eligibility, scope, evidence requirements, version admission, activation, update and rollback gates.
- Hermes may execute a specialized binding only under Task Contract after a demonstrated capability gap and separate approval.
- Pantheon Cockpit may project governed binding status, evaluation summaries, limitations and approval requests. Optional runtime clients may expose runtime interaction status only; neither surface hosts the graph runtime or mutates traffic weights.
- Human approval is required before installation, activation, provider or connector configuration, professional-data use, plugin loading, traffic-shift mutation or external-effect execution.
- The project remains a separate execution runtime. Calling one of its directories `control_plane` does not give it Pantheon governance authority.

Useful patterns that may be distilled without adopting the runtime:

```text
strict typed input and output contracts for domain packs
explicit pack versions and recorded version used
deterministic golden-dataset evaluation before traffic changes
per-run cost ceilings and bounded stream timeouts
allowlisted third-party pack discovery
SBOM generation and signed container images
LangGraph interrupt/resume before an irreversible action
```

Boundary findings:

- The main regulated-pack review queue records approval or rejection after output generation; queue creation is best effort and cannot be treated as a blocking Pantheon approval gate.
- A correct pre-action `interrupt()` / `Command(resume=...)` pattern exists only as a standalone example in the reviewed repository, not as the default API review path.
- The pack-weight API can mutate traffic allocation directly. Any future adapter must convert that mutation into proposal, human approval, activation observation and rollback evidence.
- The stack owns orchestration, provider selection, operational memory, connectors and plugin discovery. Adopting those responsibilities wholesale would duplicate Hermes and collapse the execution boundary.
- OAuth2/OIDC, scoped professional identity, tenant governance and production hardening remain operator responsibilities; infrastructure templates and security checks are not proof of safe deployment.

Required non-equivalences:

```text
pack_registered != dependency_adopted
pack_weight_changed != activation_authorized
review_recorded != action_approved
runtime_success != evidence
health_ok != safe_for_professional_data
interrupt_example_present != governed_HITL_implemented
```

Forbidden placement:

```text
LangGraph Agent Stack as Pantheon runtime
its control_plane as Pantheon governance authority
its review store as Pantheon approval authority
its run history or checkpoints as canonical memory
its provider factory as Pantheon provider router
its plugins as automatically approved capabilities
direct traffic-weight mutation without Pantheon gate
automatic result-to-evidence or result-to-register promotion
```

Current decision:

```text
retain on the external watchlist
distill patterns only
do not install
do not activate
do not create a Pantheon dependency
do not add a Hermes binding without a demonstrated capability gap
```

### Hermes Uplink

Reviewed source: [`mr-september/hermes-uplink`](https://github.com/mr-september/hermes-uplink), retrieved 2026-07-14.

Refused as a Pantheon Next integration and retained only as an external UX reference.

Placement:

- Pantheon may govern a remote-access policy, but it does not host or execute Uplink.
- Hermes would remain the execution runtime reached by the client.
- Pantheon Cockpit remains the governed projection surface; Uplink must not become a parallel decision or approval surface, and no runtime client is selected by this register.
- Human approval would be required before any remote endpoint, shared credential, gateway restart, automatic start or public tunnel.
- The reviewed project is oriented toward native Windows and direct Hermes access. Compatibility with the current containerized architecture is not established.

Useful patterns that may be distilled without adopting the runtime:

```text
mobile-first session list
resume existing Hermes sessions
low-bandwidth streamed turns
clear local / remote availability state
explicit credential warning
```

Forbidden import:

```text
direct Hermes bypass around the consequential chokepoint
single shared credential as governed identity
public Funnel endpoint as default cockpit access
full session or capability exposure without per-scope authorization
launcher-driven Hermes configuration as Pantheon behavior
Uplink status treated as Hermes safety or Pantheon approval
```

Reference visibility is not adoption.

## Current decision

```text
GSAP skills -> Hermes skill candidate.
Browser Eyes MCP -> Hermes privileged MCP skill candidate.
Rowboat -> external reference / possible adapter candidate.
Spice -> external reference / UX and method distillation only; refused as core or decision runtime.
PaddleOCR -> dashboard-installable, Hermes-managed document extraction candidate; no Pantheon dependency.
Awesome Free Models -> external tooling watchlist source only; may seed candidates, never approve them.
Opik -> external observability and evaluation candidate; compare with Langfuse before any bounded lab.
iFixAi -> external evaluation-method reference only; distill coverage and provenance patterns, do not install or use as an approval gate.
LangGraph Agent Stack -> external runtime reference only; distill industrialization patterns, do not adopt as Pantheon or default Hermes runtime.
Hermes Uplink -> external UX reference only; refused as an integration or parallel cockpit.
```

Do not add any of these to Pantheon core.

Do not call them implemented until a real Hermes skill, adapter, profile or integration exists outside Pantheon and has been reviewed.
