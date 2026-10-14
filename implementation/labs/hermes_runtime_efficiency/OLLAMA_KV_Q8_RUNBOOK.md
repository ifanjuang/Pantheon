# Ollama KV-cache Q8 qualification runbook

Status: bounded qualification procedure for Pantheon issue Pantheon-Next#1047. This file does not claim that a live run has occurred and does not activate any runtime setting.

## Objective

Determine whether changing only Ollama's KV-cache type from `f16` to `q8_0` materially reduces GPU-memory pressure for the current governed Hermes workload without degrading source recall, result completeness, tool behavior, or operational stability.

This is a runtime qualification, not a model-selection exercise.

```text
Qwen model weights unchanged
Hermes runtime/profile unchanged
PAIR route unchanged
context/workload unchanged
Flash Attention enabled in both variants
only controlled variable: OLLAMA_KV_CACHE_TYPE=f16 -> q8_0
```

## Current-state caveat

Repository state and live-machine state are separate facts.

At preparation time, repository `main` was revalidated at:

```text
0528c0f82dee100b02a8b0583ea746eb3ae3b200
```

The operator reports that the live primary model is currently Qwen 3.5 27B under PAIR and working. That report is an execution input to re-observe on the serving node before the lab; it is not promoted to repository-observed runtime truth by this runbook.

The older `docs/install/HERMES_LOCAL_RUNTIME_STATUS.md` snapshot must not be used as proof of the current model.

## External behavior revalidated for this slice

Current upstream documentation establishes that:

- PAIR routes one complete inference request to one eligible node; it does not pool VRAM across nodes;
- a manual node selection takes precedence over automatic scheduling;
- PAIR's Ollama-compatible proxy normally occupies the client-facing port while the local Ollama engine is moved behind it;
- PAIR may either own an engine it started or adopt an already-running engine;
- Ollama exposes `OLLAMA_KV_CACHE_TYPE`; its default is `f16` and `q8_0` is the recommended reduced-memory alternative;
- quantized KV cache requires Flash Attention;
- `OLLAMA_KV_CACHE_TYPE` is global to an Ollama server, not per request or per model.

Reference material:

- https://docs.nvidia.com/local-ai/nvpair/getting-started/
- https://docs.nvidia.com/local-ai/nvpair/engine-lifecycle/
- https://docs.nvidia.com/local-ai/nvpair/
- https://github.com/ollama/ollama/blob/main/docs/faq.mdx
- https://github.com/ollama/ollama/blob/main/envconfig/config.go

These upstream observations are not proof of the live host state.

## Authority ceiling

This lab may observe and compare runtime behavior. It does not:

```text
select or approve a model
change Pantheon authorization
create Evidence
change memory ownership
change PAIR authority
persist q8_0 into deployment configuration
widen context admission
turn a successful inference into a valid professional result
```

A live runtime experiment is reversible and local. Any persistent activation requires a later explicit decision after measured results.

## Gate 1 — identify the exact serving node and engine owner

Before changing anything, record:

```text
PAIR version
serving node identity
GPU and driver
Ollama version
Ollama engine port
whether Ollama is PAIR-owned or adopted
Hermes runtime identity
Hermes profile identity/hash
exact model identity shown by the serving Ollama engine
model/weights digest when observable
context length
current Flash Attention state
current KV-cache type
```

Use PAIR's Jobs / `Ran on` observation or a manual node pin to prove the serving node. Baseline and candidate are not comparable if different nodes serve them.

If engine ownership is ambiguous, stop.

### PAIR-owned Ollama

PAIR documentation says to prefer PAIR controls for a PAIR-managed engine. No documented PAIR setting currently provides a generic UI field for arbitrary Ollama environment variables.

Do not patch PAIR internals, its engine manager, or its persisted state merely to force this experiment. If the PAIR-owned process has no already-supported, observable environment-injection seam on the installed version, stop this path and use an adopted/disposable Ollama qualification instance instead.

### Adopted Ollama

An already-running Ollama can be adopted by PAIR. This is the preferred bounded path when the operator controls the process environment directly.

The process must remain loopback-only and use the existing PAIR-supported topology. Do not expose a new LAN endpoint for the experiment.

## Gate 2 — keep the serving node fixed

For the A/B pair, either:

1. manually pin the eligible PAIR node for the test; or
2. make only one test node eligible for the exact model during the bounded window.

Record the `Ran on` node for every request. Any pair that crosses nodes is invalid.

Do not interpret a successful PAIR request as pooled VRAM or distributed inference.

## Gate 3 — establish canonical settings digests

Each observation must carry two digests:

```text
settings_digest
  SHA-256 of the complete effective test settings, including kv_cache_type

invariant_settings_digest
  SHA-256 of the same canonical settings with only kv_cache_type removed
```

The canonical payload should include every setting capable of changing the comparison, at minimum:

```text
runtime identity
profile identity
model identity / weight digest when observable
PAIR version and serving node
Ollama version
context length
Flash Attention state
parallelism / loaded-model policy when relevant
prompt/workload case identity
sampling parameters
```

The two variants must have different `settings_digest` values and identical `invariant_settings_digest` values. Otherwise the adapter fails closed.

## A/B variants

### Baseline

```text
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=f16
```

### Candidate

```text
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
```

Do not test `q4_0` in this slice. A lower-bit experiment is a separate decision only if q8_0 later proves insufficient.

Restart or reload the Ollama server/model as required so that the effective server-level KV setting is known for each variant. Do not assume changing a shell variable alters an already-running Ollama process.

## Workload cases

Run at least three matched A/B pairs. Give each repetition its own `case_id` so the existing comparator never hides run-to-run variation.

Use representative, non-sensitive cases drawn from issue Pantheon-Next#1047:

1. a long admitted-context case that materially fills the KV cache;
2. a bounded agency-style source task requiring exact source recall and synthesis;
3. a tool-using Hermes task that exercises normal tool selection and return handling.

Use the same prompt/workload fixture, admitted sources and expected checks for each A/B pair.

## GPU-memory observation

For every run record `peak_gpu_memory_bytes` on the fixed serving node.

Prefer a quiet node and sample GPU memory repeatedly across model load, prefill and generation. Record the peak observed value, not a hand-estimated KV-cache size.

Example NVIDIA sampling surface on Linux:

```bash
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader,nounits
```

Example PowerShell sampling surface on Windows:

```powershell
nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader,nounits
```

The command reports MiB; convert the recorded peak to bytes before writing `peak_gpu_memory_bytes`.

A lower peak is an observed resource gain only. It does not prove preserved model quality.

## Observation envelope

Start from the existing issue-#1047 observation envelope and add:

```json
{
  "kv_cache_type": "f16",
  "flash_attention": true,
  "settings_digest": "sha256:...",
  "invariant_settings_digest": "sha256:...",
  "peak_gpu_memory_bytes": 0
}
```

The candidate changes only:

```json
{
  "kv_cache_type": "q8_0",
  "settings_digest": "sha256:different-full-settings-digest"
}
```

All source-recall, quality, lineage and result-status fields from the core lab remain mandatory when relevant.

## Compare

Run:

```bash
python implementation/labs/hermes_runtime_efficiency/compare_kv_cache.py \
  baseline.json candidate.json
```

The adapter delegates quality/provenance and ordinary operational-cost comparison to the existing `compare.py` owner. It adds only:

```text
controlled_experiment
resource_metrics.peak_gpu_memory_bytes
resource_qualification
```

It does not execute Hermes, PAIR or Ollama and cannot mutate a live runtime.

## Interpretation

A useful q8_0 result requires all of the following:

```text
same runtime/model/profile
same serving node
same invariant_settings_digest
quality_gate = pass
all required source-recall checks pass
result_status = complete for both variants
resource_qualification = memory_gain_observed
no unexplained regression in elapsed time, turns or tool calls
```

`candidate_for_further_qualification` or `memory_gain_observed` does not mean `activate q8_0`.

If quality regresses, reject the candidate even if memory improves.

If the cost trade-off is mixed, retain it as mixed rather than inventing a threshold after seeing the result.

## Rollback

After every bounded live experiment:

1. restore the original Ollama ownership/start mode;
2. restore the original Flash Attention and KV-cache environment;
3. remove any temporary PAIR manual pin;
4. restart/reload the original engine if required;
5. verify the original model is advertised and a normal Hermes request succeeds;
6. verify no repository deployment file, model store or governed state was changed by the lab.

## Done criteria

This slice is complete only when:

- the adapter tests pass;
- the exact live engine ownership and serving node are re-observed;
- at least three matched f16/q8_0 pairs are recorded;
- every pair is comparable or explicitly rejected as invalid;
- quality/provenance remains separate from resource gain;
- rollback is observed;
- issue Pantheon-Next#1047 records the measured result and one of: retain f16, qualify q8_0 further, or inconclusive.

Until then, q8_0 remains a candidate setting only.
