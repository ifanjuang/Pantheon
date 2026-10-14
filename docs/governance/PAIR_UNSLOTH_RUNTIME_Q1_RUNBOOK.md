# PAIR + Unsloth Runtime Q1 Runbook

Status: candidate execution runbook. This file defines how to execute Q1; it does not claim that any live stage has run or passed.

Companion contract: `docs/governance/PAIR_UNSLOTH_RUNTIME_QUALIFICATION.md`.
Machine-readable planning state: `tests/fixtures/pair_unsloth_runtime_q1.json`.

## 1. Lab topology and authority ceiling

Use this topology only for qualification:

```text
Linux RTX 4080, always on
  - PAIR headless/TUI
  - isolated PAIR HOME
  - isolated Unsloth source/venv/home/cache
  - current Pantheon Hermes container when Q1C/Q1D requires its namespace

Windows RTX 4090, always on
  - PAIR Desktop
  - second cluster node
  - Jobs / "Ran on" observation surface
```

Do not change these repository-owned deployment inputs during Q1:

```text
deployment/ubuntu/release.env
deployment/ubuntu/install-node
implementation/hermes/distribution/pantheon-standard.lock.yaml
```

Q1 does not select deployment, activate a runtime, authorize work or admit Evidence.

```text
artifact downloaded != artifact qualified
runtime reachable != runtime accepted
model available != model approved
PAIR routed request != Pantheon authorization
Unsloth provider configured != provider authorized
successful execution != Evidence
```

## 2. Sensitive-data rules

Never put these in committed files or Q1 artifacts:

- PAIR pairing PINs;
- Unsloth API keys;
- Hermes/provider secrets;
- prompt bodies;
- generated response bodies;
- unrelated private host/user/document content.

A SHA-256 fingerprint of a temporary API key may be recorded. Do not record the key itself.

Do not use Hermes `--yolo`. If the bounded tool test asks for approval, approve only the exact harmless command specified below. That approval is not standing authorization.

Do not run PAIR Desktop and `nvpair-tui` simultaneously on the same host. Linux uses TUI; Windows uses Desktop.

## 3. Fixed Q1 workload inputs

These are test workloads, not production model selections:

```text
PAIR model:          qwen3.5:4b
Unsloth model:       unsloth/Qwen3.5-4B-GGUF:UD-Q4_K_XL
Unsloth context:     16384
Unsloth API port:    18888/tcp
Hermes temp profile: pantheon-q1-unsloth
```

The small model keeps routing/failover/provider behavior as the subject of the test rather than VRAM pressure.

## 4. Linux common preparation

Run from this PR branch.

### 4.1 Resolve external targets from the existing pin authority

```bash
cd /path/to/Pantheon-Next

eval "$(python implementation/tools/export_external_qualification_pins.py \
  personal-ai-router unsloth hermes-agent)"

for name in \
  PAIR_PIN_ID PAIR_VERSION PAIR_REF PAIR_REPOSITORY \
  UNSLOTH_PIN_ID UNSLOTH_VERSION UNSLOTH_REF UNSLOTH_REPOSITORY \
  HERMES_PIN_ID HERMES_VERSION HERMES_REF; do
  test -n "${!name:-}" || { echo "missing $name" >&2; exit 1; }
done
```

Do not restate current version/commit literals elsewhere; the registry remains sole qualification-target owner.

### 4.2 Create isolated Q1 paths

```bash
export Q1_ROOT="$HOME/pantheon-labs/pair-unsloth-q1"
export Q1_ARTIFACTS="$Q1_ROOT/artifacts"

export Q1_PAIR_HOME="$Q1_ROOT/pair-home"
export Q1_PAIR_BIN="$Q1_ROOT/pair-bin"

export Q1_UNSLOTH_SRC="$Q1_ROOT/unsloth-src"
export Q1_UNSLOTH_VENV="$Q1_ROOT/unsloth-venv"
export Q1_UNSLOTH_HOME="$Q1_ROOT/unsloth-home"
export Q1_HF_HOME="$Q1_ROOT/hf-cache"

export PAIR_Q1_MODEL="qwen3.5:4b"
export UNSLOTH_Q1_MODEL="unsloth/Qwen3.5-4B-GGUF:UD-Q4_K_XL"
export UNSLOTH_Q1_CONTEXT="16384"
export UNSLOTH_Q1_PORT="18888"

mkdir -p \
  "$Q1_ARTIFACTS" \
  "$Q1_PAIR_HOME/.config" \
  "$Q1_PAIR_BIN" \
  "$Q1_UNSLOTH_HOME" \
  "$Q1_HF_HOME"
chmod 700 "$Q1_ROOT" "$Q1_ARTIFACTS" "$Q1_PAIR_HOME" "$Q1_UNSLOTH_HOME"
```

### 4.3 Capture the live host baseline

```bash
{
  date --iso-8601=seconds
  uname -a
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  docker --version 2>/dev/null || true
  python --version
  git rev-parse HEAD
} > "$Q1_ARTIFACTS/linux-baseline.txt"

systemctl is-active ollama \
  > "$Q1_ARTIFACTS/system-ollama-before.state" 2>&1 || true

systemctl show ollama \
  -p FragmentPath -p DropInPaths -p Environment \
  > "$Q1_ARTIFACTS/system-ollama-before.txt" 2>&1 || true

sudo ss -ltnp | grep -E ':(11434|11435|1234|1235|18888)\b' \
  > "$Q1_ARTIFACTS/inference-listeners-before.txt" 2>&1 || true
```

### 4.4 Protect the Pantheon-owned Ollama model store

The current Ubuntu candidate owns `/srv/ai/models/ollama`. Q1 must not use it as the PAIR lab store.

```bash
if sudo test -d /srv/ai/models/ollama; then
  sudo find /srv/ai/models/ollama -type f -printf '%P\t%s\n' \
    | sort | sha256sum \
    > "$Q1_ARTIFACTS/pantheon-ollama-store-before.sha256"
else
  printf 'absent\n' \
    > "$Q1_ARTIFACTS/pantheon-ollama-store-before.sha256"
fi
```

This hashes names/sizes, not model content.

## 5. Helper: temporarily free the PAIR proxy port

Before any Linux PAIR stage:

```bash
if systemctl is-active --quiet ollama; then
  export Q1_SYSTEM_OLLAMA_WAS_ACTIVE=1
  sudo systemctl stop ollama
else
  export Q1_SYSTEM_OLLAMA_WAS_ACTIVE=0
fi

if sudo ss -ltnp | grep -q ':11434\b'; then
  echo 'STOP: 11434 is still occupied; identify its owner.' >&2
  sudo ss -ltnp | grep ':11434\b' >&2 || true
  exit 1
fi
```

Do not kill an unknown listener just to continue.

Restore afterward with:

```bash
if [ "${Q1_SYSTEM_OLLAMA_WAS_ACTIVE:-0}" = 1 ]; then
  sudo systemctl start ollama
fi
```

## 6. Q1A — isolated PAIR on Linux RTX 4080

### 6.1 Download the exact selected release asset

Resolve the release from the canonical PAIR version and validate the concrete Linux archive against GitHub's published asset digest.

```bash
PAIR_RELEASE_JSON="$Q1_ROOT/pair-release.json"
PAIR_ARCHIVE="$Q1_ROOT/service-binaries-linux-x64.zip"

curl -fsSL \
  "https://api.github.com/repos/${PAIR_REPOSITORY}/releases/tags/v${PAIR_VERSION}" \
  -o "$PAIR_RELEASE_JSON"

PAIR_ASSET_URL="$(jq -r '.assets[] | select(.name == "service-binaries-linux-x64.zip") | .browser_download_url' "$PAIR_RELEASE_JSON")"
PAIR_ASSET_DIGEST="$(jq -r '.assets[] | select(.name == "service-binaries-linux-x64.zip") | .digest // empty' "$PAIR_RELEASE_JSON")"

test -n "$PAIR_ASSET_URL" || { echo 'PAIR Linux x64 asset not found'; exit 1; }

curl -fL "$PAIR_ASSET_URL" -o "$PAIR_ARCHIVE"
PAIR_ASSET_SHA256="$(sha256sum "$PAIR_ARCHIVE" | awk '{print $1}')"
printf '%s\n' "$PAIR_ASSET_SHA256" \
  > "$Q1_ARTIFACTS/pair-linux-asset.sha256"

if [ -n "$PAIR_ASSET_DIGEST" ]; then
  test "sha256:$PAIR_ASSET_SHA256" = "$PAIR_ASSET_DIGEST" \
    || { echo 'PAIR asset digest mismatch'; exit 1; }
fi

rm -rf "$Q1_PAIR_BIN"
mkdir -p "$Q1_PAIR_BIN"
unzip -q "$PAIR_ARCHIVE" -d "$Q1_PAIR_BIN"

PAIR_TUI="$(find "$Q1_PAIR_BIN" -type f -name nvpair-tui -perm -u+x | head -n1)"
test -x "$PAIR_TUI" || { echo 'nvpair-tui not found'; exit 1; }
"$PAIR_TUI" --version \
  > "$Q1_ARTIFACTS/pair-tui-version.txt"
```

If the release metadata has no digest, record the measured SHA-256 and mark published-digest validation `unresolved`; do not call it verified.

### 6.2 Start PAIR with isolated HOME/XDG state

Run the helper in section 5 first.

```bash
tmux new -s pair-q1
```

Inside tmux:

```bash
export HOME="$Q1_PAIR_HOME"
export XDG_CONFIG_HOME="$Q1_PAIR_HOME/.config"
exec "$PAIR_TUI"
```

Detach with `Ctrl-b d`. Reattach with:

```bash
tmux attach -t pair-q1
```

### 6.3 Install a PAIR-owned Ollama

In TUI:

1. **Engines** (`6`).
2. Select Ollama.
3. `i` — install.
4. Wait for running/healthy.
5. `p` — pull `qwen3.5:4b`.
6. **Proxies** (`4`) — record displayed Ollama client endpoint and selected upstream.
7. **Engines** (`6`) — record actual backend port.

Do not assume backend `11435`; set the observed value:

```bash
export PAIR_Q1_BACKEND_PORT='<observed-backend-port>'
```

### 6.4 Verify client proxy and backend ownership

```bash
sudo ss -ltnp | grep -E ':(11434|'"$PAIR_Q1_BACKEND_PORT"')\b' \
  | tee "$Q1_ARTIFACTS/q1a-listeners.txt"

curl -fsS http://127.0.0.1:11434/v1/models \
  | jq '{object,model_count:(.data|length),model_ids:[.data[].id]}' \
  > "$Q1_ARTIFACTS/q1a-proxy-models-shape.json"
```

PASS `proxy_port_11434_behavior` only if PAIR owns the client-facing endpoint and `/v1/models` succeeds through it.

PASS `backend_relocation_if_pair_managed` only if the PAIR-installed Ollama is on a distinct PAIR-controlled backend port and PAIR reports that port as upstream.

### 6.5 Verify the managed engine directly

```bash
PAIR_OLLAMA="$(find "$Q1_PAIR_HOME" -type f -path '*/engine-bin/ollama/*' -name ollama -perm -u+x | head -n1)"
test -x "$PAIR_OLLAMA" || { echo 'PAIR-managed Ollama not found'; exit 1; }

PAIR_OLLAMA_ROOT="$(dirname "$(dirname "$PAIR_OLLAMA")")"
LD_LIBRARY_PATH="$PAIR_OLLAMA_ROOT/lib/ollama${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
OLLAMA_HOST="127.0.0.1:$PAIR_Q1_BACKEND_PORT" \
  "$PAIR_OLLAMA" list \
  > "$Q1_ARTIFACTS/q1a-backend-model-list.txt"
```

The test model must be visible both directly and through PAIR.

### 6.6 Bounded inference without retaining content

```bash
Q1_BODY="$Q1_ROOT/q1a-body.json"

HTTP_CODE="$(curl -sS -o "$Q1_BODY" -w '%{http_code}' \
  http://127.0.0.1:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"$PAIR_Q1_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Return the single token OK\"}],\"max_tokens\":8}")"

printf '%s\n' "$HTTP_CODE" \
  > "$Q1_ARTIFACTS/q1a-http-code.txt"

jq '{object,model,choices_count:(.choices|length),finish_reason:.choices[0].finish_reason,usage}' \
  "$Q1_BODY" \
  > "$Q1_ARTIFACTS/q1a-inference-shape.json"
rm -f "$Q1_BODY"
```

Do not store the response text.

Inspect TUI **Workloads** (`5`) and record only state/model/timing metadata.

### 6.7 Verify model retention across PAIR engine uninstall

Locate the isolated PAIR model store; never use `/srv/ai/models/ollama` here.

```bash
PAIR_MODEL_STORE=""
if [ -d "$Q1_PAIR_HOME/.ollama/models" ]; then
  PAIR_MODEL_STORE="$Q1_PAIR_HOME/.ollama/models"
else
  PAIR_MODEL_STORE="$(find "$Q1_PAIR_HOME" -type d -path '*/.ollama/models' -print -quit 2>/dev/null || true)"
fi

if [ -z "$PAIR_MODEL_STORE" ] || [ ! -d "$PAIR_MODEL_STORE" ]; then
  echo 'model store not located: retention check is unresolved' >&2
else
  find "$PAIR_MODEL_STORE" -type f -printf '%P\t%s\n' | sort | sha256sum \
    > "$Q1_ARTIFACTS/q1a-pair-model-store-before.sha256"
fi
```

In **Engines**, uninstall only the PAIR-installed Ollama with `u`; do not delete the model.

```bash
if [ -n "$PAIR_MODEL_STORE" ] && [ -d "$PAIR_MODEL_STORE" ]; then
  find "$PAIR_MODEL_STORE" -type f -printf '%P\t%s\n' | sort | sha256sum \
    > "$Q1_ARTIFACTS/q1a-pair-model-store-after.sha256"
  diff -u \
    "$Q1_ARTIFACTS/q1a-pair-model-store-before.sha256" \
    "$Q1_ARTIFACTS/q1a-pair-model-store-after.sha256"
fi
```

PASS only if uninstall completes and the model files remain. If the store cannot be identified confidently, result = `unresolved`.

### 6.8 Q1A rollback

Quit TUI (`q`) and end only the lab session:

```bash
tmux kill-session -t pair-q1 2>/dev/null || true
```

Restore section 5's pre-lab Ollama state.

Re-hash the Pantheon-owned model-store metadata:

```bash
if sudo test -d /srv/ai/models/ollama; then
  sudo find /srv/ai/models/ollama -type f -printf '%P\t%s\n' \
    | sort | sha256sum \
    > "$Q1_ARTIFACTS/pantheon-ollama-store-after-q1a.sha256"
else
  printf 'absent\n' \
    > "$Q1_ARTIFACTS/pantheon-ollama-store-after-q1a.sha256"
fi

diff -u \
  "$Q1_ARTIFACTS/pantheon-ollama-store-before.sha256" \
  "$Q1_ARTIFACTS/pantheon-ollama-store-after-q1a.sha256"
```

Any unexplained difference stops Q1.

## 7. Q1B — Linux + Windows PAIR cluster

### 7.1 Windows baseline and exact installer

From the PR checkout in PowerShell:

```powershell
$lines = python implementation/tools/export_external_qualification_pins.py personal-ai-router
foreach ($line in $lines) {
  $name, $value = $line -split '=', 2
  Set-Item -Path "Env:$name" -Value $value
}

$Q1Root = Join-Path $HOME 'pantheon-labs\pair-unsloth-q1'
$Artifacts = Join-Path $Q1Root 'artifacts'
New-Item -ItemType Directory -Force -Path $Artifacts | Out-Null

nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader |
  Out-File (Join-Path $Artifacts 'windows-gpu-baseline.txt')
```

If PAIR is already installed/configured for non-Q1 use on Windows, stop and record that pre-existing state; do not overwrite a live cluster configuration.

Resolve and verify the selected x64 installer:

```powershell
$release = Invoke-RestMethod "https://api.github.com/repos/$env:PAIR_REPOSITORY/releases/tags/v$env:PAIR_VERSION"
$assetName = "NVPAIR-Setup-$($env:PAIR_VERSION)-x64.exe"
$asset = $release.assets | Where-Object { $_.name -eq $assetName } | Select-Object -First 1
if (-not $asset) { throw 'PAIR x64 Windows installer not found' }

$installer = Join-Path $Q1Root $assetName
Invoke-WebRequest $asset.browser_download_url -OutFile $installer

$actual = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant()
$expected = (($asset.digest ?? '') -replace '^sha256:', '').ToLowerInvariant()
$actual | Out-File (Join-Path $Artifacts 'pair-windows-asset.sha256')
if ($expected -and $actual -ne $expected) { throw 'PAIR Windows asset digest mismatch' }

Start-Process -FilePath $installer -Wait
```

If using Windows PowerShell 5.1 where `??` is unsupported, replace the `$expected` assignment with:

```powershell
$expected = ''
if ($asset.digest) { $expected = ($asset.digest -replace '^sha256:', '').ToLowerInvariant() }
```

### 7.2 Prepare Windows engine/model

In PAIR Desktop:

1. select the local node;
2. install/start Ollama through PAIR, or explicitly record if an existing engine is adopted;
3. add `qwen3.5:4b`;
4. wait until the model appears in local inventory;
5. copy the actual client endpoint from **Endpoints**.

Do not assume the displayed port if it differs from the standard endpoint.

### 7.3 Restart Linux Q1 PAIR

Run section 5 to free the proxy port. Restart TUI with the same isolated HOME:

```bash
tmux new -s pair-q1
```

Inside tmux:

```bash
export HOME="$Q1_PAIR_HOME"
export XDG_CONFIG_HOME="$Q1_PAIR_HOME/.config"
exec "$PAIR_TUI"
```

If Q1A uninstalled the PAIR-owned Ollama, reinstall it with `i`. Verify whether its retained model reappears without a fresh weight download; record the actual behavior.

### 7.4 Firewall only when necessary

Inspect first:

```bash
sudo ufw status verbose 2>/dev/null || true
```

If UFW is active and pairing/discovery is blocked, scope temporary rules to the Windows LAN IP:

```bash
export WINDOWS_Q1_IP='<windows-lan-ip>'
sudo ufw allow from "$WINDOWS_Q1_IP" to any port 5353 proto udp comment 'PAIR-Q1'
for p in 14318 14319 14320 14321 14322 14323; do
  sudo ufw allow from "$WINDOWS_Q1_IP" to any port "$p" proto tcp comment 'PAIR-Q1'
done
```

If a port/protocol differs in the live PAIR release, stop and reconcile with the selected release's documentation; do not broaden the firewall as a shortcut.

### 7.5 Pair nodes

Preferred flow:

1. Windows Desktop → **Add node** → Linux LAN IP/discovered node.
2. Linux TUI → **Cluster** (`7`) → accept inbound with `a`.
3. Enter the six-digit PIN.
4. Do not record the PIN.
5. Confirm both nodes show the same cluster membership.

Record whether discovery worked versus direct-IP pairing. These are distinct observations.

### 7.6 Verify both nodes are eligible

Before traffic:

- both nodes online;
- Ollama healthy on both;
- exact same model ID present on both;
- no accidental manual node pin;
- Linux TUI **Proxies** is in automatic mode (`a`) unless a subtest explicitly says otherwise.

### 7.7 Twelve-request concurrent burst from Windows

Use the endpoint displayed by PAIR Desktop:

```powershell
$PairBase = 'http://127.0.0.1:11434' # replace if Endpoints displays another port
$Model = 'qwen3.5:4b'

$jobs = 1..12 | ForEach-Object {
  Start-Job -ArgumentList $PairBase, $Model, $_ -ScriptBlock {
    param($Base, $ModelName, $Index)
    $body = @{
      model = $ModelName
      messages = @(@{ role='user'; content="Return only OK $Index" })
      max_tokens = 16
    } | ConvertTo-Json -Depth 5
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
      $null = Invoke-RestMethod "$Base/v1/chat/completions" -Method Post -ContentType 'application/json' -Body $body
      $sw.Stop()
      [pscustomobject]@{index=$Index;status='success';elapsed_ms=$sw.ElapsedMilliseconds}
    } catch {
      $sw.Stop()
      [pscustomobject]@{index=$Index;status='error';elapsed_ms=$sw.ElapsedMilliseconds;error=$_.Exception.Message}
    }
  }
}

$results = $jobs | Receive-Job -Wait
$jobs | Remove-Job
$results | ConvertTo-Json | Out-File (Join-Path $Artifacts 'q1b-burst-results.json')
```

The script discards response bodies.

Use Windows **Jobs** to record only `Ran on` counts for the twelve calls. Linux TUI does not provide per-request serving-node attribution, so Desktop is the canonical Q1B observation surface for that field.

PASS `concurrent_request_distribution` requires successful requests and actual use of both eligible nodes during the bounded burst. If all requests stay on one node while both remain eligible, record that scheduler outcome; do not invent balancing.

### 7.8 Failover

Quit Linux TUI with `q` or terminate only `tmux pair-q1`.

Wait until Windows marks Linux offline/ineligible, then issue three new bounded requests.

PASS requires:

- three successful requests;
- Windows **Jobs** shows all three served by Windows;
- none is attributed to the stopped Linux node.

### 7.9 Rejoin

Restart Linux TUI with the same isolated HOME.

Record whether membership persists or re-pairing is required.

PASS `returning_node_becomes_eligible_again` requires Linux to become eligible again with its engine/model inventory visible. Run another concurrent burst and record whether Linux is used again.

### 7.10 Q1B rollback

- leave/remove the temporary cluster if Q1B is complete;
- quit Linux TUI;
- restore the pre-stage system Ollama state;
- remove only temporary `PAIR-Q1` firewall rules if added;
- on Windows, uninstall PAIR only if it was installed solely for Q1 and there was no pre-existing PAIR state;
- never delete an existing user-managed Ollama installation.

Use `sudo ufw status numbered` and delete only Q1 rule numbers in descending order. Do not flush firewall configuration.

## 8. Q1C — current Hermes container namespace → local PAIR

Q1C asks only whether the current container namespace can access PAIR's local plaintext client ingress without a networking workaround.

### 8.1 Start the isolated Linux PAIR endpoint

Run section 5, then start the isolated PAIR TUI and its PAIR-owned Ollama. Confirm on the host:

```bash
curl -fsS http://127.0.0.1:11434/v1/models >/dev/null
```

### 8.2 Freeze current Compose/network state

```bash
sudo sha256sum /opt/pantheon-node/compose.yaml \
  > "$Q1_ARTIFACTS/q1c-compose-before.sha256"

docker inspect pantheon-hermes --format '{{json .HostConfig.ExtraHosts}}' \
  > "$Q1_ARTIFACTS/q1c-hermes-extra-hosts.json"

docker inspect pantheon-hermes --format '{{json .NetworkSettings.Networks}}' \
  > "$Q1_ARTIFACTS/q1c-hermes-networks.json"
```

Do not add `network_mode: host`, a relay, an iptables redirect or a Compose override before the measurement.

### 8.3 Probe from the real Hermes container network namespace

```bash
docker exec -i pantheon-hermes python - <<'PY' \
  > "$Q1_ARTIFACTS/q1c-container-probe.txt" 2>&1
import socket
import urllib.error
import urllib.request

url = "http://host.docker.internal:11434/v1/models"
print("container_hostname=", socket.gethostname())
try:
    print("container_ip=", socket.gethostbyname(socket.gethostname()))
except Exception as exc:
    print("container_ip_error=", type(exc).__name__)
print("host_gateway_ip=", socket.gethostbyname("host.docker.internal"))

try:
    with urllib.request.urlopen(url, timeout=10) as response:
        print("http_status=", response.status)
        print("content_type=", response.headers.get("Content-Type"))
except urllib.error.HTTPError as exc:
    print("http_status=", exc.code)
    print("error_body_prefix=", exc.read(512).decode("utf-8", errors="replace"))
except Exception as exc:
    print("transport_error=", type(exc).__name__, str(exc)[:200])
PY
```

No prompt/model response is sent in this probe.

### 8.4 Classify the transport result

Use exactly one:

```text
accepted_http_2xx
refused_http_403_loopback
connection_refused_or_timeout
other_http_error
unresolved
```

Do not pre-record `403` just because source review predicts a loopback gate.

If refused, stop Q1C. Host networking, host-native Hermes, mTLS client ingress or a relay are separate future experiments.

### 8.5 Integrity/rollback

```bash
sudo sha256sum /opt/pantheon-node/compose.yaml \
  > "$Q1_ARTIFACTS/q1c-compose-after.sha256"

diff -u \
  "$Q1_ARTIFACTS/q1c-compose-before.sha256" \
  "$Q1_ARTIFACTS/q1c-compose-after.sha256"
```

Quit PAIR and restore system Ollama state.

PASS `no_relay_or_host_network_change_in_q1` requires identical Compose hashes.

## 9. Q1D — Unsloth as a custom provider of the existing Hermes runtime

Do not use `unsloth start hermes` in Q1D. The test is provider compatibility with the selected Hermes runtime, not Unsloth ownership of a Hermes session/home.

### 9.1 Prepare exact Unsloth source and an isolated Studio/model cache

```bash
rm -rf "$Q1_UNSLOTH_SRC" "$Q1_UNSLOTH_VENV"
mkdir -p "$Q1_UNSLOTH_HOME" "$Q1_HF_HOME"

git clone --filter=blob:none \
  "https://github.com/${UNSLOTH_REPOSITORY}.git" \
  "$Q1_UNSLOTH_SRC"

git -C "$Q1_UNSLOTH_SRC" fetch --depth=1 origin "$UNSLOTH_REF"
git -C "$Q1_UNSLOTH_SRC" checkout --detach "$UNSLOTH_REF"

test "$(git -C "$Q1_UNSLOTH_SRC" rev-parse HEAD)" = "$UNSLOTH_REF" \
  || { echo 'Unsloth checkout != qualification pin'; exit 1; }

printf '%s\n' "$(git -C "$Q1_UNSLOTH_SRC" rev-parse HEAD)" \
  > "$Q1_ARTIFACTS/q1d-unsloth-source-ref.txt"

uv venv "$Q1_UNSLOTH_VENV" --python 3.13
uv pip install --python "$Q1_UNSLOTH_VENV/bin/python" \
  -e "$Q1_UNSLOTH_SRC" --torch-backend=auto

export UNSLOTH_STUDIO_HOME="$Q1_UNSLOTH_HOME"
export HF_HOME="$Q1_HF_HOME"
export XDG_CACHE_HOME="$Q1_ROOT/xdg-cache"
mkdir -p "$XDG_CACHE_HOME"

PATH="$Q1_UNSLOTH_VENV/bin:$PATH" unsloth studio setup
PATH="$Q1_UNSLOTH_VENV/bin:$PATH" unsloth --help \
  > "$Q1_ARTIFACTS/q1d-unsloth-cli-help.txt"
```

The Studio runtime, llama.cpp build and HF model cache must remain under Q1-controlled paths where the selected Unsloth code permits it. Record any dependency that escapes these paths as an observation.

### 9.1.1 Capture the effective runtime dependency closure

`UNSLOTH_REF` identifies the selected Unsloth source, not every dependency dynamically resolved by the environment or Studio setup. Capture what will actually execute before treating Q1D as reproducible.

```bash
"$Q1_UNSLOTH_VENV/bin/python" - <<'PY' \
  > "$Q1_ARTIFACTS/q1d-python-runtime-closure.json"
import importlib.metadata as md
import json
import platform
import sys

payload = {
    "python": sys.version,
    "platform": platform.platform(),
    "packages": sorted(
        {
            (dist.metadata.get("Name") or "<unnamed>"): dist.version
            for dist in md.distributions()
        }.items()
    ),
}
try:
    import torch
    payload["torch"] = {
        "version": torch.__version__,
        "cuda": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
    }
except Exception as exc:
    payload["torch_error"] = type(exc).__name__

print(json.dumps(payload, indent=2, sort_keys=True))
PY

: > "$Q1_ARTIFACTS/q1d-llama-runtime-files.txt"
while IFS= read -r -d '' file; do
  printf '%s\t' "$file" >> "$Q1_ARTIFACTS/q1d-llama-runtime-files.txt"
  sha256sum "$file" >> "$Q1_ARTIFACTS/q1d-llama-runtime-files.txt"
done < <(
  find "$Q1_UNSLOTH_HOME" "$XDG_CACHE_HOME" "$Q1_UNSLOTH_VENV" \
    -type f \( -name 'llama-server' -o -name 'llama-cli' \) -print0 2>/dev/null
)

if [ ! -s "$Q1_ARTIFACTS/q1d-llama-runtime-files.txt" ]; then
  printf 'unresolved_before_server_start\n' \
    > "$Q1_ARTIFACTS/q1d-llama-runtime-files.txt"
fi
```

PASS `runtime_dependency_closure_captured` requires the Python/Torch/CUDA environment to be recorded and the effective llama.cpp/`llama-server` runtime to be identified either here or from the running server process in section 9.2. If a dynamically resolved runtime cannot be identified, record the check as `unresolved`; do not infer it from the Unsloth source pin.

### 9.2 Bind Unsloth to the Docker bridge gateway (bridge-scoped)

Use the host-side bridge gateway already reachable from the Hermes container rather than `0.0.0.0`.

This is a bridge-scoped exposure. It is not proof that only `pantheon-hermes` can reach the endpoint; other containers attached to a compatible bridge may also be able to reach it. Record the actual bridge identity instead of calling the endpoint Hermes-only.

```bash
export Q1_DOCKER_GATEWAY="$(docker network inspect bridge -f '{{(index .IPAM.Config 0).Gateway}}')"
test -n "$Q1_DOCKER_GATEWAY" || { echo 'Docker bridge gateway unresolved'; exit 1; }
case "$Q1_DOCKER_GATEWAY" in
  0.0.0.0|::) echo 'wildcard bind refused'; exit 1 ;;
esac
printf '%s\n' "$Q1_DOCKER_GATEWAY" \
  > "$Q1_ARTIFACTS/q1d-docker-gateway.txt"
docker network inspect bridge --format '{{json .IPAM.Config}}' \
  > "$Q1_ARTIFACTS/q1d-docker-bridge-ipam.json"
```

Start in tmux:

```bash
tmux new -s unsloth-q1
```

Inside tmux:

```bash
source "$Q1_UNSLOTH_VENV/bin/activate"
export UNSLOTH_STUDIO_HOME="$Q1_UNSLOTH_HOME"
export HF_HOME="$Q1_HF_HOME"
export XDG_CACHE_HOME="$Q1_ROOT/xdg-cache"

unsloth run \
  --model "$UNSLOTH_Q1_MODEL" \
  --max-seq-length "$UNSLOTH_Q1_CONTEXT" \
  --host "$Q1_DOCKER_GATEWAY" \
  --port "$UNSLOTH_Q1_PORT" \
  --api-key-name pantheon-q1
```

From another shell, capture the actual serving process/listener without storing response content:

```bash
ps -eo pid,args | grep -E '[u]nsloth|[l]lama-server' \
  > "$Q1_ARTIFACTS/q1d-server-process.txt" || true
sudo ss -ltnp | grep -E ":${UNSLOTH_Q1_PORT}\\b" \
  > "$Q1_ARTIFACTS/q1d-server-listener.txt" || true
```

If section 9.1.1 could not identify the llama.cpp runtime, use this process observation to locate and hash the actual `llama-server` executable. If that still cannot be established, keep `runtime_dependency_closure_captured = unresolved`.

Copy the temporary API key shown by Unsloth into the operator shell without writing it to disk:

```bash
read -rsp 'Temporary Unsloth Q1 API key: ' UNSLOTH_Q1_API_KEY
echo
export UNSLOTH_Q1_API_KEY
```

Optional one-way fingerprint:

```bash
printf '%s' "$UNSLOTH_Q1_API_KEY" | sha256sum | awk '{print $1}' \
  > "$Q1_ARTIFACTS/q1d-unsloth-key-fingerprint.sha256"
```

### 9.3 Verify `/v1/models` and record the actual served model ID

```bash
Q1_MODELS_BODY="$Q1_ROOT/q1d-models.json"

curl -fsS \
  -H "Authorization: Bearer $UNSLOTH_Q1_API_KEY" \
  "http://$Q1_DOCKER_GATEWAY:$UNSLOTH_Q1_PORT/v1/models" \
  -o "$Q1_MODELS_BODY"

jq '{object,model_count:(.data|length),model_ids:[.data[].id]}' \
  "$Q1_MODELS_BODY" \
  > "$Q1_ARTIFACTS/q1d-models-shape.json"

export UNSLOTH_Q1_SERVED_MODEL="$(jq -r '.data[0].id // empty' "$Q1_MODELS_BODY")"
rm -f "$Q1_MODELS_BODY"
test -n "$UNSLOTH_Q1_SERVED_MODEL" || { echo 'served model ID unresolved'; exit 1; }
```

Do not assume the API model ID equals the Hugging Face locator.

### 9.4 Direct streaming check

```bash
Q1_STREAM="$Q1_ROOT/q1d-stream.txt"

curl -sS -N \
  -H "Authorization: Bearer $UNSLOTH_Q1_API_KEY" \
  -H 'Content-Type: application/json' \
  "http://$Q1_DOCKER_GATEWAY:$UNSLOTH_Q1_PORT/v1/chat/completions" \
  -d "{\"model\":\"$UNSLOTH_Q1_SERVED_MODEL\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"Return the single token OK\"}],\"max_tokens\":8}" \
  > "$Q1_STREAM"

python - "$Q1_STREAM" <<'PY' \
  > "$Q1_ARTIFACTS/q1d-stream-shape.txt"
import sys
from pathlib import Path
lines = [x for x in Path(sys.argv[1]).read_text(errors="replace").splitlines() if x.startswith("data:")]
print("sse_data_lines=", len(lines))
print("has_done=", any("[DONE]" in x for x in lines))
PY
rm -f "$Q1_STREAM"
```

PASS requires actual streamed SSE data, not only HTTP 200.

### 9.5 Direct structured tool-call check

The declared tool is synthetic and is not executed at this step.

```bash
Q1_TOOL_BODY="$Q1_ROOT/q1d-tool-body.json"

curl -fsS \
  -H "Authorization: Bearer $UNSLOTH_Q1_API_KEY" \
  -H 'Content-Type: application/json' \
  "http://$Q1_DOCKER_GATEWAY:$UNSLOTH_Q1_PORT/v1/chat/completions" \
  -d "{\"model\":\"$UNSLOTH_Q1_SERVED_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Use the q1_echo tool with value PANTHEON_Q1_TOOL_OK.\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"q1_echo\",\"description\":\"Return a test string\",\"parameters\":{\"type\":\"object\",\"properties\":{\"value\":{\"type\":\"string\"}},\"required\":[\"value\"]}}}],\"tool_choice\":\"auto\",\"max_tokens\":64}" \
  > "$Q1_TOOL_BODY"

jq '{model,finish_reason:.choices[0].finish_reason,tool_call_count:(.choices[0].message.tool_calls // [] | length),tool_names:[(.choices[0].message.tool_calls // [])[].function.name]}' \
  "$Q1_TOOL_BODY" \
  > "$Q1_ARTIFACTS/q1d-direct-tool-shape.json"
rm -f "$Q1_TOOL_BODY"
```

PASS requires a structured tool call. A textual description of a tool call is not a PASS.

### 9.6 Hash `pantheon-governed` before the Hermes lab profile

Do not print profile file contents or secrets.

```bash
docker exec pantheon-hermes sh -lc '
  if [ -d /opt/data/profiles/pantheon-governed ]; then
    find /opt/data/profiles/pantheon-governed -type f -printf "%P\t%s\n" | sort | sha256sum
  else
    echo absent
  fi
' > "$Q1_ARTIFACTS/q1d-governed-profile-before.sha256"
```

### 9.7 Create a fresh temporary profile, not a clone

Do not clone `pantheon-governed`: Hermes profile clone copies configuration and `.env`, which would duplicate secrets unnecessarily. Create a fresh temporary profile and keep its scope minimal.

```bash
docker exec -it pantheon-hermes \
  hermes profile create pantheon-q1-unsloth --no-skills
```

Do not set it as the sticky/default profile.

Get its config path:

```bash
docker exec pantheon-hermes \
  hermes -p pantheon-q1-unsloth config path \
  > "$Q1_ARTIFACTS/q1d-hermes-lab-config-path.txt"
```

### 9.8 Write only the temporary profile's provider/model/memory posture

Provider contract:

```yaml
model:
  provider: custom:unsloth-q1
  default: <exact-id-returned-by-Unsloth-v1-models>

providers:
  unsloth-q1:
    api: http://host.docker.internal:18888/v1
    key_env: UNSLOTH_API_KEY
    transport: chat_completions

memory:
  provider: ""
  memory_enabled: false
```

The key remains process-local; it is not written into YAML.

```bash
Q1_CONFIG="$(tr -d '\r\n' < "$Q1_ARTIFACTS/q1d-hermes-lab-config-path.txt")"

docker exec -i \
  -e Q1_CONFIG="$Q1_CONFIG" \
  -e Q1_MODEL="$UNSLOTH_Q1_SERVED_MODEL" \
  pantheon-hermes python - <<'PY'
import os
from pathlib import Path
import yaml

path = Path(os.environ["Q1_CONFIG"])
data = yaml.safe_load(path.read_text()) or {}
data["model"] = {
    "provider": "custom:unsloth-q1",
    "default": os.environ["Q1_MODEL"],
}
data["providers"] = {
    "unsloth-q1": {
        "api": "http://host.docker.internal:18888/v1",
        "key_env": "UNSLOTH_API_KEY",
        "transport": "chat_completions",
    }
}
data["memory"] = {
    "provider": "",
    "memory_enabled": False,
}
path.write_text(yaml.safe_dump(data, sort_keys=False))
PY
```

Check configuration without printing secrets:

```bash
docker exec pantheon-hermes \
  hermes -p pantheon-q1-unsloth config check \
  > "$Q1_ARTIFACTS/q1d-hermes-config-check.txt" 2>&1
```

### 9.9 Hermes one-shot through Unsloth

```bash
set +e
docker exec \
  -e UNSLOTH_API_KEY="$UNSLOTH_Q1_API_KEY" \
  pantheon-hermes \
  hermes -p pantheon-q1-unsloth -z 'Return the single token OK' \
  > /dev/null
Q1_HERMES_EXIT=$?
set -e
printf '%s\n' "$Q1_HERMES_EXIT" \
  > "$Q1_ARTIFACTS/q1d-hermes-oneshot-exit.txt"
```

PASS requires exit 0 and provider/model telemetry showing the named Unsloth custom provider; a silent fallback is FAIL.

### 9.10 Bounded Hermes tool round trip under normal approval policy

```bash
docker exec -it \
  -e UNSLOTH_API_KEY="$UNSLOTH_Q1_API_KEY" \
  pantheon-hermes \
  hermes -p pantheon-q1-unsloth chat \
  -t terminal \
  --max-turns 3 \
  -q 'Use the terminal tool once to run: printf PANTHEON_Q1_TOOL_OK . Return exactly its stdout.'
```

Do not add `--yolo`.

If an approval prompt appears, approve only that exact `printf` action.

PASS requires:

- structured tool call accepted by Hermes;
- actual terminal-tool invocation;
- bounded command execution;
- tool result returned to the model;
- completed turn;
- no fallback provider.

Record only exit/result classification, provider/model identity and whether an approval prompt occurred; do not retain conversation text.

### 9.11 Context behavior

Generate synthetic content only; do not use Pantheon/project documents. Exercise a prompt materially larger than the smoke test but below `16384` tokens. Record:

```text
input token estimate
HTTP/Hermes exit status
first-token latency if available
total latency
completion status
provider/model identity
```

This is a bounded compatibility observation, not a context-window qualification for the model itself.

### 9.12 Deliberate provider error and no-fallback check

```bash
set +e
docker exec \
  -e UNSLOTH_API_KEY='q1-deliberately-invalid' \
  pantheon-hermes \
  hermes -p pantheon-q1-unsloth -z 'Return OK' \
  > /dev/null 2> "$Q1_ARTIFACTS/q1d-invalid-key-error.txt"
Q1_BAD_KEY_EXIT=$?
set -e
printf '%s\n' "$Q1_BAD_KEY_EXIT" \
  > "$Q1_ARTIFACTS/q1d-invalid-key-exit.txt"
```

Inspect/redact the error artifact before retaining it. PASS requires a clear provider/auth failure and no silent fallback to another provider.

### 9.13 Q1D rollback

Delete only the temporary profile, interactively if Hermes requests confirmation:

```bash
docker exec -it pantheon-hermes \
  hermes profile delete pantheon-q1-unsloth
```

Hash the governed profile again:

```bash
docker exec pantheon-hermes sh -lc '
  if [ -d /opt/data/profiles/pantheon-governed ]; then
    find /opt/data/profiles/pantheon-governed -type f -printf "%P\t%s\n" | sort | sha256sum
  else
    echo absent
  fi
' > "$Q1_ARTIFACTS/q1d-governed-profile-after.sha256"

diff -u \
  "$Q1_ARTIFACTS/q1d-governed-profile-before.sha256" \
  "$Q1_ARTIFACTS/q1d-governed-profile-after.sha256"
```

PASS `pantheon_governed_profile_not_mutated` requires equality.

Stop the isolated Unsloth server and clear the temporary key:

```bash
tmux kill-session -t unsloth-q1 2>/dev/null || true
unset UNSLOTH_Q1_API_KEY
```

The Q1 source/venv/cache may remain under `$Q1_ROOT` until Q1E review. Their existence is not installation/activation truth.

## 10. Q1E — observation rows and classification

Do not classify from memory or chat narrative. Create one sanitized row for each required check:

```json
{
  "check_id": "",
  "stage_id": "",
  "host": "",
  "command_or_action": "",
  "expected_observation": "",
  "actual_observation": "",
  "status": "pass|fail|unresolved|not_run",
  "artifact_ref": "",
  "started_at": "",
  "ended_at": "",
  "notes": ""
}
```

No row may contain secrets, pairing PINs, prompt bodies or response bodies.

### 10.1 PAIR decision gate

PAIR may be classified `accepted` for a later deployment-design PR only if observations establish:

- exact selected artifact identity;
- PAIR-owned client proxy/backend behavior;
- same-model two-node request routing;
- clean node exclusion/failover/rejoin;
- serving-node observability through an available surface;
- model retention across PAIR engine uninstall;
- rollback to prior system Ollama state;
- unchanged Pantheon Ollama model-store metadata;
- explicit Q1C container-to-PAIR result;
- explicit future owner decision still required for Ollama lifecycle/port.

A Q1C loopback refusal rejects the current container/plaintext path; it does not by itself reject PAIR as a physical router.

### 10.2 Unsloth decision gate

Unsloth may be classified `accepted` for a later provider/deployment-design PR only if observations establish:

- exact selected source identity;
- effective runtime dependency closure, including Python/Torch/CUDA and the actual llama.cpp/`llama-server` identity when discoverable;
- isolated OpenAI-compatible endpoint;
- bridge-scoped bind explicitly distinguished from Hermes-only access;
- streaming;
- structured tool-call output;
- Hermes one-shot through the named custom provider;
- bounded Hermes tool round trip under normal approval policy;
- context behavior;
- provider-error behavior with no silent fallback;
- unchanged `pantheon-governed` profile;
- no `unsloth start hermes` ownership path;
- rollback of temporary profile/server.

### 10.3 Outcome vocabulary

Use only:

```text
accepted
rejected
unresolved
```

`accepted` still means only “eligible for the next design decision”; it does not mean deployed, activated, authorized or Evidence-admitted.

## 11. Stop conditions

Stop the current stage rather than bypassing the condition if:

- release digest validation fails;
- source checkout does not match the canonical pin;
- an unknown process owns a required port;
- `/srv/ai/models/ollama` changes unexpectedly;
- progress requires editing production Compose, `release.env`, `install-node` or the Hermes lock;
- PAIR requires exposing its plaintext local proxy to the LAN;
- Unsloth requires `0.0.0.0` merely to reach the current Hermes container;
- a secret would need to be persisted in a committed/lab artifact;
- Hermes silently falls back to another provider;
- `pantheon-governed` changes during Q1D.

A stop condition is itself a valid qualification observation. Do not weaken the boundary merely to get a green lab.
