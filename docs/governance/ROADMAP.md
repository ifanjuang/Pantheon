# Pantheon Next Roadmap

Status: active support doctrine — outcome-oriented repository roadmap — implemented as documentation.
Boundary profile: active_support_doctrine.

This roadmap states the next governed outcomes for Pantheon Next. It is not a document inventory, a release checklist or a runtime implementation plan.

Use the repository status spine for current facts:

```text
STATUS.md          -> current repository posture and unresolved clusters
WHAT_RUNS.md       -> what actually runs, is static, is partial or is absent
AUTHORITY_INDEX.md -> authority and repository state
MODULES.md         -> ownership and boundary by governance area
```

If this roadmap conflicts with that spine, the status spine wins.

## Doctrine

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`:

```text
compatible Hermes clients -> runtime interaction
Hermes Agent              -> external execution / PEP
Pantheon policy service   -> bounded deterministic PDP interface
Pantheon Cockpit          -> governed projections and review/decision surfaces
Pantheon Next             -> governance authority and consequential status
human                     -> consequential decision when required
```

Pantheon may govern consequential status: truth, memory, Evidence, approval, scope, external action, activation, proposed installation, update authorization, runtime-health visibility and rollback visibility.

Pantheon must not become an execution runtime, installer authority, scheduler, queue, provider router, plugin manager, memory engine, automatic approval system or external sender.

## Current position

Status: partial but structurally coherent.

### Repository and monorepo boundary

Outcome: established.

Current posture:

- Pantheon Next is the canonical governance repository and monorepo host;
- the former standalone `pantheon-mvp` repository is historical provenance only;
- executable candidate behavior is co-located under `implementation/`;
- co-location does not imply adoption, activation, deployment or authority transfer;
- the repository root remains deliberately non-distributable;
- protected-path review and repository checks remain the normal change path.

### Governance kernel

Outcome: coherent baseline under controlled consolidation.

Current posture:

- roles, Task Contracts, Evidence, approvals, scope, Knowledge, runtime-memory and Registre Probatoire boundaries are documented;
- capability placement, external-runtime and client boundaries are explicit;
- status headers, boundary profiles and non-equivalence rules reduce free-form drift;
- the remaining work is primarily convergence: reduce duplicated owners, retire stale vocabulary and turn important invariants into existing schemas and tests rather than more prose.

### Policy and verification surfaces

Outcome: implemented read-only / partial.

Current posture:

- `mcp-server/` carries the bounded policy/verification distribution;
- the same bounded policy meaning is projected through local MCP and authenticated internal HTTP;
- policy decisions are returned as data and do not execute consequential effects;
- CI and the Governance Doctor provide structural verification, not adoption or professional validation.

Exact runtime enforcement and deployment observations remain owned by `WHAT_RUNS.md` and the relevant implementation and review artifacts; this roadmap does not restate their fast-moving state.

### Candidate implementation and Cockpit

Outcome: executable candidate / not adopted.

Current posture:

- `implementation/` contains candidate persistence, APIs, document/Knowledge paths, Hermes seams and Cockpit foundations;
- Pantheon Cockpit is executable and tested as a candidate governed projection surface;
- Card/navigation/projection success does not create authorization or persistence authority;
- live deployment, real-data bindings, operational acceptance and professional validation remain separate decisions.

### External execution and operator deployment

Outcome: bounded external-runtime and operator candidates exist; production adoption remains separate.

Current posture:

- Hermes Agent is the selected external execution runtime;
- Hermes Web/dashboard is the selected interaction baseline, with compatible clients remaining replaceable;
- Obsidian/Hindsight is a qualified optional reference composition, not a Pantheon prerequisite;
- `deployment/ubuntu/` contains an operator bootstrap candidate for a bounded Ubuntu node; its existence is not a turnkey agency product or production authorization.

### Professional use

Outcome: not adopted for real professional dossiers by repository presence alone.

Real professional use still requires the applicable deployment, source, confidentiality, Evidence, approval, rollback and human-authority conditions. Synthetic qualification and sanitized professional patterns may improve confidence without becoming professional validation.

## Governed outcomes

### R1 — Keep the current-state surfaces converged

Status: in progress.

Target outcome:

```text
one short stable read path
+ public pages and diagrams aligned with the same owners
+ no retired product presented as current architecture
+ status spine remains the factual source for fast-moving state
```

Exit criteria:

- active public/readme/diagram surfaces do not present OpenWebUI, Paperless or the former standalone `pantheon-mvp` topology as current owners;
- `implementation/` is consistently described as co-located candidate, not adopted runtime authority;
- public explanation distinguishes execution, governance, persistence and projection;
- currentness regressions that are cheap to express are held by existing checks rather than recurring manual audits.

### R2 — Reduce governance ontology and owner duplication

Status: in progress.

Target outcome:

```text
canonical concepts stay few
+ lifecycle functions reuse existing Roles and gates
+ candidates converge into existing owners
+ duplicated public/support descriptions are reduced
```

Exit criteria:

- lifecycle, workflow and memory documents do not introduce parallel canonical Role identities without a separate promotion decision;
- one responsibility has one discoverable owner;
- candidate documents have an explicit promote / merge / archive / refuse path;
- navigation cost decreases rather than moving duplication to another index.

### R3 — Make consequential boundaries observable and enforceable

Status: active implementation and verification work; exact state belongs to `WHAT_RUNS.md`.

Target outcome:

```text
policy meaning is deterministic
+ consequential entry points declare their guard regime
+ required PDP/PEP paths fail closed when selected
+ runtime success remains separate from Evidence and approval
```

Exit criteria:

- every consequential mutation path has a reviewable guard owner;
- the deployed target can demonstrate the applicable Pantheon policy round-trip where required;
- local guards, policy checks, human approval and technical outcome remain distinguishable;
- no client UI state substitutes for Pantheon approval.

### R4 — Prove one complete professional vertical on non-production data

Status: qualification in progress.

Reference vertical:

```text
architecture_devis_reprise
```

Target loop:

```text
bounded Task Contract
-> admitted source/context acquisition
-> Hermes external execution
-> Result Candidate + Evidence Pack Candidate
-> Pantheon structural/policy review
-> governed Cockpit projection where useful
-> explicit human decision
-> rollback / reproducibility evidence
```

Exit criteria:

- source identity, retrieved context, runtime output, Evidence and human decision remain distinct;
- the professional method owner is reused rather than duplicated in the runtime;
- contradictions, missing information and currentness limits stay visible;
- the run is reproducible on bounded non-production material;
- observed gaps become separate owner-coherent changes rather than hidden exceptions.

### R5 — Qualify deployment, then decide adoption

Status: blocked on sufficient end-to-end evidence, not on repository presence.

Target outcome:

```text
operator bootstrap candidate
-> exact reviewed component identities
-> install / update / rollback observations
-> bounded external-runtime path
-> one accepted vertical
-> explicit adoption decision
```

Possible decisions remain:

```text
refuse adoption
continue a bounded trial
adopt one binding for one scope
request more evidence
```

Adoption remains separate from installation, health, enablement, qualification and runtime success.

## Work-selection rule

Before adding a new permanent model or document, answer:

1. Which existing owner cannot express the needed rule?
2. What observed consequence requires the addition?
3. What referent will support promotion?
4. What is the exit criterion: promote, merge, archive or refuse?
5. Does the proposal reduce or increase repository navigation and maintenance cost?

Default:

```text
reuse native/runtime behavior when sufficient
-> extend an existing owner
-> encode an invariant in an existing schema/test when useful
-> add a new owner only for a genuinely distinct responsibility
```

## Current priority order

```text
1. close active public/current-state drift
2. converge lifecycle and Role/gate ownership without ontology growth
3. finish consequential-boundary verification and target enforcement evidence
4. execute and review one complete non-production professional vertical
5. qualify the operator deployment path and rollback
6. decide adoption from evidence
```

## Final rule

```text
Do not expand the doctrine to avoid testing it.
Reduce.
Stabilize owners and contracts.
Run one bounded vertical.
Measure the gaps.
Promote, merge, archive or refuse.
```
