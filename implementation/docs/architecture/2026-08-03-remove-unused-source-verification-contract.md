# Removal of the Unused Source Verification Contract

Status: proposed evidence-based removal record.

Date: 2026-08-03.

## Removed surface

```text
mvp_vertical/source_verification.py
tests/test_source_verification.py
```

## Usage evidence

The cross-repository module usage inventory classified `mvp_vertical.source_verification` as `test_only`:

- no non-test Python importer;
- no API route;
- no application composition reference;
- no entrypoint;
- no dynamic import;
- no configuration or workflow reference;
- no active governance owner or contract reference found in Pantheon-Next;
- its only consumer was `tests/test_source_verification.py`.

Repository searches for the contract names and its source-aligned verification vocabulary returned no additional active consumer or governed owner.

## Why removal is preferable to retention

The module defined a complete candidate observation model that had never been connected to the document compilation, observation, Evidence or Cockpit flows. Retaining it would preserve an alternative semantic contract beside the active document and observation models without an implementation owner.

```text
implemented in isolation != adopted contract
tested in isolation != runtime usage
available model != governed owner
```

The removal does not weaken an active source-verification path because no such path consumed this module.

## Recovery

The deleted implementation and tests remain recoverable from Git history. A future source-aligned verification capability must start from a governed contract and a real consumer rather than restoring this module merely because it existed.

## Non-goals

This change does not remove source provenance, exact capture hashes, document observations, Evidence candidates, professional review or any active verification gate.
