# Governed Hermes runtime-efficiency qualification

Status: qualification lab for Pantheon issue Pantheon-Next#1047. Not installed, activated, adopted or wired into any product/runtime path.

## Purpose

Measure whether the exact governed Hermes runtime used by Pantheon has a demonstrated efficiency problem before prototyping any SoL-inspired mechanism.

```text
recorded governed Hermes observation
            +
recorded candidate observation
            ↓
provider-neutral comparison
            ↓
quality/provenance gate first
            ↓
operational cost comparison second
            ↓
qualification decision only
```

This lab does not execute Hermes, install SoL-Pi, change Hermes configuration, select a model/provider, persist runtime state or create Pantheon authority.

## Current baseline

Opened from:

```text
Pantheon-Next main: 836219b7e9c271d64a4850bd2484d3767c56a38f
Pantheon deployment target: nousresearch/hermes-agent:v2026.9.11
reference project: NVlabs/SoL-Pi
issue: Pantheon-Next#1047
```

Revalidate those identities before a live qualification run. Repository state here is provenance, not proof of what is currently installed on the Linux node.

## Existing owners remain unchanged

```text
Pantheon Context Pack / scoped context = admitted working perimeter
Hermes                         = runtime execution mechanics
Hermes native compression     = runtime context hygiene
Pantheon Evidence owners      = Evidence semantics/admission
Pantheon Memory doctrine      = Registre boundary
human / existing gates        = consequential decision
```

No `efficiency engine`, `ObservationPack`, `DistilledContext`, reducer owner, memory owner, Evidence owner or Capability Slot is introduced.

## Comparison envelope

Each observation is a local JSON object consumed by `compare.py`.

Required identity fields:

```text
case_id
variant
runtime_identity
result_status
```

Identity fields to record when observable:

```text
model_identity
profile_identity
settings_digest
```

Operational metrics are optional; missing values are `null`, never zero by inference:

```text
input_tokens
output_tokens
llm_turns
tool_calls
elapsed_seconds
max_context_tokens
repeated_context_tokens
large_tool_result_count
large_tool_result_chars
```

`elapsed_seconds` must be finite and non-negative. `NaN`, `Infinity` and overflow-to-infinity values are rejected rather than allowed to contaminate deltas or JSON output.

Quality/provenance fields:

```text
source_recall_checks
source_recall_passes
source_recall_check_ids: [stable opaque check identity, ...]
required_quality_checks: {name: boolean}
retrieved_refs
admitted_refs
used_refs
notes
```

When source recall is observed, stable `source_recall_check_ids` are mandatory and their count must equal `source_recall_checks`. The A/B perimeter is compared by those identities, not merely by the number of checks.

Opaque task-local refs are preferred. Do not commit client content or sensitive document locators merely to populate a lab fixture.

When lineage refs are recorded, all three sets must be present and the harness enforces:

```text
used ⊆ admitted ⊆ retrieved
```

## Result status

Accepted observation statuses are deliberately operational only:

```text
complete
partial
blocked
failed
unknown
```

They do not create Pantheon result validity, Evidence status or approval.

Operational-cost qualification requires both the baseline and candidate to be `complete`. A partial, blocked, failed or unknown run cannot appear cheaper merely because it terminated earlier. Candidate `blocked`/`failed` is a quality regression; any other non-complete pair is inconclusive.

## Quality-first rule

The candidate cannot be preferred merely because it uses fewer tokens or fewer calls.

The harness rejects or makes inconclusive a candidate when it:

- is not a completed equivalent execution;
- fails required source-recall checks;
- uses a different source-recall check perimeter;
- fails an explicitly required quality/provenance check;
- returns `blocked` or `failed`;
- lacks a required quality observation.

Unknown quality remains `unknown` and yields an inconclusive decision rather than a token-saving claim.

```text
fewer tokens != better result
summary != source
reduced context != Evidence
runtime success != result validity
```

## Comparability

An A/B pair must use the exact same `case_id` and different variant names.

A runtime identity mismatch blocks causal comparison. Known model/profile/settings mismatches also block comparison. Missing model/profile/settings identity is preserved as a warning rather than silently treated as equal.

This lets the first live qualification expose incomplete observability without fabricating parity.

## Cost comparison

For each known metric the harness reports:

```text
baseline
candidate
delta = candidate - baseline
percent_change when baseline != 0
```

Lower is treated as operationally cheaper for the listed cost metrics only after the quality/provenance gate passes. There is deliberately no universal score or arbitrary token threshold.

Possible lab decisions:

```text
candidate_for_further_qualification
mixed_cost_tradeoff
no_measured_gain
reject_candidate
inconclusive
```

None means `adopted`.

## Representative live cases

Use the same model/profile/settings per A/B pair whenever technically possible.

### C1 — large admitted representation

Exercise a large admitted document/Knowledge representation, including the current scoped-context pressure/oversize boundary where relevant.

Goal: determine whether native Hermes/scoped-context handling is already sufficient before considering handle-based recall.

### C2 — large diagnostic/tool output

Use a long terminal, test or diagnostic result whose raw source remains locally recoverable.

Goal: measure whether repeated large observations materially dominate model context.

### C3 — edit/validate loop

Exercise several deterministic edit → validation cycles on disposable code/text fixtures.

Goal: measure whether LLM-turn overhead is material enough to justify an Action-Fusion-like runtime experiment.

### C4 — long agency source task

Use synthetic/non-sensitive agency-style material requiring project context, bounded memory/workspace retrieval, source checking and synthesis/calculation.

Goal: measure real professional-work context pressure rather than coding-only performance.

## CLM passive shadow-ranking slice

A bounded Contrastive-LM experiment is prepared under the same Pantheon-Next#1047 lab because it asks an efficiency/selection question without changing Hermes execution.

```text
state + fixed candidate set
        |
        v
local CLM /v1/rank
        |
        v
shadow observation only
```

Files:

```text
clm_shadow_rank.py
clm_shadow_cases.json
CLM_SHADOW_RUNBOOK.md
```

The initial corpus is synthetic and short. It measures expected top-1 match and candidate-order stability across deterministic permutations. It intentionally does not use CLM's typed `score` mode and does not test long contexts.

The slice is not a Q1/Q2/Q3 arm from Pantheon-Next#1093. CLM does not alter direct/delegation/goal/Kanban execution while those tactics are being causally compared.

```text
CLM rank != Hermes decision
CLM rank != Pantheon authorization
shadow observation != Evidence
```

A good first shadow result may justify a larger held-out shadow corpus. It does not justify a router, CandidateRanker abstraction, production service or Hermes wiring.

See `CLM_SHADOW_RUNBOOK.md` for the exact runtime receipt requirements. The first prepared live topology keeps CLM on the Pantheon Linux node and serves the exact Qwen3-8B pooling encoder from gpu-node/WSL through an authenticated SSH local forward:

```text
Linux CLM -> 127.0.0.1:18090 -> SSH local forward -> gpu-node/WSL vLLM -> RTX 4090
```

The gpu-node vLLM HTTP service remains loopback-only. Placement is recorded separately from model identity; quality/stability observations remain attributable to the pinned model candidate, while transport latency is topology-specific and must not be compared as if it were a local encoder baseline.


### Optional agency French shadow corpus (Pantheon-Next#1166)

`clm_shadow_cases_fr.json` is a separate, synthetic 10-case corpus covering bounded email handling, document revisions and context selection. It reuses the existing `clm_shadow_rank.py` loader and the exact Pantheon-Next#1047 CLM runtime pin; run it by passing this corpus path instead of `clm_shadow_cases.json` in the existing shadow runbook. The original 12-case reference and its BF16/quantized acceptance gate are unchanged.

These are **human-authored expected choices, not live measurements**. Compare only identical corpus digests and runtime identities. Retain all per-case failures and candidate-ordering sensitivity; a high matching rate here neither proves professional correctness nor warrants Hermes routing or model activation. Pantheon-Next#1093 retains the independent direct/delegation/goal/Kanban experiment; Pantheon-Next#1166 is a conditional follow-up only if the existing rule/CLM/native baselines leave a measured classification gap. All candidate inference must remain on operator-controlled local hosts with no remote fallback.

### Quantized Linux encoder arm

The merged reference arm remains the exact Qwen3-8B/vLLM encoder used by the published CLM head. A separate bounded arm now qualifies a Linux-local GGUF encoder without redefining that reference:

```text
gpu-node / BF16 / vLLM
= numerical reference

Linux / Q8_0 or Q4_K_M / llama.cpp
= experimental deployment candidate
```

`CLM_QUANTIZED_ENCODER_RUNBOOK.md` reuses the same corpus, public CLM head and `/v1/rank` observer. `compare_clm_shadow_reports.py` compares identical case/order observations and reports top-1 agreement, full-rank agreement, probability drift and order-stability regressions. It selects no encoder and creates no activation decision.

The Linux target is not accepted merely because a GGUF fits in 16 GiB. After ranking comparison it must also demonstrate real co-residency/reload behavior beside the 9B fallback and Hindsight workload. If Q8 is faithful but cannot satisfy the node envelope, Q4_K_M is tested as a distinct candidate rather than silently substituted.

## Decision order after measurement

```text
native Hermes sufficient
→ stop; no new mechanism

large/repeated observation cost dominates
→ only then consider a bounded handle/exact-recall prototype

edit/validation turn cost dominates
→ only then consider Action-Fusion-like behavior

long diagnostic-log cost dominates
→ only then consider local provenance-preserving reduction

completed-step history dominates
→ only then consider additional compaction trigger logic
```

Prefer configuration or reuse of an existing Hermes mechanism before new runtime code.

## SoL-Pi boundary

SoL-Pi is reference material only. This lab does not depend on Pi or SoL-Pi packages.

If one mechanism is later justified, reimplement only the smallest required behavior through an exact, verified Hermes extension surface. Do not copy Pi's extension architecture into Pantheon.

Remote reducer/model use is outside this slice. Local-only is the default posture for any future diagnostic-log reduction experiment.

## Run locally

Prepare two JSON observations, then:

```bash
python implementation/labs/hermes_runtime_efficiency/compare.py baseline.json candidate.json
```

The output is a qualification report, not persisted governed state.

## Removal test

Removing these files restores prior behavior completely:

```text
implementation/labs/hermes_runtime_efficiency/
implementation/tests/test_hermes_runtime_efficiency_lab.py
.github/workflows/implementation-hermes-runtime-efficiency-qualification.yml
```

No product module imports this lab.

## Current status

Implemented in this slice:

- provider-neutral observation parser;
- `used ⊆ admitted ⊆ retrieved` validation when lineage is observed;
- identity/comparability checks;
- complete-run equivalence gate before cost preference;
- stable source-recall perimeter identities;
- quality-before-cost comparison;
- finite numeric validation and strict JSON emission;
- unknown-metric preservation;
- regression tests and isolated CI lane.

Not yet performed:

- real Linux-node Hermes A/B runs;
- dominant-cost classification from real traces;
- any SoL-inspired prototype;
- live CLM shadow-ranking run on the Linux node;
- any runtime/deployment change.

The lab remains open until issue Pantheon-Next#1047 records measured runs or closes with `native_sufficient` / `inconclusive` without adding architecture.
