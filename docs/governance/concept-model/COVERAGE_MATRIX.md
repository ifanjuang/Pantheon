# Pantheon Concept Coverage Matrix

Status: validation-only support map — documented non-implemented.
Boundary profile: validation_only_trace.

This matrix measures repository coverage. It does not promote a document, accept evidence, adopt a binding, authorize implementation or define a roadmap automatically.

## Vocabulary

```text
implemented
= a repository artifact exists and performs the stated bounded function.

partial
= some artifacts exist, but coverage or conformance is incomplete.

documented non-implemented
= doctrine/specification exists without the corresponding implementation.

to verify
= existence or conformance has not been established sufficiently.

not applicable
= the layer is intentionally irrelevant to the concept.
```

A static HTML prototype counts only in the Prototype column. It does not count as implementation.

## Coverage dimensions

- **Doctrine** — owned meaning and boundaries;
- **Semantics** — distinctions, lifecycle, statuses and relations sufficiently specified;
- **Semiotics** — perceptual signs for those distinctions;
- **Visual language** — reusable visual rules/tokens rather than one-off styling;
- **Prototype** — static or interactive illustrative asset;
- **Implementation** — bounded production or validation artifact for the concept;
- **Tests** — deterministic checks for the claimed implementation or contract.

## Initial coverage

| Concept | Doctrine | Semantics | Semiotics | Visual language | Prototype | Implementation | Tests | Main verified gap |
|---|---|---|---|---|---|---|---|---|
| Case | implemented as documentation | partial | documented non-implemented | documented non-implemented | partial | documented non-implemented in Pantheon | partial / to verify | owner family remains distributed; no single cockpit-ready Case projection contract |
| Source | implemented as documentation | implemented as documentation | documented non-implemented | documented non-implemented | partial | external implementation observed / Pantheon non-implemented | partial / to verify | perceptual distinction between original, derived and retrieved records not stabilized |
| Evidence | implemented as documentation | implemented as documentation | documented non-implemented | documented non-implemented | partial | partial declarative/read-only artifacts | partial | visual reliance, contradiction and acceptance states remain under-specified |
| Gate | implemented as documentation | implemented as documentation | documented non-implemented | documented non-implemented | partial | partial read-only validation; no approval engine | partial | block, requirement and satisfaction need non-color signs and relation grammar |
| Decision | implemented as documentation and contracts | implemented as documentation | documented non-implemented | documented non-implemented | partial | partial declarative contracts; resolver non-implemented | partial | current applicability, supersession and expiry are not yet projected deterministically |
| Register | implemented as documentation and some contracts | partial | documented non-implemented | documented non-implemented | to verify | partial declarative validation; storage/admission engine absent | partial | durable admission and supersession must remain distinct from runtime recall |
| Runtime | implemented as status/support documentation | implemented as documentation | documented non-implemented | documented non-implemented | partial | external runtime only; Pantheon read-only surfaces partial | partial / to verify | healthy, installed, adopted, activated and safe require independent visual axes |
| Card | candidate support doctrine | partial | partial | partial | implemented as static prototype | documented non-implemented | not applicable until renderer exists | card type is visible, but authority/status grammar is not yet reusable or tested |
| Scene | candidate support doctrine | partial | partial | partial | implemented as static prototype | documented non-implemented | not applicable until composition exists | deterministic composition and completeness rules remain non-implemented |

## Cross-cutting findings

The initial slice shows a consistent pattern:

```text
doctrine and semantics
> semiotics and visual language
> production projection and tests
```

The most mature next targets are not new concepts. They are missing translations of existing distinctions:

1. governance state semiotics;
2. relation and tension semiotics;
3. reusable visual-language rules;
4. deterministic Current Decision resolution;
5. only later, broader current-view composition.

## Roadmap use rule

This matrix may support prioritization, but empty cells do not authorize implementation.

A gap proceeds only when:

```text
owner confirmed
+ non-duplication reviewed
+ jurisdiction bounded
+ human priority decision
+ protected-path approval where applicable
```

## Lens and Perspective posture

`Lens` and `Perspective` are not rows in the coverage table because they do not yet have an admitted owner or stable semantics.

```text
useful idea != owned concept
candidate vocabulary != implementation instruction
```

Their next legitimate step is a bounded non-duplication review against existing Scene, view, Context Stack, role and cockpit concepts.
