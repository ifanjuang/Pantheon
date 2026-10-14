# Work Issue projection SQL baseline

Date: 2026-08-04

Status: measured optimization record — non-authoritative.

## Scenario

The measurement creates three empty Work Issues for one exact `case_ref`, resets the SQL counter and executes:

```text
work_issue_read.list_issue_projections(connection, case_ref)
```

The probe uses a real PostgreSQL connection wrapped only to count `execute` calls. It does not replace owner reads, projection logic or governed schema validation.

## Before

Main commit before optimization: `5731b458fb6488674d406c40b0b7a6b1beeb1156`.

```json
{
  "issue_count": 3,
  "projection_count": 3,
  "sql_queries": 16,
  "expected_current_formula": "1 + 5N"
}
```

The previous path performed:

```text
1 query  — ordered issue identities for the exact case_ref
N queries — Work Issue rows
N queries — comments
N queries — Hermes runs
N queries — events
N queries — Work Card metadata
```

## After

The list projection now performs five bounded queries for every non-empty case:

```text
1 query — ordered Work Issue rows for the exact case_ref
1 query — comments for the selected issue identities
1 query — Hermes runs for the selected issue identities
1 query — events for the selected issue identities
1 query — Work Card metadata for the selected issue identities
```

Measured result for three issues:

```json
{
  "issue_count": 3,
  "projection_count": 3,
  "sql_queries": 5,
  "query_strategy": "constant_batch_for_non_empty_case",
  "expected_current_formula": "5"
}
```

Measured change:

```text
16 -> 5 SQL executions
-11 queries / -68.75%
```

An empty exact case returns after the first issue query.

## Preserved contracts

- exact `case_ref` scope;
- terminal-status filter and limit validation;
- initial ordering by `updated_at DESC, issue_id ASC`;
- final stable status ordering;
- comments ordered by `created_at, comment_id` inside each issue;
- runs ordered by `created_at, run_id` inside each issue;
- events ordered by `occurred_at, event_id` inside each issue;
- transition payload projection;
- Work Card metadata and subject-tag cap;
- one governed schema validation per aggregate;
- `work_activity` projection;
- single-item `work_issues.get_issue` behavior.

The batching remains in the read-only Cockpit adapter. It creates no aggregate mutation, scheduler, queue or task authority.

## Non-equivalences

```text
batched read != broader scope
fewer queries != weaker validation
projection batching != aggregate mutation
query reduction != authorization
Cockpit read optimization != workflow engine
```
