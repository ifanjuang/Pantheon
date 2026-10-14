# Import provenance

`implementation/` is the history-preserving import of the former
`ifanjuang/pantheon-mvp` repository.

- source repository: `ifanjuang/pantheon-mvp`
- source cutoff: `d960862dd0e23b7003a0f3e4ee0ea630ffc12af9`
- import method: `git filter-repo --to-subdirectory-filter implementation`
- semantic intent: repository co-location only; no transfer of governance authority

The former repository remains the historical reference for its original
pull requests, issues and commit identifiers. Runtime success, projection,
persistence or schema conformance do not by themselves grant authorization,
Evidence status or governed identity.

## Retirement audit — 2026-08-31

The former repository's `main` still equals the imported cutoff above. A retirement
audit against `Pantheon-Next/main@3ffc583ac4232552aca9c34fa1407c11f388a59c`
confirmed that the historical divergent branch families do not constitute a second
active implementation trajectory: their material responsibilities are represented
by current monorepo owners or have been explicitly superseded/consolidated.

The audit covered Decision Requests, Professional Document revision/admission/
comparison/currentness/inbox/impact paths, ProjectClaim candidates, storage
retention, Project Anatomy projections, APU cross-family behavior, EntityRelation
migration coverage and Cockpit/Tool projection convergence.

Historical Git divergence is retained as provenance; it is not interpreted as
current implementation authority. The audit was semantic/owner-based rather than a
claim that every historical branch commit has a byte-identical successor SHA.

All formerly open issues were reconciled on 2026-08-31:

- former #94: completed in the monorepo Cockpit path and closed;
- former Pantheon-Next#165: residual Knowledge mobile/offline work moved to `Pantheon-Next#906`;
- former Pantheon-Next#227: real-environment Hermes/NAS qualification superseded by `Pantheon-Next#644` under `Pantheon-Next#607`;
- former Pantheon-Next#338: non-project solicitation closed and locked.

## Working-tree trace cleanup — 2026-09-20

The imported repository originally carried a local `ai_logs/` trace corpus and
the July `ADOPTION_REVIEW.md` snapshot. After monorepo convergence, current
implementation docs, tests and owner contracts no longer consume those files.
They were removed from the working tree under Pantheon-Next#1091 cleanup rather than kept as
a second historical record beside Git and the current owners. The public
Pantheon repository starts without them; provenance lives in the private Pantheon-Next archive.

The original contents remain recoverable from Git history and the former
repository lineage. Their removal changes no implementation status, adoption
state, Evidence status or authority.

```text
imported trace != current owner
historical review != current adoption status
Git history = archive
```

The standalone repository README now marks it as historical provenance only and
forbids new implementation work. The repository is therefore eligible for the
GitHub archive setting while remaining useful for original PR/issue URLs and
original commit identifiers.

```text
retired repository != deleted provenance
historical branch != active owner
archived repository != authority transfer
```

The standalone repository README now marks it as historical provenance only and
forbids new implementation work. The repository is therefore eligible for the
GitHub archive setting while remaining useful for original PR/issue URLs and
original commit identifiers.

```text
retired repository != deleted provenance
historical branch != active owner
archived repository != authority transfer
```
