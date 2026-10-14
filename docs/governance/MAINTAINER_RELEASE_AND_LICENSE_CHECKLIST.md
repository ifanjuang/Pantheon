# Maintainer release and licence checklist

Status: validation-only / maintainer checklist.
Boundary profile: validation_only_trace.

Related issues:

```text
Pantheon-Next#261 — post-consolidation git tags
Pantheon-Next#262 — PDF licence qualification and optional history purge
Pantheon-Next#264 — out-of-repo handoff
```

This document records maintainer actions that are outside the assistant connector and outside Pantheon runtime scope.

It does not implement a runtime, release system, legal decision, history rewrite, approval engine, memory engine, scheduler, queue, provider router or external action.

## 1. Version tag checklist

The repository root is not a Python distribution. Its authoritative current
package/checkpoint marker and mirrors are:

```text
VERSION
CHANGELOG.md head
mcp-server/pyproject.toml project.version
installed pantheon-mcp-server metadata
```

CI checks these markers, builds the MCP wheel, installs it in a clean
environment and compares runtime `__version__` with installed metadata.

Changelog headings are repository checkpoints. They do not claim a GitHub
release exists. A tag is a publication event and is optional; when published it
must be named `v<VERSION>` and target a commit whose markers agree. The
2026-07-15 verification found no repository tags, so checkpoints through
`0.1.61` are explicitly unreleased.

Before publishing a future tag, verify:

```text
git fetch origin --tags
git checkout main
git pull --ff-only
python3 .github/scripts/check_packaging_contract.py
python3 -m build mcp-server --outdir dist
git tag -a v0.1.61 <verified-commit> -m "v0.1.61"
git push origin v0.1.61
```

Replace the example version with the current `VERSION`. Do not backfill a tag
onto an arbitrary commit and do not describe an untagged checkpoint as released.

## 2. PDF licence qualification checklist

Current stance:

```text
base_metier/architecte/ = external professional corpus / to verify
not authority
not proof
not vertical-slice grounding material
source PDFs out of current git tree
manifest retained for provenance/integrity only
```

Decision required for each source family:

```text
source name:
source owner:
original URL or acquisition path:
licence / terms found:
redistribution allowed: yes / no / unclear
private internal use allowed: yes / no / unclear
derivative text extraction allowed: yes / no / unclear
can remain referenced in manifest: yes / no / unclear
can ground examples or vertical slices: yes / no
maintainer decision:
decision date:
```

Default until cleared:

```text
MAF professional material: treat as not redistributable without written authorization.
Ordre des Architectes publications: verify terms before redistribution.
Official legal texts: lower risk, but reproduction conditions still need verification.
Unknown-origin PDFs: do not redistribute and do not ground examples.
```

## 3. Optional history purge decision

A current-tree deletion is not a history purge.

Run a history rewrite only after maintainer/legal decision and team coordination.

Decision options:

```text
A. No purge: accept history risk and keep repo as-is.
B. Purge PDFs only: remove base_metier/**/*.pdf from all history.
C. New clean repository: archive old repo and continue in a clean successor.
```

If purge is required:

```bash
# Fresh mirror clone.
git clone --mirror git@github.com:ifanjuang/Pantheon.git Pantheon.git
cd Pantheon-Next.git

git filter-repo \
  --path-glob 'base_metier/**/*.pdf' \
  --invert-paths

git push --force --mirror
```

Operational warnings:

```text
Do not run during active PR work.
Notify collaborators before and after rewrite.
Existing clones should be recloned or carefully reset.
Old PR references and tags may require attention.
CI caches may need clearing.
GitHub Pages may need rebuild verification.
```

## 4. Closure criteria

Issue Pantheon-Next#261 can close when:

```text
required tags exist on origin
version files and tag targets are verified
```

Issue Pantheon-Next#262 can close when:

```text
licence decision is recorded
history purge decision is recorded
any chosen purge is completed or explicitly refused
base_metier remains excluded from vertical-slice grounding until cleared
```

Issue Pantheon-Next#264 can close when:

```text
Pantheon-Next#261 is closed
Pantheon-Next#262 is closed
Pantheon-Next#273 has either completed the first external run or recorded why it is deferred
```

The validated remains.
