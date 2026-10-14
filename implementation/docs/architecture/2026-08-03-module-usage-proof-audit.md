# Python Module Usage Proof Audit

Status: implemented report-only audit record.

Date: 2026-08-03.

## Purpose

Architecture convergence now has zero active generation-named artifacts and zero internal versioned routes. The next task is to prove which implementation modules are actually consumed before removing anything.

The existing broad architecture inventory could report false orphan candidates because it did not resolve relative imports against the importing package. Examples include:

```text
from . import agency_directory
from .app_lifecycle import install_post_start_initializer
```

These imports are active usage and must not be treated as absence of a consumer.

## New report

`tools/audit_module_usage.py` produces:

```text
PANTHEON_MODULE_USAGE.json
PANTHEON_MODULE_USAGE.md
```

For each Python module, the report records:

- absolute local imports resolved from relative syntax;
- non-test importers;
- test-only importers;
- route declarations;
- `__main__` or setup entrypoint posture;
- dynamic module references;
- non-historical configuration references;
- parse errors;
- a bounded usage state.

Usage states include:

```text
active_entrypoint
active_imported
active_dynamic_or_configured
package_initializer
test_only
candidate_unreferenced
history
reference
migration
parse_error
```

## Removal rule

`candidate_unreferenced` is not deletion authorization.

A removal requires all of the following:

1. no non-test Python importer;
2. no route, main or package entrypoint;
3. no dynamic or configuration reference;
4. no deployment/runtime reference found by human review;
5. no governed owner requiring the implementation;
6. full CI after removal;
7. explicit human review of the PR.

```text
static usage evidence != runtime deployment proof
candidate_unreferenced != deletion authorization
CI success != semantic or operational authority
```

## CI posture

The usage report is published beside the architecture inventory and uploaded as an artifact. It is report-only in this tranche. It does not fail CI merely because candidates exist and does not remove modules automatically.

## Next step

After this audit lands, its artifact will be inspected on the current `main` branches. Only modules that remain unreferenced after deployment and runtime review may enter a separate deletion PR.
