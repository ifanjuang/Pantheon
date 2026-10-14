# Pantheon Next / implementation — repository placement boundary

Status: **active support decision — monorepo convergence recorded 2026-08-23**.

This document supersedes the 2026-07-23 sibling-repository placement decision that hosted the executable candidate implementation in `ifanjuang/pantheon-mvp`.

The earlier decision remains preserved in Git history. The current placement is one repository with explicit responsibility boundaries.

It does not install, activate, execute, approve, migrate professional data or create a deployment runtime.

## Core split

```text
Pantheon governance surfaces define what must be true and how it is checked.
implementation/ implements and demonstrates bounded executable candidate behavior.
External runtimes such as Hermes execute under governed contracts.
A private deployment layer configures one real environment.
Private governed storage holds real professional data.
```

```text
same repository != same authority
implementation success != authorization
schema conformance != professional approval
projection != persistence
workspace folder != governed identity
```

## Repository layout

```text
Pantheon-Next/
├── docs/governance/        canonical doctrine and status
├── schemas/                canonical structural contracts
├── catalog/                governed declarative candidates
├── mcp-server/             bounded policy / verification projection
├── implementation/         executable candidate implementation
└── .github/workflows/      governance and implementation checks
```

The repository root remains a governance/documentation workspace and is intentionally not a Python distribution. `mcp-server/` and `implementation/` retain their own bounded packaging responsibilities.

## Dependency direction

The monorepo removes the need for a repository-level copy boundary, but not the authority direction.

```text
source of governance       = canonical root governance surfaces
implementation consumer    = implementation/
allowed semantic direction = implementation -> governed contracts
reverse authority transfer = forbidden
conflict or divergence     = canonical governance source prevails
schema validation          = conformance only
runtime success            = implementation evidence only
```

The implementation consumes canonical root contracts directly from `schemas/`. Standalone build artifacts carry a generated digest-verified snapshot of the schema tree so they remain autonomous outside a checkout. That generated payload is ignored by Git and is distribution material only, never a second source of truth or authority.

## Governance surfaces retain

Pantheon governance surfaces retain artifacts whose primary purpose is governance or conformance:

- doctrine, vocabulary, roles, rites, gates and status rules;
- canonical schemas and validation contracts;
- read-only validators and policy/preflight projections;
- positive and negative conformance fixtures;
- expected validation reports;
- capability passports, Task Contract templates and handoff contracts;
- declarative Hermes and OpenWebUI templates without executable adapter ownership;
- governance-only visual grammar prototypes;
- authority indexes, status maps and intervention traces.

A fixture remains in a governance surface when its purpose is to prove that a contract accepts or refuses a bounded structure.

## `implementation/` owns executable candidate artifacts

`implementation/` contains artifacts whose primary purpose is execution, product demonstration or runtime integration:

- Cockpit HTML, CSS, JavaScript and renderer code;
- synthetic projects, documents, Knowledge Items and Work Issues displayed by the Cockpit;
- fictional dossier corpora used by ingestion or retrieval;
- executable scenario runners and runtime adapters;
- OpenWebUI functions, tools, pipes or actions implemented as code;
- Hermes-side executable adapters and bindings;
- runtime-return fixtures and integration recordings;
- browser, API, database and end-to-end integration tests;
- local demo configuration and product screenshots.

A fixture belongs in `implementation/` when it feeds an executable flow, product screen or integration test.

Repository placement does not promote these artifacts into governance authority.

## Historical import

The initial monorepo import uses a fixed source cutoff:

```text
former repository = ifanjuang/pantheon-mvp
source cutoff      = d960862dd0e23b7003a0f3e4ee0ea630ffc12af9
destination        = Pantheon-Next/implementation/
method             = history-preserving git filter-repo subdirectory rewrite
```

The former repository remains the historical reference for original PR numbers, issues and original commit identifiers until it is explicitly archived. It is not a second active implementation trajectory after the cutoff.

New executable implementation work converges on `implementation/` after the monorepo migration is admitted.

## CI and architecture guards

Co-location must make boundaries easier to test, not weaker.

The repository runs separate governance and implementation test suites from one root workflow surface. Architecture checks reason about bounded zones and logical responsibility identities rather than requiring two Git repositories.

The initial compatibility debt has been converged in reviewed follow-up changes:

```text
canonical contracts       = root schemas consumed directly in checkout
standalone distribution   = generated digest-verified schema snapshot, not authority
Hermes distribution       = revision 3, one Pantheon monorepo root
Architecture Audit zones  = governance-core + implementation
logical owners            = Pantheon governance + Pantheon implementation
former repository names   = historical provenance only
```

Do not reintroduce committed governance vendoring, a second active implementation source path, repository-name owner identities or a two-repository audit model merely for compatibility.

Target invariant:

```text
governance can be checked independently
implementation can be tested independently
integration can be tested together
one repository does not imply one authority owner
```

## Data boundary

Real client documents, plans, contractual files, standards corpora and professional Knowledge do not belong in the public repository.

```text
public repository   -> code, contracts, synthetic fixtures, qualified metadata
private deployment  -> environment-specific configuration and secret references
private storage     -> real sources, derived representations and governed records
secret manager      -> credentials and keys
```

Copyrighted standards or contractual corpora may be represented by synthetic metadata and source manifests. Their full content remains outside Git unless licence and disclosure are explicitly qualified.

## Deployment separation

A future private deployment repository or equivalent operator-controlled configuration layer may contain:

- pinned repository revisions;
- Compose or Portainer configuration;
- reverse-proxy and network configuration;
- storage mount declarations;
- backup, health and rollback procedures;
- references to secrets stored elsewhere.

That layer remains configuration, not an automatic installer, scheduler, provider router, approval engine or Pantheon runtime.

## Non-equivalences

```text
co-located != adopted
installed != approved
healthy != safe
runtime fixture != Evidence
public demo != production deployment
binding selected != dependency adopted
update available != update authorized
green CI != professional authorization
repository merge != authority merge
```

## Migration rule

A significant placement migration records:

- source repository/component and path;
- destination repository/component and path;
- exact source and destination revisions;
- whether history was preserved, transformed, copied or deleted;
- whether incoming references were updated;
- whether adoption or activation remains absent;
- which compatibility shims remain and how they will be retired.

Pantheon governs the classification. `implementation/` carries bounded candidate implementation. OpenWebUI exposes operational surfaces where installed. Hermes performs authorized work where separately activated. The human approves consequential migration, adoption and activation.