# Current Decision Resolution Specification

Status: validation-only algorithm specification — documented non-implemented by this document alone.
Boundary profile: validation_only_trace.
Owner context: issue Pantheon-Next#374, `APPROVALS.md`, `catalog/schemas/handoff-decision.schema.json`.

This specification translates existing decision, scope and temporal rules into a deterministic read-only resolver. It does not create a new decision doctrine, approval engine, authorization token, identity service, runtime callback, scheduler, queue or external action.

## Function boundary

```text
HandoffDecision records
+ exact handoff candidate identity
+ exact scope
+ evaluation timestamp
→ CurrentDecisionProjection
```

The resolver determines applicability. It does not decide, approve, execute, activate, install, sign or promote memory.

```text
recorded != current
current != executable
projection != permission token
approval != activation
valid at T != perpetual permission
```

## Stable outcomes

| Outcome | Meaning |
|---|---|
| `none` | No valid decision is applicable to the exact subject, scope and evaluation time. |
| `current` | Exactly one approval is applicable and no concurrent blocking decision applies. |
| `blocked` | Exactly one refusal, revocation or recorded expiration is applicable. |
| `ambiguous` | Multiple incompatible decisions are concurrently applicable. Fail closed. |
| `invalid-record-set` | Identity, reference or supersession-graph invariants are broken. Fail closed. |

`current` is intentionally not named `approved`: the projection outcome and the recorded decision type remain separate fields.

## Algorithm

```text
1. normalize timestamps and exact scope values
2. validate unique record identities
3. validate supersession references and graph acyclicity
4. retain records for the exact subject
5. retain records for the exact authorized/reviewed scope
6. exclude records not yet effective at evaluation time
7. resolve explicit revocation and recorded expiration against approvals
8. apply natural approval expiry
9. classify currently applicable approvals and blockers
10. detect incompatible concurrent applicability
11. produce a stable projection and optional technical trace
```

Graph validation precedes temporal filtering. A broken chain must not disappear merely because one malformed record is future-dated or outside the requested scope.

## Scope matching

Matching is exact across `environment`, `resource`, `configuration_ref`, `provisioner` and `one_time`. No subset, wildcard, inherited, global or approximate match is permitted in the first slice.

```text
scope_match != global_scope
binding_selected != dependency_adopted
```

## Historical multiplicity

Multiple approval records may exist historically.

```text
multiple recorded approvals
!=
multiple currently applicable approvals
```

Successive non-overlapping approvals are legitimate history. Two approvals applicable at the same evaluation time for the same subject and exact scope produce `ambiguous`.

## Supersession effects

- `revoke` and `expire` reference an existing approval through `supersedes`;
- reviewed scope exactly matches the superseded approval scope;
- effective revocation or recorded expiration blocks that approval;
- natural expiry derives from approval `expires_at` and is not revocation;
- `refuse` is a standalone blocking decision for its reviewed scope;
- broken references, duplicate identifiers and cycles produce `invalid-record-set`.

```text
expired != revoked
revoked != rolled_back
superseded != deleted
```

## Stable projection versus technical trace

`CurrentDecisionProjection` is the stable cockpit-facing result. `ResolutionTrace` is optional diagnostic material for tests and audit and is not part of the normative projection contract.

```text
projection reason != hidden chain-of-thought
technical trace != governance evidence
```

## Card Stack boundary

```text
Decision Records
→ deterministic resolver
→ CurrentDecisionProjection
→ Card Stack display
```

The Card Stack displays but does not recalculate applicability. No card interaction converts the projection into execution authorization.

## Required scenario coverage

No decision; current, future and naturally expired approval; refusal; revocation; recorded expiration; wrong subject; wrong scope; duplicate identifiers; orphan supersession; cycle; concurrent approvals; approval plus refusal; successive non-overlapping approvals; expired approval followed by a new current approval.

## Promotion condition

This specification remains validation-only. Schema validity, passing fixtures, CI success, merge or prototype display do not promote it into canonical doctrine or runtime authorization.
