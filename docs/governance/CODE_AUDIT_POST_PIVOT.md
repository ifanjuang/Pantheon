# Code Audit Post Pivot

Status: active support note — independently maintained historical runtime audit.

Historical provenance is preserved in git history; this file has no external source dependency.

This document defines how Pantheon Next audits legacy code, operational assets and historical runtime surfaces after the governance-first pivot.

It is an audit register and classification doctrine.

It is not an implementation plan.

It does not reactivate legacy code.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work, Pantheon Cockpit projects governed audit state, and historical product references do not restore current ownership.

## Purpose

Pantheon Next has pivoted away from an autonomous agentic runtime.

This document prevents two opposite mistakes:

1. deleting useful legacy assets too early;
2. silently reactivating the old autonomous runtime path.

Legacy code must be classified before reuse, deletion, migration, extension or documentation as current behavior.

A useful historical component is not automatically a Pantheon Next component.

A documented risk is not approval to use the risky surface.

## Audit scope

This register applies to:

- historical predecessor code;
- legacy FastAPI applications;
- old agent/runtime modules;
- old workflow loaders;
- old provider or tool wrappers;
- old memory code;
- old installers;
- old Docker and environment files;
- old CI and tests;
- copied snippets or examples from historical runtime code;
- future proposed re-use of any of the above.

It also applies to Pantheon Next if a future contribution introduces runtime-like behavior.

## Classification statuses

Use this vocabulary during code or asset review:

```text
keep
reorient
archive
delete_later
to_verify
legacy
blocked_until_review
voluntarily_not_migrated
```

| Status | Meaning |
|---|---|
| `keep` | Aligned with Pantheon Next doctrine and may remain active as documentation, schema or read-only support. |
| `reorient` | Contains useful logic, vocabulary or patterns, but must be reframed as governance, schema, evidence, policy or Hermes-side capability. |
| `archive` | Kept for history only and must not be imported by active Pantheon behavior. |
| `delete_later` | Appears obsolete, but removal requires confirmation and trace. |
| `to_verify` | Requires inspection before decision. |
| `legacy` | Belongs to the previous autonomous architecture and must not be extended without review. |
| `blocked_until_review` | High-risk surface that must not be used, enabled, exposed or routed to until reviewed. |
| `voluntarily_not_migrated` | Deliberately not migrated because it conflicts with current doctrine or has insufficient governance value. |

## Approval thresholds

Audit work is normally C0 when it only reads and classifies.

It becomes C1 when it drafts a recommendation.

It becomes C3 when it changes repository files, schemas, tests, operations tooling or configuration.

It becomes C4 or C5 if it affects external systems, secrets, deployment, client-facing output, destructive actions or irreversible state.

No audit finding may self-approve a code change.

## Runtime drift indicators

A legacy component is runtime-drift risk if it introduces or implies:

```text
agent loop
execution engine
tool runtime
provider router
scheduler
queue
message bus
workflow engine
LangGraph central runtime
MCP server layer
plugin manager
automatic installer
automatic memory promotion
automatic approval
automatic external send
automatic patch apply
hidden dashboard authority
```

Any of these patterns must be classified as `legacy`, `reorient` or `blocked_until_review`, not `keep`, unless a separate governed decision proves a safe read-only role.

## Legacy surfaces recorded from the historical predecessor

The historical source register identified runtime-oriented surfaces that must not be treated as Pantheon Next core.

Examples include:

```text
platform/api/apps/agent/
platform/api/apps/orchestra/
platform/api/apps/memory/
platform/api/apps/webhooks/
platform/api/worker.v2.py
platform/api/core/queue.v2.py
platform/api/core/checkpointer.v2.py
platform/api/core/base_engine.py
modules.yaml
plugins.yaml
docker-compose.yml
scripts/install/ui/
legacy generic skills
```

Known legacy endpoint patterns recorded for risk visibility:

```text
POST /agent/run
POST /orchestra/run
POST /orchestra/run-hitl
POST /orchestra/stream
POST /orchestra/runs/{id}/approve
GET /runtime/context-pack
```

This list is historical risk inventory.

It does not mean these routes exist in Pantheon Next.

It does not approve them.

It does not authorize routing OpenWebUI or Hermes to them.

## Current Pantheon Next posture

Pantheon Next currently treats runtime-oriented historical assets as non-canonical unless explicitly migrated as governance doctrine.

Allowed current forms:

- Markdown governance doctrine;
- fictional examples;
- schemas as validation contracts;
- Hermes profile templates as candidate-only execution templates;
- future read-only Doctor checks;
- future read-only validation tests.

Forbidden current forms:

- active execution API;
- provider router;
- scheduler;
- queue;
- workflow runtime;
- internal agent runtime;
- automatic memory promotion;
- automatic approval;
- runtime-client plugin implementation inside Pantheon;
- Hermes bridge implementation inside Pantheon;
- Docker runtime stack.

## Reclassification patterns

| Old runtime concept | Correct Pantheon Next classification |
|---|---|
| Agent loop inside Pantheon | Hermes-side execution under Task Contract, with Pantheon governance only. |
| Decision plan | Task Contract or User Decision Gate candidate. |
| Execution result | Evidence Pack or Result Candidate. |
| Tool registry | External Tools Policy and allowed capability list. |
| Workflow engine | Workflow Manifest plus Hermes-side execution if authorized. |
| Scheduler | External runtime concern, never Pantheon core. |
| Provider router | Runtime/provider concern outside Pantheon governance core. |
| Patch auto-apply | Patch Candidate plus Evidence Pack plus approval. |
| Memory consolidation job | Register Candidate plus C3+ promotion review. |
| Plugin manager | External tool policy, allowlist/blocklist and review discipline. |
| Dashboard runtime | compatible runtime-client interaction or Pantheon Cockpit governed projection, depending the state being shown |
| Runtime traces | Evidence Pack summary or Run Trace View. |
| RAG engine | Knowledge retrieval capability, not memory or evidence by default. |
| Ingestion job | Governed source preparation candidate, not automatic evidence or memory. |

## Component decision matrix

When reviewing any historical component, record:

```text
component_name
source_path
former_role
observed_behavior
current_status
recommended_decision
runtime_drift_risk
memory_drift_risk
external_effect_risk
approval_level
next_safe_action
evidence_reference
```

A review must state whether the component is:

```text
documentation-only
schema-only
read-only-tooling
external-runtime-candidate
Hermes-side candidate
runtime-client-side candidate
Pantheon-Cockpit-projection candidate
blocked
archive-only
```

## Evidence required for audit decisions

Every audit decision must identify:

- files read;
- imports checked;
- active routes checked, if a codebase is present;
- configuration files checked;
- commands run, if any;
- assumptions;
- limitations;
- risk level;
- proposed decision;
- rollback or archive path.

Consequential decisions require an Evidence Pack.

A model summary is not evidence.

A passing test is not governance approval.

A historical route is not a current capability.

## Doctor check implications

A future read-only Doctor may check for forbidden runtime surfaces.

Allowed future checks:

```text
forbidden endpoint pattern present
legacy runtime folder present
schema governance_refs unresolved
stub still marked non implemented
Hermes profile missing candidate-only boundary
README/status/roadmap mismatch
```

Forbidden Doctor behavior:

```text
automatic deletion
automatic migration
automatic disabling
automatic approval
automatic memory promotion
automatic runtime start
secret inspection
network mutation
Docker control
```

A Doctor may report.

A Doctor must not govern.

## Migration safety rules

When evaluating material inherited from the historical predecessor:

1. Read the source fully.
2. Identify runtime-oriented claims.
3. Convert useful content into governance language.
4. Remove or invert obsolete runtime behavior.
5. Preserve the runtime-client / Pantheon Cockpit / Hermes / Pantheon authority boundaries.
6. Record the transformation in an ai_log.
7. Update status and migration mapping.
8. Do not touch protected implementation areas without confirmation.

## Hard blockers

The following must not be reintroduced inside Pantheon Next:

```text
Execution Engine
Agent Runtime
Tool Runtime
LLM Provider Router
Scheduler
Queue
Message Bus
LangGraph central orchestrator
memory auto-promotion
agency memory
self-evolution auto-merge
plugin batch install
Docker socket access
secret access by default
public admin dashboard without auth/VPN
automatic external communication
automatic OpenWebUI database access by Hermes
direct write access to Registre Probatoire entry
```

## CI and tests posture

The historical predecessor contained CI and test breakage diagnostics tied to its old codebase.

Those details are not imported as Pantheon Next current state.

Pantheon Next currently treats tests and operations tooling as absent implementation areas unless `STATUS.md` says otherwise.

Future test work must stay read-only unless explicitly approved.

## Final rule

Code audit is a governance discipline.

It may classify, warn, preserve evidence and recommend next safe action.

It must not execute, repair, deploy, approve, promote memory, route providers, install skills, start workflows or mutate systems automatically.
