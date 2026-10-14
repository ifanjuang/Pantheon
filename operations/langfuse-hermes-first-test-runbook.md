# Langfuse / Hermes First-Test Runbook

Status: qualified synthetic test procedure — production deployment not authorized.

This runbook records the current converged path:

```text
Hermes bundled observability/langfuse plugin
→ Langfuse Python SDK
→ operator-selected Langfuse instance
```

Pantheon does not maintain a second tracing adapter, a Langfuse server fork, a copied Docker Compose, or a server `.env` contract.

```text
Langfuse observes.
Hermes executes.
Pantheon governs.
```

A successful trace is not Evidence, approval, memory, truth, authorization or professional validation.

## Governing references

- `docs/governance/HERMES_RUNTIME_SURFACE_REVIEW.md`
- `docs/governance/HERMES_CAPABILITY_BINDINGS.md`
- `docs/governance/EXTERNAL_RUNTIME_MEMORY_ADAPTERS.md`
- `docs/governance/EXTERNAL_TOOLS_POLICY.md`

These governance documents remain applicable even though the tracing implementation has converged on the bundled Hermes plugin.

## Qualified synthetic matrix

The repository has executable CI coverage for:

```text
Hermes 0.20.5
commit 4c1f53be10d0fce1d25aee1975e5149b6c54f25a

Langfuse Python SDK 4.14.5

Langfuse server v4.18.0
commit c2257f7d86b4407a2b27e8d3a95f719736ef4b01
official upstream docker-compose.yml
```

Observed in the Q2 real-ingestion slice:

- official Langfuse v4 web/worker + Postgres + ClickHouse + Redis + object storage became healthy;
- the initialized project credentials authenticated against the v4 Observations API;
- direct SDK transport produced an observation;
- the real bundled Hermes plugin produced a Hermes turn and tool observations;
- `HERMES_LANGFUSE_CAPTURE=metadata` exposed no synthetic prompt/tool/result/final-response marker in v4 API readback;
- the ephemeral stack and volumes were removed after the test;
- no Hindsight, CouchDB, Evidence or Pantheon governed-state write occurred.

These versions are a recorded qualification matrix, not a claim that future upstream versions are equivalent.

## Selected initial posture

```text
network_exposure: LAN_or_VPN_only
public_exposure: refused
trace_capture: metadata
client_dossier_content: refused_until_data_review
Langfuse_prompt_management: disabled_initially
Langfuse_datasets: disabled_initially
Dashboard_posture: link_only
selected_trace_paths: api_server | runs | openwebui_chat
```

`selected_trace_paths` means the live Hermes surfaces actually chosen for a deployment. A path is not accepted merely because another Hermes surface produced a trace.

The `sanitized` capture mode may be considered for controlled debugging after payload review. `full` is not the default Pantheon posture.

## Preconditions

Before a real deployment, record:

```text
target_host:
operator:
exact_hermes_version_or_commit:
exact_langfuse_release_or_commit:
exact_langfuse_sdk_version:
secret_storage_location:
persistent_volume_locations:
backup_location:
retention_policy:
private_exposure_model:
rollback_owner:
selected_trace_paths: api_server | runs | openwebui_chat
```

If a selected version differs materially from the qualified matrix, re-run or adapt the existing Langfuse qualification rather than assuming compatibility.

## Step 1 — obtain the server runtime from Langfuse upstream

Use the official Docker Compose from the exact Langfuse release/commit selected for deployment.

Do not copy a Pantheon-owned Langfuse compose: the former local v3 compose was intentionally removed after the upstream v4 composition was directly qualified.

Keep the runtime folder and all generated secrets outside the Pantheon governance repository.

## Step 2 — configure the server according to that exact upstream release

Generate deployment secrets outside Git and use the environment variables required by the selected Langfuse release.

Do not paste real secrets into:

```text
Git
GitHub issues
AI logs
Notion
prompts
chat
Obsidian notes
```

The server environment contract belongs to Langfuse upstream and may change independently of Pantheon.

## Step 3 — constrain exposure

Initial deployment must remain private:

```text
localhost, LAN or VPN
```

Public exposure, public DNS and external reverse-proxy publication require their own security review.

## Step 4 — enable and observe the Hermes bundled plugin

Use the plugin shipped by the selected Hermes revision:

```bash
pip install langfuse
hermes plugins enable observability/langfuse
```

Configure Hermes outside Git:

```text
HERMES_LANGFUSE_PUBLIC_KEY
HERMES_LANGFUSE_SECRET_KEY
HERMES_LANGFUSE_BASE_URL
HERMES_LANGFUSE_CAPTURE=metadata
```

Optional environment/release/sample-rate tags may be configured using the current Hermes plugin contract.

The following distinctions are acceptance gates:

```text
plugin present != plugin loaded
plugin loaded != SDK installed
SDK installed != endpoint reachable
endpoint reachable != traces received
trace received on one path != selected live paths instrumented
```

For every `selected_trace_paths` entry, verify the actual Hermes runtime surface reaches the plugin. Do not infer delivery from repository presence, plugin discovery, SDK import or Langfuse health alone.

If a selected live surface cannot demonstrate hook delivery, stop that path and record:

```text
capability_gap: langfuse_hook_path_not_observed
```

## Step 5 — server health

Confirm the selected self-hosted server is healthy before emitting traces.

For the v4 matrix qualified by Q2, the public health endpoint was:

```text
/api/public/health
```

A future release must be checked against its own current documentation.

## Step 6 — synthetic ingestion and live-path test

Emit synthetic-only Hermes activity containing at least:

```text
one turn
one LLM request lifecycle
one tool call
one tool result
final response
```

Then repeat or adapt the fixture through each selected live Hermes surface:

```text
api_server | runs | openwebui_chat
```

Do not use real project/client content during first deployment verification.

Verify via the current Langfuse read surface. For the qualified v4 matrix, Q2 used:

```text
/api/public/v2/observations
```

Do not use the legacy `/api/public/traces` endpoint as the acceptance readback for v4; Q2 demonstrated that doing so creates a false negative even when native OTEL ingestion is functioning.

For each selected path, record enough stable identifiers to prove correlation between the Hermes execution and the received observation. Where a governed run exists, retain the run/Task Contract correlation rather than inferring identity from free-form trace text.

Required completion observation:

```text
run_correlation_verified: true | false | not_applicable
```

A received observation without the expected runtime-path or run correlation is a partial result, not successful acceptance for that path.

## Step 7 — content boundary

In `metadata` mode verify that the server readback does not expose synthetic content markers representing:

```text
prompt body
tool arguments
tool result
final response
```

Structural metadata such as tool names, IDs, timings, token usage and costs may still be present by design.

```text
metadata capture verified in one fixture != universal DLP guarantee
```

Real dossier content remains disallowed until retention, access and data-exposure policy are reviewed for the actual deployment.

## Step 8 — operational checks before production use

A NAS/production qualification still needs to record and test:

```text
persistent volumes
restart/redeploy
backup/restore
retention/deletion
credential rotation
private network/TLS posture
user/project access control
resource consumption
upgrade/rollback
plugin + SDK health
```

Successful ephemeral CI ingestion does not prove any of these deployment properties.

## Dashboard posture

Pantheon may expose only an observability status/link unless a separate UI decision is made:

```text
module: observability.langfuse
state: reachable | degraded | unavailable
ui_url: internal link
open_ui_action: external_link
embedded_view: false
```

Dashboard must not interpret trace success as proof, approval or memory.

## Failure posture

The bundled Hermes plugin is designed to fail open when its optional SDK or credentials are unavailable. Q1 verified the no-credentials path does not block Hermes.

Therefore:

```text
Langfuse unavailable != Hermes unavailable
```

But silent loss of observability is still an operational degradation and should be surfaced by health monitoring.

## Rollback

Rollback of a self-hosted test is owned by the selected upstream deployment composition and operator. Do not delete persistent volumes merely because a trace test is complete unless deletion is intentional and authorized.

The Q2 CI fixture used ephemeral volumes and explicitly removed them because it contained synthetic data only.

## Completion record

Record at minimum:

```text
host:
hermes_identity:
langfuse_server_identity:
langfuse_sdk_identity:
exposure:
health_status:
plugin_enabled:
sdk_available:
selected_trace_paths:
observed_trace_paths:
trace_ingestion_verified:
v4_observations_readback_verified:
run_correlation_verified:
capture_mode:
real_content_enabled: false
persistent_storage_verified:
backup_restore_verified:
retention_verified:
rollback_verified:
capability_gaps:
```

## Boundary phrase

```text
The runbook tests observation.
It does not validate truth, approve action, canonize memory or govern the dossier.
```
