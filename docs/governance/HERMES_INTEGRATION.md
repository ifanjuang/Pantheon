# Hermes Integration

Status: active doctrine — integration boundary stabilization.
Boundary profile: active_governance_doctrine.

Hermes Agent is the selected external execution runtime for Pantheon-governed work.

Pantheon Next does not implement Hermes Agent.

Pantheon Next does not install Hermes Agent.

Pantheon Next does not own Hermes internal runtime state.

A runtime client is optional and replaceable.

Pantheon Cockpit is the governed projection surface, not a second Hermes runtime client.

```text
Optional runtime client     -> runtime interaction
Hermes Agent                -> admitted reasoning / runtime execution
Pantheon effect owner / PEP -> exact consequential external effect
Pantheon Cockpit            -> governed Cards, status, Evidence gaps and decisions
Pantheon Next               -> governance / PDP responsibility
human                       -> consequential decision
```

```text
client selected != authority transfer
runtime success != Evidence
projection != persistence
approval UI != Pantheon approval
```

## 1. Purpose

This document owns the stable governance boundary between Pantheon Next and Hermes Agent.

It defines:

- what Pantheon may provide to Hermes;
- what Hermes may return;
- where Policy Decision Point and Policy Enforcement Point responsibilities sit;
- how Task Contracts, Evidence, approval, memory and external effects remain separated from execution;
- how optional runtime clients and Pantheon Cockpit project different classes of state.

It does not define:

- Hermes installation;
- a Hermes release pin;
- provider routing;
- Hermes internal workers, queues, retries or scheduling;
- a client implementation;
- a browser automation adapter;
- a Kanban runtime;
- a simulation runtime;
- an observability backend;
- an automatic approval system;
- an automatic memory system.

Release- and feature-specific review belongs to `HERMES_RUNTIME_SURFACE_REVIEW.md` and other bounded candidate owners. Historical review material formerly absorbed into this file remains available in the private Pantheon-Next archive; it is not current integration authority.

## 2. Stable responsibility split

Pantheon governs legitimacy.

Hermes executes admitted reasoning and runtime work externally.

Consequential-effect enforcement belongs to an effect-specific Pantheon-owned
PEP / adapter outside Hermes' internal hook chain. Before a governed task is
launched, its admitted capability and tool surface must exclude any raw
consequential route or credential that could bypass that owner.

The current Pantheon decision interface is the bounded policy service described by `mcp-server/docs/HTTP_API_CONTRACT.md`.

That service exposes deterministic policy/preflight decisions as the Policy
Decision Point; it does not perform the consequential effect. The exact
effect-specific owner may perform the external operation after the applicable
PDP / canonical Decision / one-use checks have passed. This does not make the
Pantheon kernel an execution runtime.

Optional runtime clients expose interaction with the execution runtime.

Pantheon Cockpit projects governed professional state.

The human makes consequential decisions when required.

```text
runtime interaction != governed projection
governed projection != persistence
PDP decision != effect executed
PEP success != Evidence
human interaction != approval unless the exact gate records it
```

Hermes WebUI is one optional/proposed runtime-client candidate. Its upstream availability does not make it required, installed, selected, qualified or authoritative.

```text
Hermes WebUI available != Hermes WebUI selected
Hermes WebUI selected != Pantheon authority transferred
```

## 3. Kernel versus runtime adapter

Hermes version changes are adapter/review events by default.

Pantheon follows the latest published stable Hermes release. A new stable Hermes release moves the runtime qualification target; Pantheon adapts its bindings, tests and projections rather than holding Hermes on an older release to preserve a historical integration assumption.

Stable Hermes features are embraced as runtime capabilities by default. They do not require a matching Pantheon object, Role, Rite, Profile or service merely because they exist, and they do not inherit Pantheon authority.

They do not rewrite the Pantheon kernel unless they reveal a missing tool-agnostic governance distinction.

Pantheon owns concepts such as:

```text
truth / claim status
scope
Evidence status
approval status
memory / Register status
external-effect legitimacy
capability placement
Task Contract boundary
User Decision Gate
```

Hermes owns runtime mechanics such as:

```text
profiles
skills
tools
MCP connections
connectors
runtime plugins
subagents
delegation
bot / groupchat coordination
goal-style iteration
Kanban / task-graph coordination
background tasks
scheduling / automation
provider configuration
messaging channels
runtime memory mechanics
runtime traces
runtime-client interaction state
```

```text
runtime feature added != Pantheon authority added
runtime feature available != task authorized
runtime configuration != governance doctrine
new stable release != reason to preserve an older Hermes runtime
```

## 4. Consequential-effect chokepoint

A consequential effect is an effect that can materially produce, if wrong or unauthorized:

```text
false governed status
external transmission or mutation
wrong Register entry
invalid approval
illegitimate scope expansion
professional or contractual consequence
```

Before such an effect occurs, the exact effect-specific PEP must consult the
Pantheon policy decision appropriate to that effect. That PEP is a Pantheon-owned
integration boundary, not a Hermes-internal hook.

Before launch:

```text
raw consequential provider tool / credential
-> not admitted to Hermes

governed effect-request capability
-> may be admitted when the Task Contract permits it

pre_tool_call
-> optional defense in depth only
-> never the sole effect boundary
```

Conceptually:

```text
Task Contract / governed request
        |
        v
Execution Admission / admitted tool envelope
        |
        v
Hermes reasoning / runtime work
        |
        +--> Result Candidate / Runtime Observation
        |
        +--> Effect Request Candidate
                    |
                    v
          Pantheon effect owner / PEP
                    |
                    v
          Pantheon policy check (PDP)
          + canonical Decision / gate
                    |
          +---------+-------------------+
          |                             |
          v                             v
        block                     allow exact effect
                                        |
                                        v
                               consequential effect
                                        |
                                        v
                           Outcome Observation Candidate
```

Pantheon core and the PDP do not perform the effect. The effect-specific
owner/PEP may perform the exact external operation. Credentials or provider
routes whose possession would allow bypass must remain with that owner rather
than with the Hermes runtime.

Hermes must not substitute model judgment, runtime smart approval, client UI
state or a successful `pre_tool_call` hook for the policy check when the effect
requires it.

The effect-specific PEP is responsible for:

- fail-closed behavior when required policy is unavailable;
- validating the applicable gate signals and exact effect payload;
- consuming one-use authorization/idempotency state where relevant;
- performing the external operation only after the gate is satisfied;
- returning a truthful technical outcome observation.

A Hermes-side guard such as `pre_tool_call` may reject an illegitimate request
earlier, but loss, bypass or failure of that guard must not make the raw effect
reachable.

```text
pre_tool_call != Pantheon PEP
runtime approval != Pantheon Decision
policy allow != effect executed
signed decision != one-use consumption
runtime retry != renewed authorization
guard bypassed != effect boundary bypassed
```

## 5. What Pantheon may provide to Hermes

Pantheon may provide bounded governance artifacts and references such as:

```text
Task Contract
Execution Admission when applicable
Context Pack
source references
Role viewpoint request
capability/binding constraints
approval expectation
Evidence expectation
memory / Register rule
risk note
output expectation
User Decision Gate requirement
```

These artifacts constrain execution.

They do not define Hermes internal worker topology, queue progression, retry policy, provider route or tool dispatch.

A Task Contract is not a runtime job.

Execution Admission, where used, authorizes one exact bounded execution opportunity; it is not a tool router.

## 6. What Hermes may return

Hermes may return candidate and technical observation material such as:

```text
Result Candidate
Evidence Pack Candidate
Patch Candidate
Register Candidate
Capability Gap
Risk Escalation
Review Note
Output Artifact Reference
Outcome Observation Candidate
Runtime Trace Reference
Deliberation Candidate when separately admitted
```

Everything returned keeps its own status.

```text
Hermes done != Pantheon approved
runtime output != Evidence
Evidence Pack Candidate != admitted Evidence Pack
runtime trace != proof
candidate retained != canonical
```

Hermes must report partial, blocked, failed or unknown outcomes instead of flattening them into success.

## 7. Task Contract boundary

A Task Contract is expected when work includes material risk, protected mutation, external effects, consequential tool use, memory/Register proposals or other governed boundaries.

Hermes may decide how to execute inside that boundary.

Hermes must stop or return a Capability Gap when execution requires broader scope, stronger permissions, another source class, another external effect or another approval ceiling.

```text
scope gap != permission to widen scope
tool available != tool authorized
provider available != provider authorized for the data
```

## 8. Runtime clients

Runtime clients are interaction surfaces, not governance owners.

They may expose:

- sessions and conversation;
- model/runtime controls;
- technical task status;
- tool-call status;
- candidate outputs;
- runtime workspace views;
- runtime-side approval or safety affordances.

Those features remain runtime features.

They must not silently become:

- Pantheon human approval;
- Evidence admission;
- memory/Register promotion;
- canonical source authority;
- governance persistence;
- Task Contract authorization.

Hermes WebUI may be selected as one such client after separate deployment/security qualification. Because upstream can run Hermes Agent in-process, it must be evaluated as a real runtime surface rather than assumed to be a passive skin.

```text
runtime approval card != Pantheon approval
workspace file visible != source admitted
client memory != Registre Probatoire
client retrieval != Evidence
```

## 9. Pantheon Cockpit

Pantheon Cockpit is the governed projection surface for professional state.

It may project:

```text
Cards
Work status
Task Contract status
Evidence Packs and Evidence gaps
User Decision Gates
approval state
Register Candidates
risk and limitation summaries
Run Trace Views / bounded execution summaries
```

It does not become Hermes chat, a generic runtime dashboard or an execution engine.

```text
Cockpit projection != persisted authority
Cockpit button != runtime authorization unless the governed action contract says so
Cockpit visible != approved
```

## 10. Evidence boundary

Hermes may produce evidence-relevant material, but Pantheon owns the governance semantics for Evidence.

A governed return should preserve, as applicable:

```text
linked Task Contract
sources used
source versions / locators
assumptions
limitations
material actions
outputs
risks
scope gaps
approval gap
memory/Register impact
runtime outcome references
```

Raw runtime logs, hidden reasoning, private scratchpads and provider traces are not Evidence Packs.

Technical traces may be referenced when useful for reproducibility or diagnosis.

```text
trace recorded != Evidence admitted
citation present != source verified
runtime observation != professional conclusion
```

## 11. Source and retrieval boundary

Hermes may perform bounded retrieval through admitted source paths and bindings.

The source/retrieval model is owned by `SOURCE_INGESTION_RETRIEVAL_MODEL.md` and related capability owners, not by the runtime client.

Hermes must preserve:

```text
source identity
scope
provenance
coverage
limitations
retrieval status
```

Direct source/context access is valid when sufficient. A vector store, RAG product or client Knowledge feature is not required by this integration boundary.

Hermes must not infer:

```text
available source == authorized source
retrieved == true
retrieved == Evidence
not returned == absent
repeated retrieval == memory
```

## 12. Memory boundary

Hermes runtime memory is runtime state.

Pantheon governed durable retention remains separate.

Hermes may propose Register Candidates when the Task Contract permits it.

Hermes must not promote a Registre Probatoire entry.

Runtime memory mechanisms, client memory, session history, profile notes, caches and external memory providers do not acquire Pantheon authority through use.

```text
runtime memory != Registre Probatoire
memory recalled != source verified
provider selected != memory admitted
conversation synchronized != Register Candidate accepted
```

Current runtime-memory qualification, if any, belongs to the relevant runtime/provider review and deployment profile, not this stable integration boundary.

## 13. Roles and profiles

Pantheon Roles are governance responsibilities.

Hermes profiles are execution profiles.

A profile may be shaped to support a role-aligned task, but it does not inherit the Role's authority.

```text
Hermes profile != Pantheon Role
model viewpoint != governance authority
profile selected != approval
```

Canonical Role authority remains with `AGENTS.md` and related governance owners.

Profiles may produce candidates. They must not self-approve, promote memory, mutate doctrine outside authorization or impersonate ZEUS/human decision.

## 14. Deliberation and subagents

Hermes may use subagents, multiple models or other runtime decomposition when the admitted runtime/binding supports it and the Task Contract permits it.

Pantheon does not define the hidden execution topology.

The governed return must preserve material dissent, missing slots, scope gaps and Evidence gaps when those affect the result.

```text
more models != more truth
model agreement != Evidence
aggregator synthesis != ZEUS arbitration
subagent success != approval
```

Topology-specific candidates belong to their dedicated review owners such as `LANGGRAPH_RUNTIME_CANDIDATE.md`, `EVALUATION_AND_SIMULATION_CANDIDATE.md` or other admitted external-runtime notes; they do not enlarge this boundary automatically.

## 15. Tools, skills, MCP and plugins

Hermes may expose external capability surfaces such as skills, tools, MCP servers or plugins.

Their presence is runtime availability only.

Pantheon reuses existing Capability, binding, Task Contract and external-tool governance rather than creating a Hermes-specific authority path.

```text
skill installed != capability approved
plugin present != plugin adopted
MCP server reachable != tool authorized
binding selected != dependency adopted
tool call success != Evidence
```

Portable packaging such as Agent Plugins remains an external interoperability concern under `AGENT_PLUGINS_INTEROPERABILITY.md`.

## 16. Messaging and external channels

Hermes may interact through messaging or other external channels when a selected runtime configuration provides them.

Inbound content is source material, not proof.

Outbound delivery is an external effect when it reaches another party or system.

For consequential outbound actions, preserve at least:

```text
recipient / destination
approved content revision or digest
effect type
Task Contract / decision reference
idempotency key when retries can duplicate the effect
technical outcome
```

```text
message received != approval
reply drafted != sent
sent != true
retryable != safely repeatable
```

## 17. Repository and artifact mutation

Hermes may prepare Patch Candidates and may perform bounded repository operations only when the applicable authorization and protected-path rules allow it.

Repository change discipline remains independent of runtime success.

```text
patch produced != merge decision
commit created != doctrine approved
CI green != deployment authorized
```

## 18. Capability gaps

Hermes must expose missing or unsafe prerequisites rather than hiding them.

Capability gaps may include:

```text
missing source
missing tool
missing permission
missing context
missing approval
unsupported task
protected area touched
scope exceeds contract
external dependency not verified
binding not qualified
runtime version not reviewed
client not qualified
```

A Capability Gap is a governance-relevant signal, not an invitation to widen scope automatically.

## 19. Runtime currentness and release review

This stable document must not carry a permanently frozen claim that one historical Hermes version is the current runtime.

Release-specific review belongs to:

- `HERMES_RUNTIME_SURFACE_REVIEW.md` — reviewed external release and surface mapping;
- `HERMES_RUNTIME_GOVERNANCE.md` — runtime capability placement;
- `HERMES_RUN_LAUNCH_JUNCTION.md` — candidate Runs API launch junction;
- `HERMES_CAPABILITY_BINDINGS.md` — optional binding governance;
- deployment/operator artifacts for the exact installed instance.

The latest published stable Hermes release is always the current qualification target. The exact commit/ref remains pinned so tests and observations are reproducible, but the pin is a moving qualification snapshot rather than a compatibility ceiling.

```text
new stable release published
-> qualification target moves
-> pin / adapter / tests are refreshed
-> current target is requalified
-> Pantheon bindings adapt where needed
```

A compatibility failure is classified and repaired in the nearest existing adapter, binding, Skill, Method, context owner or runtime qualification. The normal response is not to keep an older Hermes release. If a newly available capability is unsafe for a consequential task, Pantheon governs that task/effect rather than pretending the capability does not exist.

Before claiming an operational Hermes capability, verify the exact deployed release, binding, profile, tool surface and relevant acceptance evidence.

```text
latest stable selected != deployed instance updated
release reviewed != professional capability validated
runtime feature available != task authorized
repository implementation != deployment
endpoint documented != live instance compatible
profile created != profile qualified
```

Version-specific historical material removed from this active boundary remains in the private Pantheon-Next archive.

## 20. Optional Hermes WebUI posture

Hermes WebUI is a proposed optional runtime-client surface, not a Pantheon dependency.

If selected, qualify at least:

```text
exact version / commit or artifact
network exposure and authentication
secret handling
filesystem/workspace access
runtime tool visibility
runtime memory behavior
approval-card semantics
attachment handling
in-process versus gateway-backed Hermes execution
logging / trace posture
rollback / disable path
```

The qualification must demonstrate that client convenience cannot widen the already admitted Hermes/Pantheon boundary.

No Pantheon schema, role, Evidence rule or approval rule changes merely because a WebUI is selected.

## 21. Forbidden drift

This integration must never become:

- a Pantheon execution runtime;
- a Pantheon scheduler or queue;
- a Pantheon provider router;
- a Pantheon-owned Hermes worker graph;
- a client-specific governance authority;
- an automatic approval bridge;
- an automatic memory promotion path;
- a hidden tool authorization mechanism;
- a route where runtime success becomes truth or Evidence;
- a route where Cockpit projection becomes persistence.

If Hermes must widen scope silently to complete a task, the boundary has failed.

If a runtime client can grant Pantheon approval merely by UI state, the boundary has failed.

If Pantheon must replay or own Hermes runtime state to govern the result, the boundary has failed.

## 22. Final invariants

```text
Pantheon governs; Hermes executes admitted runtime work.
Pantheon-owned effect owner / PEP remains outside Hermes internals.
PDP decision != PEP execution.
pre_tool_call != Pantheon PEP.
execution success != authorization.
runtime output != Evidence.
retrieved != true.
runtime memory != Registre Probatoire.
Hermes profile != Pantheon Role.
client selected != authority transfer.
Hermes WebUI available != Hermes WebUI selected.
projection != persistence.
Cockpit display != approval.
human consequential decision remains explicit when required.
```

The stable integration boundary stays deliberately small. Runtime reach, clients, providers, plugins and execution techniques may evolve outside Pantheon without turning those implementation choices into governance authority.
