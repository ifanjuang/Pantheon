# GitHub requirements

This directory contains Python dependency files used by GitHub Actions only.

## Governance CI

```text
governance-ci.in       direct dependency intent
governance-ci.lock.txt resolved dependency set
governance-ci.txt      stable workflow entry point delegating to the lockfile
```

The Governance CI workflow keeps using `governance-ci.txt` as a stable path. That file delegates to `governance-ci.lock.txt`.

The `.in` file records the direct packages expected by the checks. The lockfile records the direct and transitive packages currently accepted for CI reproducibility.

This is CI support. It is not Pantheon doctrine, runtime configuration, schema, test data, approval logic or memory behavior.

## Maintenance rule

Update `governance-ci.in` only when the direct CI dependency intent changes.

Update `governance-ci.lock.txt` in the same PR when the resolved dependency set changes.

Keep `governance-ci.txt` as a stable wrapper unless the workflow path is deliberately changed.

Do not move these dependencies into `pyproject.toml` unless the repository adopts a broader Python packaging policy.

Do not replace this with a hash-locked file unless a dedicated supply-chain hardening decision is made.
