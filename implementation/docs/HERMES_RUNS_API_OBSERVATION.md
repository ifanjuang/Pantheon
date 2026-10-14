# Hermes Agent Runs API — observation candidate

Status: verified public API contract / external runtime not connected / no run dispatch implemented here.

Observed upstream release: `v0.19`.

Date verified: 2026-07-25.

Upstream references:

- https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server/
- https://hermes-agent.nousresearch.com/docs/developer-guide/programmatic-integration
- https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference

The upstream release number identifies the observed external contract. It is metadata, not a Pantheon architecture generation.

The stable Hermes Agent API server exposes a machine-readable discovery surface suitable for control-plane observation:

```text
GET /v1/capabilities
GET /v1/toolsets
```

The observed Runs API surface includes:

```text
POST /v1/runs
GET  /v1/runs/{run_id}
GET  /v1/runs/{run_id}/events
POST /v1/runs/{run_id}/approval
POST /v1/runs/{run_id}/stop
```

`POST /v1/runs` is a work-execution primitive. It is not interpreted here as a native capability lifecycle primitive for install, enable, update or retire.

## Current Pantheon boundary

`mvp_vertical.hermes_runs_observer.HermesRunsApiObserver` performs only:

```text
GET /v1/capabilities
GET /v1/toolsets
```

It does not submit a run, stop a run, resolve an approval, install a capability or change runtime activation.

The observer checks support for:

```text
run_submission
run_status
run_events_sse
run_stop
```

It may compare the active concrete API-server tools to an explicit operator-reviewed allowlist.

Without that allowlist:

```text
safety_status = not_evaluated
```

A reachable Hermes API server with the broad default API-server toolset is not automatically qualified for a Pantheon `read_only` admission.

```text
reachable != healthy
healthy != safe
Runs API available != run authorized
toolset configured != toolset approved
```

## Tool surface requirement

The public `/v1/toolsets` endpoint returns the toolsets resolved for the `api_server` platform, including the concrete tool list.

A future live Pantheon-governed binding should use a reviewed, restricted Hermes runtime profile and tool surface. The exact deployment configuration is not adopted by this document.

The observer does not hard-code a claimed safe Hermes toolset name. It receives reviewed `allowed_tools` and `required_tools` configuration and fails qualification when the active surface contains unexpected tools or omits required tools.

## Retired assumption: `/v1/capabilities:operate`

`HermesCapabilityExecutor` previously defaulted to:

```text
/v1/capabilities:operate
```

That path was an earlier candidate assumption. It is not part of the observed stable public API described by the upstream API-server contract.

The generic transport remains available only when an explicitly reviewed native capability-operation endpoint is supplied by a real binding.

```text
transport implemented != native binding verified
/v1/runs available != install/enable/update semantics
```

The Runs API must not be substituted into the capability lifecycle manager merely because it is a real Hermes endpoint.

## Responsibility allocation

Pantheon governs:

- whether a runtime observation is sufficient to qualify a candidate binding;
- the reviewed allowed and required tool surface;
- run admission and later consequential-effect gates;
- displayed runtime status and provenance.

Hermes executes:

- actual agent runs;
- configured tools;
- runtime status, events, stop and approval semantics exposed by its API server.

Cockpit or OpenWebUI may expose:

- observed Runs API compatibility;
- active toolsets and tools;
- qualification mismatch and missing requirements;
- `healthy != safe` warnings.

Human or operator approves:

- runtime profile and toolset configuration;
- binding adoption and activation;
- execution admission under the applicable Pantheon policy.

Forbidden in this slice:

- Pantheon calling `POST /v1/runs`;
- using the observer as a dispatcher;
- assuming broad Hermes API-server tools are safe for `read_only`;
- treating `/v1/runs` as a capability installer;
- inferring approval or Evidence from API reachability.
