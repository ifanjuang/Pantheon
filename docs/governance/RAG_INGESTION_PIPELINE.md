# RAG / Retrieval Ingestion Pipeline — compatibility profile

Status: reference / compatibility profile — non-authoritative; no independent doctrine ownership.
Boundary profile: documentation_only.

This retained path preserves compatibility for older links while the current responsibilities are owned elsewhere.

## Current owners

```text
source access, derivation, scope, provenance and retrieval progression
-> SOURCE_INGESTION_RETRIEVAL_MODEL.md

retrieval/context interpretation and transition toward Evidence
-> RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md

observed implementation coverage and concrete retrieval seams
-> SOURCE_RETRIEVAL_IMPLEMENTATION_COVERAGE.md

runtime/binding selection
-> HERMES_CAPABILITY_BINDINGS.md and ADAPTERS_AND_BINDINGS.md
```

## Compatible deployment profiles

These remain examples, not architecture requirements:

```text
direct bounded source/context access
co-located document retrieval candidate (for example Docling + PostgreSQL/pgvector)
qualified optional workspace/retrieval composition (for example Obsidian + Hindsight)
other replaceable binding when a demonstrated gap requires it
```

No profile changes Evidence, approval, memory or authority semantics.

```text
retrieved != truth
indexed != Evidence
runtime success != authorization
provider selected != authority transfer
```

Do not add new ingestion or RAG doctrine here. Historical detailed pipeline material remains available in Git history.
