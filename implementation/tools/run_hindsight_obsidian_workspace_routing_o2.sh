#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?}"
: "${RUNNER_TEMP:?}"
: "${HINDSIGHT_API_URL:=http://127.0.0.1:8888}"

OBSIDIAN_ROOT="$GITHUB_WORKSPACE/hindsight-obsidian"
CLI="$OBSIDIAN_ROOT/dist/cli.js"
LAB_ROOT="$RUNNER_TEMP/hindsight-obsidian-o2-routing"
ARTIFACTS="$RUNNER_TEMP/hindsight-obsidian-o2/artifacts"
VAULT="$LAB_ROOT/Workspace"
AFFAIRES_BANK="workspace-projects"
DOCUMENTAIRES_BANK="workspace-reference"
AFFAIRES_INDEX="$LAB_ROOT/index-affaires.json"
DOCUMENTAIRES_INDEX="$LAB_ROOT/index-documentaires.json"

export HINDSIGHT_API_URL ARTIFACTS VAULT AFFAIRES_BANK DOCUMENTAIRES_BANK AFFAIRES_INDEX DOCUMENTAIRES_INDEX
mkdir -p "$ARTIFACTS" "$VAULT/Affaires/Verger/CR" "$VAULT/Documentaires/Technique"

cat > "$VAULT/Affaires/Verger/CR/CR03.md" <<'EOF'
---
tags: [affaire, cr]
created: 2026-08-24
---
PANTHEON_O2_AFFAIRES_MARKER. Verger CR03 : le détail de rive est propre à cette affaire.
EOF

cat > "$VAULT/Documentaires/Technique/bardage.md" <<'EOF'
---
tags: [documentaire, technique]
created: 2026-08-24
---
PANTHEON_O2_DOCUMENTAIRES_MARKER. Référence transversale : vérifier ventilation et lame d'air du bardage.
EOF

run_route() {
  local bank="$1" include="$2" index="$3" output="$4"
  node "$CLI" reconcile \
    --vault "$VAULT" \
    --vault-name Workspace \
    --bank "$bank" \
    --api-url "$HINDSIGHT_API_URL" \
    --include "$include" \
    --prefix-doc-id \
    --index "$index" \
    | tee "$output"
}

run_route "$AFFAIRES_BANK" Affaires "$AFFAIRES_INDEX" "$ARTIFACTS/routing-affaires-initial.txt"
run_route "$DOCUMENTAIRES_BANK" Documentaires "$DOCUMENTAIRES_INDEX" "$ARTIFACTS/routing-documentaires-initial.txt"
grep -F 'reconcile: +1 added, ~0 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/routing-affaires-initial.txt"
grep -F 'reconcile: +1 added, ~0 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/routing-documentaires-initial.txt"

python - <<'PY'
import json, os, time, urllib.request
from pathlib import Path

base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
out=Path(os.environ['ARTIFACTS'])

def recall(bank, query, tags):
    url=f"{base}/v1/default/banks/{bank}/memories/recall"
    body={'query':query,'types':['world','experience'],'tags':tags,'tags_match':'all_strict'}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    last={}
    for _ in range(120):
        with urllib.request.urlopen(req,timeout=10) as resp:
            last=json.loads(resp.read().decode())
        if last.get('results'):
            return last
        time.sleep(0.25)
    return last

def items(value):
    return [x for x in value.get('results',[]) if isinstance(x,dict)]

a=recall(os.environ['AFFAIRES_BANK'],'PANTHEON_O2_AFFAIRES_MARKER',['vault:Workspace','folder:Affaires'])
d=recall(os.environ['DOCUMENTAIRES_BANK'],'PANTHEON_O2_DOCUMENTAIRES_MARKER',['vault:Workspace','folder:Documentaires'])
a_cross=recall(os.environ['AFFAIRES_BANK'],'PANTHEON_O2_DOCUMENTAIRES_MARKER',['vault:Workspace','folder:Affaires'])
d_cross=recall(os.environ['DOCUMENTAIRES_BANK'],'PANTHEON_O2_AFFAIRES_MARKER',['vault:Workspace','folder:Documentaires'])

aa=items(a); dd=items(d); ax=items(a_cross); dx=items(d_cross)
assert any(x.get('document_id')=='Workspace/Affaires/Verger/CR/CR03.md' for x in aa), a
assert any((x.get('metadata') or {}).get('path')=='Affaires/Verger/CR/CR03.md' for x in aa), a
assert all(x.get('document_id','').startswith('Workspace/Affaires/') for x in aa), aa
assert any(x.get('document_id')=='Workspace/Documentaires/Technique/bardage.md' for x in dd), d
assert any((x.get('metadata') or {}).get('path')=='Documentaires/Technique/bardage.md' for x in dd), d
assert all(x.get('document_id','').startswith('Workspace/Documentaires/') for x in dd), dd
assert not any('PANTHEON_O2_DOCUMENTAIRES_MARKER' in str(x.get('text','')) for x in ax), ax
assert not any('PANTHEON_O2_AFFAIRES_MARKER' in str(x.get('text','')) for x in dx), dx

ia=json.loads(Path(os.environ['AFFAIRES_INDEX']).read_text())
idoc=json.loads(Path(os.environ['DOCUMENTAIRES_INDEX']).read_text())
assert set(ia.get('syncIndex',{}))=={'Affaires/Verger/CR/CR03.md'}, ia
assert set(idoc.get('syncIndex',{}))=={'Documentaires/Technique/bardage.md'}, idoc
(out/'workspace-routing-before-delete.json').write_text(json.dumps({'affaires':a,'documentaires':d},indent=2,ensure_ascii=False))
PY

# Pruning one routed scope must not delete or mutate the other bank/index.
rm "$VAULT/Affaires/Verger/CR/CR03.md"
run_route "$AFFAIRES_BANK" Affaires "$AFFAIRES_INDEX" "$ARTIFACTS/routing-affaires-delete.txt"
grep -F 'reconcile: +0 added, ~0 updated, -1 deleted, =0 unchanged' "$ARTIFACTS/routing-affaires-delete.txt"
run_route "$DOCUMENTAIRES_BANK" Documentaires "$DOCUMENTAIRES_INDEX" "$ARTIFACTS/routing-documentaires-after-affaires-delete.txt"
grep -F 'reconcile: +0 added, ~0 updated, -0 deleted, =1 unchanged' "$ARTIFACTS/routing-documentaires-after-affaires-delete.txt"

python - <<'PY'
import json, os, urllib.request
from pathlib import Path

base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
def recall(bank, query, tags):
    url=f"{base}/v1/default/banks/{bank}/memories/recall"
    body={'query':query,'types':['world','experience'],'tags':tags,'tags_match':'all_strict'}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as resp:
        return json.loads(resp.read().decode())

a=recall(os.environ['AFFAIRES_BANK'],'PANTHEON_O2_AFFAIRES_MARKER',['vault:Workspace','folder:Affaires'])
d=recall(os.environ['DOCUMENTAIRES_BANK'],'PANTHEON_O2_DOCUMENTAIRES_MARKER',['vault:Workspace','folder:Documentaires'])
assert not any('PANTHEON_O2_AFFAIRES_MARKER' in str(x.get('text','')) for x in a.get('results',[]) if isinstance(x,dict)), a
assert any('PANTHEON_O2_DOCUMENTAIRES_MARKER' in str(x.get('text','')) for x in d.get('results',[]) if isinstance(x,dict)), d
ia=json.loads(Path(os.environ['AFFAIRES_INDEX']).read_text())
idoc=json.loads(Path(os.environ['DOCUMENTAIRES_INDEX']).read_text())
assert set(ia.get('syncIndex',{}))==set(), ia
assert set(idoc.get('syncIndex',{}))=={'Documentaires/Technique/bardage.md'}, idoc
summary={
  'kind':'hindsight_obsidian_workspace_routing_o2_acceptance',
  'status':'passed',
  'one_human_vault_verified':True,
  'affaires_folder_to_projects_bank_verified':True,
  'documentaires_folder_to_reference_bank_verified':True,
  'separate_indexes_verified':True,
  'cross_bank_leakage_not_observed':True,
  'independent_prune_verified':True,
  'synthetic_neutral_bank_ids_used':True,
  'real_vaults_changed':False,
  'pantheon_state_mutated':False,
  'evidence_admitted':False,
}
Path(os.environ['ARTIFACTS']).joinpath('workspace-routing-acceptance-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
PY

cat "$ARTIFACTS/workspace-routing-acceptance-summary.json"
