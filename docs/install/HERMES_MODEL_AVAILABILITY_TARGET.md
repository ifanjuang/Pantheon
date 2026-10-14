# Hermes model availability target — Linux baseline + gpu-node quality tier

Status: selected operational target for qualification under Pantheon-Next#644. This document does not prove the live nodes currently match the target and does not authorize runtime activation.

## Objective

Keep the professional assistant usable when gpu-node is asleep, unavailable or unable to serve the larger model, without introducing a Pantheon provider router.

```text
Linux — always available
├── AFFAIRES producer
├── Hindsight
├── CLM candidate service
└── qwen3.5:9b via local Ollama / PAIR
        ↑
        │ native Hermes fallback
        │
gpu-node — quality tier
└── qwen3.5:27b via Ollama / PAIR
```

The intended generation policy is:

```text
Hermes primary request  = qwen3.5:27b
Hermes fallback request = qwen3.5:9b
PAIR                     = transport/node selection for the requested model
Pantheon                 = neither model router nor inference scheduler
```

## Observed repository and upstream facts

Pantheon `main` selected this target after Pantheon-Next#1154 retired LiveSync/CouchDB and Pantheon-Next#1150 merged the passive CLM qualification.

The currently selected Hermes deployment pin is 0.21.3 / `v2026.9.14`. At that exact release, upstream Hermes already exposes the top-level `fallback_providers` chain, supports a `custom` OpenAI-compatible endpoint, and applies primary fallback to messaging gateway sessions. Therefore the availability requirement does not justify a new Pantheon proxy or router.

The older `HERMES_LOCAL_RUNTIME_STATUS.md` observation where 9B became the primary remains historical evidence of the then-live configuration. Its statement that there was no *configured* inter-model fallback must not be read as an absence of fallback capability in Hermes 0.21.3.

## Target runtime shape

Use the same PAIR client-facing endpoint for both model identities when the deployment exposes both there. The exact live provider name and endpoint remain operator/runtime observations; no LAN IP or credential belongs in this document.

Illustrative Hermes shape:

```yaml
model:
  provider: custom
  default: qwen3.5:27b
  base_url: http://127.0.0.1:<PAIR_OPENAI_PORT>/v1

fallback_providers:
  - provider: custom
    model: qwen3.5:9b
    base_url: http://127.0.0.1:<PAIR_OPENAI_PORT>/v1
```

A named custom provider may be retained instead of the literal `custom` form when that is what the live profile already uses. Qualification must record the effective provider/model/base URL rather than rewriting a working provider definition merely to match this example.

## Why fallback belongs in Hermes

Hermes already owns runtime execution mechanics and model/provider fallback. PAIR owns transport and eligible-node routing for a requested model. Pantheon only needs to observe the effective requested/served model and preserve governance boundaries.

```text
primary model unavailable
-> Hermes fallback policy
-> request qwen3.5:9b
-> PAIR routes that requested model to an eligible node

PAIR node selection
!= inter-model fallback

Hermes fallback
!= task authorization

served model
!= result validity
```

Do not add a Pantheon model router, inference scheduler or retry owner.

## Linux responsibilities

The Linux node is the availability baseline:

```text
NAS / AFFAIRES
-> standalone producer
-> Hindsight

Linux GPU/runtime
-> qwen3.5:9b availability tier
-> CLM quantized-encoder candidate after Pantheon-Next#1047 qualification
```

Hindsight memory remains derived context, not Evidence. CLM rank remains an observation, not a decision or authorization.

The Linux 16 GiB GPU budget must be tested with both the 9B fallback workload and the CLM encoder. Do not infer co-residency merely because the individual model files fit.

## gpu-node responsibilities

gpu-node is the optional quality tier:

```text
gpu-node available + qwen3.5:27b advertised
-> primary 27B request may be served

gpu-node unavailable / model unavailable / qualifying server failure
-> Hermes may switch the same turn to the declared 9B fallback
```

gpu-node availability must improve quality/capacity, not become a prerequisite for basic assistant availability.

Wake-on-LAN, sleep inhibition and idle policy are operational optimizations. They do not alter the fallback boundary.

## H5.9b qualification

Under Pantheon-Next#644, record one exact live runtime envelope and exercise at minimum:

1. primary 27B healthy — observe requested and served model;
2. primary 27B unavailable — observe Hermes native switch to 9B;
3. fallback 9B unavailable — observe bounded failure rather than a hidden third route;
4. next turn after a transient failure — verify current Hermes per-turn primary retry behavior;
5. one messaging-gateway request — verify fallback is not CLI-only.

Record:

```text
Hermes version/ref
effective profile
provider/base URL
requested model
served model
PAIR catalogue observation
node/model availability observation
failure class
fallback event/trace
result status
```

No client document is required for this availability qualification.

## Acceptance

The target can be promoted from qualification to operational selection only when:

- 27B success is observed on gpu-node;
- an induced/real qualifying 27B failure switches to 9B;
- the 9B response remains within the same admitted Task Contract and capability/effect ceiling;
- no hidden provider or cloud route is used;
- a fallback failure remains a visible failure;
- model switching does not alter memory, source-access, credential or authorization boundaries;
- runtime traces preserve requested vs served model when observable.

```text
fallback succeeded != professional answer correct
fallback succeeded != Evidence
fallback succeeded != authorization
```
