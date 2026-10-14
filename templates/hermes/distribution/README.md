# Hermes Distribution Lock

Status: template-only composition contract — no installer, runtime or authority.

This directory defines how an operator may record one reproducible composition of Pantheon artifacts for an external Hermes installation.

```text
distribution-lock.schema.yaml   validation contract
distribution-lock.example.yaml  fictional revision 3 example only
```

## Current contract

Revision 3 is the only accepted contract and reflects the Pantheon monorepo topology:

```text
one reviewed Pantheon repository pin
        +
monorepo-relative component paths
        +
exact component content digests
        +
exact external Hermes runtime target
```

A component path identifies where bytes live. It does not define semantic ownership, runtime authority or governed identity. Ownership remains governed elsewhere.

Revision 2 was a temporary migration bridge used while the active lock and the independently pinned Architecture Audit authority moved to revision 3. That bridge is closed: revision 2 locks, `pantheon_mvp` source pins and per-component `source_repository` fields are rejected by the current schema.

The lock records:

- one reviewed `Pantheon-Next` repository revision;
- an exact external Hermes runtime version target;
- the installed Hermes artifact digest when it has actually been observed;
- independently reviewable monorepo-relative component paths and exact content digests;
- which components are required or optional;
- the abstract capabilities each component exposes;
- the acceptance checks required for the composition;
- factual installation and acceptance observations.

Repository refs provide review provenance. They are not sufficient to identify a composition stored inside that repository because the final commit cannot contain its own future SHA. Exact component identity is therefore established by `content_digest`.

Revision 3 deliberately does not repeat a repository or zone identity on every component. All Pantheon component paths resolve from the single reviewed `pantheon_repository` root. A folder or zone is not an authority identity.

It does not merge the components into a new runtime or authority layer.

```text
composition pinned != components installed
components installed != binding activated
acceptance passed != task authorized
runtime success != accepted result
runtime output != Evidence
```

## Digest contract

Every declared component has a `digest_mode` and `content_digest`.

For `digest_mode: file`:

```text
sha256(raw file bytes)
```

For `digest_mode: tree`:

1. reject symbolic links anywhere below the selected tree;
2. enumerate regular source files recursively;
3. exclude ephemeral or repository-control paths:

```text
.git/
__pycache__/
*.pyc
*.pyo
.DS_Store
```

4. sort retained paths by their POSIX relative path;
5. compute the SHA-256 hexadecimal digest of each retained file's raw bytes;
6. append one UTF-8 record per retained file:

```text
<relative-path>\0<file-sha256-hex>\n
```

7. compute SHA-256 over the concatenated records.

The exclusion list is closed and implementation-independent. It removes generated metadata that can appear after checkout or test execution without changing the selected source. Other files remain covered.

The digest covers source content only. It does not indicate installation, compatibility, safety, activation or task authorization.

## Runtime artifact

`source_pins.hermes_runtime.version` is an exact version, not a range or wildcard. `artifact_digest` remains `null` while the lock is only a candidate. A lock marked `observed` or `qualified` must contain the SHA-256 digest of the runtime artifact actually observed by the operator.

```text
reviewed runtime version != installed runtime
artifact observed != binding activated
```

## Operator runbook

Use the focused manual procedure:

```text
docs/install/HERMES_EXECUTION_BRIDGE_RUNBOOK.md
```

The runbook covers revision 3 distribution verification, context-bridge installation, runtime observation, one-shot launch and reconciliation, real host correlation checks, trace capture and rollback. It performs no automatic installation or activation.

## Ownership

`Pantheon-Next` owns this declarative template contract. The candidate operational lock is currently co-located under `implementation/hermes/distribution/`; an external operator may keep a deployment-specific lock outside the repository.

Each component retains its own governed owner and lifecycle independently of this composition record. A dashboard update does not require treating the run binding as changed, and a skill may remain absent even when the required execution bridge is installed.

## Validation

A consumer should validate the lock against the schema, resolve every declared path inside the reviewed Pantheon repository root, verify every content digest, verify route and plugin contracts, and run one composed read-only acceptance scenario.

A check result is a technical observation only. Human activation and per-task admission remain separate decisions.
