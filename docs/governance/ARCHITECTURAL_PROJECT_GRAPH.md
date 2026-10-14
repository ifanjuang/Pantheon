# Architectural Project Graph

Status: candidate orientation — architecture domain graph, visualization and boundary note.
Boundary profile: candidate_support_note.

This document is a candidate orientation, not an implementation.

It does not create a graph database, BIM runtime, IFC parser, GraphRAG runtime, vector database, memory engine, approval engine, evidence register, project database, UI component or external action.

## Purpose

Pantheon may expose a unified project graph for architecture dossiers.

The project graph is a governed visualization and status surface that can combine:

```text
project knowledge / building anatomy
+ evidence and statuses
+ runtime memory diagnostics
```

The goal is not to duplicate information across separate systems.

The goal is to make architectural project knowledge readable across:

- spatial structure;
- building anatomy;
- phases and time;
- documents and sources;
- evidence status;
- decisions as firm status events;
- runtime memory as external diagnostic context.

## Core distinction

```text
Building anatomy explains where and what.
Evidence explains why an assertion is supported, contradicted or uncertain.
Status records where that object stands after qualification.
Runtime memory recalls operational context but does not prove anything.
```

## Building anatomy as comprehension schema

The architecture layer is not a duplicate evidence store.

It is a comprehension schema for the building and project anatomy.

Typical nodes:

```text
project
parcel
building
level
zone
room
wall
floor
ceiling
roof
opening
structure
network
access
circulation
interface
pathology
reserve
work item
```

Typical relations:

```text
contains
adjacent_to
opens_to
above
below
supports
serves
affects
located_in
belongs_to_phase
```

This layer answers:

```text
Where is it?
What does it belong to?
What is spatially or constructively connected?
```

It must not repeat evidence details such as decision date, proof status, contradiction history or approval state. Those belong to the evidence/status layer and are linked to building anatomy nodes.

## Sources are not necessarily BIM

The project graph must not assume that every architecture dossier has a BIM model.

Sources may include:

- IFC / BIM;
- PDF plans;
- JPG / PNG plan images;
- sketches;
- site photos;
- renderings;
- scanned drawings;
- emails;
- reports;
- CCTP / DCE documents;
- meeting minutes;
- manual professional input.

A spatial or constructive relation may therefore carry a confidence level:

```text
certain
probable
approximate
to_verify
```

Source mode may be tracked as:

```text
ifc
pdf_plan
image_plan
photo
sketch
text
manual
unknown
```

## buildingSMART / IFC placement

buildingSMART / IFC should be treated as an interoperability adapter, not as the central Pantheon model.

When IFC is available, it can map into the building anatomy layer:

```text
IfcProject          -> project
IfcSite             -> parcel / site
IfcBuilding         -> building
IfcBuildingStorey   -> level
IfcSpace            -> room / space
IfcWall             -> wall
IfcDoor             -> door / opening
IfcWindow           -> window / opening
IfcSlab             -> floor / slab
IfcRoof             -> roof
```

This keeps compatibility with openBIM without requiring every dossier to be BIM-native.

```text
buildingSMART describes a building well when a model exists.
Pantheon must also understand a building when it only exists as a dossier.
```

## Evidence and status layer

The evidence layer is the governed probative layer.

It links sources, assertions, contradictions, impacts, approvals and firm status events to the project anatomy.

Typical nodes:

```text
source
excerpt
claim
evidence_candidate
evidence_validated
contradiction
approval
action_candidate
status_event
actor
```

Typical relations:

```text
supports
contradicts
depends_on
supersedes
replaces
approved_by
blocked_by
impacts
derived_from
located_in
```

## Decision as firm evidence status

A decision should not be modeled as a completely separate duplicated object when it is the stabilization of an evidence object.

A decision is the firm current status of a governed evidence object after qualification.

```text
source arrives
-> evidence candidate
-> modified / contradicted / clarified
-> validated / refused / blocked / obsolete
-> firm decision state
```

The current evidence object should carry:

```text
current_status
current_decision
last_decision_date
last_decider
firmness_level
status_history
modification_history
linked_sources
linked_anatomy_nodes
linked_contradictions
```

The registry is therefore not a separate memory system.

It is a status view over the same evidence chain.

```text
Evidence = object under probative examination.
Registry = governed status view of the same object after qualification.
```

## Runtime memory layer

Runtime memory belongs to Hermes Agent, Mem0 or another execution runtime / memory system.

Pantheon may expose it for diagnostic visibility but must not treat it as proof.

Typical nodes:

```text
memory_item
chunk
embedding_cluster
namespace
retrieval_result
runtime_context
```

Typical relations:

```text
similar_to
retrieved_with
derived_from
grouped_with
mentions
```

Boundary:

```text
Runtime memory may recall.
It does not validate.
It does not become evidence automatically.
It does not become canonical Pantheon memory.
```

## GraphRAG placement

GraphRAG may be used to generate candidate relations, claims, communities and retrieval paths.

It must not be the evidence graph authority.

Correct placement:

```text
GraphRAG proposes candidate graph fragments.
Hermes / LangGraph may execute retrieval or extraction.
Pantheon qualifies status, proof, contradiction, approval and scope.
The human decides.
```

Candidate mapping:

```text
GraphRAG entity       -> actor / document / concept / building element candidate
GraphRAG relationship -> relation candidate
GraphRAG claim        -> assertion candidate
GraphRAG community    -> thematic cluster candidate
GraphRAG text unit    -> source excerpt candidate
```

Output envelope:

```text
Task Contract in
-> GraphRAG / extraction / retrieval module
-> Result Candidate + Evidence Pack Candidate out
-> Pantheon status qualification
```

## Unified graph page

The cockpit should avoid splitting anatomy, evidence and registry into unrelated pages.

Target page:

```text
Project graphs
```

or:

```text
Preuves & statuts / Graphe projet
```

The page should provide:

- project selector;
- layer toggles;
- graph view;
- timeline view;
- registry/status view;
- detail panel;
- filters;
- legend.

Layer toggles:

```text
Project knowledge / building anatomy
Evidence and statuses
Runtime memory
```

Filters:

```text
project
phase
date
decision_date
status
risk
topic
zone
building element
trade
source
decision_expected
```

Color modes:

```text
topic
project zone
decision date
trade
status
object type
none
```

Only one primary color mode should be active at a time.

Secondary encodings may be used for status, type and importance.

## Visual grammar

Node type defines the visual grammar.

Color mode defines the variable color.

### Building anatomy nodes

Stable project structure.

```text
shape: block / rounded rectangle / solid mass
fill: solid color
text: white
outline: none
visual weight: high
```

These nodes represent the building anatomy: zones, rooms, elements, constructive systems and spatial anchors.

### Evidence nodes

Probative examination objects.

```text
shape: circle
fill: transparent or very light
outline: colored
text: colored
visual weight: medium
```

Status may be expressed by border style:

```text
solid     -> validated / firm
pointed   -> candidate / to verify
red       -> contradiction / blocking
muted     -> obsolete / refused
```

### Runtime memory nodes

External operational memory.

```text
shape: soft capsule / light circle / cluster point
fill: semi-transparent
outline: none or very weak
text: hidden until zoom or selection
visual weight: low
```

Runtime memory should not dominate the graph because it is diagnostic, not probative.

## Zoom behavior

At low zoom:

```text
show building anatomy
show main evidence nodes
hide most memory labels
```

At medium zoom:

```text
show anatomy labels
show evidence labels
show selected / important memory labels
```

At high zoom:

```text
show memory details
show evidence metadata
show anatomy attributes
```

Labels should appear when:

```text
node is selected
layer is isolated
zoom threshold is reached
node carries high risk or firm decision
```

## Edge grammar

Building anatomy edges:

```text
stable
neutral
moderate thickness
```

Evidence edges:

```text
clear
status-aware
solid for validated
pointed for candidate
red for contradiction
thicker for strong impact
```

Runtime memory edges:

```text
thin
translucent
low dominance
```

## No duplication rule

A building anatomy node should not duplicate evidence content.

An evidence node should not duplicate full building anatomy.

A runtime memory node should not duplicate either as canonical data.

Correct pattern:

```text
Kitchen RDC
-> linked_to -> Evidence E-042
-> mentioned_by -> runtime memory M-884
```

Not:

```text
Kitchen RDC stores all evidence text.
Evidence E-042 stores all room anatomy.
Memory M-884 becomes canonical project fact.
```

## Governance boundary

This orientation is visual and doctrinal.

It does not implement:

- graph database;
- vector database;
- IFC parser;
- GraphRAG runtime;
- memory engine;
- approval engine;
- evidence registry write;
- external action;
- automatic decision.

Pantheon governs:

```text
truth status
proof status
memory status
approval
scope
action boundary
```

Execution remains in the appropriate external runtime.

## Doctrine summary

```text
The building graph explains the project anatomy.
The evidence graph qualifies assertions and decisions.
The memory graph shows external runtime recall.
The status view records the latest governed state.
GraphRAG may propose.
IFC may structure.
Hermes may execute.
Pantheon governs.
The human decides.
```
