# Changelog

## Unreleased - public repository start (2026-10-14)

- Public history starts from a reviewed snapshot of the private Pantheon-Next
  repository at `40f2a1ae` plus its five then-open pull requests.
- Removed `ai_logs/` and its index/path tooling; provenance links now point to
  the private Pantheon-Next archive.
- Real project data pseudonymized; real case examples removed.
- Agency- and host-specific identifiers genericized (`vault-read`,
  `vault-search`, `project-context`, `hindsight-project`, `AGENCY_PROJECTS`);
  host names, NAS paths and LAN addresses replaced by placeholders.
- Archive issue/PR references qualified as `Pantheon-Next#<n>`.

## 0.1.66 - 2026-09-10

Hermes-first test checkpoint after the post-0.1.65 convergence cycle. This
heading records the repository state selected for controlled runtime testing.
It does not claim a published tag, installed deployment, provider adoption,
professional validation or production authorization.

### Added

- Project-context and exact-document routing for agency professional work, with
  explicit project continuity, alias/identity separation and the distinction
  `mentioned != exact source present != relevant content inspected`.
- ProjectClaim provenance, temporal-read and conflict-candidate structures,
  plus project/document identity and workspace source-materialization
  qualification paths.
- Context-admission and external-context candidate surfaces for Hermes, with
  bounded retrieval and source/data exposure rules.
- Qualification material for PAIR + Unsloth, Obsidian/Hindsight workspace
  composition and related runtime/source boundaries.

### Changed

- Hermes integration converged on adaptive runtime selection: Pantheon bounds
  legitimacy, scope, data exposure, effect ceilings and approvals while Hermes
  may choose qualified tools, skills, plugins, MCP capabilities, models and
  delegation inside that admitted boundary.
- Boundary-profile vocabulary and placement were migrated across governance,
  architecture-domain, examples, assets, templates and Hermes profile
  documentation, reducing duplicated authority prose and retired-owner drift.
- Workspace, memory, Evidence, exact-source and governed-identity distinctions
  were tightened so retrieval, filesystem organization, derivatives and
  runtime success cannot silently acquire authority.
- CI now enforces additional authority/boundary consistency, AI-log index
  currentness and qualification contracts introduced during the convergence
  cycle.

### Test checkpoint

The selected source checkpoint is `main@bc2ac9a80c662f252ebf3749775c00f061edcd58`
before this version-only release PR. Open experimental work such as Google
Drive provider qualification remains outside this checkpoint until separately
rebased, reviewed and admitted.

```text
checkpoint versioned != tag published
green CI             != runtime qualified
runtime qualified     != effect authorized
test deployment       != production adoption
```

## 0.1.65 - 2026-09-02

Consequential-mutation inventory closed and one chokepoint gap wired. This
heading records an implementation candidate checkpoint and does not claim a
published tag, installed service, live Hermes enforcement, activation or
production authorization.

### Added

- The consequential-mutation entry-point inventory now enumerates and has
  individually reviewed all 92 discovered mutation entry points under
  `implementation/mvp_vertical`; the unreviewed ceiling moves from a bound on
  a shrinking backlog (21) to a rule (0) — a newly discovered entry point must
  be reviewed when it is added.
- `human_access.bind_oidc_identity`, the write that makes an external OIDC
  identity able to act as a governed principal, now routes through
  `policy_gate.enforce_consequential` when a decision point is supplied, with
  the decision expectation bound to a digest of the exact binding
  (`principal_ref`, `issuer`, `subject`, `valid_until`) rather than to its
  name. The only production path (`mvp-vertical bind-oidc-identity`) fails
  closed without a configured decision point unless
  `MVP_POLICY_ENFORCEMENT=disabled` is declared explicitly.
- `test_semantic_order_is_total_when_distances_tie` and
  `test_a_pending_gate_is_still_absent_from_the_code_it_names`: regression
  tests that plant the defect they guard against instead of waiting to
  observe it, and assert an absence rather than a surviving fragment.

### Fixed

- `mvp_vertical.store.retrieve_scoped` ordered semantic hits on vector
  distance alone at both call sites, so equal-distance rows could return in
  either order between two identical calls. Both queries now carry the same
  tiebreak (`source_ref`, `source_digest`, `chunk_no`) the lexical retrieval
  path already used.
- `apu_write_preparation.apply_authorized_write_command` read the latest
  write authorization outside the transaction that applies the command, so a
  `reject_application` committing in the gap did not block the apply. Both
  `apply_authorized_write_command` and `append_authorization` now take the
  command row `FOR UPDATE` before reading or writing the decision.
- `store.ingest` accepted a `replace_dossier` parameter it never read, while
  both call sites passed `False` believing it protected the dossier from
  replacement; removed. The protection is the digest-scoped `DELETE`, named
  where it actually lives.
- `project_change_variants.select_variant_for_change_candidate`'s replay
  branch looked its selection disposition up by the current call's
  idempotency key after testing and discarding the disposition id already on
  the candidate row, so a replay under a different key raised as if the
  disposition did not exist. It now looks the disposition up by that id.

### Changed

- The mutation inventory's pending-gate anchor changed from a literal code
  fragment expected to remain present to a normalized-body digest and a
  reachability check against `enforce_consequential`, so a repair is detected
  by the absence of the gap rather than by a fragment that survives the
  repair. Required-gate ceiling: 9 -> 5 (`store_reviewed_dossier`,
  `publish_knowledge`, `complete_edit_request`, `apply_edit_request`,
  `act_working_information` remain).
- Reviewed Ubuntu release targets refreshed for the current bootstrap
  candidate under `deployment/ubuntu/`.

### Boundary clarification

Reviewing an entry point and wiring one gate change what this repository can
say about its own consequential-write surface. They do not change adoption,
deployment or professional validation status.

```text
entry point reviewed  != entry point authorized
gate reachable         != gate observed enforced in a live deployment
identity bound          != identity granted access
green CI               != adoption
implemented            != installed
```

## 0.1.64 - 2026-07-22

Read-only policy transport checkpoint. This heading records an implementation
candidate and does not claim a published tag, installed service, live Hermes
enforcement, activation or production authorization.

### Added

- `PantheonPolicyService`, a transport-neutral application facade shared by MCP
  and HTTP projections.
- `pantheon-policy-api`, an authenticated internal FastAPI adapter with separate
  liveness/readiness, request classification, deterministic candidate-work
  preflight, consultation, candidate preparation, validation, provided-evidence
  verification and Context Pack planning/validation routes.
- A hardened candidate `Dockerfile.policy-api` and `compose.policy-api.yaml` for
  `ai-net`, with no host port, a read-only checkout/filesystem, dropped Linux
  capabilities and no Docker socket.
- HTTP acceptance tests for fail-closed authentication, policy parity, K4 gate
  behavior, request-size limits, legacy-route refusal and Context Pack schema
  validation.
- `mcp-server/docs/HTTP_API_CONTRACT.md` and a candidate Hermes enforcement
  blueprint under `templates/hermes/connection/`.

### Changed

- MCP tools now call the same application facade as the HTTP adapter rather than
  wiring policy modules independently.
- The package exposes optional `http` dependencies and the
  `pantheon-policy-api` console entry point.
- Repository status and authority maps distinguish MCP consultation, HTTP
  policy/preflight data, Hermes enforcement and human decision.
- `VERSION`, this changelog head and package metadata advance together to
  `0.1.64`; the repository root remains non-distributable.
- The `mcp-server` module migrates to the `mcp` Python SDK 2.x line (`mcp>=2,<3`):
  the stdio server now uses `mcp.server.MCPServer` (the v2 successor to the
  removed `mcp.server.fastmcp.FastMCP`). Read-only tools, resources and the
  end-to-end stdio conformance harness are unchanged; the surface stays
  side-effect-free.

### Compatibility posture

- `POST /domain/approval/classify` remains a temporary classification alias and
  has no approval effect.
- `GET /runtime/context-pack` and `GET /domain/snapshot` fail explicitly with
  `501 contract_not_defined`; their ambiguous semantics are not invented.

### Boundary clarification

The API never authorizes external or canonical effects in V0. Gate references
remain caller-provided, unverified signals. Hermes remains the Policy
Enforcement Point and execution runtime; OpenWebUI exposes; the human decides.

```text
MCP consultation != HTTP enforcement
classification != authorization
provided gate reference != validated decision
ready != safe
runtime_success != evidence
implementation present != activated
```

## 0.1.63 - 2026-07-21

Repository-efficiency consolidation checkpoint. This heading records the
repository and MCP-package state after PRs Pantheon-Next#424 through Pantheon-Next#428. It is not a
published release: no `v0.1.63` tag is claimed.

### Added

- `pantheon-verify <family> <evidence>` as one static read-only CLI for install,
  observability, backup, exposure and update verification; the five historical
  command names remain compatible.
- Fail-closed duplicate-identifier detection for the Architecture Project
  Understanding dossier checker, with direct positive and negative tests.
- A current predecessor-independence guard that rejects active Pantheon-OS
  remotes, checkout paths, environment variables and vendored snapshots.
- A reusable runtime-boundary language guard extracted from GitHub Actions YAML.

### Changed

- The governance read path and roadmap now prioritize current status, ownership,
  blockers and exit criteria instead of repeating document inventories.
- `base_metier/architecte/` is explicitly qualified as an external professional
  corpus and adapter proving area, not an internal Pantheon RAG or runtime.
- Active governance documents use `Register Candidate` and `Registre Probatoire
  entry` where the governed record is meant, while Hermès retains runtime-memory
  ownership.
- AI intervention logs are limited to one durable trace per coherent material PR;
  mechanical corrections do not require an autonomous log.
- Governance CI no longer maintains completed-migration bookkeeping. It checks
  the present invariant that Pantheon Next is independent from its predecessor.
- `VERSION`, this changelog head and MCP package metadata advance together to
  `0.1.63`; the repository root remains deliberately non-distributable.

### Fixed

- Duplicate APU identifiers can no longer overwrite an earlier declaration
  silently in the dossier-wide reference index.
- Update evidence now uses the same schema-backed fail-closed validation path as
  install, observability, backup and exposure evidence.
- The large inline runtime-language program and two migration-era assertions were
  removed from the active workflow without removing current governance, APU, MCP,
  root-test or packaging checks.

### Validation posture

Each consolidation PR was refreshed onto the successive `main` state and passed
Governance CI plus Obsolete Authority Consistency before squash merge. The final
CI rewrite validated itself, including root tests, APU referential integrity,
MCP unit/end-to-end tests, wheel construction and clean-install metadata checks.

### Boundary clarification

No live runtime inventory, network probe, installer, scheduler, queue, provider
router, plugin manager, external action, update execution, automatic approval or
automatic register admission is introduced.

```text
installed != approved
healthy != safe
update_available != update_authorized
runtime_success != evidence
binding_selected != dependency_adopted
checkpoint recorded != tag published
```

### Earlier entries

- Versions `0.1.42` through `0.1.62` remain preserved in the immutable parent
  snapshot [`cc927ec:CHANGELOG.md`](https://github.com/ifanjuang/Pantheon-Next/blob/cc927ec93191e1fbbec148c1971714e89ba27488/CHANGELOG.md).
