# UHP ↔ Hermes execution-transport qualification

Status: qualification lab for Pantheon issue Pantheon-Next#1141. Not installed, activated, adopted or wired into any product/runtime path.

## Objective

Measure whether UHP can replace meaningful Hermes-specific **external transport** plumbing while preserving Pantheon's existing admission, scoped-context, provenance and effect boundaries.

```text
paired immutable execution basis
        |
        +--> admission A -> native Hermes Runs binding -> Hermes
        |
        `--> admission B -> external UHP client -> UHP server -> Hermes
```

`admission A` and `admission B` MUST be distinct. They MUST bind the same Task Contract, Context Pack and execution-basis digest. One Pantheon Execution Admission is consumable once and is never reused to manufacture an A/B test.

## Current pins

Revalidate before a live run:

```text
Pantheon-Next baseline at lab creation:
  80e2b4458d001b38d941aa64ffda23db7f5d3a2b

HarnessRouter/harnessrouter:
  7d0fa14bf70e81a2226d232bc519e729d32793d3

UHP normative version:
  2026-09-28

initial characterized UHP evidence:
  2026-09-12 / HarnessRouter CE 0.25.6 / 76 pass, 0 fail
```

The 2026-09-28 protocol adds surfaces beyond the selected Pantheon need. This lab still starts with UHP Core and uses Extended only for demonstrated file/artifact tests. UHP Full lifecycle management is not a target.

## Authority

```text
lab receipt != Evidence
lab task accepted != Pantheon authorization
UHP session != Pantheon memory
UHP file != Source admission
UHP artifact != professional Source
runtime tool available != effect authorized
successful execution != authorization
```

The lab does not create a scheduler, queue, provider router, memory owner, Evidence owner, Source owner or effect authority. The Pantheon-owned consequential-effect PEP remains outside Hermes/UHP.

## Test cases

### T1 — matched read-only execution

Run the same synthetic prompt/context through paired admissions with the same immutable basis digest. Compare runtime identity, profile/model identity, exactly-once submission, result status and return reconciliation.

### T2 — host-level admission correlation

Prove the candidate path can bind the exact Pantheon admission to Hermes host task/session context without relying on prompt text, model-visible instructions or an arbitrary echoed metadata field.

```text
client metadata echo != host-level admission correlation
```

If this cannot be proven, the UHP path cannot fully replace the native binding.

### T3 — effective tool surface

Compare the concrete Hermes tool surface. A configured UHP `disabledTools` value is not accepted as proof of a hard block when the underlying runtime only receives a standing instruction.

### T4 — streaming / reconnect / cancellation

Exercise monotonic stream sequence numbers, terminal events, response re-read after disconnect, explicit cancellation and partial-output preservation.

### T5 — ambiguous submission / idempotency

Exercise a dropped/ambiguous submit. No second execution may be started. A candidate claiming safe retry must prove the exact UHP idempotency behavior on the tested server.

### T6 — transient source file (Pantheon-Next#1125)

Use the deterministic synthetic EML fixture. Record exact SHA-256, immutable basis binding, bounded lifetime, fail-closed expiry/loss and absence of AFFAIRES/Hindsight/Source persistence.

UHP file transport alone does not satisfy this case.

### T7 — artifact

Produce a deterministic artifact, download its raw bytes, hash them and verify that the result remains candidate material only: no automatic Source, Knowledge or Evidence promotion.

### T8 — deletion measurement

List the native Hermes-specific components that become deletable if UHP is selected, and separately list runtime-specific components that must remain.

```text
UHP added + native plumbing unchanged = reject
real deletion + retained necessary runtime seam = partial_transport_only
complete transport replacement with all boundaries preserved = replace_native_binding
```

## Observation contract

`qualification.py` consumes one native observation and one UHP observation. Comparability requires:

- same `case_id`;
- same Task Contract ref;
- same Context Pack ref;
- same immutable execution-basis digest;
- different one-shot admission IDs;
- matching Hermes/profile/model identities when they are known.

Unknown safety/provenance observations never become inferred passes.

## Decision vocabulary

```text
replace_native_binding
partial_transport_only
watch
reject
inconclusive
```

`inconclusive` is an intermediate lab result, not a final Pantheon-Next#1141 posture.

## Utilities

Build deterministic non-sensitive fixtures:

```bash
python implementation/labs/uhp_hermes_transport/build_fixtures.py /tmp/pantheon-uhp-1141
```

Compare two normalized observations:

```bash
python implementation/labs/uhp_hermes_transport/qualification.py native.json uhp.json
```

`uhp_client.py` is an operator/lab HTTP client for UHP discovery, task, stream, cancellation, file and artifact surfaces. It is not imported by product code.

## Removal test

Removing this directory and `implementation/tests/test_uhp_hermes_transport_lab.py` restores prior product behavior completely. No `mvp_vertical` module imports this lab.
