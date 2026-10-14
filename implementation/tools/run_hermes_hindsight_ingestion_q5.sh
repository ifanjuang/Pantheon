#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?}"
: "${RUNNER_TEMP:?}"
: "${HERMES_ROOT:?}"
: "${OBSIDIAN_ROOT:?}"
: "${HINDSIGHT_VERSION:?}"
: "${HINDSIGHT_OBSIDIAN_VERSION:?}"
: "${HINDSIGHT_API_URL:=http://127.0.0.1:8888}"
: "${HINDSIGHT_BANK_ID:=pantheon-hermes-q5-synthetic}"

LAB_ROOT="$RUNNER_TEMP/hermes-hindsight-ingestion-q5"
ARTIFACTS="$LAB_ROOT/artifacts"
VAULT="$LAB_ROOT/vault"
INDEX="$LAB_ROOT/index.json"
CLI="$OBSIDIAN_ROOT/dist/cli.js"
NOTE_REL="Affaires/Alpha/hermes-note.md"
NOTE="$VAULT/$NOTE_REL"
CREATE_MARKER="PANTHEON_HERMES_Q5_CREATE"
PATCH_MARKER="PANTHEON_HERMES_Q5_PATCH"

export ARTIFACTS HINDSIGHT_API_URL HINDSIGHT_BANK_ID
mkdir -p "$ARTIFACTS" "$VAULT/Affaires/Alpha"

retain_batch_count() {
  docker logs pantheon-hermes-q5-hindsight 2>&1 \
    | grep -c "Starting background batch retain for bank_id=${HINDSIGHT_BANK_ID}" || true
}

recall_contains() {
  local marker="$1"
  MARKER="$marker" python - <<'PY'
import json, os, urllib.request
base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
bank=os.environ['HINDSIGHT_BANK_ID']
marker=os.environ['MARKER']
body={
    'query': marker,
    'types':['world','experience'],
    'tags':['vault:Hermes-Q5','folder:Affaires/Alpha'],
    'tags_match':'all_strict',
}
req=urllib.request.Request(
    f"{base}/v1/default/banks/{bank}/memories/recall",
    data=json.dumps(body).encode(),
    headers={'Content-Type':'application/json'},
    method='POST',
)
with urllib.request.urlopen(req,timeout=30) as resp:
    value=json.loads(resp.read().decode())
items=value.get('results',[]) if isinstance(value,dict) else []
found=any(marker in str(x.get('text','')) for x in items if isinstance(x,dict))
print(json.dumps({'marker':marker,'found':found,'result_count':len(items)}))
raise SystemExit(0 if found else 1)
PY
}

wait_for_recall() {
  local marker="$1"
  for _ in $(seq 1 120); do
    if recall_contains "$marker" > "$ARTIFACTS/recall-${marker}.json" 2>/dev/null; then
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for Hindsight recall marker: $marker" >&2
  return 1
}

hermes_action() {
  local action="$1"
  ACTION="$action" \
  HERMES_ROOT="$HERMES_ROOT" \
  OBSIDIAN_VAULT_PATH="$VAULT" \
  TERMINAL_CWD="$VAULT" \
  NOTE_REL="$NOTE_REL" \
  CREATE_MARKER="$CREATE_MARKER" \
  PATCH_MARKER="$PATCH_MARKER" \
  python - <<'PY'
import os, sys
from pathlib import Path

root=Path(os.environ['HERMES_ROOT']).resolve()
vault=Path(os.environ['OBSIDIAN_VAULT_PATH']).resolve()
note=vault/os.environ['NOTE_REL']
sys.path.insert(0,str(root))
from tools.file_tools import patch_tool, read_file_tool, write_file_tool

action=os.environ['ACTION']
if action=='create':
    content=(
        '---\n'
        'tags: [q5, hermes]\n'
        'created: 2026-08-25\n'
        '---\n'
        f"{os.environ['CREATE_MARKER']}. Synthetic note created by the real Hermes file tool.\n\n"
        'Status: draft\n'
    )
    result=write_file_tool(str(note),content)
    assert note.read_text(encoding='utf-8')==content, result
elif action=='patch':
    current=read_file_tool(str(note))
    assert 'Status: draft' in current, current
    result=patch_tool(
        mode='replace', path=str(note),
        old_string='Status: draft',
        new_string=f"Status: {os.environ['PATCH_MARKER']}",
    )
    after=note.read_text(encoding='utf-8')
    assert os.environ['PATCH_MARKER'] in after, result
else:
    raise SystemExit(f'unsupported action {action}')
PY
}

run_sync() {
  local output="$1"
  node "$CLI" reconcile \
    --vault "$VAULT" \
    --vault-name Hermes-Q5 \
    --bank "$HINDSIGHT_BANK_ID" \
    --api-url "$HINDSIGHT_API_URL" \
    --prefix-doc-id \
    --index "$INDEX" \
    | tee "$output"
}

BEFORE_CREATE=$(retain_batch_count)
hermes_action create
test -f "$NOTE"
grep -Fq "$CREATE_MARKER" "$NOTE"
AFTER_HERMES_CREATE=$(retain_batch_count)
test "$BEFORE_CREATE" = "$AFTER_HERMES_CREATE"
if recall_contains "$CREATE_MARKER" > "$ARTIFACTS/pre-sync-create-recall.json" 2>/dev/null; then
  echo "Hermes file write unexpectedly appeared in Hindsight before producer reconcile" >&2
  exit 1
fi

run_sync "$ARTIFACTS/create-sync.txt"
grep -F 'reconcile: +1 added, ~0 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/create-sync.txt"
wait_for_recall "$CREATE_MARKER"
AFTER_CREATE_SYNC=$(retain_batch_count)
test "$AFTER_CREATE_SYNC" -gt "$AFTER_HERMES_CREATE"

BEFORE_PATCH=$AFTER_CREATE_SYNC
hermes_action patch
grep -Fq "$PATCH_MARKER" "$NOTE"
AFTER_HERMES_PATCH=$(retain_batch_count)
test "$BEFORE_PATCH" = "$AFTER_HERMES_PATCH"
if recall_contains "$PATCH_MARKER" > "$ARTIFACTS/pre-sync-patch-recall.json" 2>/dev/null; then
  echo "Hermes patch unexpectedly appeared in Hindsight before producer reconcile" >&2
  exit 1
fi

sleep 0.02
run_sync "$ARTIFACTS/patch-sync.txt"
grep -F 'reconcile: +0 added, ~1 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/patch-sync.txt"
wait_for_recall "$PATCH_MARKER"
AFTER_PATCH_SYNC=$(retain_batch_count)
test "$AFTER_PATCH_SYNC" -gt "$AFTER_HERMES_PATCH"

python - <<'PY'
import json, os, urllib.request
from pathlib import Path
base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
bank=os.environ['HINDSIGHT_BANK_ID']
body={
  'query':'PANTHEON_HERMES_Q5_PATCH',
  'types':['world','experience'],
  'tags':['vault:Hermes-Q5','folder:Affaires/Alpha'],
  'tags_match':'all_strict',
}
req=urllib.request.Request(
 f"{base}/v1/default/banks/{bank}/memories/recall",
 data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=30) as r: value=json.loads(r.read().decode())
items=[x for x in value.get('results',[]) if isinstance(x,dict)]
assert items, value
assert any(x.get('document_id')=='Hermes-Q5/Affaires/Alpha/hermes-note.md' for x in items), items
assert any((x.get('metadata') or {}).get('path')=='Affaires/Alpha/hermes-note.md' for x in items), items
Path(os.environ['ARTIFACTS'],'final-scoped-recall.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
PY

BEFORE_CREATE="$BEFORE_CREATE" AFTER_HERMES_CREATE="$AFTER_HERMES_CREATE" AFTER_CREATE_SYNC="$AFTER_CREATE_SYNC" \
BEFORE_PATCH="$BEFORE_PATCH" AFTER_HERMES_PATCH="$AFTER_HERMES_PATCH" AFTER_PATCH_SYNC="$AFTER_PATCH_SYNC" \
HERMES_ROOT="$HERMES_ROOT" OBSIDIAN_ROOT="$OBSIDIAN_ROOT" python - <<'PY'
import json, os, subprocess
from pathlib import Path
out=Path(os.environ['ARTIFACTS'])
summary={
 'kind':'hermes_hindsight_ingestion_q5_acceptance',
 'status':'passed',
 'hermes_commit':subprocess.check_output(['git','-C',os.environ['HERMES_ROOT'],'rev-parse','HEAD'],text=True).strip(),
 'hindsight_obsidian_commit':subprocess.check_output(['git','-C',os.environ['OBSIDIAN_ROOT'],'rev-parse','HEAD'],text=True).strip(),
 'hindsight_version':os.environ['HINDSIGHT_VERSION'],
 'hindsight_obsidian_version':os.environ['HINDSIGHT_OBSIDIAN_VERSION'],
 'hermes_create_verified':True,
 'hermes_patch_after_fresh_read_verified':True,
 'hermes_direct_hindsight_write':False,
 'pre_reconcile_create_absent_from_hindsight':True,
 'pre_reconcile_patch_absent_from_hindsight':True,
 'official_producer_create_ingestion_verified':True,
 'official_producer_update_ingestion_verified':True,
 'single_hindsight_producer_kind':'hindsight-obsidian-sync',
 'source_provenance_verified':True,
 'hindsight_writeback_to_vault':False,
 'pantheon_state_mutated':False,
 'evidence_admitted':False,
 'retain_batches':{
   'before_create':int(os.environ['BEFORE_CREATE']),
   'after_hermes_create':int(os.environ['AFTER_HERMES_CREATE']),
   'after_create_sync':int(os.environ['AFTER_CREATE_SYNC']),
   'before_patch':int(os.environ['BEFORE_PATCH']),
   'after_hermes_patch':int(os.environ['AFTER_HERMES_PATCH']),
   'after_patch_sync':int(os.environ['AFTER_PATCH_SYNC']),
 },
}
(out/'acceptance-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
PY
