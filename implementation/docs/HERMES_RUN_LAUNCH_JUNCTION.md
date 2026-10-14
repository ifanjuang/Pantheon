# Hermes Run Launch Junction

Status: external implementation candidate — tested in isolation / live Hermes binding not established / production activation not authorized.

Date: 2026-07-25

## Purpose

This document describes the narrow executable junction between one already-admitted Pantheon Work Issue and the public Hermes Agent Runs API.

It does not make Pantheon a runtime, dispatcher, scheduler, queue, retry worker, provider router, MCP host, plugin manager or memory engine.

```text
Pantheon governs the launch opportunity and scope.
An external Hermes Run Binding performs the native Runs API call.
Hermes executes the agent run.
The human remains the authority for admission and consequential effects.
```

## Sequence

```text
human creates bounded Execution Admission
        ↓
admission_state = admitted
        ↓
external Run Binding observes Hermes API + concrete tool surface
        ↓
runs_api_status = compatible
AND safety_status = qualified
        ↓
external Run Binding reserves exact launch
        ↓
admission_state = launch_reserved
immutable Launch Context Snapshot
        ↓
external Run Binding calls Hermes POST /v1/runs exactly once
        ↓
Hermes returns external run_id
        ↓
Run Binding reports exact run_id + launch_reservation_id to Pantheon
        ↓
admission_state = consumed
HermesRun observation = running
        ↓
Hermes may re-read exact current admitted context
        ↓
Hermes executes
        ↓
one-shot status reconciliation may record return candidate
```

## Launch reservation

`hermes_run_launch_reservations` is an immutable one-per-admission record.

It records:

```text
launch_reservation_id
admission_id
snapshot_id
snapshot_digest
snapshot_payload
field_projection_version
work_issue_version
launch_expires_at
idempotency_key
reserved_by
reserved_at
```

The reservation consumes the revocable launch window before the external network call.

```text
admitted
→ launch_reserved
→ consumed

launch_reserved
→ launch_expired  # lazy projection only
```

No scheduler is introduced to expire reservations.

A `launch_reserved` admission cannot be revoked in this first slice. This avoids a race where a human revokes an admission while the external binding is already submitting the admitted run to Hermes.

The reservation itself does not call Hermes.

```text
launch reservation != dispatch
launch reservation != Hermes run
reservation consumed != runtime start recorded
```

## Ambiguous network outcome

The first slice deliberately has no automatic retry.

If `POST /v1/runs` times out or otherwise has an uncertain outcome after reservation:

```text
launch reservation remains immutable
no second automatic POST /v1/runs
operator reconciliation required
```

If Hermes returns a `run_id` but the Pantheon start callback fails:

```text
run_id is retained by the raised reconciliation state
launch_reservation_id is retained
no second run is submitted automatically
```

This is intentionally conservative. Duplicate agent execution is worse than an explicit reconciliation requirement.

## Launch Context Snapshot

The snapshot is created in a PostgreSQL `REPEATABLE READ` transaction from the exact admitted Context Pack.

It uses the same frozen field contract as Scoped Hermes Data Access:

```text
field_projection_version = scoped-context-v1
```

The snapshot is bounded to 120000 serialized characters.

It may contain only the materializable admitted entity projections already allowed by the Context Pack. Document/Knowledge representations remain derived bounded Markdown where available; source binaries are never included.

```text
launch snapshot != Evidence
launch snapshot != global Agency Data
launch snapshot != source binary
launch snapshot != future current owner value
```

After runtime start, current values are available only through the exact active-context read path. A later owner revision may therefore differ from the immutable launch snapshot.

## Exact admitted source materialization

Workspace `source_refs` can identify an exact admitted source basis without making that source content available to Hermes. The current boundaries stay explicit:

```text
Launch Context Snapshot: source_binary_included = false
Scoped Hermes Context:   source_dereference_available = false
```

Those values remain `false`. Exact source materialization must not be implemented by widening the Pantheon context plugin into a generic source browser or by embedding source binaries in the launch snapshot.

The execution-side seam is instead:

```text
exact source_ref already present in the admitted Context Pack
        ↓
external Run Binding resolves only that declared source
        ↓
secure exact read + SHA-256 verification against the admitted digest
        ↓
0..n transient source representations
        ↓
Context Admission v2 framing as untrusted data
        ↓
bounded Hermes run material
```

For the Workspace path, the first implementation target is the already-issued form:

```text
workspace://<workspace_ref>/<relative_path>?sha256=<digest>
```

Materialization must preserve the exact source basis. The implementation must reuse the existing Workspace exact-read/no-follow/digest discipline rather than introduce arbitrary path reads, folder scans or implicit sibling discovery.

At minimum:

```text
workspace_ref must resolve through an explicitly configured Workspace root
relative_path must remain inside that root
symlink/path replacement must be refused
source SHA-256 must equal the admitted digest
missing/changed source must fail closed
no folder scan or global search is implied by one source_ref
```

A verified source may produce more than one transient representation because architectural sources are not reducible to one extraction channel:

```text
structural/text representation
  -> existing DocumentConverter abstraction
  -> bounded provider such as the current Docling Serve adapter

visual representation
  -> future bounded page/image adapter when qualified

other representation
  -> only through a separately reviewed replaceable adapter
```

`Docling` is therefore one current structural-analysis provider, not the architecture of source materialization. A future visual adapter must not create a second source identity, second document owner or parallel persistence path.

All model-bound extracted/rasterized/transcribed content is source data, not instruction authority. Before it is included in Hermes model input it must use the existing Context Admission v2 framing or an exactly equivalent reviewed boundary:

```text
content_role = data
instruction_authority = none
transport_class = untrusted_data
```

Transport does not make the content true, Evidence, approved, applicable or professionally validated.

The materialization is transient by default:

```text
materialized source bytes != persisted Document
transient Markdown/JSON != Workspace Contenu
transient visual pages != new source
conversion success != source truth
conversion success != Evidence
Hermes interpretation != Project Anatomy claim
```

No `<basename>.md`, Document, Knowledge, Evidence or canonical record is created merely because a qualification run needed the source content.

The separate explicit Workspace effect remains:

```text
Qualifier
= exact source -> transient run material -> Hermes candidate

Ingérer
= exact source -> reviewed structural-analysis path -> persistent <basename>.md Contenu
```

The same replaceable conversion abstraction may be reused by both paths; transient versus persistent effect must remain explicit.

The contract permits a bounded set of explicitly admitted source refs in one run. The first executable proof should stay narrower and demonstrate one exact Workspace PDF end to end before widening to multi-source materialization. Multi-source composition must still require every source to be explicitly admitted; it must not infer project-wide vault access.

The implementation must also define bounded source byte size, conversion timeout and model-bound representation size. A conversion or materialization failure is a visible refusal/capability gap, never a reason to widen scope or silently substitute another source.

This seam exists to enable real qualification such as Pantheon-Next#986, where the product value is not merely that Hermes can read a PDF but that it can keep admitted contradictory sources separate and surface the contradiction before a professional decision.

## Hermes Runs API binding

The external module `mvp_vertical.hermes_run_binding.ExternalHermesRunBinding` is the execution-side junction.

Before launch it requires the read-only observer to report:

```text
runs_api_status = compatible
safety_status = qualified
```

The binding then performs one native Hermes call:

```text
POST /v1/runs
```

The request provides:

```text
input        = immutable launch material
session_id   = exact Pantheon admission_id
instructions = fixed read-only governance constraints
```

It deliberately does not provide:

```text
model override
provider override
arbitrary conversation history
arbitrary external tools
```

Provider/model selection therefore remains Hermes runtime behavior rather than Pantheon behavior.

## Session-bound current context

The external Run Binding sets:

```text
Hermes session_id = Pantheon admission_id
```

A candidate native Hermes plugin is included at:

```text
hermes/plugins/pantheon-context-bridge/
```

It registers only:

```text
pantheon_context_manifest
pantheon_context_entity
```

The model does not receive `admission_id` or `run_id` parameters in either tool schema.

The plugin derives the Pantheon admission identity from the Hermes host-supplied `task_id`. It accepts only a value shaped as a Pantheon `admission-*` identity and fails closed otherwise.

The plugin then calls:

```text
GET /v1/hermes/execution-admissions/{admission_id}/active-context
GET /v1/hermes/execution-admissions/{admission_id}/active-context/entities/{entity_type}/{entity_id}
```

Pantheon resolves the single exact `running` HermesRun server-side and delegates to Scoped Hermes Data Access.

```text
model-selected entity != model-selected admission
caller_supplied run_id = false
active context != global Agency Data
```

### Live verification still required

Hermes plugin documentation states that per-session tool handlers receive `task_id` through host context. The joined candidate assumes the Runs API `session_id` supplied as the Pantheon `admission_id` is the host session/task identity delivered to the tool handler.

That exact equality has not yet been exercised against a live Hermes v0.19 target in this repository.

Therefore:

```text
plugin implementation = implemented candidate
plugin session identity binding = to verify live
plugin installation = not performed
plugin enablement = not performed
plugin activation = not authorized
```

Any mismatch fails closed because the plugin refuses a missing/non-`admission-*` host `task_id`.

## Tool-surface qualification

Installing or enabling the plugin does not make a Hermes profile safe.

The Runs API observer qualifies the concrete active tool surface against an explicit operator-reviewed allowlist.

For the narrowest read-only profile, a future reviewed configuration can require exactly the Pantheon context tools and any other separately justified read-only tools.

```text
plugin installed != approved
plugin enabled != activated for this scope
Runs API healthy != safe
prompt says read-only != tool authority removed
```

The general Hermes API-server tool surface is not automatically qualified merely because this plugin exists.

## One-shot reconciliation

`ExternalHermesRunBinding.reconcile_once()` performs at most one:

```text
GET /v1/runs/{run_id}
```

It is not a poller.

Current mapping:

```text
completed -> result_candidate
failed    -> failed
running   -> observation only
pending   -> observation only
stopping  -> observation only
cancelled -> observation only; no invented normalized mapping
```

A completed runtime output remains candidate material.

```text
Hermes completed != Evidence
Hermes completed != Work Issue resolved
technical receipt != Evidence
```

## Responsibility allocation

### Pantheon governs

- exact Work Issue / Task Contract / Context Pack admission;
- launch opportunity and reservation identity;
- immutable launch snapshot provenance;
- bounded read scope and field projection contract;
- runtime start/return observations;
- consequential effect gates;
- Evidence, Knowledge, Decision and canonicalization boundaries.

### Hermes executes

- the actual agent run;
- provider/model routing inside Hermes;
- runtime tool calls within the configured/qualified surface;
- runtime run identity and status;
- candidate output generation.

### External Run Binding executes

- read-only capability/toolset observation;
- exact admitted source materialization needed for one launch;
- transient source conversion through reviewed replaceable adapters;
- one launch reservation request;
- exactly one native Hermes `/v1/runs` submission;
- start callback registration;
- optional explicit one-shot status reconciliation.

It owns no source identity, Document persistence, queue, scheduler, retry worker or autonomous monitor.

### Cockpit / OpenWebUI exposes

- Work Issue scope;
- admission state;
- launch reservation/run observation state when projected;
- returned candidate/review need.

It does not receive Hermes or Pantheon service credentials through this candidate.

### Human approves

- Work Issue creation where required;
- Execution Admission;
- any consequential effect decision required by the effect chokepoint;
- later installation/enablement/activation of the Hermes plugin/profile.

### Forbidden

- Pantheon calling Hermes `/v1/runs` itself;
- PostgreSQL becoming a work queue;
- silent retry after ambiguous launch;
- model-selected admission or run identity;
- global Agency Data search through the context plugin;
- source binary dereference through the context plugin;
- source materialization widening beyond exact admitted refs;
- implicit folder/project scan from a source ref;
- transient conversion being persisted as Contenu/Document/Evidence automatically;
- plugin installation implying approval;
- runtime success being treated as Evidence or professional truth.

## Implementation status

```text
launch reservation persistence         implemented candidate
launch snapshot                        implemented candidate
admission launch_reserved state        implemented candidate
external Hermes Runs HTTP client       implemented candidate
one-shot launch binding                implemented candidate
one-shot status reconciliation         implemented candidate
active-context server resolution       implemented candidate
Hermes context plugin                  implemented candidate
exact Workspace source materialization not implemented
structural/text transient adapter use  not wired into Run Binding
visual transient adapter               not implemented
task_id == Runs session_id live proof  to verify
live Hermes target                     not connected
plugin installation                    not performed
plugin enablement                      not performed
production activation                  not authorized
```
