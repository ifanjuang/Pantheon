# Anti-pattern: Conductor as Zeus

Status: reference — implemented as documentation.

A runtime conductor may coordinate execution.

It is not ZEUS.

## Symptom

A runtime orchestrator selects workers, routes tasks or reports completion, then its coordination status is treated as procedural arbitration.

## Pantheon rule

```text
Conductor coordinates execution.
ZEUS arbitrates status and procedure under governance.
```

## Correction

Require:

- Task Contract boundary;
- Evidence Pack or review note;
- approval status;
- unresolved tension record;
- User Decision Gate when procedure is insufficient.

## Final rule

```text
Runtime coordination is not governance arbitration.
```
