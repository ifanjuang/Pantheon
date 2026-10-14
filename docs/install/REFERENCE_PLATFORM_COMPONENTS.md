# Reference Platform Components — Operator Guide

Status: candidate support note — selected-stack operator guide — documented non-implemented.
Boundary profile: candidate_support_note.

This guide classifies the external technical components that may surround Pantheon Next. It does not define a universal stack, install anything, store secrets, activate capabilities or authorize production use.

```text
Hermes Web/dashboard handles runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
Obsidian is the human Markdown workspace direction.
The human/operator installs and maintains infrastructure.
```

## Required foundation

The smallest current platform foundation is:

```text
operator-controlled runtime/container substrate where needed
private network boundary
persistent storage and backup/rollback posture for selected stateful services
Hermes Agent
Hermes Web/dashboard
model/provider configuration required by Hermes
bounded professional source paths when file ingestion is used
```

A Pantheon policy/MCP service is required only where the selected deployment invokes Pantheon governance through that interface. Repository presence does not prove live enforcement.

## Governed projection and workspace surfaces

```text
Pantheon Cockpit
  candidate governed projection surface
  not a second general-purpose Hermes chat client

Obsidian
  human-authored Markdown workspace
  not a DMS, Evidence store or governed Project identity

Hindsight / Hermes memory
  optional derived/runtime recall
  memory != truth != Evidence
```

## Conditional components

Install only when an existing capability/binding owner demonstrates the need:

| Component family | Typical purpose | Boundary |
|---|---|---|
| PostgreSQL / pgvector | selected co-located persistence/retrieval implementation | database presence does not grant semantic authority |
| Ollama / vLLM / other model runtime | local inference | model available != model approved |
| embedding service | retrieval representation | embedding != Knowledge or Evidence |
| SearXNG / search binding | external retrieval | retrieved != truth |
| Chromium / Browserless | browser automation | reachable browser != action authorized |
| Docling / structural parser | document derivation | derivative != source truth |
| OCR / VLM extraction | text/structure derivation | extraction confidence != Evidence |
| observability/evaluation backend | runtime observation | green signal != approval |
| Hindsight / memory provider | associative/runtime recall | memory != Evidence |
| compatible Hermes mobile/PWA client | replaceable Hermes interaction client | client compatibility != Pantheon adoption |
| third-party connector | bounded external integration | connected != authorized |

OpenWebUI and Paperless are not selected baseline components. Historical compatibility artifacts may remain temporarily until the protected cleanup slice proves their consumers can be removed.

## Operator record

For every installed external component, record outside the repository as appropriate:

```yaml
component_installation_record:
  component:
  purpose:
  source:
  version_or_image_digest:
  installation_status: not_checked | absent | installed | configured | enabled
  reachability: not_checked | reachable | unreachable | partial
  health_observation: not_checked | observed_ready | degraded | failed | unknown
  internal_service_name:
  internal_port:
  published_port:
  persistent_paths:
  secret_owner:
  backup_reference:
  rollback_reference:
  selected_binding_ref:
  activation_status: inactive | sandbox | project | blocked | to_verify
  evidence_refs:
```

This is an operational record, not a deployment manifest or approval record.

## Network posture

Prefer private service-to-service communication and explicit exposure decisions.

```text
internal service reachable != publicly exposed
publicly exposed != acceptable risk
TLS present != caller authorized
health endpoint green != safe use
```

`ai-net` may be used by the current candidate implementation, but the network name is not a governed identity or universal requirement.

## Persistence and source boundary

Keep operational state, professional source files, workspace notes and governed records distinct.

```text
Hermes runtime/session state
  external runtime responsibility

Pantheon implementation persistence
  candidate/governed implementation records under existing contracts

professional source files
  exact source/provenance responsibility

Obsidian Markdown
  human workspace and editable projections

Hindsight/runtime memory
  derived recall
```

```text
storage location != semantic authority
folder != governed identity
projection != persistence
memory != Evidence
```

## Model/provider posture

For every selected model/provider, record identity and capability posture separately from installation.

```text
model downloaded != model approved
provider configured != provider authorized for every data class
model answers != professional validation
```

Use the existing capability/passport/binding owners rather than inventing a second provider registry in this operator guide.

## Update and rollback

Before changing a selected component:

```text
pin or record current version/configuration
review upstream/current repository state
record backup/rollback target
review exposure/data/capability changes
obtain required human authorization
```

After change, observe installation, reachability and health independently. Do not infer activation, task authorization or production adoption from a successful restart.

## Refused former platform defaults

The historical platform treated these as default components:

```text
OpenWebUI -> general chat/cockpit exposure
Paperless -> preferred document-source management
```

Those defaults are refused by the current target architecture. Their useful responsibilities are already owned by Hermes clients, the Pantheon Cockpit, bounded source ingestion and existing source/document governance.

## Final rule

Use the smallest externally operated platform that satisfies demonstrated needs.

```text
reuse existing owners
keep clients and bindings replaceable
avoid duplicate runtimes and dashboards
preserve source/workspace/memory/Evidence distinctions
```
