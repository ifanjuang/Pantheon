# Maintainer Actions

Status: validation-only / maintainer-only operational checklist.
Boundary profile: validation_only_trace.

Date: 2026-07-01

This document records actions that cannot be completed safely by the assistant connector.

It does not create doctrine, approve a merge, rewrite history, create a tag, determine licence rights, execute Hermes, create runtime behavior, create a scheduler, create a queue, approve external actions or promote memory.

## Why this exists

After the B-1 to B-8 cleanup sequence, three actions remain maintainer-side:

```text
1. Git tags for the current version line.
2. Optional history purge for removed PDF binaries.
3. Final licence determination for MAF / Ordre / professional-source PDFs.
```

The current connector can update repository files, comments and planning documents, but it cannot push git tags, run destructive history rewrite commands or make a legal/licence determination.

## A. Tags

Current intended invariant:

```text
VERSION = CHANGELOG head = git tag
```

Known merge references:

```text
v0.1.59 target: e45f37276f0ee2153909efd660ac4d4fa1720001
  Pantheon-Next#250 — chore: realign VERSION with CHANGELOG head (B-7)

current post-cleanup head to consider for next tag:
  after Pantheon-Next#251 to Pantheon-Next#255 and Pantheon-Next#218, verify current main before tagging.
```

Recommended maintainer action:

```bash
git fetch origin --tags
git checkout main
git pull --ff-only

git tag -a v0.1.59 e45f37276f0ee2153909efd660ac4d4fa1720001 -m "v0.1.59"
git push origin v0.1.59
```

If the repository has advanced beyond `0.1.59`, create a later tag only after verifying that:

```text
VERSION
CHANGELOG.md head
pyproject.toml project.version
mcp-server/pyproject.toml project.version
```

all intentionally agree.

Do not create a new tag if those files diverge.

## B. Optional PDF history purge

Pantheon-Next#255 removed the source PDFs from the current tree and added:

```text
base_metier/**/*.pdf
```

to `.gitignore`.

It did not purge the PDFs from git history.

This matters because the removed files include MAF / Ordre / professional-source PDFs whose redistribution rights are not yet determined.

Recommended only if the maintainer decides the history must be purged:

```bash
# Work from a fresh mirror clone.
git clone --mirror git@github.com:ifanjuang/Pantheon.git Pantheon.git
cd Pantheon-Next.git

# Requires git-filter-repo.
git filter-repo \
  --path-glob 'base_metier/**/*.pdf' \
  --invert-paths

# Destructive history rewrite.
git push --force --mirror
```

After a history rewrite:

```text
existing local clones should be recloned or carefully reset;
old PR references may point to unreachable objects;
old tags may need recreation;
CI caches may need clearing;
collaborators must be notified before and after rewrite.
```

Do not run this during active PR work.

## C. Licence determination

Current repository stance after Pantheon-Next#255:

```text
base_metier/architecte/ = external professional corpus / to verify
not authority
not proof
not vertical-slice grounding material
source PDFs out of git current tree
manifest retained for provenance and integrity only
```

The licence decision remains with the maintainer / legal reviewer.

Recommended default posture until cleared:

```text
MAF_OUTILS_* PDFs: treat as not redistributable without written authorization.
Ordre des Architectes publications: verify terms before redistribution.
CCAG / official legal texts: lower risk, but verify reproduction conditions.
GLOSSAIRE.pdf origin: to verify.
```

For the architecture vertical slice:

```text
do not ground a proof loop on these PDFs until licence status is cleared;
prefer public official links, maintainer-owned notes or synthetic fixtures;
record any source used in an Evidence Pack Candidate;
do not promote the corpus into proof or authority.
```

## Decision state

```text
Tags: maintainer action pending.
History purge: optional, maintainer decision pending.
Licence: maintainer/legal decision pending.
Vertical slice dependency on base_metier: blocked until source status is qualified.
```

## Boundary

This checklist records actions and commands.

It does not execute them.

```text
A documented command is not an executed command.
A manifest is not a licence grant.
A removed file from current tree is not a purged history.
A tag recommendation is not a created tag.
```
