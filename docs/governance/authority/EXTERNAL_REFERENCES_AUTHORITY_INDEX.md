# Pantheon Next — External References Authority Index

Status: candidate support map — populated (external-references migration group); awaiting review.

This sub-index carries the external-reference rows migrated out of the Current authority map of `docs/governance/AUTHORITY_INDEX.md`, per `docs/governance/AUTHORITY_INDEX_DECOMPOSITION_PLAN.md` (PR D).

It does not override the authority vocabulary, promotion rule, placement test, tool naming rule, terminology boundary rule or sensitive-path guardrail of `docs/governance/AUTHORITY_INDEX.md`. The master index defines how to read authority; this file only lists where documents sit. External reference remains non-authoritative unless distilled into doctrine elsewhere.

## External references map

| Path or area | Authority class | Repo state | Notes |
|---|---|---|---|
| `docs/governance/reference_reviews/` | external reference / support review | to verify | Tool and ecosystem reviews (grouped row). They do not become doctrine unless distilled. |
| `docs/governance/SPICE_REFERENCE_DISTILLATION.md` | external reference / support review | documented non-implemented | Distills useful Spice decision-layer patterns while refusing Spice as Pantheon core, approval engine, memory engine, Hermes default orchestrator or source of truth. |
| `docs/domain-packs/architecture/PROJECT_UNDERSTANDING_EXTERNAL_REFERENCES.md` | external reference | documented non-implemented | Candidate-only register of external standards, libraries, tools, datasets and research that may inspire Architecture Project Understanding adapters/examples/benchmarks. Non-canonical; no runtime, schema or dependency. |

The grouped row `docs/governance/reference_reviews/` migrated here once the read-only coverage check (`.github/scripts/check_index_coverage.py`) was extended to compute grouped-row coverage from the master index and its registered sub-indexes.

## Boundary

This file moves rows; it decides nothing. Authority classes and repo states are copied verbatim from the master index at migration time. Any class change routes through its own reviewed PR against the master index rules.
