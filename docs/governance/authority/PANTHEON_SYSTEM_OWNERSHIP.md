# Pantheon system ownership registry

Status: candidate support registry — documented non-implemented.

`PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json` records separate ownership dimensions for the principal concepts used across Pantheon governance, Pantheon implementation, Hermes and Pantheon Cockpit.

It supports architecture convergence and machine checks. It does not replace `AUTHORITY_INDEX.md`, promote a candidate, authorize an execution, admit Evidence, approve a binding or make an implementation authoritative.

The three ownership surfaces have different jobs:

```text
AUTHORITY_INDEX.md
  -> classifies repository artifacts and doctrine status

PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json
  -> records system responsibility dimensions for governed concepts

MODULES.md
  -> human-readable navigation by governance family
```

They must converge, but none silently replaces another.

## Ownership topology

A governed concept has exactly one semantic owner. Other owner dimensions are declared only where the responsibility exists.

```text
semantic owner
  defines meaning, invariants and governed status

implementation owner
  realizes the bounded executable contract

transition owner
  owns the admitted implementation path that changes governed state

persistence owner
  owns durable technical recording of that state

runtime owner
  executes external/runtime work

projection owner
  renders or exposes rebuildable governed projections
```

These dimensions must not be collapsed.

In particular:

```text
transition owner != decision authority
persistence owner != truth authority
runtime owner != Evidence authority
projection owner != persistence owner
projection owner != authorization authority
```

A transition owner may implement an admitted mutation, but it does not decide by itself that the mutation is legitimate. Consequential eligibility remains governed through Pantheon policy semantics, the PDP/PEP boundary and the human decision where required.

A persistence owner may record durable state, but storage does not make the stored value true, verified, approved or evidentiary.

A projection owner may display status, review gaps or decisions, but a UI state is not an authorization and a projection is not canonical persistence.

## Current logical owner identities

Owner identities name responsibilities. They are deliberately independent from Git repository names and filesystem paths.

```text
repository != owner identity
zone/path != owner identity
co-location != authority transfer
```

Current registry identities are:

- `Pantheon governance`: doctrine, governed semantics, schemas, statuses, scope, approvals and Capability Slots;
- `Pantheon implementation`: PostgreSQL persistence, APIs, admitted governed-state transition paths, executable projections, bounded adapters and integration seams;
- `Hermes/external runtime`: execution, tools, provider routing and runtime-local state;
- `Pantheon Cockpit`: governed Cards, navigation, status, Evidence-gap, review and decision projections.

Hermes Web/dashboard and compatible runtime clients remain replaceable runtime-interaction surfaces. They are not governance owners and are not currently used as concept-owner identities in this registry.

The governance and implementation responsibilities are currently co-located in the `Pantheon-Next` monorepo. Governance material primarily lives at the repository root while the bounded executable candidate lives under `implementation/`. This physical topology does not merge their responsibilities or authority.

A concept appearing in several zones is not automatically a contradiction. It becomes a priority finding when a zone exceeds its assigned dimension, for example by redefining a lifecycle it only implements, by executing work it only governs, by treating persistence as truth, or by treating a projection as authorization.

## Revision 4 convergence

Revision 4 extends the existing responsibility model without creating a new governance authority.

Changes:

- adds `transition_owner` and `persistence_owner` as explicit dimensions;
- replaces the obsolete `Cockpit/OpenWebUI` owner identity with `Pantheon Cockpit`;
- adds bounded machine concepts for governed decisions and governed identity so upcoming temporal/provenance/conflict/identity work has an explicit ownership envelope;
- binds core governed-state concepts such as ProjectClaim, Evidence and Document Source to separate semantic, transition, persistence and projection responsibilities;
- retains the registry status as `candidate_support_registry`.

Not changed:

- canonical Evidence, approval, scope or identity doctrine;
- PDP/PEP semantics;
- implementation placement;
- database schemas;
- the independently pinned merge-gating Architecture Audit snapshot.

```text
registry candidate changed
!= audit authority pin changed
```

The Architecture Audit deliberately evaluates a candidate registry change against its independently pinned prior snapshot and reports drift. Updating that pin is a separate reviewed change after the new registry revision is accepted.

## Core envelopes

The upcoming convergence work depends on five especially important concept families:

```text
ProjectClaim
Source / Document
Evidence
Decision
Governed Identity
```

For these families the registry now makes the following separation explicit:

```text
semantic_owner     = Pantheon governance
transition_owner   = Pantheon implementation
persistence_owner  = Pantheon implementation
projection_owner   = Pantheon Cockpit
runtime_owner      = absent unless runtime execution is genuinely involved
```

This is an ownership envelope, not an execution sequence. It does not imply that every transition is authorized, that every persisted row is canonical, or that every projection is authoritative.

## Repository-name migration

Registry revision 3 retired repository names as active owner identities:

- former semantic-owner label `Pantheon-Next` -> `Pantheon governance`;
- former implementation-owner label `pantheon-mvp` -> `Pantheon implementation`.

Revision 4 keeps that closure and removes the remaining product-composite projection identity:

- former projection-owner label `Cockpit/OpenWebUI` -> `Pantheon Cockpit`.

OpenWebUI remains a refused/retired target integration. Historical documents may continue to mention former products or repositories when describing provenance; they are not current owner identities.

## Naming

Active concepts, modules, routes and contracts use responsibility-based names. Generation labels such as `v0`, `v1`, `v2` or `v3` are not stable architectural identities.

Revisions remain valid where they carry real history:

- ordered database migrations;
- source and Information revisions;
- ChangeCandidate base revisions;
- schema revisions;
- external protocol versions isolated at an adapter boundary.

A reference to an externally versioned endpoint is not equivalent to an internally versioned architecture. The adapter must isolate that protocol detail instead of propagating it into domain or Cockpit identities.

## Use

The executable Architecture Audit is co-located under `implementation/tools/` and consumes an independently pinned snapshot of this registry. The registry is a candidate ownership map; the audit remains report-only and its pin remains a separately reviewed merge-gating baseline.

```text
audit finding != deletion proof
semantic owner != implementation owner
implementation owner != transition owner
transition owner != decision authority
transition owner != persistence owner by definition
persistence owner != semantic authority
implementation owner != runtime owner
projection owner != authorization authority
runtime success != Evidence
```
