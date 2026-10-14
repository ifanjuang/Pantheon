# Reference Boundaries

Status: active support doctrine — external reference interpretation boundary; implemented as documentation.
Boundary profile: active_support_doctrine.

This document owns the boundary between learning from an external reference and adopting its architecture or runtime responsibilities.

It does not approve dependencies, integrations, capabilities, runtimes, clients, persistence systems or implementation.

Runtime/client placement is inherited from `HERMES_INTEGRATION.md`. Reading or reviewing an external reference does not transfer Pantheon governance responsibility to the referenced system.

## Owner boundary

The external-reference family has four complementary owners:

```text
WATCHLIST.md
  -> observe and triage external references

REFERENCE_BOUNDARIES.md
  -> define what may be learned without importing the referenced system's responsibilities

DISTILLATION_REGISTRY.md
  -> record patterns actually extracted, their destination and status

REJECTED_PATTERNS.md
  -> retain patterns explicitly refused under current doctrine
```

When an external capability is considered for actual use, `EXTERNAL_TOOLS_POLICY.md` and the applicable capability/binding owners govern that separate review.

```text
observed != adopted
reference != authority
pattern extracted != doctrine adopted
tool available != tool authorized
runtime success != Evidence
```

## Core rule

```text
External references may inform Pantheon governance.
They do not authorize importing runtime responsibility, persistence ownership or decision responsibility into Pantheon.
```

A reference may inform an existing owner about scope, provenance, Task Contract constraints, Evidence expectations, review boundaries, memory distinctions, role/rite pressures, interaction requirements, governed projection needs, failure modes or rejected patterns.

The destination owner remains responsible for deciding whether the extracted pattern belongs in its doctrine.

## Reference classes

Classify a reference by the responsibility it demonstrates, not by vendor name.

| Reference class | Legitimate learning | Boundary to preserve |
|---|---|---|
| Runtime / agent framework | interruption, handoff, bounded execution and state visibility | no Pantheon execution engine or hidden orchestration |
| Observability / evaluation system | trace, evaluation and regression-review signals | trace or score is not Evidence admission or approval |
| Retrieval / graph / knowledge system | provenance, corpus structure, retrieval and contradiction patterns | retrieval or graph output is not truth, Evidence or governed memory |
| Skill / plugin ecosystem | capability anatomy, compatibility, lifecycle and anti-patterns | no marketplace, installer or auto-loader by implication |
| Connector / gateway ecosystem | scoped access, least capability and effect interception | no provider router or plugin manager by implication |
| Coding / terminal agent | patch candidates, bounded execution and verification discipline | no coding runtime inside Pantheon by reference alone |
| Professional vertical assistant | source discipline, domain checks and review gates | no autonomous professional authority |
| Prompting / reasoning method | reasoning or review motifs | no hidden workflow or self-approval loop |
| Memory / context system | recall, freshness and invalidation tensions | runtime/shared memory is not Registre Probatoire |
| Client / dashboard surface | interaction, review and projection patterns | client/projection is not persistence or governance authority |

## Boundary test

Before distilling a reference, answer:

```text
What concrete governance problem does this reference illuminate?
Which existing Pantheon owner should receive the useful pattern?
What responsibility must remain outside Pantheon?
Does the pattern preserve human consequential decision where required?
Does it preserve candidate versus admitted/canonical status?
Does it preserve source/provenance and scope isolation?
Does it preserve memory != Evidence?
Does it preserve runtime/client/provider != governance authority?
Does it avoid creating a duplicate owner or hidden implementation commitment?
```

If the destination or boundary is unclear, keep the item in `WATCHLIST.md` with an appropriate review status rather than creating doctrine.

## Routing outcomes

Use existing owner vocabularies instead of introducing a parallel reference lifecycle.

| Review outcome | Destination |
|---|---|
| Interesting but insufficiently reviewed | `WATCHLIST.md` |
| Boundary identified; pattern not yet extracted | keep the watch item and reference this owner |
| Useful governance pattern extracted | `DISTILLATION_REGISTRY.md` |
| Reasoning/tool method needs risk review | `EXTERNAL_TOOLS_POLICY.md` |
| Skill-specific signal | `SKILL_WATCHLIST.md` |
| Explicitly incompatible pattern | `REJECTED_PATTERNS.md` |
| Pattern changes active doctrine | the existing destination owner through its normal review path |
| Actual tool/runtime adoption considered | capability/binding review plus `EXTERNAL_TOOLS_POLICY.md` |

A routing outcome is not implementation approval.

## Distillation discipline

A valid distillation identifies:

```text
source reference
problem observed
useful pattern
existing destination owner
responsibility that must not be imported
status of the extracted pattern
```

Prefer the smallest useful pattern. Do not copy an external architecture wholesale because several parts look useful.

```text
reuse a pattern, not a product topology
reuse a constraint, not a foreign authority model
reuse a review signal, not its vendor-specific runtime
```

Concrete product/repository evaluations belong in `WATCHLIST.md`, `SKILL_WATCHLIST.md`, `DISTILLATION_REGISTRY.md`, `reference_reviews/`, `EXTERNAL_TOOL_PLACEMENT_REGISTER.md` as appropriate. They are not maintained here as a second catalogue.

## Evidence and memory boundary

An external reference may be cited as a source, comparison, limitation or rationale, but its existence does not validate a claim.

```text
reference retrieved != Evidence admitted
citation displayed != claim validated
benchmark score != professional validation
popularity != authority
```

Any durable memory or Register Candidate produced from reference analysis remains governed by `MEMORY.md`, scope rules and the applicable Evidence/approval path. Repetition, embedding or retrieval does not promote it.

## Runtime and projection boundary

External runtime/client patterns may influence interface requirements, but they do not change the established placement:

```text
Pantheon policy service -> bounded PDP
external runtime / Hermes -> execution and PEP
compatible runtime clients -> optional interaction
Pantheon Cockpit -> governed projection
human -> consequential decision where required
```

A reference that combines these responsibilities does not require Pantheon to combine them.

## Forbidden drift

This owner must not become a vendor catalogue, dependency list, product ranking, implementation backlog, runtime roadmap, second Watchlist, second Distillation Registry, proof-of-safety register or adoption shortcut.

Historical product-specific boundary notes remain available through the private Pantheon-Next archive; current product observations belong with their present owners.

## Final rule

```text
Observe in the Watchlist.
Interpret through the reference boundary.
Record extracted patterns in the Distillation Registry.
Reject explicitly when required.
Adopt nothing by implication.
```
