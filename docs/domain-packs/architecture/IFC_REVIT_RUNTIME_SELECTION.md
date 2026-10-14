# IFC and Revit runtime selection for Architecture Project Understanding

Status: candidate implementation selection. This note records the current source-adapter choices; it does not activate a runtime or authorize a task.

## Objective

Use mature external runtimes for IFC and Revit plumbing while preserving one Architecture Project Understanding (APU) candidate seam and one eventual production path per source family.

```text
IFC source -> IFClite read-only adapter ----------------\
                                                       -> Observation Bundle Candidate -> APU review/application
Revit     -> selected read-only Revit runtime adapter --/
```

The existing `architecture-project-understanding` skill remains a semantic qualification skill. It does not become an IFC parser, a Revit controller or a persistence owner.

## IFC selection

### IFClite

Pinned qualification target: **v10.3.0**, MPL-2.0.

First admitted surface is read-only CLI observation only:

- `info --json`;
- `query ... --json`;
- `diff ... --json` when comparing explicitly supplied source revisions;
- `ids ... --json` as requirement-check candidate material.

Editing, export mutation, create, merge, convert, MCP write calls and any source mutation remain outside this slice.

## Revit convergence

Three implementations have different roles during qualification. They are not three production authorities.

### Preferred runtime candidate — Bimwright rvt-mcp

Pinned qualification target: **v1.1.0**, Apache-2.0.

Reasons for preferred qualification status:

- native `--read-only` mode with per-tool filtering;
- `send_code` is removed by read-only mode and remains explicitly non-admitted;
- local per-session authentication token;
- explicit per-instance targeting and refusal of silent rebinding after a Revit restart;
- bounded `revit_survey_change_impact` semantics with incomplete coverage kept explicit;
- Revit 2022–2027 release support.

Pantheon qualification additionally disables runtime change-history dependence. Runtime-local history may assist diagnostics but is not Pantheon Memory, Evidence or Project Anatomy.

### Fallback qualification candidate — Horizun Revit MCP

Pinned qualification target: **v2.1.5**, Apache-2.0.

Horizun remains a strong fallback and comparison baseline because it publishes extensive live multi-version probe evidence and a broad typed Revit surface. The public Windows release is unsigned; SHA-256 verification establishes byte integrity against release metadata but does not authenticate a Windows publisher.

Only a bounded upstream read-only subset is considered during this qualification. Python, save/sync/delete/purge, model creation and delivery tools remain non-admitted.

### Contract oracle — Pantheon Revit W0

The existing Pantheon-owned Revit W0 branch remains the reference for:

- document/view/selection freshness scopes;
- source-representation-first observations;
- requested scope vs actual observed coverage;
- partial coverage and `absence_inference_allowed=false`;
- governed project/task references;
- Observation Bundle shape.

W0 is not automatically retained as a production runtime. Its contract behavior is compared against external runtimes so generic Revit plumbing can be removed if an external runtime satisfies the same boundaries.

## Required convergence test

The same bounded RVT and the same observation cases must be exercised across the available implementations.

```text
                  same RVT / same cases
                         |
          +--------------+--------------+
          |              |              |
      Pantheon W0     rvt-mcp        Horizun
          |              |              |
          +--------------+--------------+
                         |
                 normalized receipts
                         |
          +--------------+--------------+
          |              |              |
       coverage       freshness      identity
       fidelity       latency        security
       limits         payload        install/update
                         |
                         v
                  one runtime selected
                  redundant paths removed
```

Minimum cases:

1. active document identity and runtime/Revit version;
2. active view context;
3. bounded room query;
4. bounded door query;
5. selected-element query;
6. missing/non-existent target handling;
7. multi-instance target ambiguity or explicit targeting;
8. Revit restart / stale-target behavior;
9. partial/limited observation represented without absence inference;
10. proof that write-capable and arbitrary-code tools are absent from the admitted read-only surface.

The winner is not the runtime with the most tools. Prefer the implementation that satisfies the contract with the least Pantheon-owned adapter code and the smallest admitted surface.

## Required boundary

```text
runtime installed != binding activated
binding activated != task authorized
source observation != project truth
IFC GlobalId != stable_object_id
Revit ElementId != stable_object_id
runtime success != Evidence
runtime-local history != Pantheon Memory
IDS pass != professional approval
```

All source runtimes must return or be normalized into the current
`PROJECT_UNDERSTANDING_ADAPTER_CONTRACT.md` Observation Bundle Candidate shape.

## Implementation ownership

- Pantheon-Next owns contracts, candidate resource/capability declarations and review rules.
- Pantheon-plugins owns local installation/bootstrap, normalization and qualification harnesses.
- External runtimes own their executable implementation.
- APU/Pantheon review remains the only route to retained Project Anatomy state.

## Done criteria

- IFClite remains the single preferred IFC runtime candidate;
- rvt-mcp and Horizun are reproducibly installable from pinned release artifacts;
- both Revit candidates are exercised through an explicitly read-only surface;
- W0, rvt-mcp and Horizun produce comparable qualification receipts for the same cases;
- one Revit runtime is selected after live proof;
- the two redundant Revit execution paths are retired or retained only as non-production references;
- no runtime gains Evidence, Memory, identity or effect authority by successful execution.
