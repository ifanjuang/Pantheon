# Architecture Evidence Pack Candidate Template

Status: template candidate — non-executable.

An Evidence Pack Candidate supports review. It is not proof by itself.

## Evidence identity

```text
evidence_pack_candidate_id:
linked_task_contract:
linked_context_pack:
project_alias:
prepared_date:
prepared_by:
```

## Claim table

| Claim ref | Claim | Status | Source fragment refs | Assumption? | Risk |
|---|---|---|---|---|---|
| CL-001 |  | candidate / supported / contradicted / insufficient |  | yes / no | low / medium / high |

## Source fragments

| Fragment ref | Source ref | Location | Excerpt summary | Used for |
|---|---|---|---|---|
| FR-001 | SRC-001 | page / section / paragraph |  |  |

## Contradictions

| Contradiction ref | Description | Sources involved | Impact | Required decision |
|---|---|---|---|---|
| CT-001 |  |  |  | verify / arbitrate / exclude |

## Missing evidence

```text
List claims that cannot be supported with the admitted corpus.
```

## Assumptions

```text
List assumptions separately from supported claims.
```

## Risk triggers

```text
- regulatory limit
- contractual liability
- structural implication
- thermal / energy implication
- planning / urbanism implication
- cost / scope implication
- client-facing wording
- external-action request
```

## Retrieval / graph candidates

```text
Retrieval Candidate refs:
Graph Candidate refs:
Hybrid search notes:
```

## Capability gaps

```text
source_absent:
source_version_unknown:
fragment_provenance_missing:
contradiction_unresolved:
approval_missing:
memory_impact_unclear:
```

## Review conclusion

```text
Sufficient for internal draft? yes / no
Sufficient for external delivery? no by default in MVP
User Decision Gate required? yes / no
```

## Boundary reminder

```text
A retrieved excerpt is not evidence by itself.
A graph relation is not a fact by itself.
A high similarity score is not validation.
The human decides.
```
