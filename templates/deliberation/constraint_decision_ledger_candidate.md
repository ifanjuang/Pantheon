# Constraint & Decision Ledger Template

Status: template candidate — non-executable.

This is the pinned working-state ledger of an iterative deliberation (see
`docs/governance/ITERATIVE_DELIBERATION_LIFECYCLE.md`). It records the constraints
and decisions that must survive context summarization, truncation and session
restart, so the final candidate is not built from a partial view of the
transcript.

It is governed working state, not canon. It stays candidate / non-canonical and
never bypasses the Registre Probatoire — only a gate promotes any element to
canon. It is not a chat memory, not a parallel register, not an approval record.

## Ledger identity

```text
ledger_id:
linked_subject:
linked_workflow:
project_alias:
opened_date:
last_updated:
```

## Recto — five-second read

```text
[Constraint & Decision Ledger]
Working state · scope
N active constraints · M open decisions
Last change: <short>
Next action: <short>
Gate: none | pending on an element
```

## Constraints

A constraint persists across turns until explicitly changed. One row per
constraint; it is an entity, not a lifecycle state.

| Ref | Constraint (short) | Origin (turn / message) | Scope | Status | Affected cards | Modifiable by |
|---|---|---|---|---|---|---|
| C-001 |  |  | subject / project / global | active / superseded / lifted | | architect / role-facet proposal |

```text
Status meaning:
  active      — currently binding the deliberation;
  superseded  — replaced by a later constraint (keep the lineage);
  lifted      — explicitly removed by the human.
A superseded or lifted constraint is never deleted; it stays as trace.
```

## Decisions

Working decisions taken during the deliberation. A decision here is not an
approval and not a canonical memory; it is the recorded state of the search.

| Ref | Decision (short) | Turn | Basis (evidence / constraint refs) | Status | Reopen condition |
|---|---|---|---|---|---|
| D-001 |  |  |  | held / reopened / promoted-candidate | |

## Contradictions surfaced

```text
List cross-turn contradictions detected (a later turn reversing an earlier one).
The latest turn does not win by default; the human resolves.
```

| Ref | Earlier (turn) | Later (turn) | What conflicts | Resolution status |
|---|---|---|---|---|
| X-001 |  |  |  | open / resolved-by-human |

## Verso — governed detail

```text
Definition: what this ledger holds and does not hold.
Origin: how each entry entered (turn, message, role-facet proposal).
Detailed status: why each constraint/decision is active, superseded or lifted.
Useful links: affected evidence, drafts, gates, actions.
History: creation and every change, with before/after.
Risks: a dropped constraint, a stale decision, a silent contradiction.
Possible actions: edit, supersede, lift, request source, open gate.
Limits: this ledger decides nothing; it never promotes to canon by itself.
```

## Promotion boundary

```text
Nothing in this ledger is canon.
Promotion of any element (a validated value, a decision, a memory) is a separate
gate, under human decision, recorded in the Registre Probatoire.
Finalizing a CR opens at minimum a diff-review gate; transmission, canonical
memory or external effect each open a separate gate.
```

## Boundary reminder

```text
This is governed working state.
It is not approval.
It is not canonical memory.
It is not a chat-memory engine or an event store.
It does not bypass the Registre Probatoire.
```
