# Common Installation Baseline

Status: candidate support doctrine — selected common installation direction — documented non-implemented.
Boundary profile: candidate_support_note.

This document records the smallest common deployment baseline justified by the current target architecture. It creates no installer, Compose stack, secret store, provider router, scheduler, queue, plugin manager or approval engine.

```text
Hermes Web/dashboard handles runtime interaction.
Hermes Agent executes externally.
Pantheon governs consequential status.
The human installs and approves consequential changes.
```

## Core decision

One baseline, with optional services added only when a reviewed capability binding requires them.

OpenWebUI and Paperless are not baseline dependencies.

```text
document_ingestion
  core capability

local/NAS governed source
  default bounded source path where file ingestion is used

human Markdown workspace
  Obsidian

external associative/runtime recall
  optional Hindsight / Hermes memory binding
```

Obsidian is not a DMS. Professional source files retain exact source/provenance identity under the existing document/source owners.

## Required foundation

| Component | Baseline posture |
|---|---|
| Execution substrate | operator-managed container/runtime environment or equivalent |
| Operator maintenance access | required for bootstrap/maintenance; not a Pantheon shell runtime |
| Private network boundary | required for internal runtime communication |
| Persistent storage and backup/rollback posture | required for selected stateful services |
| Hermes Agent | required external execution runtime for the selected Hermes architecture |
| Hermes Web/dashboard | current interaction baseline for chat, sessions and runtime controls |
| Governed source path(s) | required when professional files are ingested; scope/path/provenance checks apply |
| Pantheon policy/governance interface | required only where the selected deployment invokes Pantheon governance; current repository implementation remains candidate/partial until target proof |

The co-located Pantheon implementation may require PostgreSQL or other implementation-specific services. That is an implementation contract, not a universal doctrine requirement for every external runtime configuration.

## Selected but separately deployed workspace

Obsidian is the current human workspace direction for Markdown notes and editable working projections.

Hindsight may be deployed as a derived memory/index only when its separate binding, synchronization and exposure boundaries are satisfied.

```text
Obsidian note != professional source file
filesystem folder != governed Project identity
Hindsight recall != truth
memory != Evidence
```

## Conditional services

Install only when a reviewed binding needs them:

- PostgreSQL/pgvector for the selected co-located Pantheon persistence/retrieval implementation;
- Ollama or another reviewed model runtime;
- embedding service;
- SearXNG or another reviewed search binding;
- Chromium/Browserless or another browser binding;
- Docling or another document structural-analysis binding;
- OCR/VLM extraction bindings;
- observability/evaluation backend;
- external runtime memory such as Hindsight;
- optional compatible Hermes client such as a mobile/PWA client;
- other connectors admitted through existing capability/binding owners.

```text
service documented != service required
service installed != binding selected
binding selected != activated
activated != task-authorized
reachable != healthy
healthy != safe
runtime success != Evidence
```

## Canonical interaction/execution path

```text
user
-> Hermes Web/dashboard or selected compatible Hermes client
-> Hermes Agent
-> Pantheon policy/admission boundary where the task/effect requires it
-> candidate result / observation
-> governed qualification and human decision as applicable
```

The Pantheon Cockpit is a separate governed projection surface. It may show status, Cards, decisions and review state; it is not a second general-purpose Hermes chat/runtime client.

## Core document ingestion path

```text
bounded local/NAS source
-> Task Contract declared-source check
-> path/scope boundary check
-> exact source locator + digest
-> selected extraction binding when needed
-> Document / Project Document candidate
-> optional Knowledge publication through existing owner
```

No DMS product is required to preserve this contract.

## Refused former baseline dependencies

### OpenWebUI

Former role: required exposure/chat surface connected to Hermes.

Current decision: refused as a baseline dependency because Hermes Web/dashboard already owns runtime interaction and the Pantheon Cockpit owns governed projections.

### Paperless-ngx

Former role: preferred binding for optional `document_source_management`.

Current decision: refused as a baseline dependency because core exact-source/local-NAS ingestion does not require a DMS product. A future DMS may be reconsidered only if a demonstrated capability gap remains and the binding stays replaceable.

## Default network posture

Internal runtime/data services remain private by default. Publishing any port or exposing any dashboard beyond the selected private network is a separate operator/security decision.

For Hermes clients, prefer same-origin/private-network access and supported authentication contracts. A mobile/PWA client is not made safe merely by being installable.

## Data and authority separation

```text
Hermes runtime state
  external execution/session responsibility

Pantheon implementation persistence
  implementation-specific governed/candidate records

Obsidian Markdown
  human workspace/source notes

Hindsight/runtime memory
  derived recall

professional source files
  exact source/provenance owner
```

No database, vector store, workspace folder, runtime memory bank or UI becomes Evidence, approval or governed identity by storage alone.

## Update and rollback discipline

Before a consequential service update:

```text
verify upstream/current repository state
record current version/configuration
verify backup/rollback target
review changed capability/exposure/data boundaries
obtain required human authorization
```

After update, observe version/reachability/health and keep activation/adoption distinct until reviewed.

## Final baseline

```text
Hermes Agent + Hermes Web/dashboard
Pantheon governance boundary where selected
bounded professional source paths
operator-managed persistence/backup for selected services
Obsidian as human Markdown workspace
optional Hindsight/runtime recall
optional replaceable clients/adapters only when justified
```

Do not reintroduce OpenWebUI, Paperless or another parallel product merely to recreate responsibilities already covered by this baseline.
