# PAIR + Unsloth Runtime Qualification

Status: candidate qualification plan. No live lab has been executed by this document.

Execution runbook: `docs/governance/PAIR_UNSLOTH_RUNTIME_Q1_RUNBOOK.md`.
Machine-readable planning state: `tests/fixtures/pair_unsloth_runtime_q1.json`.

## Objective

Determine whether NVIDIA Personal AI Router (PAIR) can safely provide the external physical inference-routing layer for Pantheon's local GPU fleet, and whether Unsloth can be used as a separate local Hermes model/provider surface, without adding a Pantheon scheduler, inference router, runtime owner, memory owner, or authorization path.

The exact external artifacts are owned only by `implementation/qualification/external-pins.json`. Upstream observations are owned separately by `implementation/qualification/external-upstream-observations.json`.

## Authority boundary

The candidate composition under qualification is:

```text
Pantheon
  -> governs capability / admission / consequence
Hermes
  -> semantic orchestration and selected provider/model use
PAIR
  -> physical placement of an eligible Ollama/LM Studio request
Ollama / LM Studio
  -> inference execution on one node

Hermes
  -> optional custom OpenAI-compatible provider binding
Unsloth
  -> separate local inference / training / quantization surface
```

PAIR is not a Pantheon authorization owner. Unsloth is not a second Hermes owner. A successful request does not become Evidence.

## Existing seams that make the lab necessary

The Ubuntu deployment candidate currently installs and starts Ollama itself on the standard Ollama port. PAIR can expose that same standard port as its local compatibility proxy and may relocate a PAIR-managed backend behind it. The ownership interaction must therefore be observed before any deployment change.

The Ubuntu deployment candidate currently runs Hermes in Docker Compose. PAIR's source-reviewed plaintext client ingress is loopback-only, while paired peer traffic uses cluster mTLS. The current container-to-host path must be executed as-is before proposing host networking, a native Hermes process, or any relay.

These are qualification questions, not conclusions about the live environment.

## Q1 execution topology

The runbook uses the current known hardware topology without making it architectural authority:

```text
Linux RTX 4080 always-on
  -> PAIR headless/TUI in isolated HOME
  -> Unsloth in isolated source/venv/home/cache

Windows RTX 4090 always-on
  -> PAIR Desktop
  -> second cluster node
  -> Jobs / serving-node observation

Current Pantheon Hermes container
  -> used only for Q1C/Q1D namespace/provider compatibility checks
```

The test models, ports and temporary profile names are fixture/runbook inputs only. They are not production selections or model approvals.

## Q1 sequence

### Q1A — isolated PAIR on the always-on Linux GPU node

Use an isolated PAIR HOME and a PAIR-owned Ollama rather than the Pantheon Ubuntu deployment candidate's model store. Resolve the selected PAIR artifact from the external pin registry and validate the concrete release asset before execution.

Observe service lifecycle, Ollama ownership mode, standard-port proxy behavior, backend relocation when PAIR owns the engine, one-model inference, workload visibility, and engine-uninstall behavior. Confirm the PAIR-owned model weights remain after PAIR engine uninstall, as the selected upstream release documents, while independently proving that `/srv/ai/models/ollama` did not change.

The existing Pantheon Ollama service may be stopped only for the bounded lab window to free the proxy port; its unit, drop-in, model path and repository deployment definition are not modified. Its pre-lab state must be restored.

### Q1B — add the always-on Windows GPU node

Use PAIR Desktop on Windows and `nvpair-tui` on Linux; do not run both surfaces on the same host.

Pair the Linux and Windows nodes explicitly. Put the same bounded test model on both engines as independent copies. Distinguish successful mDNS discovery from direct-IP pairing.

Generate concurrent independent requests from the Windows PAIR endpoint and use Desktop Jobs / `Ran on` as the serving-node observation surface. Stop the Linux PAIR service, confirm exclusion and continued Windows service, then restart Linux and observe whether prior membership/eligibility returns.

Do not interpret success as pooled VRAM, model sharding, or one request split across machines.

### Q1C — current Hermes container to local PAIR proxy

Use the current Pantheon candidate Compose networking path without first adding a workaround. A transport probe must originate inside the actual `pantheon-hermes` container network namespace and target `host.docker.internal` at the local PAIR client endpoint.

Record HTTP status, PAIR error if any, container/source network identity and the current Compose hash. In particular, do not pre-record `403` merely because source review indicates a loopback-only gate.

If the current path is refused, end Q1C with that observed finding. Host networking, native Hermes, mTLS client access or a relay are separate candidate experiments and must not be smuggled into the same result. The Compose hash must remain unchanged.

### Q1D — Unsloth through the existing Hermes provider seam

Resolve the Unsloth target from the external pin registry and check out that exact source into an isolated venv, Studio home and model cache.

After dependency installation and `unsloth studio setup`, capture the effective runtime closure before claiming reproducibility: Python version, installed Python package versions, Torch version and CUDA view, and the identity/hash of the effective `llama-server`/llama.cpp runtime when discoverable. If a dynamically resolved component cannot be identified, record that check as `unresolved`; do not infer it from the Unsloth source pin.

Bind the Unsloth API to the host-side Docker bridge gateway needed by the current Hermes container; do not use wildcard/LAN exposure merely for the lab. This is a bridge-scoped exposure, not proof that Hermes is the only container able to reach it. Record the bridge/network identity actually used.

Do not use `unsloth start hermes`. Use the selected Hermes runtime already present in the container, create a fresh temporary `pantheon-q1-unsloth` profile, and configure only that profile with a named custom OpenAI-compatible provider. Do not clone `pantheon-governed`, because Hermes profile cloning would copy `.env` and other configuration that Q1 does not need.

Observe endpoint health, streaming, structured tool-call output, a bounded Hermes tool round trip under normal approval policy, context behavior, explicit provider-error behavior, absence of silent fallback, and rollback of the temporary profile/server.

Hash `pantheon-governed` before and after Q1D. It must remain unchanged.

Unsloth does not enter the PAIR cluster in Q1. Current PAIR engine support and generic external OpenAI-compatible endpoint support are separate upstream concerns.

### Q1E — classify without activating

Create one sanitized observation row for every required check before classification. Each row must carry check/stage/host/action, expected and actual observation, status, artifact reference and timestamps; no PINs, secrets, prompts or generated response bodies are admitted into the observation record.

Classify PAIR and Unsloth independently as `accepted`, `rejected`, or `unresolved` candidates from those records. A PAIR result must not automatically decide Unsloth, and vice versa.

Before any later deployment PR, the review must explicitly resolve or retain as open:

- Ollama process/port ownership between the Pantheon bootstrap candidate and PAIR;
- Hermes container access to PAIR's local client ingress;
- rollback behavior;
- exact runtime artifact identities, including dynamically resolved Unsloth dependencies actually used in Q1D;
- supported model/engine scope;
- network exposure and telemetry posture;
- whether the resulting topology removes duplication rather than adding another routing path.

## Q1 done gate

Q1 is complete only when every required check in `tests/fixtures/pair_unsloth_runtime_q1.json` has a real sanitized observation row and the two candidates have an explicit classification.

The Q1 planning PR must remain `live_executed = false` and every stage `not_run`. A later observation PR may change those fields only from actual lab records.

No Q1 planning result may change `deployment/ubuntu/release.env`, `deployment/ubuntu/install-node`, the Hermes distribution lock, runtime activation state, task authorization, or Evidence state.

## Non-equivalences

```text
retrieved upstream information != truth about the live machine
upstream observed != qualification pin selected
qualification pin selected != runtime observed
runtime observed != runtime qualified
runtime qualified != runtime activated
PAIR node reachable != model approved
PAIR routing success != Pantheon authorization
Unsloth endpoint configured != provider authorized
runtime success != Evidence
projection != persistence
```
