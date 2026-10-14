# Hermes Runtime Topology Pilot

Status: implementation candidate — projection, read-only Cockpit topology view
and contradictory-review binding contract implemented; live `pantheon-governed`
Runs delegation not yet qualified.

## Objective

Use the public Hermes Agent subagent lifecycle already available on the Runs SSE
surface without creating a Pantheon multi-agent runtime. Release identity remains
owned by `implementation/qualification/external-pins.json`; this pilot must be
re-reviewed when that selected Hermes target changes materially.

```text
Pantheon Role != Hermes subagent
Role viewpoint != worker identity
runtime parent_id != inferred causal edge
runtime completion != Evidence
runtime success != authorization
projection != persistence
```

## Runtime topology projection

`mvp_vertical.hermes_runtime_topology_projection.HermesRuntimeTopologyProjector`
accepts only public `subagent.start` and `subagent.complete` events. It retains
Hermes-reported `subagent_id`, `parent_id`, `delegation_id`, child session,
depth, status and bounded execution metrics. It deliberately omits
`output_tail`, subagent tool chatter and private reasoning.

The existing `HermesRoleTraceRelay` remains the sole upstream Runs SSE consumer
for a run. It now multiplexes two presentation event kinds from that one stream:

```text
role.stage       -> governed semantic Role presentation
runtime.subagent -> explicit Hermes worker topology
```

The SSE event name preserves that distinction. No relation is synthesized from
time, ordering, Role labels or handoff prose. A runtime worker is explicitly
marked `governed_identity: false`.

## Cockpit presentation

The composed Cockpit keeps the existing Role Trace Graph as DOM/CSS semantic
lanes and renders Runtime Hermes separately. The runtime view uses a lazily
loaded, integrity-pinned D3 tree layout only after a `runtime.subagent` event is
observed.

```text
Role Trace Graph
-> semantic responsibility lanes
-> no worker identity

Runtime Hermes
-> D3 hierarchy/tree presentation
-> explicit parent_id -> subagent_id relations only
-> synthetic run root is display containment only
```

D3 is not a state store, scheduler, causal model or authority source. A missing
parent event creates no inferred parent edge. Cycles are cut for display and
reported rather than repaired. If D3 cannot load, the Cockpit falls back to a
plain bounded list of observed worker identifiers and parent identifiers.

The main Cockpit continues to use the existing Swiper-owned collection motion.
On mobile, compact card collections expose an explicit fraction position while
preserving horizontal sibling swipe, vertical parent/child swipe and the
existing previous/next fallback when Swiper is unavailable. The Workspace
Cockpit remains a filtered dossier inventory and is not reinterpreted as the
same governed card carousel.

## `AUTOCRITIQUE_CONTRADICTOIRE` pilot

`mvp_vertical.hermes_contradictory_review_runtime` prepares the Hermes
`delegate_task` shape reviewed against the selected Hermes source:

```text
tasks[]
  goal
  context
  output_schema
```

Only findings are model-authored:

```text
observations
analogous_occurrences
limits
```

Task Contract identity, candidate digest, binding identity, runtime execution
identity and Rite closure semantics remain caller-owned. A schema-valid child
result is passed through the existing deterministic
`contradictory_review.report_from_payload` compiler. The child cannot repair the
reviewed candidate, widen scope, create Evidence, approve output or close the
Rite.

### Context-isolation source review

The exact Hermes source selected by the canonical external pin was re-read for
this qualification slice. Its delegated child starts with a fresh conversation,
its own task/session identity and a system prompt built from the explicit goal +
context. The child constructor also sets:

```text
skip_context_files = true
skip_memory        = true
```

That is useful isolation, but it is not complete isolation. The same constructor
passes the parent's `prefill_messages` to the child. The selected request
assembly path inserts those prefill messages into the child's API request
immediately after the system prompt on every model call. The child also records
`parent_session_id` for lineage, which is not itself a transcript copy.

Pantheon's binding therefore protects only what Pantheon controls directly: its
`delegate_task` payload contains exactly one explicit review task with
`goal`, `context` and `output_schema`; the serialized context contains only the
candidate identity/digest, governed claims, bounded review context and review
constraints. It does not add parent transcript, session history, runtime memory
or private reasoning.

```text
fresh child conversation != fully isolated reviewer
skip_memory != no inherited prefill
parent_session_id lineage != parent transcript
Pantheon bounded context != proof of runtime context isolation
independent_review != same context asked to reconsider itself
```

No new Pantheon verifier, context engine or subagent runtime is justified by
this finding. The existing binding remains the owner; runtime qualification must
prove that inherited prefills are absent or otherwise explicitly neutralized for
the selected `pantheon-governed` review route.

### Admitted-scope narrowing on the return path

Bounding what Pantheon sends is only half the boundary. The outbound task states
`do not widen scope` as a constraint, and a stated constraint is not an observed
one: before this slice, the compiled report recorded `scope_expanded = false` on
the child's word alone.

The binding therefore observes the return path against the same admitted set the
existing report already publishes as `rite_review_card.inputs_considered` — the
reviewed candidate plus the source refs carried by the admitted claims. A child
observation citing an artifact reference outside that set is refused, because
Pantheon gave the child nothing else to cite.

```text
constraint stated != constraint observed
child asserted scope != admitted scope
contract refusal != review verdict
admitted claim source_refs != whole workspace
delegated_scope != parent_scope
```

This is a contract refusal, not a judgment: it says the returned envelope is
unusable, not that the reviewed candidate is defective. It adds no verifier,
Role, Rite or runtime — the existing deterministic compiler stays the only
owner, and the check reuses the admitted set that owner already computes.

It is also the repository-side detector for the inherited-prefill finding above.
Material reaching the child through prefills rather than through the admitted
context is only observable at Pantheon's boundary when the child cites it, so
this check narrows the unqualified surface without claiming to close it.

## Qualification boundary

Repository implementation does not prove that the currently deployed
`pantheon-governed` runtime envelope exposes `delegate_task` through the exact Runs API
route used by the external Pantheon binding. Repository source review also does
not prove the effective deployed runtime/model/prefill state.

Therefore this pilot is not activated merely because the projection and binding
contracts exist. Live acceptance must prove, on the exact selected Hermes
artifact and route:

1. `delegate_task` is present in the reviewed active Runs tool envelope;
2. the one-child `output_schema` contract validates and returns a bounded result;
3. `subagent.start` and `subagent.complete` expose the expected explicit runtime
   identifiers on the same admitted `run_id`;
4. no Role identity is assigned to the worker;
5. Pantheon's outbound child context contains only the admitted candidate,
   claims, bounded review context and constraints — no parent transcript,
   session history, runtime memory or private reasoning;
6. effective `prefill_messages` for the review child are observed empty, or a
   separately reviewed Hermes mechanism proves they are not inherited for this
   route; a configured-empty file/path must not be assumed from repository text
   alone;
7. a sentinel placed only in parent conversational context is not recoverable by
   the child unless it is explicitly included in the admitted review context;
   a sentinel surfacing as a child artifact reference is refused by the
   admitted-scope check above, but a sentinel the child reads without citing
   remains undetectable from the repository side;
8. the existing contradictory-review candidate path remains non-authoritative;
9. no second Runs SSE consumer, scheduler, queue or retry loop is introduced.

Until those checks pass, the live capability remains unqualified rather than
silently falling back to inferred topology, simulated Role agents or a claim of
review independence that the deployed runtime has not demonstrated.
