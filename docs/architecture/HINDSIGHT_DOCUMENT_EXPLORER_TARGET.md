# Hindsight document explorer target

Status: selected architecture target for Pantheon-Next#659 / Pantheon-Next#660.

## Objective

Reduce the AFFAIRES document path to one professional source tree, one technical producer,
one derived Hindsight document index/memory layer and optional user interfaces.

```text
NAS / AFFAIRES
      |
      v
AFFAIRES producer
- startup scan
- watcher + periodic reconcile
- exclusions
- technical occurrence identity
- source hash / path / sync state
      |
      v
Hindsight
- retained document
- metadata
- tags
- chunks
- memories
      |
      +----> Hermes
      |
      +----> Cockpit (optional explorer)
```

The Cockpit is not a document owner. Productive deployment runs the AFFAIRES
producer as a separate process/service. Turning the Cockpit off must not stop
AFFAIRES scanning, Hindsight synchronization or Hermes retrieval.

## Ownership

```text
NAS / AFFAIRES
= durable professional source files

producer + technical SQLite
= synchronization mechanics only

SQLite loss
= index can be rebuilt, but a previously generated technical occurrence id is
  not claimed to be recoverable across a prior move unless another durable
  declaration preserves that continuity

Hindsight
= derived document index, classification/retrieval metadata and memory

Hermes
= conversational consumer

Cockpit
= optional visual explorer and NAS/Hindsight health inspector
```

Preserve:

```text
retrieved != truth
memory != Evidence
metadata != professional validation
path/folder != governed identity
sync success != authorization
```

## Cartouches

A Markdown cartouche is optional enrichment, not an admission gate.

Supported source files without a cartouche are eligible for the normal Hindsight source
route. A cartouche may still carry explicit human context or a declared stable identity
when such context is useful, but the system must not require one beside every source.

No automatic summary or inferred revision relation becomes a source claim.

## Technical document identity

For a source without a declared cartouche `document_id`, the producer assigns a technical
occurrence identity and persists only the reconstructible mapping needed for synchronization.

The identity is neither the path nor the SHA-256:

```text
path != identity
hash != identity
```

Move handling is deliberately conservative:

- exact current path reuses its technical identity;
- when the old path disappeared and exactly one prior occurrence has the same source hash,
  the identity may follow that move;
- a simultaneous identical copy receives a separate identity;
- ambiguous matching does not silently merge occurrences.

This technical identity is a synchronization key, not governed professional identity.

## SQLite boundary

SQLite may keep only technical/reconstructible state such as:

```text
document_id
workspace
current source path
source sha256
Hindsight document id
operation/sync status
last error
timestamps
```

Business descriptions, summaries, professional status and semantic memory must not depend
on this database.

## Cockpit boundary

Cockpit has two optional read projections.

### Hindsight explorer

Display Hindsight-backed document information such as tags, metadata, derived memory and
synchronization status.

### NAS health inspector

Compare the current indexed NAS projection with Hindsight synchronization state:

```text
NAS present + Hindsight present
= synchronized candidate

NAS present + no Hindsight state
= not retained / pending / ineligible

NAS present + Hindsight error
= ingestion failure to inspect

NAS absent + Hindsight retained state
= first observation quarantines derived state from active recall
= second observation deletes the exact derived Hindsight document
```

This lifecycle runs only while the source workspace is available and includes a
mass-disappearance circuit breaker. It never deletes the NAS source.

Cockpit may expose an **Open file** action. The browser must never supply an arbitrary
filesystem path that is trusted directly. The server resolves only a source that already
exists in the current indexed projection, then revalidates that the resolved file is a
regular non-symlink below the admitted AFFAIRES root before serving it.

```text
browser path claim
-> indexed projection match
-> admitted root lookup
-> strict resolve
-> root containment check
-> regular non-symlink file
-> open
```

Hindsight `source_path` metadata is provenance only and is never authorization to read a
NAS path.

## Producer rule

There remains exactly one AFFAIRES filesystem producer. In productive deployment
it is the standalone `workspace-producer` / `pantheon-affaires-producer.service`.
Cockpit runs in persisted-projection mode and must not scan the NAS recursively,
own the watcher or write to Hindsight.

Watcher provides responsiveness. Periodic reconcile remains the convergence guarantee.

## Open items

Live-node qualification remains required for:

- real NAS move/event ordering;
- restart and network outage recovery;
- one-active-producer proof;
- Hindsight persistence/restore;
- bank/project isolation regression;
- live quarantine/delete behavior against the productive bank, including recovery
  after transient source disappearance.

Those operational qualifications do not justify reintroducing Cockpit ownership or
mandatory cartouches.
