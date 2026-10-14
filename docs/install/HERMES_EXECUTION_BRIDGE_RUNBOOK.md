# Hermes Execution Bridge — Operator Runbook

Status: candidate manual runbook — no automatic installation, activation or task authorization.

This runbook complements `COMMON_BASELINE_RUNBOOK.md` for the bounded Pantheon execution bridge co-located under `implementation/`. It describes explicit operator actions only.

## Responsibility boundary

```text
Pantheon governance        -> contracts, boundaries and distribution schema
Pantheon implementation    -> candidate run binding, context bridge, observer and CLI
Hermes                     -> runtime process, profiles, tools, sessions and model execution
Human                      -> installation, secrets, activation and consequential decisions
```

The physical repository path does not grant authority to the implementation zone.

```text
component copied != component enabled
component enabled != binding activated
binding activated != task authorized
profile route answered != governed profile qualified
fresh memory observation != task authorized
configured reasoning hidden != observed reasoning hidden
runtime return != accepted result
runtime output != Evidence
```

## 1. Select exact artifacts

Record outside the repository:

```text
PANTHEON_REPOSITORY_COMMIT
HERMES_VERSION
HERMES_ARTIFACT_DIGEST
DISTRIBUTION_LOCK_PATH
OPERATOR_ID
INSTALLATION_TARGET
ROLLBACK_TARGET
```

Use an exact Hermes version such as `0.20.0`, not `0.20+`, `latest` or another range. Record the digest of the installed package, image or immutable runtime artifact. A reviewed version without an observed artifact digest remains a candidate only.

## 2. Verify the distribution lock

Use the `pantheon-hermes` CLI from the reviewed Pantheon monorepo checkout:

```bash
cd /opt/pantheon/implementation
pantheon-hermes verify-distribution \
  --manifest hermes/distribution/pantheon-standard.lock.yaml \
  --schema /opt/pantheon/templates/hermes/distribution/distribution-lock.schema.yaml \
  --monorepo-root /opt/pantheon
```

Expected:

```text
schema valid
all component paths bounded to the Pantheon monorepo root
all file and tree digests match
stable Pantheon routes present
retired internal /v1/hermes routes absent
authority_effect = none
```

Digest validation proves source integrity only. It does not prove installation, health, safety, activation or task authorization.

## 3. Configure the external API seam and governed profile route

Keep secrets outside the repository:

```text
PANTHEON_HERMES_API_BASE
PANTHEON_HERMES_API_KEY
PANTHEON_HERMES_ACTOR
HERMES_API_BASE
HERMES_API_KEY
HERMES_GOVERNED_PROFILE
```

Recommended first governed profile identity:

```bash
export HERMES_GOVERNED_PROFILE=pantheon-governed
export HERMES_API_BASE="http://<HERMES_HOST>:<HERMES_PORT>/p/${HERMES_GOVERNED_PROFILE}"
```

`HERMES_API_BASE` must target the exact named `/p/<profile>` route and must not include a trailing `/v1` path. A default unscoped route such as `http://<host>:<port>` is not sufficient for governed qualification.

Required separation:

```text
PANTHEON_HERMES_API_KEY -> bounded Pantheon execution API
HERMES_API_KEY          -> external Hermes Runs API
```

Do not reuse a provider credential as either bridge credential. Do not grant the bridge Docker, SSH, database-administrator or repository-write authority.

The governed client must not send `X-Hermes-Session-Key`. The bridge uses `session_id` only for run correlation; that is not long-term-memory opt-in.

## 4. Install the context bridge plugin

Command Candidate — execute only after reviewing the pinned checkout, the exact Hermes plugin command surface and the component digest:

```bash
docker exec -it <HERMES_CONTAINER> \
  hermes plugins install \
  "file:///opt/pantheon#implementation/hermes/plugins/pantheon-context-bridge" \
  --no-enable
```

Review the copied plugin and configure:

```text
PANTHEON_HERMES_API_BASE
PANTHEON_HERMES_API_KEY
```

Enable separately only after review:

```bash
docker exec -it <HERMES_CONTAINER> \
  hermes plugins enable pantheon-context-bridge
```

The plugin exposes only:

```text
pantheon_context_manifest
pantheon_context_entity
```

It must not expose global search, global listing, arbitrary source dereferencing or mutation.

## 5. Capture the governed profile memory posture

Run the capture in an execution environment where the `hermes` command resolves the exact target profile home. The capture must not be produced from another profile, host or configuration.

```bash
pantheon-hermes capture-memory-status \
  --profile "${HERMES_GOVERNED_PROFILE}" \
  --output memory-status-observe.json
```

The CLI invokes one read-only command without a shell:

```text
hermes -p pantheon-governed memory status
```

It retains a sanitized technical receipt, not the raw command output.

Verify the receipt:

```text
kind = hermes_profile_memory_observation
observation_source = hermes_memory_status_cli
profile = pantheon-governed
exit_code = 0
external_provider = off
built_in_memory_injection = off
built_in_user_profile_injection = off
memory_tool = off
missing_axes = []
active_axes = []
status = qualified
raw_output_retained = false
write_effect = false
activation_changed = false
authority_effect = none
technical_receipt_is_evidence = false
stdout_digest starts with sha256:
```

The receipt is valid for at most five minutes. It must be regenerated after any Hermes profile, plugin, memory or tool configuration change.

```text
hermes memory off != built-in memory injection off
provider absent != memory context absent
memory tool absent != memory injection disabled
stored memory != admitted memory
```

## 6. Observe the named Hermes Runs API, tool surface and memory posture

Supply the exact profile, the fresh memory receipt and an operator-reviewed tool allowlist. Do not qualify an unspecified tool surface.

```bash
pantheon-hermes observe \
  --expected-profile "${HERMES_GOVERNED_PROFILE}" \
  --memory-status-receipt memory-status-observe.json \
  --allowed-tool pantheon_context_manifest \
  --allowed-tool pantheon_context_entity \
  --required-tool pantheon_context_manifest \
  --required-tool pantheon_context_entity \
  --output runtime-observation.json
```

Verify the actual nested result paths:

```text
runs_api_status = compatible
safety_status = qualified
profile_surface.status = qualified
profile_surface.observed_profile = pantheon-governed
profile_surface.route_observed = true
tool_surface.status = qualified
tool_surface.unexpected_tools = []
tool_surface.missing_required_tools = []
memory_posture.status = qualified
memory_posture.external_provider = off
memory_posture.built_in_memory_injection = off
memory_posture.built_in_user_profile_injection = off
memory_posture.memory_tool = off
memory_posture.session_memory_key = absent
memory_posture.age_seconds <= 300
session_memory_header_sent = false
run_submission_performed = false
write_effect = false
authority_effect = none
```

If `memory_posture.status` is not `qualified`, capture a new receipt and investigate the profile configuration. Do not edit a receipt manually.

The current observer does not inspect Hermes display configuration or prove what a user-facing channel renders. Do not infer private-reasoning safety from `safety_status = qualified` until the presentation check below has also been completed for the admitted surface.

```text
reachable != healthy
healthy != safe
profile route answered != governed profile qualified
tool surface qualified != production activated
memory posture qualified != task authorized
runtime safety_status qualified != presentation posture observed
observation != Evidence
```

## 7. Verify OpenWebUI enrichment posture

Before exposing the profile through OpenWebUI, verify that the governed route adds no hidden context outside the admitted Context Pack:

```text
OpenWebUI memory injection = disabled for governed route
OpenWebUI automatic RAG = disabled for governed route
OpenWebUI model/pipe route = exact /p/pantheon-governed route
fallback to default or personal profile = refused
X-Hermes-Session-Key = absent
```

Record the configuration source, observed route and observation time. A UI route label alone is not proof of the backend profile or memory posture.

## 7A. Verify governed presentation posture

Private model reasoning must not be projected onto a governed user-facing surface. Safe commentary and meaningful interim progress are preferred when the exact Hermes version and channel support them, but their absence is an UX degradation rather than an automatic safety failure.

First record the exact profile configuration values. On Hermes versions that support these keys, the recommended baseline is:

```bash
hermes -p "${HERMES_GOVERNED_PROFILE}" config set display.show_reasoning false
hermes -p "${HERMES_GOVERNED_PROFILE}" config set display.show_commentary true
hermes -p "${HERMES_GOVERNED_PROFILE}" config set display.interim_assistant_messages true
hermes -p "${HERMES_GOVERNED_PROFILE}" config set plugins.stream_reasoning_deltas false
```

Then read them back with the exact installed runtime rather than assuming that the write was accepted:

```bash
hermes -p "${HERMES_GOVERNED_PROFILE}" config get display.show_reasoning
hermes -p "${HERMES_GOVERNED_PROFILE}" config get display.show_commentary
hermes -p "${HERMES_GOVERNED_PROFILE}" config get display.interim_assistant_messages
hermes -p "${HERMES_GOVERNED_PROFILE}" config get plugins.stream_reasoning_deltas
```

If a key is unsupported on the exact reviewed Hermes version, record it as unsupported and verify the effective behavior directly. Do not add a compatibility shim merely to satisfy this checklist.

Expected baseline when supported:

```text
display.show_reasoning = false
plugins.stream_reasoning_deltas = false
display.show_commentary = true              # preferred, not a safety gate
display.interim_assistant_messages = true   # preferred, not a safety gate
```

Configuration is not proof. Run one bounded read-only task on each user-facing surface that will be admitted for governed work and inspect the actual user-visible output.

Required behavioral result:

```text
no private scratchpad shown
no chain-of-thought / reasoning block shown
no reasoning delta streamed to the user-visible surface
no "💭 Reasoning" block or equivalent private-reasoning projection
safe commentary/progress may appear
final governed result remains available even if interim progress is unsupported
```

Qualification rule:

```text
observed private reasoning disclosure -> not_qualified
reasoning visibility cannot be sufficiently observed -> not_qualified for that surface
commentary unavailable -> presentation degraded, not automatically unsafe
interim messages unavailable -> presentation degraded, not automatically unsafe
```

Preserve a bounded technical record containing the exact Hermes version/profile/surface, relevant configuration values or unsupported-key result, observation time and pass/fail outcome. Do not retain private reasoning content merely to prove that it leaked; a minimal redacted marker or digest is sufficient when incident evidence must be preserved.

```text
show_reasoning false != private reasoning proven hidden
reasoning hidden in CLI != reasoning hidden in Telegram/WebUI/another surface
private reasoning != Pantheon activity
commentary != chain-of-thought
presentation observation != task authorization
```

## 8. Activate the binding separately

Activation is an explicit human deployment decision outside the distribution lock. Record:

```text
binding identity
operator identity
exact distribution lock digest
activation scope
activation time
expiry or review date
rollback target
```

Do not encode persistent task authorization in the plugin, lock or CLI.

## 9. Recapture memory posture and launch one admitted task

Create and human-admit the handoff through Pantheon first.

Immediately before launch, capture a new receipt so the launch does not depend on an observation older than five minutes:

```bash
pantheon-hermes capture-memory-status \
  --profile "${HERMES_GOVERNED_PROFILE}" \
  --output memory-status-launch.json
```

Then execute one explicit launch:

```bash
pantheon-hermes launch \
  --expected-profile "${HERMES_GOVERNED_PROFILE}" \
  --memory-status-receipt memory-status-launch.json \
  --allowed-tool pantheon_context_manifest \
  --allowed-tool pantheon_context_entity \
  --required-tool pantheon_context_manifest \
  --required-tool pantheon_context_entity \
  --admission-id admission-<ID> \
  --idempotency-key <UNIQUE-OPERATOR-KEY> \
  --output launch-receipt.json
```

The CLI performs one sequence only:

```text
observe exact profile, reviewed tools and fresh memory posture
→ reserve one admitted launch
→ submit one Hermes run
→ record the exact runtime start
→ exit
```

Verify the launch receipt:

```text
runtime_submission_performed = true
session_memory_header_sent = false
automatic_retry_performed = false
provider_routing_performed = false
model_override_performed = false
technical_receipt_is_evidence = false
observation.safety_status = qualified
observation.profile_surface.status = qualified
observation.tool_surface.status = qualified
observation.memory_posture.status = qualified
```

The launch receipt does not by itself prove the governed presentation posture. Keep the separate surface observation from step 7A with the operational qualification record.

It performs no daemon loop, scheduler, queue, automatic retry, provider routing or model override.

A replayed reservation or ambiguous network outcome requires manual reconciliation. Do not rerun the command with a new key merely to bypass uncertainty.

## 10. Verify host correlation and bounded context

For the admitted run, verify on the real Hermes version:

```text
Hermes host task_id == Pantheon admission_id
Hermes session_id == Pantheon admission_id
X-Hermes-Session-Key absent
```

The context bridge must fail closed if the host does not provide an `admission-...` identity or if the observed task/session correlation differs from the reviewed runtime behavior.

Verify one manifest read and one admitted entity read. Confirm that an entity outside the Context Pack is refused.

## 11. Reconcile once

After observing a terminal Hermes status, execute one explicit reconciliation:

```bash
pantheon-hermes reconcile \
  --receipt launch-receipt.json \
  --idempotency-key <UNIQUE-OPERATOR-KEY> \
  --output return-receipt.json
```

The command observes the run once and records a terminal candidate when safely mappable. It does not poll, retry, accept the result, mutate a Project or admit Evidence.

Expected top-level fields for a completed read-only run:

```text
kind = hermes_run_reconciliation
pantheon_return_recorded = true
scheduler_effect = false
retry_effect = false
technical_receipt_is_evidence = false
```

The bounded Pantheon API response is carried under `recorded`. Inspect it as a separate technical response. Do not infer result acceptance, Evidence admission or Project mutation from `pantheon_return_recorded = true` or from runtime success. Only explicit governed fields in the current API contract may establish those statuses.

```text
pantheon_return_recorded != result accepted
runtime success != Evidence
recorded response != Project mutation authorization
```

## 12. Record factual observations

Preserve as technical trace:

```text
exact Pantheon repository commit
component digests
Hermes exact version and artifact digest
exact governed profile route
plugin inventory
Runs API capability response
toolset response
memory receipt profile, captured_at and stdout_digest
memory posture qualification
OpenWebUI enrichment observation
governed presentation configuration values or unsupported-key result
governed user-visible surface tested
private-reasoning exposure pass/fail result
commentary/interim capability when available
launch reservation identity
run identity
absence of X-Hermes-Session-Key
context access results
return receipt
operator identity and timestamps
```

Do not rewrite the candidate distribution lock to `observed` or `qualified` unless the runtime artifact digest and corresponding observation references are present.

## 13. Revoke and rollback

Revocation order:

```text
revoke or expire active admissions
disable the binding entrypoint
disable pantheon-context-bridge
restore the previous reviewed Hermes profile configuration when required
verify that bounded Pantheon context reads fail
capture and retain the post-rollback memory posture
preserve logs and receipts
```

Routine rollback must not delete Hermes sessions, memory files, PostgreSQL data, models or application volumes.

## Acceptance boundary

The GitHub sentinel introduced by Pantheon-Next#1105 is not target acceptance. If an
operational or consequential binding claims a Hermes-side runtime guard such as
`pre_tool_call`, that guard must be re-observed on the exact deployed artifact
and exact named profile route. The retained target receipt must bind at least:

```text
installed Hermes artifact identity / digest
named profile route
observed tool surface
guard behavior
observation time
target identity sufficient to distinguish it from the GitHub lab
```

If no reviewed target-local sentinel procedure is available, record the
Hermes-side guard as `not_qualified`; do not substitute the Pantheon-Next#1105 lab receipt.
This does not weaken the Pantheon-owned effect PEP, which must remain the
non-bypassable consequential-effect boundary independently of the runtime guard.

```text
Pantheon-Next#1105 lab pass != target runtime guard qualified
runtime guard unqualified != effect PEP unavailable
pre_tool_call != Pantheon PEP
```

A real installation is accepted only when all of the following are observed together:

```text
distribution digests match
exact Hermes artifact recorded
exact /p/pantheon-governed route observed
Runs API compatible
reviewed tool surface qualified
fresh complete memory posture qualified
X-Hermes-Session-Key absent
OpenWebUI hidden memory and automatic RAG disabled
private reasoning absent from each admitted governed user-visible surface
reasoning deltas not projected to each admitted governed user-visible surface
commentary/interim capability recorded when available but not required for safety
context bridge installed and bounded
host task/session correlation verified
one human-admitted read-only run completed
candidate returned without automatic acceptance, mutation or Evidence admission
rollback verified
```

This acceptance remains an operational qualification. It does not authorize future tasks.