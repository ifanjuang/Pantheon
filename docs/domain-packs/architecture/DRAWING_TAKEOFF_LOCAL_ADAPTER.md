# Drawing Takeoff Local Adapter Boundary

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.
Date: 2026-08-07.

This document specializes `PROJECT_UNDERSTANDING_ADAPTER_CONTRACT.md` for a local drawing and quantity-takeoff engine. It records how a tool such as OpenTakeoff may be used by Pantheon without becoming a Pantheon authority, a Revit dependency, an economy authority or a project database.

Terminology note after Project Anatomy V0.2 convergence: where this document uses the generic bridge term `Result Candidate`, the APU domain payload is the `Observation Bundle Candidate` defined by `PROJECT_UNDERSTANDING_ADAPTER_CONTRACT.md`. The companion `Evidence Pack Candidate` remains separate.

The reviewed external reference is `Kentucky-ai/opentakeoff`. At review time its MCP package advertised version `0.9.38`; that observation is reference material, not a version adoption decision. No OpenTakeoff package, MCP server, model, runtime, adapter or workflow is installed or admitted by this document.

```text
reviewed external implementation != adopted dependency
installed package != admitted binding
MCP tool visible != Pantheon capability admitted
quantity produced != quantity accepted
marked plan exported != document published
agent proposal != human review
```

Where this document conflicts with the generic APU adapter contract, `REVIT_LOCAL_ADAPTER.md`, an active schema, a reviewed capability registry or a later adopted binding record, those owners prevail.

## 1. Purpose

The target is a replaceable local source adapter for architectural drawing understanding and takeoff:

```text
PDF plan set / drawing set
-> local drawing-takeoff engine
-> bounded technical observations and measured candidates
-> Hermes cross-source reasoning
-> Observation Bundle Candidate + Evidence Pack Candidate
-> reviewed alignment with Project Anatomy
```

Its useful scope includes:

```text
sheet and document-set observation
text and schedule extraction
layer and drawing-role observations
areas, lengths, surfaces and counts
room and finish candidates
marked-plan review artifacts
source-local relations and unresolved references
quantity reports with explicit measurement provenance
```

It does not own:

```text
stable project identity
APU canonization
accepted DPGF quantities
prices or contractual amounts
Revit model truth
RE2020 compliance
ACV approval
site acceptance
professional validation
publication or transmission decisions
```

## 2. Placement beside Revit, not inside it

The drawing-takeoff adapter and the Revit adapter are sibling bindings over different source representations.

```text
                         Pantheon Next
                         governance
                              |
                         pantheon-mvp
                    persisted authority/review
                              |
                            Hermes
                  admitted métier orchestration
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
    Drawing Takeoff       Revit Local       IFC / other
       Adapter              Adapter           Adapter
             |                |                |
             v                v                v
       PDF / plans        live RVT model     IFC/source
```

The drawing engine must not be embedded into the Revit add-in merely because both concern geometry and quantities. Revit already exposes native model objects and exact model relationships; a PDF engine solves a different source problem.

```text
PDF geometry != Revit geometry
PDF room candidate != Revit Room
OpenTakeoff shape id != Revit ElementId
OpenTakeoff shape id != stable_object_id
Revit UniqueId != stable_object_id
```

A cross-source match between a measured drawing occurrence and a Revit element remains a mapping candidate under the APU contract.

## 3. Responsibility split

### Pantheon Next

Pantheon Next governs:

```text
Capability Slot identity
binding adoption and revocation posture
Task Contract scope
Context Pack requirements
source and Evidence expectations
effect ceilings
human review requirements
result status semantics
```

Pantheon Next does not execute the drawing engine, parse PDFs, run MCP tools, maintain the engine session or calculate takeoff geometry.

### pantheon-mvp

A reviewed implementation may persist:

```text
binding observations and adopted version metadata
Task Contract / Context Pack references
Execution Result and Result Candidate references
source artifact and digest references
mapping and review records
Project Anatomy projections
human decisions and accepted project values under their owning contracts
```

The MVP remains authoritative for persisted project state and review state. Engine-local session state is not a project authority.

### Hermes

Hermes may:

```text
select an admitted drawing-takeoff capability
call the bounded local adapter
combine PDF observations with Revit, IFC, CCTP, DPGF and project context
resolve or preserve ambiguities
prepare mapping, quantity, contradiction or method candidates
continue independent task actions when one takeoff action is withheld or blocked
return limitations, provenance and technical trace
```

Hermes must not:

```text
invent a capability absent from the admitted manifest
turn an engine confidence score into truth
silently accept measured quantities as DPGF values
silently overwrite project files
promote an engine rule into agency doctrine
approve its own result
```

### Local drawing-takeoff binding

The binding owns technical adaptation only:

```text
process start/stop and version observation
local transport such as MCP stdio
closed capability mapping
input/output schema translation
source-path minimization and redaction
local timeouts and bounded resource limits
engine error normalization
technical result provenance
```

It does not own workflow state, approval, Project Anatomy, accepted quantities, pricing or memory.

### External engine

An engine such as OpenTakeoff may own its own deterministic PDF parsing, geometry, takeoff session, local undo journal, export generation and internal technical confidence signals. Those remain implementation details behind the binding.

## 4. Generic APU interface

The binding reuses the existing APU chokepoint:

```text
Task Contract + admitted source references + Context Pack
-> local drawing-takeoff binding
-> technical execution result
-> Hermes qualification
-> Observation Bundle Candidate + Evidence Pack Candidate
```

The source payload should be bounded to the documents and sheets needed by the task. Loading a whole project archive when one admitted drawing set is sufficient is not the default.

Important result fields should preserve at least:

```text
source artifact reference and digest
professional index/date when known
sheet/page identity
source-local locator or normalized geometry
scale source and calibration posture when quantities depend on scale
measurement or extraction method
engine and binding version/digest
operation id
units and conversion posture
warnings, withheld items and refusal reasons
source-local ids and labels
observation timestamp
```

## 5. Capability identity

Pantheon capability identity should describe the abstract drawing function rather than an upstream tool name or MCP verb.

Candidate families:

```text
drawing_takeoff.observe.document_set
drawing_takeoff.observe.sheet
drawing_takeoff.observe.text
drawing_takeoff.observe.layers
drawing_takeoff.observe.schedule
drawing_takeoff.measure.area
drawing_takeoff.measure.linear
drawing_takeoff.measure.surface
drawing_takeoff.measure.count
drawing_takeoff.resolve.reference
drawing_takeoff.derive.quantity
drawing_takeoff.review.render_overlay
drawing_takeoff.export.marked_set
drawing_takeoff.export.report
```

A specific binding may map these to versioned technical operations:

```text
opentakeoff.sheet.info.v1
opentakeoff.rooms.detect.v1
opentakeoff.measure.area.v1
opentakeoff.schedule.resolve.v1
opentakeoff.takeoff.summary.v1
opentakeoff.marked_set.export.v1
```

These operation names are binding examples only. Pantheon must not depend on an upstream count such as "40 MCP tools" as a capability contract.

```text
Capability Slot != MCP tool name
MCP transport != capability identity
upstream tool added != Pantheon capability admitted
upstream tool removed != silent capability substitution
```

The binding should expose a closed, versioned manifest with a digest. A new upstream verb remains unavailable until explicitly mapped and reviewed.

## 6. Full-local and packaging invariant

Production use must work with Internet access disabled.

Development evaluation may use ordinary upstream installation methods. Adopted local deployment should instead retain an explicit offline supply bundle containing, as applicable:

```text
exact package or source archive
lockfile
resolved runtime dependencies
integrity digests
license and notice material
SBOM or equivalent dependency inventory
required Node/Python/runtime versions
offline restoration instructions
```

The production launch path must not depend on:

```text
npx -y fetching the latest package
package-registry availability
remote model endpoints
cloud authentication
silent auto-update
remote telemetry required for function
hidden online fallback
```

A future local VLM or OCR adapter may be added behind a separately admitted capability. Model availability does not broaden the drawing binding automatically.

## 7. Binding state distinctions

The following states must remain distinct:

```text
supported       mapped by this binding version
packaged        exact offline supply artifact available
installed       present on the machine
healthy         technical liveness checks pass
locally_enabled exposed by local configuration
available       current source/context permits the operation
admitted        Pantheon accepts this binding/capability for the scope
task_scoped     included in the exact Task Contract
executed        technical call attempted or completed
reviewed        result inspected through its owning review path
accepted        result adopted by the owning project/business authority
```

No single `enabled` or `ready` boolean should collapse these states.

## 8. Measurement and scale discipline

A PDF-derived quantity is only as strong as its coordinate and scale evidence. The binding must preserve whether the measurement came from:

```text
vector geometry
raster trace
manual polygon or line
engine-derived geometry
explicit scale label
accepted detected scale
manual calibration
unknown or scale-blind context
```

A technical engine may offer a confidence score, but Pantheon should prefer named evidence and warning factors over a single number.

```text
confidence 1.0 != verified geometry
clean technical signals != professional acceptance
scale detected != scale adopted
calibration performed != source dimension correct
```

For French/metric use, the adapter must normalize quantities through explicit unit metadata. An upstream implementation using feet, SF or LF internally is not by itself a reason to expose those units as the Pantheon contract.

## 9. `withheld` and refusal semantics

A useful pattern from the reviewed engine is to distinguish an item that was detected but deliberately not committed from a hard technical failure.

Recommended technical outcome vocabulary:

```text
success
withheld
refused
failed
cancelled
rolled_back
```

`withheld` means the adapter has material worth surfacing but lacks enough evidence to make the requested bounded claim safely. Examples:

```text
room candidate found but schedule assignment ambiguous
transition proximity detected but a wall prevents a defensible joint location
symbol near-match below commit threshold
scale needed before real-world quantity can be emitted
```

A withheld item should carry:

```text
reason code
source locator
candidate data already measured or observed
missing prerequisite or discriminating question
possible recovery action
```

Hermes may continue independent actions and later resume the blocked action. The adapter must not invent a separate project task lifecycle to do so.

## 10. Provenance and correction preservation

Machine output must remain distinguishable from human-reviewed work.

For any machine-proposed geometric or classification result that a human changes, the system should preserve both:

```text
original proposal
accepted/corrected value
correction actor
correction kind
source and method
review timestamp/reference
```

The original proposal must not be overwritten merely because the corrected result becomes the accepted project view. This enables later evaluation of the adapter without corrupting the project truth.

A source-engine local `reviewed` flag is useful provenance, but it is not a Pantheon approval record.

```text
engine reviewed flag != Pantheon Decision
engine approval mark != Evidence admission
human correction captured != reusable agency rule admitted
```

## 11. Deterministic correction rules

A second useful pattern is to turn repeated accepted corrections into deterministic, inspectable rules rather than natural-language re-prompts.

Candidate flow:

```text
machine proposal
-> human correction
-> Rule Candidate
-> explicit review of predicate, scope and affected examples
-> admitted deterministic rule
-> replay produces new candidates
```

A reusable rule must declare:

```text
project or agency scope
seed correction/provenance
exact predicate
inputs and output effect
idempotency/dedup behavior
known exclusions
version
review status
```

The rule engine belongs outside Pantheon execution authority. Pantheon governs whether the rule may be used and whether its outputs are accepted.

For the first wave, project-scoped rules are safer than automatically generalizing one project correction across the agency.

## 12. Human/agent parity and conformance

Where a local engine has both a human canvas and an agent surface, they should share the same deterministic calculation implementation whenever feasible.

The required engineering property is:

```text
same source + same bounded operation + same parameters
-> same technical result
```

An adapter adoption test suite should include:

```text
human-surface versus agent-surface parity
valid-input schema conformance
invalid-input refusal
semantic-misuse refusal
failure leaves the session usable
idempotent replay where claimed
undo/rollback behavior where claimed
version/manifest consistency
```

A transport-only test is insufficient if the human and agent paths can still call different geometry logic.

## 13. Benchmark corpus

Quantity and geometry changes should be judged against a fixed corpus rather than isolated anecdotes.

A local architecture corpus may contain public or safely anonymized drawing excerpts with independently reviewed answer keys for:

```text
room boundaries
areas and lengths
room labels
finish schedules
counts
cross-sheet references
known ambiguities/refusals
metric scales and mixed scales
vector and raster sheets
Revit-exported PDFs with layer metadata
```

Useful gates include:

```text
absolute quantity error
relative quantity error
geometry overlap where applicable
false-positive/double-count rate
refusal rate
correct-refusal rate
cross-resolution stability
parity between human and agent surfaces
corpus fixture count to detect silent fixture loss
```

Benchmark success remains engineering evidence for a binding version. It does not admit the binding or accept a project quantity.

## 14. Safe file effects

Reading and measuring a source is different from writing a deliverable.

Exports such as marked PDFs, reports, JSON or spreadsheets are filesystem effects and should follow explicit ownership rules:

```text
target absent -> write may proceed when task-scoped
target recognized as prior output of the same binding -> bounded re-export may proceed
target exists but ownership is unknown -> refuse by default
explicit overwrite -> requires the exact task/effect posture that permits replacement
```

The binding should stamp producer/version/provenance into generated artifacts where the format permits it.

```text
file created != Document authority updated
marked plan exported != marked plan transmitted
report generated != DPGF accepted
```

## 15. Cross-source workflows with Revit

The main value of this binding is not a second quantity database. It is an independent source witness that Hermes can compare with Revit and project documents.

Examples:

### PDF room/finish versus Revit room

```text
PDF sheet + schedule
-> measured room candidate + finish assignment citation

Revit
-> Room observation + area + phase + identifiers

Hermes
-> mapping/contradiction candidate

Pantheon
-> reviewed object/source alignment
```

### Drawing quantity versus model quantity

```text
PDF quantity candidate
+ Revit quantity observation
+ DPGF accepted quantity/value where available
-> discrepancy candidate with three separate provenance chains
```

No engine wins automatically because it appears more structured.

### Site and revision support

A marked drawing result may provide a useful review locator, while Revit provides a model locator. Project Anatomy may expose both around the same stable object after reviewed alignment.

## 16. Economy, RE2020 and carbon boundary

Drawing-derived quantities can support the first architecture-led professional wave, but they remain source-backed inputs.

```text
drawing quantity candidate != accepted economic quantity
drawing material label != specified product
area extracted != RE2020 validated geometry
material quantity extracted != ACV scenario accepted
```

Specialist economy, RE2020 and ACV calculations remain separate bindings or governed project records. The drawing adapter supplies evidence-bearing inputs and contradictions, not professional conclusions.

## 17. Adoption strategy for OpenTakeoff

The reviewed OpenTakeoff repository shows enough alignment with Pantheon principles to justify a bounded local evaluation, especially:

```text
shared deterministic engine across human and MCP paths
typed tool schemas and structured error results
provenance separating machine and human work
explicit withheld/refusal behavior
undoable command patterns
deterministic correction rules
parity/conformance tests
scored benchmark corpus
safe overwrite protection
optional local AI adapter rather than model logic in the core
local capture of correction data
```

The recommended posture is:

```text
1. DISTILL the generic engineering patterns now.
2. EVALUATE an exact upstream version as a local optional binding.
3. PACKAGE it for offline reproducibility before adoption.
4. MAP only required Pantheon Capability Slots, not all upstream tools.
5. FORK only if an essential boundary cannot be expressed through a thin adapter.
```

Forking is not the default because upstream is evolving quickly and a fork would create a second maintenance surface before Pantheon has proven which changes are actually necessary.

## 18. Patterns offered to the Revit implementation

The following patterns are useful engineering input for the Revit implementation, but this document does not modify the Revit authority contract:

```text
one closed operation registry as the single source for UI and agent exposure
one deterministic implementation behind human and Hermes entry points
structured technical outcome families including withheld/refused
central provenance policy for every meaningful mutation
preserve original machine proposal before human correction
deterministic correction rules instead of re-prompt loops
human/agent parity tests
operation conformance tests in both success and refusal directions
fixed benchmark corpus and regression gates
safe ownership checks before file overwrite
```

`REVIT_LOCAL_ADAPTER.md` remains the authority for Revit execution, preflight, authorization, transaction and Action Report requirements.

## 19. Rejected imports

The following must not be imported from any drawing-takeoff reference by implication:

```text
engine session as Project Anatomy authority
engine condition/tag registry as stable project identity
engine review flag as Pantheon approval
upstream MCP registry as Pantheon capability registry
arbitrary upstream tools becoming callable automatically
US-unit assumptions as Pantheon quantity contract
agent confidence as professional verification
capture corpus as automatic memory promotion
filesystem export as document publication
upstream update as automatic installed update
```

## 20. Acceptance criteria before a real binding is called adopted

A later implementation/adoption PR should prove at least:

```text
exact upstream/package identity and license review
offline install and offline startup
no hidden remote fallback
closed Pantheon capability mapping and manifest digest
metric-unit normalization
bounded source path handling and redaction
one representative Revit-exported vector PDF
one raster/scanned drawing case
one schedule/reference case
human/agent parity for shared operations
withheld/refusal propagation
safe export overwrite behavior
Observation Bundle Candidate + Evidence Pack Candidate provenance
cross-source comparison with one Revit observation
removal of the binding without loss of Project Anatomy authority
```

## 21. Final rule

```text
OpenTakeoff may measure drawings.
Hermes may orchestrate an admitted drawing workflow.
Pantheon governs scope, provenance, review and adoption.
Revit remains a separate local model executor.
Project Anatomy owns no engine session and no source-native identity.
The human accepts consequential project values.
```

This document implements no binding, installation, MCP server, workflow, model, APU write, Project Anatomy projection, Revit command, quantity acceptance, Evidence admission or external publication.
