#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_WORKSPACE:?}"
: "${RUNNER_TEMP:?}"
: "${HINDSIGHT_VERSION:?}"
: "${HINDSIGHT_OBSIDIAN_VERSION:?}"
: "${HINDSIGHT_API_URL:=http://127.0.0.1:8888}"
: "${HINDSIGHT_BANK_ID:=pantheon-o2-synthetic}"

OBSIDIAN_ROOT="$GITHUB_WORKSPACE/hindsight-obsidian"
LAB_ROOT="$RUNNER_TEMP/hindsight-obsidian-o2"
ARTIFACTS="$LAB_ROOT/artifacts"
VAULT_A="$LAB_ROOT/Vault-A"
VAULT_B="$LAB_ROOT/Vault-B"
INDEX_A="$LAB_ROOT/index-vault-a.json"
INDEX_B="$LAB_ROOT/index-vault-b.json"
CLI="$OBSIDIAN_ROOT/dist/cli.js"

export ARTIFACTS HINDSIGHT_API_URL HINDSIGHT_BANK_ID HINDSIGHT_VERSION HINDSIGHT_OBSIDIAN_VERSION INDEX_A INDEX_B VAULT_A VAULT_B
mkdir -p "$ARTIFACTS" "$VAULT_A/Projects/Alpha" "$VAULT_A/Projects/Beta" "$VAULT_B/Projects/Alpha"

cat > "$VAULT_A/Projects/Alpha/note.md" <<'EOF'
---
tags: [chantier, alpha]
aliases: [Alpha source]
created: 2026-08-08
---
PANTHEON_O2_ALPHA_MARKER. Alpha belongs only to Vault-A / Projects/Alpha.
EOF
cat > "$VAULT_A/Projects/Beta/note.md" <<'EOF'
---
tags: [chantier, beta]
created: 2026-08-08
---
PANTHEON_O2_BETA_MARKER. Beta will be deleted during reconcile.
EOF
cat > "$VAULT_B/Projects/Alpha/note.md" <<'EOF'
---
tags: [reference, alpha]
created: 2026-08-08
---
PANTHEON_O2_VAULT_B_MARKER. This similarly named note belongs only to Vault-B.
EOF

run_sync() {
  local vault="$1" vault_name="$2" index="$3" output="$4"
  node "$CLI" reconcile \
    --vault "$vault" \
    --vault-name "$vault_name" \
    --bank "$HINDSIGHT_BANK_ID" \
    --api-url "$HINDSIGHT_API_URL" \
    --prefix-doc-id \
    --index "$index" \
    | tee "$output"
}

# The official client intentionally submits retains with async=true. A completed
# CLI reconcile therefore means the retain was accepted, not necessarily that
# the background worker has materialized the document. Poll recall before any
# dependent delete/rename assertion so the lab tests semantics rather than a
# scheduler race.
wait_for_marker() {
  local marker="$1" vault_tag="$2" folder_tag="$3"
  MARKER="$marker" VAULT_TAG="$vault_tag" FOLDER_TAG="$folder_tag" python - <<'PY'
import json, os, time, urllib.error, urllib.request

base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
bank=os.environ['HINDSIGHT_BANK_ID']
marker=os.environ['MARKER']
tags=[os.environ['VAULT_TAG'], os.environ['FOLDER_TAG']]
url=f"{base}/v1/default/banks/{bank}/memories/recall"
last=None
for _ in range(120):
    body={'query': marker, 'types':['world','experience'], 'tags':tags, 'tags_match':'all_strict'}
    req=urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            last=json.loads(resp.read().decode())
        items=last.get('results', []) if isinstance(last, dict) else []
        if any(marker in str(x.get('text','')) for x in items if isinstance(x, dict)):
            raise SystemExit(0)
    except urllib.error.HTTPError as exc:
        last={'http_status': exc.code, 'body': exc.read().decode(errors='replace')[:500]}
    time.sleep(0.25)
raise SystemExit(f'async retain did not materialize marker {marker}: {last!r}')
PY
}

run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/initial-a.txt"
run_sync "$VAULT_B" Vault-B "$INDEX_B" "$ARTIFACTS/initial-b.txt"
grep -F 'reconcile: +2 added, ~0 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/initial-a.txt"
grep -F 'reconcile: +1 added, ~0 updated, -0 deleted, =0 unchanged' "$ARTIFACTS/initial-b.txt"
wait_for_marker PANTHEON_O2_ALPHA_MARKER vault:Vault-A folder:Projects/Alpha
wait_for_marker PANTHEON_O2_BETA_MARKER vault:Vault-A folder:Projects/Beta
wait_for_marker PANTHEON_O2_VAULT_B_MARKER vault:Vault-B folder:Projects/Alpha

# Unchanged reconcile must not re-ingest any note.
run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/unchanged-a.txt"
run_sync "$VAULT_B" Vault-B "$INDEX_B" "$ARTIFACTS/unchanged-b.txt"
grep -F 'reconcile: +0 added, ~0 updated, -0 deleted, =2 unchanged' "$ARTIFACTS/unchanged-a.txt"
grep -F 'reconcile: +0 added, ~0 updated, -0 deleted, =1 unchanged' "$ARTIFACTS/unchanged-b.txt"

# One content edit becomes one update, with the sibling note unchanged.
printf '\nPANTHEON_O2_ALPHA_UPDATED\n' >> "$VAULT_A/Projects/Alpha/note.md"
sleep 0.02
run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/edit-a.txt"
grep -F 'reconcile: +0 added, ~1 updated, -0 deleted, =1 unchanged' "$ARTIFACTS/edit-a.txt"
wait_for_marker PANTHEON_O2_ALPHA_UPDATED vault:Vault-A folder:Projects/Alpha

# Deletion is pruned from Hindsight using only this sync engine's local index.
rm "$VAULT_A/Projects/Beta/note.md"
run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/delete-a.txt"
grep -F 'reconcile: +0 added, ~0 updated, -1 deleted, =1 unchanged' "$ARTIFACTS/delete-a.txt"

# A rename during a one-shot reconcile is observed as add(new)+prune(old), matching
# the documented CLI behavior and preserving the exact new source path.
mv "$VAULT_A/Projects/Alpha/note.md" "$VAULT_A/Projects/Alpha/renamed.md"
run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/rename-a.txt"
grep -F 'reconcile: +1 added, ~0 updated, -1 deleted, =0 unchanged' "$ARTIFACTS/rename-a.txt"
wait_for_marker PANTHEON_O2_ALPHA_MARKER vault:Vault-A folder:Projects/Alpha

# Add one realistic same-bank project-scope fixture. Projects remain folders/scopes,
# not banks. Project A contains several professional working-source types while
# Project B intentionally uses similar terminology plus one B-only fact.
mkdir -p \
  "$VAULT_A/Projects/Project-A/CR" \
  "$VAULT_A/Projects/Project-A/CCTP" \
  "$VAULT_A/Projects/Project-A/Mail" \
  "$VAULT_A/Projects/Project-B/CR" \
  "$VAULT_A/Projects/Project-B/CCTP"

cat > "$VAULT_A/Projects/Project-A/CR/CR01.md" <<'EOF'
---
tags: [chantier, compte-rendu]
created: 2026-08-01
---
PANTHEON_O2_PROJECT_A_CONTEXT. Projet A : CR01 indique que le calepinage de façade doit être repris après relevé.
EOF
cat > "$VAULT_A/Projects/Project-A/CR/CR03.md" <<'EOF'
---
tags: [chantier, compte-rendu]
created: 2026-08-15
---
PANTHEON_O2_PROJECT_A_CONTEXT. PANTHEON_O2_PROJECT_A_CR03_TARGET. Projet A : CR03 confirme la trame verticale de façade après validation du relevé.
EOF
cat > "$VAULT_A/Projects/Project-A/CCTP/facade.md" <<'EOF'
---
tags: [cctp, facade]
created: 2026-08-16
---
PANTHEON_O2_PROJECT_A_CONTEXT. Projet A : le CCTP façade prescrit la continuité de la trame verticale et les joints alignés.
EOF
cat > "$VAULT_A/Projects/Project-A/Mail/note.md" <<'EOF'
---
tags: [mail, facade]
created: 2026-08-17
---
PANTHEON_O2_PROJECT_A_CONTEXT. Projet A : note de mail rappelant de comparer le CR03 au CCTP façade avant diffusion.
EOF
cat > "$VAULT_A/Projects/Project-B/CR/CR03.md" <<'EOF'
---
tags: [chantier, compte-rendu]
created: 2026-08-15
---
PANTHEON_O2_PROJECT_B_CONTEXT. Projet B : CR03 traite aussi de trame de façade, mais la solution retenue est horizontale. PANTHEON_O2_PROJECT_B_ONLY_FACT.
EOF
cat > "$VAULT_A/Projects/Project-B/CCTP/facade.md" <<'EOF'
---
tags: [cctp, facade]
created: 2026-08-16
---
PANTHEON_O2_PROJECT_B_CONTEXT. Projet B : le CCTP façade confirme une trame horizontale. PANTHEON_O2_PROJECT_B_ONLY_FACT.
EOF

run_sync "$VAULT_A" Vault-A "$INDEX_A" "$ARTIFACTS/project-scope-ingest.txt"
grep -F 'reconcile: +6 added, ~0 updated, -0 deleted, =1 unchanged' "$ARTIFACTS/project-scope-ingest.txt"
wait_for_marker PANTHEON_O2_PROJECT_A_CR03_TARGET vault:Vault-A folder:Projects/Project-A
wait_for_marker PANTHEON_O2_PROJECT_B_ONLY_FACT vault:Vault-A folder:Projects/Project-B

# Query the real bank with strict scope tags. We verify the source anchors that
# Hindsight exposes to citations: document_id plus metadata.path. We also prove
# that a B-only answer never silently crosses the active Project-A scope.
python - <<'PY'
import json, os, urllib.request
from pathlib import Path

base=os.environ['HINDSIGHT_API_URL'].rstrip('/')
bank=os.environ['HINDSIGHT_BANK_ID']
out=Path(os.environ['ARTIFACTS'])

def recall(query, tags):
    url=f"{base}/v1/default/banks/{bank}/memories/recall"
    body={
        'query': query,
        'types': ['world','experience'],
        'tags': tags,
        'tags_match': 'all_strict',
    }
    req=urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def results(value):
    items=value.get('results', []) if isinstance(value, dict) else []
    return [x for x in items if isinstance(x, dict)]

checks={}
checks['vault_a_alpha']=recall('PANTHEON_O2_ALPHA_MARKER', ['vault:Vault-A','folder:Projects/Alpha'])
checks['vault_b_alpha']=recall('PANTHEON_O2_VAULT_B_MARKER', ['vault:Vault-B','folder:Projects/Alpha'])
checks['deleted_beta']=recall('PANTHEON_O2_BETA_MARKER', ['vault:Vault-A','folder:Projects/Beta'])
checks['project_a_cr03']=recall(
    'PANTHEON_O2_PROJECT_A_CR03_TARGET',
    ['vault:Vault-A','folder:Projects/Project-A'],
)
checks['b_only_under_a_scope']=recall(
    'PANTHEON_O2_PROJECT_B_ONLY_FACT',
    ['vault:Vault-A','folder:Projects/Project-A'],
)
checks['b_only_explicit_b_scope']=recall(
    'PANTHEON_O2_PROJECT_B_ONLY_FACT',
    ['vault:Vault-A','folder:Projects/Project-B'],
)
(out/'scoped-recall.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False))

a=results(checks['vault_a_alpha'])
b=results(checks['vault_b_alpha'])
beta=results(checks['deleted_beta'])
project_a=results(checks['project_a_cr03'])
b_under_a=results(checks['b_only_under_a_scope'])
b_explicit=results(checks['b_only_explicit_b_scope'])

assert a, checks['vault_a_alpha']
assert b, checks['vault_b_alpha']
assert any(x.get('document_id') == 'Vault-A/Projects/Alpha/renamed.md' for x in a), a
assert all(x.get('document_id','').startswith('Vault-A/') for x in a), a
assert any((x.get('metadata') or {}).get('path') == 'Projects/Alpha/renamed.md' for x in a), a
assert any('PANTHEON_O2_ALPHA_UPDATED' in str(x.get('text','')) for x in a), a
assert any(x.get('document_id') == 'Vault-B/Projects/Alpha/note.md' for x in b), b
assert all(x.get('document_id','').startswith('Vault-B/') for x in b), b
assert any((x.get('metadata') or {}).get('path') == 'Projects/Alpha/note.md' for x in b), b
assert not any('PANTHEON_O2_BETA_MARKER' in str(x.get('text','')) for x in beta), beta

# Project A targeted retrieval: exact CR03 source remains available and every
# returned source stays inside the strict active project folder.
assert project_a, checks['project_a_cr03']
assert any(
    x.get('document_id') == 'Vault-A/Projects/Project-A/CR/CR03.md'
    for x in project_a
), project_a
assert all(
    x.get('document_id','').startswith('Vault-A/Projects/Project-A/')
    for x in project_a
), project_a
assert any(
    (x.get('metadata') or {}).get('path') == 'Projects/Project-A/CR/CR03.md'
    for x in project_a
), project_a
assert not any('PANTHEON_O2_PROJECT_B_CONTEXT' in str(x.get('text','')) for x in project_a), project_a

# No silent widening: asking for a fact that exists only in Project B while
# scoped to Project A may return nothing or Project-A material, but never B.
assert all(
    x.get('document_id','').startswith('Vault-A/Projects/Project-A/')
    for x in b_under_a
), b_under_a
assert not any('PANTHEON_O2_PROJECT_B_ONLY_FACT' in str(x.get('text','')) for x in b_under_a), b_under_a
assert not any('/Projects/Project-B/' in x.get('document_id','') for x in b_under_a), b_under_a

# Widening is explicit. The same B-only query under Project-B scope must recover
# at least one B source and preserve its provenance.
assert b_explicit, checks['b_only_explicit_b_scope']
assert any('PANTHEON_O2_PROJECT_B_ONLY_FACT' in str(x.get('text','')) for x in b_explicit), b_explicit
assert all(
    x.get('document_id','').startswith('Vault-A/Projects/Project-B/')
    for x in b_explicit
), b_explicit
assert any(
    (x.get('metadata') or {}).get('path','').startswith('Projects/Project-B/')
    for x in b_explicit
), b_explicit

index_a_file=json.loads(Path(os.environ['INDEX_A']).read_text())
index_b_file=json.loads(Path(os.environ['INDEX_B']).read_text())
index_a=index_a_file.get('syncIndex', {})
index_b=index_b_file.get('syncIndex', {})
expected_a={
    'Projects/Alpha/renamed.md',
    'Projects/Project-A/CR/CR01.md',
    'Projects/Project-A/CR/CR03.md',
    'Projects/Project-A/CCTP/facade.md',
    'Projects/Project-A/Mail/note.md',
    'Projects/Project-B/CR/CR03.md',
    'Projects/Project-B/CCTP/facade.md',
}
assert set(index_a) == expected_a, index_a_file
assert set(index_b) == {'Projects/Alpha/note.md'}, index_b_file
assert index_a_file.get('lastSyncAt'), index_a_file
assert index_b_file.get('lastSyncAt'), index_b_file

summary={
    'kind':'hindsight_obsidian_o2_acceptance',
    'status':'passed',
    'official_sync_engine':True,
    'current_matrix_hindsight':os.environ['HINDSIGHT_VERSION'],
    'current_matrix_hindsight_obsidian':os.environ['HINDSIGHT_OBSIDIAN_VERSION'],
    'async_retain_materialization_waited':True,
    'create_verified':True,
    'unchanged_dedup_verified':True,
    'edit_upsert_verified':True,
    'delete_reconcile_verified':True,
    'rename_reconcile_verified':True,
    'vault_isolation_verified':True,
    'folder_isolation_verified':True,
    'strict_project_scope_verified':True,
    'no_silent_cross_project_widening_verified':True,
    'explicit_project_widening_verified':True,
    'source_document_id_verified':True,
    'source_metadata_path_verified':True,
    'separate_sync_indexes_verified':True,
    'conversation_retention':'not_used',
    'pantheon_state_mutated':False,
    'evidence_admitted':False,
}
(out/'acceptance-summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
PY

cat "$ARTIFACTS/acceptance-summary.json"
