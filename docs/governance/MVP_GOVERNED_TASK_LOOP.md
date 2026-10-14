# MVP Governed Task Loop

Status: candidate support doctrine — bounded governed-loop contract; co-located candidate implementation exists.

Date: 2026-07-07
Schema reconciliation: 2026-07-13 — issue Pantheon-Next#359.
Architecture convergence: 2026-08-27 — issue Pantheon-Next#666.

Current repository posture: a bounded co-located candidate implementation exists under `implementation/mvp_vertical/` for Task Contract validation and perimeter enforcement, scoped retrieval and Result/Evidence Pack candidate production, terminal human-decision recording, and Register Candidate proposal after distinct retention authorization. A historical end-to-end synthetic demonstration on the fictive `devis_reprise` dossier is recorded in the private Pantheon-Next archive.

That implementation and demonstration do not establish adoption, production readiness, authenticated user identity, professional correctness or Evidence sufficiency.

```text
implementation_present != adopted
synthetic_demonstration != real_dossier_acceptance
runtime_success != authorization
retrieved != truth
memory != Evidence
```

## Purpose

This document specifies the smallest complete governed task loop. It is doctrine, not a runtime architecture and not a product stack prescription.

```text
interaction  -> Hermes Web/dashboard or another compatible replaceable Hermes client
execution    -> Hermes Agent
retrieval    -> scoped replaceable retrieval binding when needed
governance   -> Pantheon contracts, Evidence and decision rules
projection   -> Pantheon Cockpit when governed review/status projection is useful
decision     -> human/professional actor when required
```

No client, retrieval provider, vector store, runtime completion or UI projection becomes an authority by being present in the loop.

## The loop — nine steps

1. **A compatible Hermes client captures the request.** The practitioner states the task and selects or identifies the working perimeter. The client captures interaction; it decides nothing.
2. **Pantheon produces or validates a Task Contract.** The request is classified and bounded by scope, forbidden scope, expected output status, Evidence expectations and approval ceiling. See `docs/governance/examples/mvp_task_contract.yaml`.
3. **Hermes Agent executes inside the authorized perimeter.** Hermes reads allowed inputs and performs bounded work. Anything outside the contract is refused or reported as a Capability Gap.
4. **Retrieval, when needed, serves finding only.** A scoped retrieval implementation returns attributable candidate passages. Direct Hermes source/context access is equally valid when sufficient. A retrieved passage is not truth or Evidence merely because it was found.
5. **Hermes returns a Result Candidate plus a conforming Evidence Pack Candidate.** The candidate object carries sources, assumptions, limitations, contradictions and unresolved risks in the governed shape required by the review/decision path. See `docs/governance/examples/mvp_evidence_pack_candidate.yaml`.
6. **A governed projection exposes review state.** The Pantheon Cockpit, another bounded governed projection, or a compatible client may display candidate status, sources, gaps and available decisions. Projection is not persistence or approval.
7. **The human decides when the gate requires it.** The closed MVP decision vocabulary is `approve`, `refuse`, `request_revision`, `request_more_evidence`. No runtime, score, timeout or UI control widens or substitutes that decision.
8. **Pantheon records the Decision Record.** The record binds the decision to the exact reviewed Result Candidate and conforming Evidence Pack Candidate through the existing identity/digest contract. See `docs/governance/examples/mvp_decision_record.yaml`.
9. **Durable retention requires both result approval and separate retention authorization.** A Register Candidate may be proposed only when the reviewed decision is `approve` and an explicit `retention_authorization` is also present; `refuse`, `request_revision` and `request_more_evidence` cannot authorize retention. The resulting Register Candidate remains subject to its own admission path. See `docs/governance/examples/mvp_memory_candidate.yaml`.

## Canonical MVP decision vocabulary

The machine-readable owner remains `schemas/mvp_governed_loop_objects.schema.yaml#/$defs/decision_value`. The co-located implementation reads that canonical contract through the existing `pantheon_contracts` seam rather than vendoring a second schema owner.

```text
approve
refuse
request_revision
request_more_evidence
```

Semantics:

- `approve` accepts the reviewed candidate for the declared review scope only; it does not by itself authorize an unrelated external effect or retention;
- `refuse` rejects the candidate and authorizes no downstream consequence;
- `request_revision` requires a new candidate;
- `request_more_evidence` keeps the review unresolved until additional support is supplied.

No second vocabulary owner is needed.

## Identity boundary

Decision identity is qualified by what the interaction/authentication layer can actually establish.

```text
terminal stand-in        -> identity_assurance: declared
authenticated session    -> identity_assurance: authenticated + authenticated_principal
```

The selected client or surrounding authentication infrastructure supplies session identity when available. Pantheon governs the Decision Record shape and status; it does not fabricate authentication and the client does not gain governance authority from authenticating a user.

## Retrieval boundary

Retrieval is capability/provider agnostic.

```text
governed source perimeter
-> optional scoped retrieval implementation
-> attributable candidate context
-> task reasoning
-> Evidence only through existing Evidence owners
```

Rules:

- scope precedes ranking;
- every returned item retains source/provenance identity;
- untraceable material is a gap, not silently trusted context;
- direct source access is valid when retrieval infrastructure adds no demonstrated value;
- `pgvector` may be a demonstrated binding, not an architectural requirement;
- indexes and embeddings do not become professional source identity or Evidence owners.

## Explicit non-equivalences

```text
indexed != Evidence
retrieved != truth
runtime_success != authorization
client display != authority
projection != persistence
Hermes output != Registre Probatoire entry
provider selected != authority transfer
```

Memory retention is never authorized implicitly by loop completion, and external effects are never implicit loop side effects. Consequential effects use their existing authorization/gate owners.

## What this MVP is not

The loop does not require or create:

```text
a Pantheon agent runtime
a scheduler or queue
a provider router
a plugin manager
a canonical RAG framework
a mandatory vector database
a second generic chat UI
automatic approval
automatic memory promotion
automatic external sending
```

If an implementation appears to require one of these, first verify whether Hermes or an existing owner already supplies the capability.

## Object owners

The illustrative examples remain structural fixtures aligned with `schemas/mvp_governed_loop_objects.schema.yaml`:

- `docs/governance/examples/mvp_task_contract.yaml` — Task Contract candidate;
- `docs/governance/examples/mvp_evidence_pack_candidate.yaml` — Evidence Pack Candidate;
- `docs/governance/examples/mvp_decision_record.yaml` — human decision record;
- `docs/governance/examples/mvp_memory_candidate.yaml` — historical plain-name fixture mapping to the current **Register Candidate** concept.

Schema validity remains structural and grants no execution, approval, retention, external action or professional authority.

## Relation to existing doctrine

This loop composes existing owners rather than creating a parallel architecture:

- `TASK_CONTRACTS.md` — task perimeter and admissible work;
- `HERMES_INTEGRATION.md` — external execution boundary;
- `RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md` and source/retrieval owners — optional retrieval boundary;
- `EVIDENCE_PACK.md` — Evidence Pack semantics;
- `USER_DECISION_GATE.md` — consequential human decision;
- `MEMORY.md` and Register contracts — durable governed retention;
- `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` and Card projection owners — governed review/status projection;
- `mcp-server/` — read-only policy/validation surface, not loop runtime.

## Acceptance criteria

The MVP is demonstrated, not promoted, when one real dossier completes the governed loop with:

- a reviewed Task Contract before execution;
- every relied-upon retrieved/source item attributable to its governed source identity;
- a conforming Evidence Pack Candidate bound to the reviewed Result Candidate;
- at least one genuine revision, refusal or request-for-more-evidence path exercising the gate;
- a Decision Record for every consequential decision;
- at most one Register Candidate, proposed only after `approve` plus distinct retention authorization.

The historical `devis_reprise` synthetic run remains validation provenance. It is not real-dossier acceptance and does not prove adoption.
