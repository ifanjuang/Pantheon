# Pantheon Platform — Implementation Roadmap

Status: validation-only roadmap — current convergence ledger — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-08-27

```text
Hermes Web/dashboard handles runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides consequential effects.
```

This roadmap records remaining implementation/deployment work one bounded slice at a time. It creates no runtime, deployment, adoption or authorization.

Historical `pantheon-mvp` PR identifiers remain provenance only. Current Pantheon candidate implementation is co-located under `implementation/`; Hermes remains the external execution runtime.

## Current source placement

```text
Pantheon governance / schemas / policy service -> repository root + mcp-server/
Pantheon executable candidate implementation   -> implementation/
Hermes execution/runtime interaction           -> external Hermes runtime + clients
human Markdown workspace                       -> external Obsidian workspace
private deployment configuration               -> operator-owned environment
```

```text
same repository != same authority
implementation path != governed identity
runtime success != authorization
```

## Chokepoint invariant

Before a consequential effect, the selected external runtime must invoke the applicable Pantheon admission/policy boundary and obey its result. Runtime/model approval features cannot substitute for the governed human decision.

```text
PDP reachable != effect authorized
valid contract != runtime permission
runtime success != Evidence
```

## Historical implementation ledger

The earlier A/C/D/E slices remain useful implementation provenance:

```text
A  coherence debt        implemented historically
E  gate validation       implemented in mcp-server/
C  PEP/policy seam       co-located under implementation/
D  capability lifecycle  bounded co-located implementation exists
B  target deployment     still not established by repository evidence
```

The former Phase B OpenWebUI/Paperless topology is refused. Paperless runtime/observer/skill compatibility has now been removed after consumer audit. Historical operator pointers that existed only for that compatibility were removed with it; Git history retains provenance.

Current operator guidance is:

```text
docs/governance/COMMON_INSTALLATION_BASELINE.md
docs/install/COMMON_BASELINE_RUNBOOK.md
```

## Current sequence

### B — Establish the selected baseline externally

Deploy only the smallest reviewed environment required for the target slice:

```text
Hermes Agent + Hermes Web/dashboard
selected model/provider
private network and persistence/rollback posture
Pantheon policy/MCP interface when required by the slice
bounded local/NAS professional source path when document intake is tested
Obsidian/Hindsight only when the separately reviewed workspace/memory path is in scope
```

OpenWebUI and Paperless are not baseline dependencies.

### C — Prove one governed document/Knowledge slice

Use the existing generic document/source owners and co-located implementation seams:

```text
exact bounded source
-> declared-source and path containment checks
-> source digest / provenance
-> selected extraction binding
-> Project Document candidate
-> optional Knowledge publication under the existing owner
-> consequential transition through the applicable admission/human gate
```

The projection surface is Pantheon Cockpit where a governed UI is needed. Hermes remains the executor.

```text
source captured != Knowledge
Knowledge != Evidence
candidate persisted != approved
```

### D — Prove one capability-management slice

Use one existing Capability Slot/binding and the current capability owners:

```text
inventory/observation
-> candidate selection
-> preflight/admission
-> human decision where required
-> native external operation by Hermes or selected tool
-> technical receipt + fresh observation
```

The Cockpit may request/display the operation but does not become the executor, installer or authorization owner.

### E — Continue assurance hardening where gaps are demonstrated

Strengthen existing policy/admission contracts only where tests or live target evidence demonstrate a gap. Do not add a second policy authority, runtime or approval engine.

## Protected cleanup now justified

Paperless protected compatibility is closed by the current convergence slice. The next protected audit is the residual OpenWebUI compatibility path:

```text
OpenWebUI adapters/templates/routes/tests
```

For each candidate deletion:

```text
find current consumers
separate reusable generic capability from product-specific code
remove only code with no selected target consumer
update tests/contracts/indexes in the same slice
run full relevant CI
```

Do not delete generic source/provenance, document ingestion, policy/PEP or Cockpit capabilities merely because an old product adapter used them.

## External blockers / live proof

Repository CI cannot establish:

```text
real Hermes deployment/adoption
real operator network/exposure state
real Obsidian synchronization state
production source-path permissions
production backup/restore proof
real-dossier authorization
```

Those remain external observations and human decisions.

## Final rule

```text
converge existing owners before adding abstractions
remove superseded compatibility after consumer proof
keep execution separate from authorization
keep workspace separate from source/Evidence authority
```
