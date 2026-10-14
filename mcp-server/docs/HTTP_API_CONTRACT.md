# Pantheon Policy HTTP API Contract

Status: implementation candidate — implemented read-only / partial / internal-network adapter; protected review required.

This document defines the HTTP projection of the transport-neutral Pantheon policy service.

```text
Optional Hermes WebUI or other compatible clients may expose runtime interaction.
Hermes Agent executes external admitted work.
The runtime Policy Enforcement Point enforces consequential preflight outcomes.
Pantheon Next governs.
Pantheon Cockpit may project governed state and decision surfaces.
The human decides consequential effects.
```

`nesquena/hermes-webui`, when selected, remains an optional/proposed runtime interaction surface. Its own runtime approval UI or technical success does not replace the Pantheon human-decision boundary.

The API is a Policy Decision Point projection. It returns policy, validation and candidate data. It is not an execution runtime, Policy Enforcement Point, approval engine, evidence store, memory engine, scheduler, queue, provider router, installer, updater, MCP host or connector gateway.

## Transport placement

```text
Pantheon policy modules
        ↓
PantheonPolicyService        one transport-neutral meaning
        ├── MCPServer stdio  agent-native consultation
        └── FastAPI HTTP     deterministic runtime preflight and service integration
```

MCP and HTTP must not implement separate policy logic. For a given operation and input, the operation-specific fields must remain semantically equivalent across the core service, MCP and HTTP projections.

## Common response fields

Every service projection includes, unless an older bounded contract already supplies the equivalent field:

```yaml
contract: pantheon.policy.v1
operation:
source_mode:
authority_effect: none
authorization_effect: none
write_effect: false
execution_effect: false
evaluated_at:
repository:
  version:
  commit:
input_sha256:
```

`input_sha256` is a reproducibility aid. It is not Evidence and does not establish truth, approval or runtime success.

## Authentication and network boundary

All policy routes and compatibility policy routes require:

```http
Authorization: Bearer <PANTHEON_POLICY_API_KEY>
```

If no server key is configured, the API fails closed with HTTP `503`. An invalid or missing client credential returns HTTP `401`.

The candidate Compose deployment:

- joins only the external Docker network `ai-net`;
- publishes no host port;
- mounts the Pantheon checkout read-only;
- uses a read-only container filesystem and a bounded `/tmp` tmpfs;
- drops all Linux capabilities;
- applies `no-new-privileges`;
- receives no Docker socket and no external credentials other than its consultation key.

## Health surfaces

### `GET /livez`

Process liveness only.

### `GET /readyz`

Checks that the governed checkout can be read and identified. It does not establish safety, approval or professional readiness.

```text
ready != safe
healthy != authorized
```

### `GET /health`

Compatibility health response. New operators should use `/livez` and `/readyz` separately.

## Metadata and repository state

### `GET /meta`

Returns the API mode, implemented surfaces, policy version and non-equivalence reminders.

### `GET /repository/state`

Returns a read-only observation of the mounted checkout and its declared version/commit.

```text
repository readable != runtime healthy
repository current != binding adopted
```

## Consultation routes

```text
GET /consultation
GET /sources
GET /sources/{key}
GET /architecture/{topic}
```

Source lookup remains allowlisted. A source key never becomes an arbitrary repository path.

## Policy classification

### `POST /policy/requests:classify`

Classifies a caller-provided request using the governed consequence, verification and approval axes.

Typical output fields:

```yaml
result: classified
consequence_level: K0 | K1 | K2 | K3 | K4
required_verification: V0 | V1 | V2 | V3 | V4
required_approval_ceiling: C0 | C1 | C2 | C3 | C4 | C5
delegated_execution: true | false
task_contract_required:
evidence_required:
blocked_until_gate:
required_gates: []
```

`delegated_execution` describes the execution boundary; it is not an authorization flag. Omitted values fail conservative to `true`. A Task Contract governs work delegated to an external runtime. A direct human governed-state effect may therefore remain consequential and decision-gated without inventing a Task Contract merely because it writes state.

Classification is not authorization.

## Deterministic preflight

### `POST /policy/preflights:evaluate`

Normal input:

```yaml
request:
  intent:
  external_effect:
  writes_state:
  delegated_execution:
  transmission_requested:
  memory_promotion_requested:
  professional_position:
  financial_or_contractual_effect:
  scope:
    scope_type:
    scope_id:
gate_signals:
  task_contract_ref:
  evidence_pack_candidate_ref:
  human_decision_ref:
  human_decision_level:
```

The implementation PEP owns the direct-human/delegated distinction for concrete effects. An arbitrary runtime candidate must not be able to escape a Task Contract requirement simply by asserting `delegated_execution: false`. Unknown effects remain delegated/fail-conservative until their execution boundary is reviewed.

For ordinary requests the gate signals remain caller-provided references. Their presence alone does not authenticate their issuer, digest, scope or currentness, and ordinary external/canonical effects remain denied.

Possible dispositions include:

```text
blocked_invalid_request
blocked_pending_scope
blocked_pending_task_contract
blocked_pending_evidence
blocked_pending_human_decision
blocked_invalid_gate
eligible_for_candidate_work
eligible_with_gate_signals_unverified
eligible_with_gate_validated
```

The normal fail-closed response keeps:

```yaml
external_effect_allowed: false
canonical_effect_allowed: false
gate_signal_validation_performed: false
replay_guard_required: false
authorization_effect: none
```

Thus the preflight can permit continued preparation of candidate work while still requiring the external runtime to block transmission, canonical mutation, memory promotion or other consequential effects.

A direct-human local governed-state write is a separate case: it may require neither a Task Contract nor an Evidence Pack when the write itself is not an assertion, external effect, professional position, contractual effect or Registre operation. It still requires the User Decision Gate, and the operational PEP must validate the human decision against the exact scope, object and digest before the effect can run.

```text
direct human effect != delegated runtime task
writes state != Evidence assertion
no Task Contract required != effect authorized
human decision ref present != decision valid
```

### Issue Pantheon-Next#664 synthetic qualification fixture

Exactly one repository-backed synthetic fixture may compose gate validation during preflight. It is identified by:

```text
intent = qualification_external_effect
Task Contract = tc.qualification.external-effect.v1
Evidence Pack Candidate = epc.qualification.external-effect.v1
scope = project / qualification-sandbox
classification = K4 / C3
```

The fixture objects live under `mcp-server/fixtures/` and conform to the existing Task Contract and Evidence Pack schemas. They are not production resources, professional Evidence or an adopted capability.

Only this fixture accepts an additional top-level preflight field using the same `{decision, expectation}` shape as `POST /policy/decisions:validate`:

```yaml
decision_validation:
  decision:
    decision_id:
    decided_by:
    expires_at:
    approval_level:
    scope: { scope_type:, scope_id: }
    object_identity:
    content_digest:
    signature:
  expectation:
    required_ceiling:
    required_scope: { scope_type:, scope_id: }
    object_identity:
    expected_digest:
```

The Task Contract ref, Evidence Pack ref, scope and effect posture are folded into a deterministic fixture effect identity/digest. The signed human decision must match that PEP-derived expectation, the `human_decision_ref` and level, must be non-expired, and its issuer must authenticate through the configured issuer-key registry. Any missing, mismatched, forged or unauthenticated gate keeps the effect denied.

When every fixture check succeeds, the PDP may return:

```yaml
policy_disposition: eligible_with_gate_validated
external_effect_allowed: true
canonical_effect_allowed: false
gate_signal_validation_performed: true
replay_guard_required: true
```

This is not a general external-effect default and does not authorize a production adapter. The PDP remains read-only and does not consume decisions. `replay_guard_required: true` instructs the operational PEP to atomically consume the decision once immediately before the synthetic effect. A replay must fail closed there.

```text
signed envelope cannot be changed != same decision cannot be reused
PDP permission != effect executed
runtime success != Evidence
fixture qualification != production activation
```

## External action check

### `POST /policy/external-actions:check`

Input:

```yaml
description: "..."
```

Returns the blocked-by-default legitimacy path. It never performs the action.

## Capability observation qualification

### `POST /observations/capabilities:qualify`

Qualifies a caller-provided status observation. It performs no runtime inventory or live probe and preserves:

```text
installed != approved
healthy != safe
update_available != update_authorized
runtime_success != evidence
```

## Candidate preparation

```text
POST /candidates/task-contracts:prepare
POST /candidates/evidence-packs:prepare
```

These routes prepare review objects only. They do not create executable authority, approve Evidence or write the Registre Probatoire.

## Validation and provided-evidence verification

```text
POST /validations/passports
POST /validations/apu-dossiers
POST /verifications/install
POST /verifications/observability
POST /verifications/backup
POST /verifications/exposure
POST /verifications/update
POST /verifications/profiles:load
GET  /doctor
```

The verification routes classify only the evidence supplied by the caller. They do not probe the NAS, fetch versions, open ports, run backups or query monitoring systems.

`POST /verifications/profiles:load` validates a caller-provided verification profile and projects a read-only evidence-gathering plan. The retained technical schema identifier `verification_preset` is historical and distinct from the installation preset model removed by the common installation baseline.

```text
verification profile != installation preset
profile validated != verification executed
plan produced != evidence gathered
```

## Context Pack split

Pantheon does not expose a generic current context through `GET /runtime/context-pack`.

### `POST /context-packs:plan`

Returns the boundaries and missing fields for a producer that will assemble a scoped Context Pack candidate.

Pantheon states the constraints. Hermes or another governed producer gathers the actual context.

### `POST /context-packs:validate`

Validates one caller-provided candidate against `schemas/context_pack.schema.yaml`.

```text
schema valid != authorized context
context included != evidence accepted
retrieved != true
```

## Compatibility routes

### `POST /domain/approval/classify`

Temporary alias of `POST /policy/requests:classify`. It classifies the approval ceiling; it does not approve.

### `POST /verifications/presets:load`

Deprecated compatibility alias of `POST /verifications/profiles:load`. The word `preset` here refers only to the retained legacy schema identifier `verification_preset`; it must not be interpreted as the retired installation-composition preset model.

### `GET /runtime/context-pack`

Returns HTTP `501 contract_not_defined` and points to the explicit Context Pack planning and validation routes.

### `GET /domain/snapshot`

Returns HTTP `501 contract_not_defined`. `snapshot` is intentionally not treated as a single object. Callers must request an explicit repository state, capability observation qualification or future typed domain object.

## Failure posture in Hermes

The API itself returns policy data. The external runtime Policy Enforcement Point remains responsible for blocking or allowing the consequential effect. In the selected Hermes execution path, Hermes-side runtime logic may implement that PEP responsibility; this does not make Hermes governance authority.

Recommended adapter behavior:

```text
non-consequential consultation unavailable
  -> continue only in visible degraded mode

consequential preflight unavailable
  -> fail closed
  -> block external and canonical effects
  -> report Pantheon policy service unavailable
```

No silent fallback from HTTP preflight to model judgment is permitted for a consequential effect.

## Body and documentation limits

The default maximum request body is 256 KiB and can be reduced with `PANTHEON_POLICY_MAX_BODY_BYTES`.

OpenAPI and Swagger are disabled by default. They may be enabled only in a bounded development environment with `PANTHEON_POLICY_ENABLE_DOCS=1`.

Request bodies and bearer credentials must not be written to logs. Uvicorn access logging is disabled by default.

## Human decision validation

### `POST /policy/decisions:validate`

The gate-validation slice. It validates a caller-provided decision reference
against the requirement the consequential effect must satisfy:

```yaml
decision:              # caller-asserted human decision reference
  decision_id:
  decided_by:          # human identity; system / service / runtime signers are refused
  expires_at:
  approval_level:      # C0..C5
  scope: { scope_type:, scope_id: }
  object_identity:
  content_digest:
expectation:
  required_ceiling:    # C0..C5
  required_scope: { scope_type:, scope_id: }
  object_identity:
  expected_digest:
```

Returns `verdict: valid | invalid`, a per-check map (structural, signer, expiry,
scope, level, object_identity, digest, issuer), `issuer_authenticated` and
`gate_signal_validation_performed: true`. This turns asserted decision content
into a checked envelope; it does not resolve an external Task Contract or
consume the decision.

### Human issuer authentication

When the operator configures an issuer key registry
(`PANTHEON_DECISION_ISSUER_KEYS_PATH` → a YAML mapping `issuer id -> shared
secret`), the decision must carry a `signature` (HMAC-SHA256 over the signed
fields `decision_id, decided_by, approval_level, scope, object_identity,
content_digest, expires_at`) that verifies against the registered key for
`decided_by`. On success `issuer_authenticated: true`; a missing, unknown-issuer
or non-verifying signature fails the verdict. The signature binds identity to the
authorization envelope, so it cannot be replayed for a *different* scope,
object, ceiling or expiry without failing verification.

That cryptographic binding is not one-use replay protection. The same untouched
valid decision can still be presented twice unless the operational PEP consumes
it exactly once. Pantheon does not add execution persistence to simulate that
responsibility.

When no registry is configured, the `issuer` check is `not_checked` and the
issuer stays **asserted, not authenticated** (the generic validation verdict is
not failed on that basis alone). The Pantheon-Next#664 qualification fixture is stricter: it
requires `issuer_authenticated: true` before the PDP may emit the bounded
external-effect permission.

```text
verdict valid != approval
validated reference != effect authorized
issuer_authenticated != approval        # authenticity of who decided, not permission
no registry configured != issuer proven
signature-bound envelope != one-use consumption
```

The API does not create or persist a human approval. The decision itself remains
external to this service.

## Route identity

Internal paths use stable responsibility names. Contract identifiers and payload schema revisions remain independently versioned.

```text
route identity != contract revision
stable route != frozen semantics
contract revision change != route rename
```

A breaking payload-contract change requires its own reviewed contract migration; it must not be hidden inside a path-generation rename.

## Final rule

```text
MCP helps the agent understand and prepare.
HTTP exposes a deterministic PDP/preflight projection.
The external runtime PEP enforces consequential-effect eligibility.
Hermes performs admitted work outside Pantheon.
Optional Hermes WebUI or another compatible client may expose runtime interaction.
Pantheon Cockpit may project governed state and decision surfaces.
The human decides consequential effects.
Neither transport nor client becomes authority, Evidence or runtime truth.
```
