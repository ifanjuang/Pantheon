# Hermes distribution composition lock

Date: 2026-08-04  
Updated: 2026-08-24

Status: candidate implementation/deployment composition — non-authoritative.

## Purpose

The Hermes integration keeps independently owned components while recording one reproducible operational core:

```text
external run binding
bounded context bridge plugin
Runs API observer
```

Skills, policy MCP and dashboard remain available candidates in the Pantheon monorepo, but are not included in `pantheon-standard.lock.yaml` until explicitly selected. The lock is a composition, not a catalog.

## Integrity contract

The active lock follows `pantheon.hermes_distribution_lock` revision 3 and records one reviewed `Pantheon-Next` monorepo revision, monorepo-relative component paths, exact component digests, deterministic digest modes, the exact Hermes target `0.20.0`, and a null runtime artifact digest while no real installation has been observed.

Revision 3 deliberately removes per-component repository identity. Component paths locate bytes from one reviewed repository root; governed ownership remains separate.

```text
path / zone != governed identity
source revision recorded != final self-containing commit
component digest matched != component installed
runtime version reviewed != runtime artifact observed
```

## Hermes 0.20 placement

`docs/governance/HERMES_RUNTIME_SURFACE_REVIEW.md` is the stable release-review identity. Its current reviewed target is Hermes 0.20.0. The release retains the Runs API used by the candidate bridge while adding A2A, outbound webhooks, grounded citations and voice.

```text
A2A peer trusted != approved actor
webhook available != external effect authorized
citation returned != Evidence admitted
voice instruction received != human approval recorded
provider/model request fields available != provider routing delegated to Pantheon
```

The run binding continues to omit `model`, `provider` and `model_options`; model and provider routing remain external Hermes configuration. The selected implementation core and its three content digests are unchanged.

## Shared validator and CLI

`mvp_vertical/hermes_distribution.py` owns schema application, monorepo containment, digest, route and non-authority checks. `tools/check_hermes_distribution_lock.py` remains the CI wrapper.

The one-shot command `pantheon-hermes` exposes `verify-distribution`, `observe`, `launch` and `reconcile`. Distribution verification accepts one `--monorepo-root`; it no longer models the former governance and implementation repositories as separate component sources.

The CLI owns no daemon, queue, scheduler, polling loop, retry, provider routing, model selection, installation, activation or approval.

## Remaining external operation

Repository tests do not prove a real Hermes installation. A real acceptance still requires the exact Hermes 0.20.0 artifact digest, plugin installation, tool-surface qualification, host task/session correlation, one human-admitted read-only run and verified rollback.

The lock therefore retains:

```text
artifact_digest: null
installation_state: not_observed
activation_state: not_activated
task_authorization_state: not_authorized
acceptance_state: not_run
```

```text
composition pinned != components installed
components installed != binding activated
acceptance passed != task authorized
runtime return != accepted result
runtime output != Evidence
```
