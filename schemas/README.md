# Governance Schemas

Status: implemented validation baseline — D3 reconciliation pending

This directory contains declarative validation schemas for Pantheon Next governance objects.

Schemas define structure only.

They do not execute workflows, run tools, install Hermes profiles, route providers, schedule jobs, promote memory or mutate governance state.

The schema baseline can lag active doctrine while a reconciliation issue is open. Always verify `docs/governance/STATUS.md`, `docs/governance/AUTHORITY_INDEX.md` and related reconciliation work before treating a schema as fully canonical for a newly stabilized doctrine cluster.

## Scope

Implemented schema files include:

- `document_knowledge_slice.schema.yaml` — transport-neutral source/extraction/chunk/Knowledge validation contract;
- `workspace_cartouche.schema.yaml` — reserved frontmatter contract for optional `.SOURCE.ext.md` source cartouches;
- `workspace_folder_context.schema.yaml` — reserved frontmatter contract for optional `_folder.md` navigation context;
- `work_issue_slice.schema.yaml` — Work Issue, comments, external runs and material-event validation contract;
- `task_contract.schema.yaml`;
- `task_contract_revision.schema.yaml`;
- `evidence_pack.schema.yaml`;
- `register_candidate.schema.yaml`;
- `register_link.schema.yaml`;
- `project_claim.schema.yaml`;
- `impact_review.schema.yaml`;
- `shared_axes.schema.yaml` — canonical E/V/K/C vocabularies;
- `shared_defs.schema.yaml` — canonical shared `scope_type` and `pantheon_role` vocabularies;
- `capability_passport.schema.yaml`;
- `module_manifest.schema.yaml`;
- `policy_decision.schema.yaml`;
- `answer_status.schema.yaml`;
- `mvp_governed_loop_objects.schema.yaml`;
- `architecture-proof-register/` — architecture proof-register validation family;
- `architecture-project-understanding/` — Project Anatomy validation family;
- `role_signal.schema.yaml`;
- `workflow_manifest.schema.yaml`;
- `skill_manifest.schema.yaml`;
- `context_pack.schema.yaml`;
- `install_verification_evidence.schema.yaml`;
- `observability_evidence.schema.yaml`;
- `backup_evidence.schema.yaml`;
- `exposure_evidence.schema.yaml`;
- `update_evidence.schema.yaml`;
- `verification_preset.schema.yaml`.

Examples are stored in `schemas/examples/`.

The detailed owner doctrine for each object remains in `docs/governance/` or the relevant domain pack. This index does not replace those owners.

## Shared vocabulary

Pantheon maintains small shared vocabulary declarations for values that must not drift across schemas.

`shared_axes.schema.yaml` owns:

```text
E — probative certainty
V — verification
K — consequence
C — approval
```

`shared_defs.schema.yaml` owns:

```text
scope_type
pantheon_role
```

The canonical Pantheon Role set is currently:

```text
ATHENA
ARGOS
THEMIS
APOLLO
ZEUS
IRIS
HEPHAISTOS
MNEMOSYNE
```

`docs/governance/AGENTS.md` remains the semantic authority for what those roles mean. `shared_defs.schema.yaml` is the machine-readable value-set declaration used to prevent schema drift.

Root schemas still repeat several shared values inline because shared `$ref` resolution has not been generalized across the whole schema corpus. `.github/scripts/check_schema_vocabulary.py` therefore compares those repeated enums against the shared declarations and fails on an undeclared divergence.

A specialized enum is not automatically a copy of the full role vocabulary. For example:

```text
workflow governed_composition.forged_by = HEPHAISTOS only
workflow pre_execution_eligibility.arbiter = ZEUS only
```

Those fields intentionally express one specialized responsibility and must not be widened merely because the canonical role set grows.

## Governance references

Each schema includes `governance_refs` defaults where applicable to preserve traceability to the Markdown governance documents that define the doctrine for the object being validated.

A schema reference to a support or candidate document does not promote that document into canonical doctrine.

Always check `docs/governance/STATUS.md` and `AUTHORITY_INDEX.md` when authority status matters.

## Phase D1 reconciliation

The baseline aligns schema vocabulary with active doctrine for:

- canonical Pantheon Role names in `AGENTS.md`;
- C0–C5 approval levels in `APPROVALS.md`;
- scope categories in `SCOPE_ISOLATION.md`;
- Task Contract boundaries in `TASK_CONTRACTS.md`;
- Evidence Pack structure in `EVIDENCE_PACK.md`;
- Register Candidate structure in `MEMORY.md` and the Registre Probatoire vocabulary;
- Role Signal vocabulary in `ROLE_SIGNALS.md`;
- Workflow Manifest doctrine in `WORKFLOW_SCHEMA.md`;
- Skill Watchlist and candidate-skill boundaries in `SKILL_WATCHLIST.md`;
- Context Pack boundaries in `CONTEXT_PACKS.md`.

The Mnemosyne role convergence extends this baseline without adding runtime behavior: `task_contract`, `role_signal`, `workflow_manifest` and `skill_manifest` accept `MNEMOSYNE`, while the shared-vocabulary checker prevents one of those general role enums from silently remaining on an older set.

## Phase D2 evidence topology fields

Task Contract supports optional `reasoning_topology` governance metadata.

Evidence Pack supports optional:

- `evidence_items`;
- `handoff_artifacts`;
- `reasoning_topology_record`.

Workflow Manifest supports optional:

- `reasoning_topology_requirements`;
- `evidence_item_requirements`;
- `handoff_artifact_requirements`.

These fields validate governance metadata only. They do not dispatch workers, route providers, schedule tasks, create a graph runtime, run Hermes, approve outputs or promote memory.

## Governed composition fields

Workflow Manifest supports an optional `governed_composition` object for a manifest forged on demand by HEPHAISTOS from declared capabilities.

It validates governance metadata only:

- `forged_by` remains HEPHAISTOS because this field describes the fabrication viewpoint rather than the complete role vocabulary;
- the composition loop records retrieve/reuse/revise/retain policies without becoming an execution loop;
- capability steps carry governance signatures, approval ceilings, register behavior, risk classes, refusal tests and dependencies;
- `pre_execution_eligibility` keeps ZEUS as procedural arbiter;
- `post_execution_evidence` records V/E expectations and register rules.

The `x-boundary` block records that composition does not dispatch or execute.

## Phase D3 partial reconciliation

This baseline also confirms:

- `module_manifest.schema.yaml` as the generic module/capability declaration contract;
- `skill_manifest.schema.yaml` as a narrower skill/watchlist profile;
- optional `evidence_items[].claim_status` for claim-ledger review posture;
- the broader scope vocabulary for repository and governance work;
- required schema example validation dependencies rather than silently skipped tests.

The `architecture-project-understanding/` family uses its own resolved `shared.schema.yaml` through the test registry. General root schemas can continue to migrate toward shared references only when that reduces duplication without changing doctrine.

## MVP vertical reconciliation

The MVP bundle formalizes reviewed structures including:

- the closed human-decision enum;
- structured commitment/advisory grounding metadata;
- decision identity and integrity;
- separate retention authorization on a Register Candidate.

A candidate output may expose available choices but cannot widen a governed vocabulary.

## Boundary rule

Schemas are validation contracts.

They are not:

- runtime components;
- provider routers;
- approval engines;
- memory promotion engines;
- workflow engines;
- Hermes installers;
- OpenWebUI plugins;
- execution gateways;
- tool routers;
- topology dispatchers;
- schedulers;
- queues.
