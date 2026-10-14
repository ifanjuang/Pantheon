# Missing Information Register Candidate

Status: template candidate — non-executable.

This register records missing information before producing or transmitting a professional output.

It is not a runtime, questionnaire engine, validation system or memory entry.

## Identity

```text
register_id:
linked_task_contract:
requested_output:
project_ref:
prepared_date:
prepared_by:
workflow_depth: fast | normal | deep
```

## Summary

```text
found_count:
missing_blocking_count:
missing_important_count:
missing_useful_count:
assumption_count:
output_possible: yes | no | candidate_only
transmission_allowed: no by default
```

## Found information

| Ref | Information | Source | Confidence | Used for |
|---|---|---|---|---|
| FOUND-001 |  |  | low / medium / high |  |

## Missing information

| Ref | Information needed | Why needed | Expected source | Criticality | Question to user | Status |
|---|---|---|---|---|---|---|
| MISS-001 |  |  |  | blocking / important / useful / optional |  | missing / answered / inferred / waived / blocked |

## Search status

```text
searched_sources:
not_searched:
connector_gaps:
unreadable_sources:
conflicting_sources:
```

## Questions to ask now

```text
1.
2.
3.
```

## Output limits

```text
What may be produced now:

What must not be produced now:

What requires confirmation before transmission:
```

## Boundary

```text
A missing source is not a blank to fill.
If low-risk, it may be assumed visibly.
If consequential, ask or block.
```
