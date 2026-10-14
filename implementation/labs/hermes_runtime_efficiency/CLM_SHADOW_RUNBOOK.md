# CLM shadow-ranking qualification — Linux + gpu-node/WSL encoder

Status: candidate qualification procedure for Pantheon issue Pantheon-Next#1047. This is not a production installation, Hermes route, authorization path or adoption decision.

## Objective

Keep the CLM server and public projection head on the Pantheon Linux node while moving the exact Qwen3-8B pooling encoder to gpu-node/WSL.

```text
Pantheon Linux
  CLM head on CPU
  127.0.0.1:8700
        |
        | embeddings
        v
  127.0.0.1:18090
        |
        | authenticated local-forward tunnel
        v
gpu-node / WSL
  vLLM pooling
  Qwen/Qwen3-8B exact revision
  127.0.0.1:8090
        |
        v
  RTX 4090
```

The vLLM HTTP endpoint stays loopback-only on gpu-node/WSL. Do not expose port 8090 directly on the LAN for this experiment.

CLM remains passive:

```text
CLM rank != Hermes decision
CLM rank != Pantheon authorization
shadow observation != Evidence
runtime success != model qualification
model qualification != activation
```

## Canonical candidate

All model/runtime identities come from:

```text
implementation/qualification/external-pins.json
  -> pins.contrastive-lm
```

The pin owns the exact:

- CLM repository/ref and package version;
- Qwen3-8B model/revision;
- CLM public head repository/revision/file/SHA-256;
- vLLM version;
- CLM ranking API surface.

Placement is an observed runtime property, not part of model identity.

## 1. Export the candidate pin on Linux

From the Pantheon-Next repository root:

```bash
python3 - <<'PY' > /tmp/clm-shadow-pin.env
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
    "CLM_HEAD_REPOSITORY": "head_repository",
    "CLM_HEAD_REVISION": "head_revision",
    "CLM_HEAD_FILE": "head_file",
    "CLM_HEAD_SHA256": "head_sha256",
    "CLM_VLLM_VERSION": "vllm_version",
    "CLM_API_SURFACE": "api_surface",
}
for env_name, field in fields.items():
    print(f"export {env_name}={shlex.quote(str(pin[field]))}")
PY

source /tmp/clm-shadow-pin.env
```

Do not hand-edit these identities to make a run pass.

## 2. Linux: isolated CLM environment and exact head

CLM itself declares vLLM as a package dependency, even though this topology uses the remote encoder. Keep the package environment exact rather than removing dependencies ad hoc.

```bash
python3 -m venv ~/.venvs/clm-shadow
source ~/.venvs/clm-shadow/bin/activate
source /tmp/clm-shadow-pin.env

python -m pip install --upgrade pip
python -m pip install \
  "git+https://github.com/${CLM_REPOSITORY}.git@${CLM_GIT_REF}" \
  "vllm==${CLM_VLLM_VERSION}" \
  huggingface_hub

CLM_PACKAGE_OBSERVED="$(python - <<'PY'
from importlib.metadata import version
print(version("contrastive-lm"))
PY
)"

test "$CLM_PACKAGE_OBSERVED" = "$CLM_VERSION" || {
  echo "contrastive-lm package version differs from canonical pin" >&2
  exit 1
}
```

Fetch the exact public head:

```bash
python - <<'PY'
import os
from pathlib import Path
from huggingface_hub import hf_hub_download

path = hf_hub_download(
    repo_id=os.environ["CLM_HEAD_REPOSITORY"],
    filename=os.environ["CLM_HEAD_FILE"],
    revision=os.environ["CLM_HEAD_REVISION"],
)
Path("/tmp/clm-shadow-head-path").write_text(path + "\n", encoding="utf-8")
print(path)
PY

HEAD_PATH="$(cat /tmp/clm-shadow-head-path)"
HEAD_SHA256="$(sha256sum "$HEAD_PATH" | awk '{print $1}')"

test "$HEAD_SHA256" = "$CLM_HEAD_SHA256" || {
  echo "CLM head SHA-256 differs from canonical pin" >&2
  exit 1
}
```

## 3. Bind the operator-managed gpu-node/WSL SSH target

Use an SSH target whose session terminates in the same WSL environment where vLLM will listen.

Do not commit an IP address, username, private key or other host secret. Set the target locally, preferably through an SSH config alias:

```bash
export CLM_ENCODER_SSH_TARGET="<operator-configured-gpu-node-WSL-ssh-target>"

scp /tmp/clm-shadow-pin.env \
  "$CLM_ENCODER_SSH_TARGET:/tmp/clm-shadow-pin.env"
```

The copied file contains only reviewed public qualification identities; it contains no credential.

## 4. gpu-node/WSL: exact vLLM encoder

Inside the WSL environment on gpu-node:

```bash
source /tmp/clm-shadow-pin.env

python3 -m venv ~/.venvs/clm-encoder
source ~/.venvs/clm-encoder/bin/activate
python -m pip install --upgrade pip
python -m pip install "vllm==${CLM_VLLM_VERSION}"

python - <<'PY'
import os
from importlib.metadata import version

observed = version("vllm")
expected = os.environ["CLM_VLLM_VERSION"]
print("vllm", observed)
if observed != expected:
    raise SystemExit(f"vLLM mismatch: observed={observed} expected={expected}")
PY

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

Start the exact encoder from the same canonical pin:

```bash
source ~/.venvs/clm-encoder/bin/activate
source /tmp/clm-shadow-pin.env

vllm serve "$CLM_ENCODER_MODEL" \
  --revision "$CLM_ENCODER_REVISION" \
  --served-model-name qwen3-8b \
  --runner pooling \
  --max-model-len 2048 \
  --host 127.0.0.1 \
  --port 8090
```

The first run deliberately stays at 2048 tokens.

Do not substitute Ollama, `qwen3-embedding`, quantization, CPU offload or another encoder in this arm.

## 5. Linux: create an authenticated loopback tunnel to gpu-node/WSL

Start the forward in a dedicated terminal on Linux:

```bash
ssh \
  -N \
  -T \
  -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18090:127.0.0.1:8090 \
  "$CLM_ENCODER_SSH_TARGET"
```

This means:

```text
Linux 127.0.0.1:18090
  -> authenticated SSH transport
  -> gpu-node/WSL 127.0.0.1:8090
```

If the available SSH target terminates on Windows rather than inside the WSL environment and cannot reach the WSL loopback service, stop. Do not solve that by exposing vLLM on `0.0.0.0` or creating an unreviewed LAN HTTP path. Use an authenticated tunnel that terminates inside WSL or fall back to the local-encoder arm.

Verify the forwarded vLLM service from Linux:

```bash
curl -fsS http://127.0.0.1:18090/health
curl -fsS http://127.0.0.1:18090/v1/models | python -m json.tool
```

The exposed model must include `qwen3-8b`.

## 6. Linux: start CLM against the forwarded encoder

Run the CLM projection head explicitly on CPU so this first remote-encoder qualification depends on gpu-node for the heavy Qwen encoder workload rather than on a second GPU.

```bash
source ~/.venvs/clm-shadow/bin/activate
source /tmp/clm-shadow-pin.env

HEAD_PATH="$(cat /tmp/clm-shadow-head-path)"

export CLM_API_KEY="$(openssl rand -hex 32)"
printf '%s\n' "$CLM_API_KEY" > /tmp/clm-shadow-api-key
chmod 600 /tmp/clm-shadow-api-key

clm-serve \
  --host 127.0.0.1 \
  --port 8700 \
  --emb-url http://127.0.0.1:18090/v1/embeddings \
  --emb-model qwen3-8b \
  --max-tokens 2048 \
  --ckpt "$HEAD_PATH" \
  --no-download \
  --device cpu \
  --no-ui
```

CLM itself remains loopback-only.

Verify:

```bash
export CLM_API_KEY="$(cat /tmp/clm-shadow-api-key)"

curl -fsS http://127.0.0.1:8700/health | python -m json.tool
curl -fsS \
  -H "Authorization: Bearer $CLM_API_KEY" \
  http://127.0.0.1:8700/v1/models | python -m json.tool
```

Required observations:

```text
health.ok       = true
health.embedder = true
health.mock     != true
clm-latest      is exposed
```

## 7. Record the exact remote topology

The report must distinguish model identity from physical placement.

On Linux, with `CLM_ENCODER_SSH_TARGET` set:

```bash
source ~/.venvs/clm-shadow/bin/activate
source /tmp/clm-shadow-pin.env

CLM_PACKAGE_OBSERVED="$(python - <<'PY'
from importlib.metadata import version
print(version("contrastive-lm"))
PY
)"

ENCODER_VLLM_VERSION="$(
  ssh "$CLM_ENCODER_SSH_TARGET" \
    'source ~/.venvs/clm-encoder/bin/activate && python -c "from importlib.metadata import version; print(version(\"vllm\"))"'
)"

ENCODER_DEVICE_NAME="$(
  ssh "$CLM_ENCODER_SSH_TARGET" \
    'nvidia-smi --query-gpu=name --format=csv,noheader | head -n1'
)"

HEAD_PATH="$(cat /tmp/clm-shadow-head-path)"
HEAD_SHA256="$(sha256sum "$HEAD_PATH" | awk '{print $1}')"

export \
  CLM_PACKAGE_OBSERVED \
  ENCODER_VLLM_VERSION \
  ENCODER_DEVICE_NAME \
  HEAD_SHA256

python - <<'PY'
import json
import os
from pathlib import Path

receipt = {
    "clm_git_ref": os.environ["CLM_GIT_REF"],
    "clm_package_version": os.environ["CLM_PACKAGE_OBSERVED"],
    "encoder_model": os.environ["CLM_ENCODER_MODEL"],
    "encoder_revision": os.environ["CLM_ENCODER_REVISION"],
    "head_sha256": os.environ["HEAD_SHA256"],
    "vllm_version": os.environ["ENCODER_VLLM_VERSION"],
    "clm_head_device_name": "cpu",
    "encoder_device_name": os.environ["ENCODER_DEVICE_NAME"],
    "encoder_placement": "remote",
    "encoder_transport": "ssh_local_forward",
    "encoder_endpoint": "http://127.0.0.1:18090/v1/embeddings",
    "encoder_node_label": "gpu-node/WSL",
}
Path("/tmp/clm-runtime.json").write_text(
    json.dumps(receipt, indent=2) + "\n",
    encoding="utf-8",
)
PY

cat /tmp/clm-runtime.json
```

The runner rejects a non-loopback encoder endpoint for this qualification and rejects a remote placement that is not recorded as `ssh_local_forward`.

## 8. Run the shadow corpus

```bash
export CLM_API_KEY="$(cat /tmp/clm-shadow-api-key)"

python implementation/labs/hermes_runtime_efficiency/clm_shadow_rank.py \
  implementation/labs/hermes_runtime_efficiency/clm_shadow_cases.json \
  --runtime-metadata /tmp/clm-runtime.json \
  --pin-registry implementation/qualification/external-pins.json \
  --base-url http://127.0.0.1:8700 \
  --max-orderings 4 \
  --output /tmp/clm-shadow-report.json
```

Inspect:

```bash
python - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/tmp/clm-shadow-report.json").read_text(encoding="utf-8"))
print(json.dumps(report["runtime_metadata"], indent=2))
print(json.dumps(report["summary"], indent=2))
PY
```

Initial signals:

```text
expected_top1_all_orderings_rate
top_candidate_order_stable_rate
per-case ranked probabilities
CLM latency header
transport elapsed time
```

The quality/stability result is valid for the exact model candidate. Latency from this arm is explicitly topology-specific because embeddings cross the authenticated tunnel.

```text
remote quality observation
!= local latency baseline
```

## 9. Local encoder fallback

The previous all-local topology remains valid as a separate arm:

```text
encoder_placement  = local
encoder_transport  = loopback_direct
encoder_endpoint   = http://127.0.0.1:8090/v1/embeddings
encoder_node_label = linux-local
```

It must use the same model revision, head, vLLM version and 2048-token limit. Do not mix local and gpu-node observations in one causal latency comparison.

## 10. Interpretation

```text
low expected-match rate
-> CLM candidate is not useful for this decision family

high expected match + low order stability
-> presentation sensitivity is material

high expected match + high order stability
-> candidate for a larger held-out shadow corpus

good shadow result
!= permission to wire CLM into Hermes
```

## 11. Removal

Deleting the CLM-specific lab files and qualification pin restores the previous Pantheon-Next#1047 lab behavior. No product module imports this runner, no schema migration is introduced, and no production runtime route depends on gpu-node or CLM.
