# Native Hermes baseline runbook

Status: operator-run qualification procedure for Pantheon issue Pantheon-Next#1047. It prepares measurements only. It does not install SoL-Pi, change Hermes configuration, select a model, change Pantheon authority, or claim that a live run has occurred.

## Objective

Record a reproducible native-Hermes baseline before considering any SoL-inspired mechanism.

The core baseline is 12 runs:

```text
C1 large textual context proxy     x 3
C2 large terminal/tool output      x 3
C3 edit -> validate task           x 3
C4 synthetic agency source task      x 3
```

Use the same live Hermes runtime, model/provider, governed profile and effective settings for the 12 runs. A later experimental variant must reuse the same `case_id` for its matched A/B pair.

## Repository and runtime separation

At preparation time repository `main` was revalidated at:

```text
da74cc056bbb3038a9313e41d37e879234aa0538
```

This includes merged PR Pantheon-Next#1057, which changed the governed Hermes profile/capability composition. The native baseline must therefore record the exact post-#1057 profile/configuration actually used by each run; never treat the name `pantheon-governed` as a sufficient identity by itself.

For this qualification slice, the repository-selected Hermes target is `nousresearch/hermes-agent:v2026.9.14` (Hermes Agent 0.21.3), as recorded by the existing external-qualification owner on 2026-09-20. This runbook does not own Hermes release tracking, installation, or upgrade policy. Repository configuration is not proof of the runtime installed on the Linux node.

Before running, observe the live runtime identity:

```bash
hermes --version
```

If Hermes is containerized, also record the exact running image/digest from the container engine. Do not substitute the desired tag for the observed running identity.

## Safety boundary

Hermes one-shot mode (`-z`) is non-interactive and auto-bypasses approval prompts. Run these cases only inside the generated disposable synthetic fixtures. Do not point this procedure at a real client workspace or professional dossier.

The exported Hermes session may contain the synthetic prompt and tool output. Keep run artifacts local. Do not commit live session exports, local configuration, credentials or real project material.

## 1. Prepare the fixtures

From the Pantheon-Next repository root:

```bash
LAB=implementation/labs/hermes_runtime_efficiency
OUT="$HOME/pantheon-qualification/hermes-native-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
python "$LAB/build_fixtures.py" "$OUT/fixtures"
```

The generated cases contain no client data.

C1 generates 100k, 300k, 490k and 510k character documents. The core baseline uses 490k. The other sizes are optional scaling probes. C1 is a Hermes large-text proxy only: reading a local file does **not** prove the Pantheon `hermes_scoped_context` admission path or its 500,000-character fail-closed boundary.

## 2. Record controlled identities once

Choose the actual profile used for the run:

```bash
PROFILE=pantheon-governed
hermes --version | tee "$OUT/hermes-version.txt"
```

Define an exact observed runtime identity. Example only:

```bash
export HERMES_BENCH_RUNTIME_IDENTITY='nousresearch/hermes-agent:v2026.9.14@<observed-digest-or-version>'
```

Record a profile identity that changes when the effective profile changes. Prefer a digest of the actual profile/projection files over a name alone. Do not hash secrets into a public artifact; the digest may remain local.

```bash
export HERMES_BENCH_PROFILE_IDENTITY='pantheon-governed@sha256:<observed-profile-digest>'
```

Record a digest of the effective non-secret runtime settings used for the batch. It should cover at least model-routing configuration, context length, reasoning level, profile, projected skill set and any relevant compression settings. Hash the canonical settings locally; do not commit the source configuration.

```bash
export HERMES_BENCH_SETTINGS_DIGEST='sha256:<canonical-effective-settings-digest>'
```

If any of those values cannot be observed, stop and record the uncertainty rather than inventing it.

## 3. Run one case

Each repetition gets a fresh writable copy of its fixture. This is mandatory for C3 and keeps the other cases symmetrical.

Example for C2 repetition 1:

```bash
CASE_ID='C2-large-tool-r1'
RUN="$OUT/runs/$CASE_ID/native"
WORK="$RUN/workspace"
mkdir -p "$RUN"
cp -a "$OUT/fixtures/C2-large-tool-output" "$WORK"

/usr/bin/time -f '%e' -o "$RUN/elapsed.txt" \
  hermes -p "$PROFILE" \
    --in "$WORK" \
    -z "$(cat "$WORK/prompt.txt")" \
    --usage-file "$RUN/usage.json" \
    > "$RUN/answer.txt" \
    2> "$RUN/stderr.log"
```

`usage.json` is the native Hermes measurement source for at least:

```text
input_tokens
output_tokens
total_tokens
api_calls -> llm_turns
model
provider
session_id
completed / failed
```

Elapsed wall time comes from `/usr/bin/time`, not from model output.

## 4. Export the exact Hermes session

After a successful or recorded run:

```bash
SID=$(jq -r '.session_id // empty' "$RUN/usage.json")
if [ -n "$SID" ]; then
  hermes -p "$PROFILE" sessions export \
    "$RUN/session.jsonl" \
    --session-id "$SID" \
    --format jsonl
fi
```

The observation builder uses the session export to count actual tool calls. When `large_tool_threshold_chars` is configured, it also counts/sums tool-result payloads at or above that case threshold.

If the session export is unavailable, omit it. `tool_calls` and large-tool metrics remain `null`; they must not be guessed as zero.

## 5. Evaluate quality deterministically

For C2:

```bash
python "$LAB/evaluate_fixture.py" \
  --case-id "$CASE_ID" \
  --workspace "$WORK" \
  --answer "$RUN/answer.txt" \
  --output "$RUN/quality.json"
```

The evaluator does not use another LLM. It checks exact fixture values. C3 runs the generated pytest suite and verifies that immutable fixture files were not altered.

A run that is operationally cheaper but fails quality is not a useful candidate.

## 6. Create run metadata

C2 example:

```bash
jq -n \
  --arg case_id "$CASE_ID" \
  --arg runtime "$HERMES_BENCH_RUNTIME_IDENTITY" \
  --arg profile "$HERMES_BENCH_PROFILE_IDENTITY" \
  --arg settings "$HERMES_BENCH_SETTINGS_DIGEST" \
  '{
    case_id: $case_id,
    variant: "native",
    runtime_identity: $runtime,
    profile_identity: $profile,
    settings_digest: $settings,
    large_tool_threshold_chars: 100000,
    notes: ["native Hermes baseline; synthetic fixture"]
  }' > "$RUN/meta.json"
```

For C1 use `large_tool_threshold_chars: 100000` if session export preserves the file-read result as a tool payload. For C3/C4 the threshold can be omitted unless a large result is intentionally part of the case.

## 7. Build the Pantheon-Next#1047 observation

```bash
ARGS=(
  --usage "$RUN/usage.json"
  --meta "$RUN/meta.json"
  --quality "$RUN/quality.json"
  --elapsed-file "$RUN/elapsed.txt"
  --output "$RUN/observation.json"
)

if [ -f "$RUN/session.jsonl" ]; then
  ARGS+=(--session "$RUN/session.jsonl")
fi

python "$LAB/native_run.py" "${ARGS[@]}"
```

`native_run.py` reuses the existing `compare.py` observation validator. It does not execute Hermes and does not persist governed state.

## 8. Core 12-run matrix

Use these exact pair identities so a later candidate can reuse them:

| Case ID | Fixture | Prompt | Repetitions |
| --- | --- | --- | ---: |
| `C1-490k-r1..r3` | `C1-large-context` | `prompt_490000.txt` | 3 |
| `C2-large-tool-r1..r3` | `C2-large-tool-output` | `prompt.txt` | 3 |
| `C3-edit-validate-r1..r3` | `C3-edit-validate` | `prompt.txt` | 3 |
| `C4-agency-source-r1..r3` | `C4-agency-source-task` | `prompt.txt` | 3 |

For C1 change the one-shot prompt source only:

```bash
-z "$(cat "$WORK/prompt_490000.txt")"
```

Never resume a previous benchmark session. Every repetition starts fresh.

## 9. Optional C1 scaling probes

After the 12 core runs, and only if useful, repeat C1 with:

```text
100000 chars
300000 chars
510000 chars
```

These probes measure Hermes/file-tool scaling. The 510k local-file run is **not** the Pantheon 500k admission test. A later governed-context slice must exercise the actual admitted Context Pack / `hermes_scoped_context` seam to qualify that boundary.

## 10. What to inspect after the native baseline

For each case, summarize the median of the three runs for known metrics only:

```text
input_tokens
output_tokens
llm_turns
actual tool_calls
elapsed_seconds
large_tool_result_count/chars when observed
source recall pass ratio
required quality checks
```

Do not average missing metrics into zero.

Interpretation order:

```text
quality unstable
-> fix the work path first; do not optimize cost

native quality stable and cost modest
-> native_sufficient

C2 dominated by repeated/large observation context
-> qualify one ObservationPack-like handle/exact-recall behavior

C3 dominated by LLM turns around deterministic edit/validate work
-> qualify one Action-Fusion-like behavior

large diagnostic text dominates but exact recall does not
-> qualify local provenance-preserving reduction

completed history dominates after the above are excluded
-> only then consider extra compaction logic
```

The already-merged Ollama KV-cache Q8 runbook is a separate controlled resource experiment. Do not mix its `f16 -> q8_0` treatment into this native baseline batch.

## 11. A/B comparison later

When one mechanism is justified, rerun the same fixture with the same `case_id` and a different `variant`.

Then:

```bash
python "$LAB/compare.py" baseline.json candidate.json
```

The comparator requires comparable runtime/model/profile/settings identities and passes quality/provenance before operational cost.

A result of `candidate_for_further_qualification` still does not mean adoption or authorization.

## Separate first agency devis/DPGF pilot (Pantheon-Next#827)

The actual CCTP/DPGF/quote comparison uses the existing fictional corpus and
operator procedure at [devis_reprise/README.md](../../dossiers/devis_reprise/README.md).
It is **not** this lab's generated C4 fixture, and C4's deterministic scorer
must not be reused for its professional claims. No extra runner is required.

## Done criteria for this native-baseline slice

Repository preparation is complete when:

- fixture generation is deterministic;
- C1-C4 quality checks are deterministic and non-LLM;
- Hermes native usage/session artifacts can be converted to the existing observation envelope;
- no real client material is required;
- no Hermes/Pantheon runtime configuration is changed by repository code.

Live qualification is complete only after the 12 native observations exist and their dominant cost is classified. Until then Pantheon-Next#1047 remains open.
