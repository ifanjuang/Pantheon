# CLM quantized encoder qualification — Linux 16 GiB

Status: bounded qualification procedure for Pantheon-Next#1047. This extends the passive CLM shadow lab; it does not replace the canonical BF16 reference, activate CLM, select a Hermes action or authorize an effect.

## Objective

Test whether the exact published CLM head can use a quantized Qwen3-8B encoder on the always-available Linux node while preserving ranking behavior closely enough to remove gpu-node from the productive CLM path.

The reference remains:

```text
gpu-node / RTX 4090
Qwen/Qwen3-8B exact revision
vLLM pooling
BF16/default reference path
        |
        v
CLM public head
```

Candidate order:

```text
Linux 16 GiB
Qwen3-8B Q8_0 GGUF + llama.cpp
        |
        +-- if co-residency is not viable --> Q4_K_M GGUF
        |
        v
same CLM public head
```

Q4 is not promoted merely because it fits. Ranking drift and co-residency are separate observations.

## Canonical identities

Load all identities from `implementation/qualification/external-pins.json -> pins.contrastive-lm`.

That entry retains the canonical CLM/Qwen/vLLM/head identity and additionally records exact experimental inputs:

```text
Qwen/Qwen3-8B-GGUF
  Qwen3-8B-Q8_0.gguf   + exact SHA-256
  Qwen3-8B-Q4_K_M.gguf + exact SHA-256

ggml-org/llama.cpp
  v0.5.0
  exact release commit
```

The GGUF files are variants of the same source model for qualification. They are not silently treated as numerically equivalent to the BF16 encoder.

## 1. Produce the BF16 reference report

Use `CLM_SHADOW_RUNBOOK.md` unchanged to produce the reference report against the exact gpu-node/vLLM encoder:

```text
/tmp/clm-shadow-bf16.json
```

The reference report must use the same committed corpus and ordering count that will be used by the Linux candidate.

## 2. Export exact candidate identities on Linux

From the Pantheon checkout:

```bash
python3 - <<'PY' > /tmp/clm-quantized-pin.env
import json
import shlex
from pathlib import Path

pin = json.loads(
    Path("implementation/qualification/external-pins.json").read_text(encoding="utf-8")
)["pins"]["contrastive-lm"]

fields = {
    "CLM_REPOSITORY": "repository",
    "CLM_VERSION": "version",
    "CLM_GIT_REF": "ref",
    "CLM_ENCODER_MODEL": "encoder_model",
    "CLM_ENCODER_REVISION": "encoder_revision",
    "CLM_HEAD_SHA256": "head_sha256",
    "CLM_VLLM_VERSION": "vllm_version",
    "CLM_GGUF_REPOSITORY": "experimental_quantized_encoder_repository",
    "CLM_GGUF_REVISION": "experimental_quantized_encoder_revision",
    "CLM_Q8_FILE": "experimental_q8_file",
    "CLM_Q8_SHA256": "experimental_q8_sha256",
    "CLM_Q4_FILE": "experimental_q4_file",
    "CLM_Q4_SHA256": "experimental_q4_sha256",
    "CLM_LLAMA_CPP_VERSION": "experimental_encoder_backend_version",
    "CLM_LLAMA_CPP_REF": "experimental_encoder_backend_ref",
}
for env_name, field in fields.items():
    print(f"export {env_name}={shlex.quote(str(pin[field]))}")
PY

source /tmp/clm-quantized-pin.env
```

Do not replace these values with a floating `main`, `latest` or an arbitrary local conversion.

## 3. Build the pinned llama.cpp backend

Use an isolated checkout:

```bash
mkdir -p ~/src
if [ ! -d ~/src/llama.cpp/.git ]; then
  git clone https://github.com/ggml-org/llama.cpp.git ~/src/llama.cpp
fi

git -C ~/src/llama.cpp fetch --tags origin
git -C ~/src/llama.cpp checkout --detach "$CLM_LLAMA_CPP_REF"
test "$(git -C ~/src/llama.cpp rev-parse HEAD)" = "$CLM_LLAMA_CPP_REF"

cmake -S ~/src/llama.cpp -B ~/src/llama.cpp/build -DGGML_CUDA=ON
cmake --build ~/src/llama.cpp/build -j --target llama-server
```

The tagged version is provenance; the exact commit is the execution identity.

## 4. Download and verify Q8_0 first

Use the Hugging Face CLI or another exact-byte download path. Example:

```bash
mkdir -p ~/.cache/pantheon/clm
hf download "$CLM_GGUF_REPOSITORY" "$CLM_Q8_FILE" \
  --revision "$CLM_GGUF_REVISION" \
  --local-dir ~/.cache/pantheon/clm

Q8_PATH="$HOME/.cache/pantheon/clm/$CLM_Q8_FILE"
test "$(sha256sum "$Q8_PATH" | awk '{print $1}')" = "$CLM_Q8_SHA256"
```

If the digest differs, stop. Do not qualify a different artifact under the same candidate name.

## 5. Start the Q8 encoder on Linux

Keep it loopback-only and preserve the CLM training pooling geometry:

```bash
~/src/llama.cpp/build/bin/llama-server \
  --model "$Q8_PATH" \
  --alias qwen3-8b \
  --embedding \
  --pooling last \
  -ngl 1024 \
  -fa on \
  -c 2048 \
  --host 127.0.0.1 \
  --port 8091
```

Verify the embeddings endpoint before starting CLM.

The candidate must use:

```text
served model alias = qwen3-8b
pooling = last
context = 2048
source model = Qwen/Qwen3-8B exact canonical revision
GGUF artifact = exact pinned bytes
```

## 6. Start the same CLM head against the local encoder

Use the same isolated CLM environment/head created by the reference run. Only the encoder backend/artifact changes.

```bash
export CLM_API_KEY="$(openssl rand -hex 32)"
printf '%s\n' "$CLM_API_KEY" > /tmp/clm-quantized-api-key
chmod 600 /tmp/clm-quantized-api-key

clm-serve \
  --host 127.0.0.1 \
  --port 8701 \
  --emb-url http://127.0.0.1:8091/v1/embeddings \
  --emb-model qwen3-8b \
  --max-tokens 2048 \
  --ckpt "$(cat /tmp/clm-shadow-head-path)" \
  --no-download \
  --device cpu \
  --no-ui
```

## 7. Create an exact Q8 runtime receipt

The canonical `encoder_model` and `encoder_revision` still identify the source Qwen model that the CLM head was trained against. The additional fields identify the actual quantized bytes/backend used for this run.

```bash
source /tmp/clm-quantized-pin.env

export Q8_PATH
python - <<'PY'
import json
import os
from pathlib import Path

receipt = {
    "clm_git_ref": os.environ["CLM_GIT_REF"],
    "clm_package_version": os.environ["CLM_VERSION"],
    "encoder_model": os.environ["CLM_ENCODER_MODEL"],
    "encoder_revision": os.environ["CLM_ENCODER_REVISION"],
    "head_sha256": os.environ["CLM_HEAD_SHA256"],
    "vllm_version": os.environ["CLM_VLLM_VERSION"],
    "clm_head_device_name": "cpu",
    "encoder_device_name": "linux-cuda-gpu",
    "encoder_placement": "local",
    "encoder_transport": "loopback_direct",
    "encoder_endpoint": "http://127.0.0.1:8091/v1/embeddings",
    "encoder_node_label": "linux-local",
    "encoder_backend": "llama.cpp",
    "encoder_backend_version": os.environ["CLM_LLAMA_CPP_VERSION"],
    "encoder_backend_ref": os.environ["CLM_LLAMA_CPP_REF"],
    "encoder_artifact_repository": os.environ["CLM_GGUF_REPOSITORY"],
    "encoder_artifact_revision": os.environ["CLM_GGUF_REVISION"],
    "encoder_artifact_file": os.environ["CLM_Q8_FILE"],
    "encoder_artifact_sha256": os.environ["CLM_Q8_SHA256"],
    "encoder_quantization": "Q8_0",
    "encoder_pooling": "last",
}
Path("/tmp/clm-runtime-q8.json").write_text(
    json.dumps(receipt, indent=2) + "\n",
    encoding="utf-8",
)
PY
```

Replace `encoder_device_name` with the exact observed GPU name before the run.

## 8. Run the existing shadow corpus

```bash
export CLM_API_KEY="$(cat /tmp/clm-quantized-api-key)"

python implementation/labs/hermes_runtime_efficiency/clm_shadow_rank.py \
  implementation/labs/hermes_runtime_efficiency/clm_shadow_cases.json \
  --runtime-metadata /tmp/clm-runtime-q8.json \
  --pin-registry implementation/qualification/external-pins.json \
  --base-url http://127.0.0.1:8701 \
  --max-orderings 4 \
  --output /tmp/clm-shadow-q8.json
```

The existing runner fails closed if the GGUF/backend receipt differs from the reviewed qualification inputs.

## 9. Compare Q8 with BF16

```bash
python implementation/labs/hermes_runtime_efficiency/compare_clm_shadow_reports.py \
  /tmp/clm-shadow-bf16.json \
  /tmp/clm-shadow-q8.json \
  --output /tmp/clm-bf16-vs-q8.json
```

Inspect at minimum:

```text
top1_agreement_rate
full_ranking_agreement_rate
mean_abs_probability_delta
max_abs_probability_delta
order_stability_regression_count
expected_top1_regression_count
```

The first synthetic gate for advancing to a larger held-out corpus is deliberately strict:

```text
top1 disagreement = 0
order-stability regressions = 0
expected-top1 regressions = 0
```

Probability drift is recorded but no arbitrary acceptance threshold is invented before observing the distribution.

Passing this 12-case gate does not activate Q8.

## 10. Measure Linux co-residency

Before considering Q8 productive, observe the actual 16 GiB node with the existing 9B/Hindsight path available.

Record:

```text
GPU name / VRAM
idle VRAM
Q8 encoder loaded VRAM
Ollama 9B loaded VRAM
Hindsight request while Q8 remains available
Hermes 9B fallback request while Q8 remains available
OOM / eviction / reload observations
latency after eviction or cold reload
```

Useful probes include:

```bash
nvidia-smi
ollama ps
```

Do not interpret individual file sizes as proof of simultaneous residency.

## 11. Q4_K_M only if Q8 cannot satisfy the node envelope

If Q8 ranking is acceptable but co-residency is not, repeat sections 4–10 with the pinned Q4 artifact and a receipt containing:

```text
encoder_artifact_file   = experimental_q4_file
encoder_artifact_sha256 = experimental_q4_sha256
encoder_quantization    = Q4_K_M
```

Do not skip the BF16 comparison for Q4.

## Decision order

```text
Q8 ranking stable + co-residency stable
-> candidate for larger held-out CLM shadow corpus

Q8 ranking stable + co-residency fails
-> test Q4_K_M

Q4 ranking stable + co-residency stable
-> candidate for larger held-out CLM shadow corpus

quantized ranking materially regresses
-> keep BF16 reference path / gpu-node dependency for CLM

all cases
-> no automatic activation
```

## Governance boundary

```text
quantized model fits != equivalent encoder
rank agreement != professional correctness
CLM rank != Hermes decision
CLM rank != authorization
Hindsight memory != Evidence
runtime success != adoption
```
