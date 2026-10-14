# Evidence Topology Anti-patterns

Status: reference — implemented as documentation.
Boundary profile: documentation_only.

These cards are non-authoritative examples of failure modes already governed by `EVIDENCE_TOPOLOGY.md`.

They do not own topology policy, Evidence semantics, runtime rules, schemas or tests. Their former links to `EVIDENCE_TOPOLOGY_GATE.md` and `EVIDENCE_TOPOLOGY_CHECKLIST.md` remain historical provenance in Git history.

## Purpose

Evidence topology failures often look productive from the outside.

They may show many agents, many messages, many summaries, a visible canvas or an apparently active swarm.

That activity does not prove the result.

These cards illustrate recurring failure patterns and the correction expected by the current Evidence Topology owner.

## Cards

| Card | Risk |
|---|---|
| [`ANTI_PATTERN_SUMMARY_ONLY_HANDOFF.md`](ANTI_PATTERN_SUMMARY_ONLY_HANDOFF.md) | Decisive details are destroyed at handoff. |
| [`ANTI_PATTERN_SWARM_AS_AUTHORITY.md`](ANTI_PATTERN_SWARM_AS_AUTHORITY.md) | Distributed execution is mistaken for decision authority. |
| [`ANTI_PATTERN_ROLE_MEMORY_AS_CANONICAL_MEMORY.md`](ANTI_PATTERN_ROLE_MEMORY_AS_CANONICAL_MEMORY.md) | Runtime continuity is mistaken for governed memory. |
| [`ANTI_PATTERN_CONDUCTOR_AS_ZEUS.md`](ANTI_PATTERN_CONDUCTOR_AS_ZEUS.md) | A runtime orchestrator is mistaken for procedural governance. |
| [`ANTI_PATTERN_CANVAS_AS_EVIDENCE_PACK.md`](ANTI_PATTERN_CANVAS_AS_EVIDENCE_PACK.md) | Visibility is mistaken for proof structure. |

## Correction pattern

Use the owner doctrine rather than these examples as the normative source:

```text
identify topology drift
recover source-linked evidence
restore approval boundary
separate runtime state from governance state
escalate to User Decision Gate if stakes remain unresolved
```

## Final rule

```text
example card != authority
activity != evidence
continuity != authority
visibility != validation
```
