#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?}"
: "${RUNNER_TEMP:?}"
: "${HERMES_RELEASE_COMMIT:?load hermes-agent qualification pin first}"
: "${HINDSIGHT_VERSION:?load hindsight qualification pin first}"
: "${HINDSIGHT_API_URL:?set HINDSIGHT_API_URL to a sandbox Hindsight endpoint}"
: "${HINDSIGHT_BANK_ID:=pantheon-o1-synthetic}"

MVP_ROOT="$GITHUB_WORKSPACE/pantheon-mvp"
UPSTREAM_ROOT="$GITHUB_WORKSPACE/hermes-upstream"
LAB_ROOT="$RUNNER_TEMP/hindsight-hermes-o1"
ARTIFACTS="$LAB_ROOT/artifacts"
HERMES_HOME="$LAB_ROOT/hermes-home"
VENV="$LAB_ROOT/venv"
PROVIDER_URL="http://127.0.0.1:9020"
FIXTURE_PID=""

export ARTIFACTS HERMES_HOME HINDSIGHT_API_URL HINDSIGHT_API_KEY="${HINDSIGHT_API_KEY:-}" HINDSIGHT_BANK_ID
mkdir -p "$ARTIFACTS"
cleanup() {
  set +e
  if [ -n "$FIXTURE_PID" ]; then kill "$FIXTURE_PID" 2>/dev/null || true; fi
  if [ -x "$VENV/bin/hermes" ]; then "$VENV/bin/hermes" profile delete assistant-personal --yes >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

cd "$UPSTREAM_ROOT"
test "$(git rev-parse HEAD)" = "$HERMES_RELEASE_COMMIT"
cd "$MVP_ROOT"

python -m pip install --disable-pip-version-check --upgrade uv
python -m venv "$VENV"
uv pip install --python "$VENV/bin/python" -e "$UPSTREAM_ROOT" "hindsight-client==${HINDSIGHT_VERSION}" "aiohttp==3.14.1"
uv pip install --python "$VENV/bin/python" -e "$MVP_ROOT"
export PATH="$VENV/bin:$PATH"

hermes profile create assistant-personal --no-skills --no-alias
hermes profile create pantheon-governed --no-skills --no-alias

python "$MVP_ROOT/tools/hindsight_hermes_o1_fixture.py" --journal "$ARTIFACTS/provider-journal.jsonl" >"$ARTIFACTS/provider.log" 2>&1 &
FIXTURE_PID=$!
for _ in $(seq 1 60); do curl -fsS "$PROVIDER_URL/health" >/dev/null && break; sleep 0.5; done

python "$MVP_ROOT/tools/run_hindsight_hermes_o1.py" configure \
  --hermes-home "$HERMES_HOME" \
  --hindsight-api-url "$HINDSIGHT_API_URL" \
  --hindsight-api-key "$HINDSIGHT_API_KEY" \
  --provider-url "$PROVIDER_URL" \
  --bank-id "$HINDSIGHT_BANK_ID" \
  --output "$ARTIFACTS/configuration.json"

# Governed profile stays explicitly memory-off, matching the existing acceptance posture.
cat > "$HERMES_HOME/profiles/pantheon-governed/config.yaml" <<'YAML'
memory:
  provider: ""
  memory_enabled: false
  user_profile_enabled: false
platform_toolsets:
  cli: []
YAML

pantheon-hermes capture-memory-status --profile pantheon-governed --hermes-command "$VENV/bin/hermes" --output "$ARTIFACTS/governed-memory-status.json"
hermes -p assistant-personal memory status > "$ARTIFACTS/assistant-memory-status.txt"
grep -i hindsight "$ARTIFACTS/assistant-memory-status.txt"

# Seed and verify the real Hindsight endpoint. The server runs with retain extraction mode=chunks,
# so this path requires no LLM call and contains synthetic data only.
python - <<'PY'
import json, os, time
from pathlib import Path
from hindsight_client import Hindsight
base=os.environ['HINDSIGHT_API_URL']
key=os.environ.get('HINDSIGHT_API_KEY') or None
bank=os.environ.get('HINDSIGHT_BANK_ID','pantheon-o1-synthetic')
marker='PANTHEON_O1_SYNTHETIC_MEMORY_MARKER'
client=Hindsight(base_url=base, api_key=key)
client.retain(bank_id=bank, content=f'{marker}: synthetic sandbox fact only', context='Pantheon O1 synthetic lab')
last=None
for _ in range(90):
    last=client.recall(bank_id=bank, query='O1 synthetic memory marker')
    if marker in json.dumps(last, default=str):
        break
    time.sleep(1)
Path(os.environ['ARTIFACTS']).joinpath('direct-recall.json').write_text(json.dumps(last, default=str, indent=2))
if marker not in json.dumps(last, default=str):
    raise SystemExit('synthetic marker was not recalled from Hindsight')
PY

hermes -p assistant-personal chat -q "Use hindsight_recall to find the O1 synthetic memory marker, then answer only after the tool returns." > "$ARTIFACTS/hermes-output.txt"
grep -F O1_HINDSIGHT_RECALL_COMPLETED "$ARTIFACTS/hermes-output.txt"
curl -fsS "$PROVIDER_URL/_lab/state" > "$ARTIFACTS/provider-state.json"

hermes profile delete assistant-personal --yes
printf '{"assistant_profile_removed":true,"pantheon_state_mutated":false}\n' > "$ARTIFACTS/rollback.json"
python "$MVP_ROOT/tools/run_hindsight_hermes_o1.py" validate --artifacts "$ARTIFACTS"
