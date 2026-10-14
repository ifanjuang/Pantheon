# Revit Runtime Qualification Contract

Status: candidate qualification contract — no runtime adoption or activation.

## Goal

Select one replaceable Revit observation runtime for Pantheon Architecture Project Understanding, then remove redundant production paths.

Candidates:

```text
contract oracle: Pantheon Revit W0
preferred runtime candidate: Bimwright rvt-mcp v1.1.0
fallback runtime candidate: Horizun Revit MCP v2.1.5
```

## Test fixture discipline

Every runtime must observe the same RVT snapshot under the same Revit version and the same requested scopes. A copied or modified fixture is a different run basis and must not be compared as if it were identical.

The receipt must preserve:

```text
fixture path or governed source reference
fixture digest when available
Revit year
runtime name/version
runtime target/session identity
case id
started_at / completed_at
requested scope
observed scope
coverage / limitations
raw-result reference or digest
normalization warnings
write-surface check
```

## Required cases

- `document_identity`
- `active_view`
- `rooms_bounded`
- `doors_bounded`
- `selection_bounded`
- `missing_target`
- `instance_targeting`
- `restart_stale_target`
- `partial_coverage`
- `read_only_surface`

A runtime may return different native JSON. Comparison happens only after each result is normalized into the same qualification receipt and, where applicable, the APU Observation Bundle Candidate seam.

## Evaluation dimensions

### Contract fidelity

Must preserve document identity, runtime version, requested scope, observed coverage and native source identifiers. Partial and unknown coverage must not support absence inference.

### Safety boundary

The admitted profile must not expose arbitrary code or consequential writes. Runtime installation, local tool exposure and Pantheon task authorization remain distinct.

### Freshness and targeting

The test must make document, view, selection and runtime target freshness observable enough to refuse or surface stale/ambiguous context. Silent rebinding to another Revit instance is a failure.

### Operational quality

Measure response time, response size, error clarity, installation/update burden and amount of Pantheon-specific adapter code required.

### Replaceability

No candidate may become the owner of Project Anatomy, Evidence, Pantheon Memory or stable identity.

## Decision rule

A candidate is eligible only if every hard boundary passes.

Among eligible candidates, prefer in order:

1. lower Pantheon-owned code and maintenance burden;
2. stronger explicit freshness/targeting semantics;
3. smaller read-only tool surface sufficient for the métier cases;
4. clearer coverage/limitation reporting;
5. stronger release/test evidence;
6. lower latency and payload cost.

Tool count is not a positive criterion by itself.

## Exit

The subject is closed only when:

```text
live receipts exist for the same fixture
-> hard boundaries pass
-> one runtime is selected
-> production binding points to it
-> redundant production runtime code is removed
-> W0 contract fixtures remain as regression tests where useful
```

Until then, all three remain qualification artifacts, not parallel authorities.
