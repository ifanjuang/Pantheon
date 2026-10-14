# Competence Model

Status: candidate support doctrine — competence composition boundary only; controlled vocabulary, capability lifecycle, task authorization, evidence and persistence remain owned elsewhere.
Boundary profile: candidate_support_note.

This document owns one narrow responsibility: how a governed reusable `Compétence` relates to professional knowledge, method support and replaceable execution means without collapsing those layers.

Controlled term definitions are owned by `TERMINOLOGY_BOUNDARIES.md`. This document does not create a competence registry, lifecycle, card schema, storage hierarchy, runtime, approval path or persistence model.

```text
Pantheon governs the reusable ability and its boundaries.
Existing capability owners govern technical eligibility and scoped activation.
A Task Contract / Execution Admission governs one task or run.
Hermes or another admitted runtime executes externally.
The professional remains the authority for consequential conclusions and effects.
```

## 1. Composition responsibility

A `Compétence` is useful only when the system preserves what each surrounding object means.

```text
Situation / professional need
        │
        ▼
Compétence
        │
        ├── uses Connaissances
        ├── is explained by Guides
        ├── may consume Resources
        ├── may structure output with Templates
        ├── may require governed Capabilities
        └── may be realized by replaceable Skills / Tools / Connectors
        │
        ▼
Candidate output / Action
        │
        ├── Evidence remains separately qualified
        ├── approval remains separately decided
        └── durable Register admission remains separately governed
```

A competence therefore describes a reusable ability such as:

- calculate a taxable surface;
- review a quotation against a CCTP;
- fill a form from qualified project information;
- perform sourced web research;
- prepare a cautious client response;
- build a reviewable chronology.

It does not identify the one tool that must perform the work.

## 2. Existing semantic owners

Do not redefine these concepts here.

| Concern | Current owner |
|---|---|
| Controlled meaning of `Compétence`, `Capability`, `Skill`, `Tool`, `Connaissance`, `Guide`, `Resource`, `Template`, `Evidence`, `Gate` | `TERMINOLOGY_BOUNDARIES.md` |
| Capability placement and uniform governance | `CAPABILITY_PLACEMENT.md`, `UNIFORM_CAPABILITY_GOVERNANCE.md` |
| Capability exact-release eligibility | Capability Passport contracts and validators |
| Replaceable implementation relation | canonical `CapabilityBinding` catalog contract |
| Scoped capability activation posture | canonical `CapabilityActivation` catalog contract |
| Task and run legitimacy | `TASK_CONTRACTS.md` and Execution Admission contracts |
| Evidence qualification | `EVIDENCE_PACK.md` and Evidence owners |
| Human approval / unresolved decision | `APPROVALS.md`, `USER_DECISION_GATE.md` |
| Durable validated memory | `MEMORY.md` and Registre Probatoire owners |
| Cockpit capability action/projection boundary | `COCKPIT_CAPABILITY_MANAGEMENT.md` |
| Cockpit product-space topology | `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` |

This model must follow those owners rather than create competence-specific substitutes for them.

## 3. Core non-equivalences

```text
Compétence != Capability
Compétence != Skill
Compétence != Tool / Connector
Compétence != Guide
Compétence != Connaissance
Compétence != Template
Compétence != approval
Compétence != professional authority
```

More specifically:

```text
available competence != capability activated
capability activated != task authorized
skill installed != competence approved
skill executed != result validated
retrieved material != Evidence
calculated value != approved professional conclusion
template-protected output != safe to transmit
runtime success != Evidence
projection != persistence
folder != governed identity
```

## 4. Knowledge and method-support boundary

`Connaissance` supplies professional, regulatory, contractual, project or Case content.

A Guide explains how an ability is applied. A Resource supports that application. A Template gives reusable form to an output.

Example:

```text
Compétence: vérifier un devis contre un CCTP

Connaissances:
- CCTP applicable;
- devis reçu;
- projet, lot et mission concernés.

Guides / Resources:
- méthode de comparaison;
- documentation d'un outil d'extraction;
- exemples de tableaux de contrôle.

Template:
- tableau de comparaison.

Execution means:
- parser, table reader or Hermes Skill selected through existing Capability owners.

Candidate result:
- écarts, omissions, contradictions and points à vérifier.

Evidence:
- exact clauses, pages, lines, quantities and source versions supporting each consequential assertion.

Gate:
- professional review before contractual conclusion or transmission.
```

Tool documentation remains Guide or Resource material. Its presence beside a competence does not make it professional Knowledge or Evidence.

## 5. Execution projection boundary

A runtime Skill may realize all or part of a Compétence. A Tool or Connector may be one technical means used by that Skill.

```text
Compétence
→ requires one or more governed effect classes
→ existing Capability owners select/qualify exact implementations
→ Task Contract / Execution Admission bounds the concrete run
→ external runtime executes
→ Pantheon receives candidates and technical observations
```

The relation is replaceable. Changing a parser, browser, model, connector or Hermes Skill must not silently create a new professional competence.

Likewise, the same runtime Skill may support several competences only when each task remains bounded by the applicable professional context and authorization.

## 6. No independent competence lifecycle

This document intentionally defines no lifecycle such as `sandbox_enabled`, `project_enabled`, `agency_enabled` or `task_authorized` for a separate competence object.

Those concerns already have owners:

```text
technical eligibility -> Capability Passport / Binding
scoped activation      -> CapabilityActivation
one task/run legitimacy -> Task Contract / Execution Admission
runtime state          -> external runtime observation
professional approval  -> Approval / User Decision Gate
```

A label such as `Competence · candidate` may be used descriptively under the controlled vocabulary, but it does not establish a second activation or authorization state machine.

## 7. No independent card or persistence owner

This model does not define a `Competence Card` schema.

If a Cockpit projection is useful, it must reuse the current card/projection grammar and compose data from existing semantic owners. A browser card does not become the competence's persistence or authority.

This model also defines no canonical `competences/` directory or resource manifest.

A filesystem folder may organize Guides, Resources, Templates or examples, but:

```text
folder location != governed identity
folder membership != Knowledge status
folder membership != Evidence status
file presence != activation
```

If durable competence identity is later demonstrated as necessary, it must first be reconciled with existing Capability and governance owners rather than inferred from a folder tree.

## 8. Cockpit boundary

`Compétence` is not a synonym for `Workspace`, Tool catalogue or Hermes inventory.

The current Cockpit implementation may project technical capability state through existing owners, while the product doctrine currently names a public `Compétences` space. The topology and implementation gap are owned by `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` and `COCKPIT_CAPABILITY_MANAGEMENT.md`, not by this model.

Do not satisfy that gap by relabelling another space or by inventing a competence registry here.

## 9. Architecture-practice safety rules

For professional work, preserve at least:

```text
filled != validated
clear != verified
calculated != approved
retrieved != Evidence
project-specific != agency-general
tool available != action authorized
Hermes done != Pantheon validated
```

A competence should make recurring work easier without weakening the distinction between candidate production and professional validation.

## 10. Convergence path

This document remains candidate support only while the composition boundary needs a dedicated explanation.

It must not expand into an independent lifecycle, registry, card schema, persistence hierarchy or runtime. If its remaining composition rules become fully expressible in the controlled vocabulary and existing capability/Cockpit owners, this document should be absorbed and removed rather than promoted merely to preserve a file.

```text
one vocabulary owner
one owner for each governed technical fact
one task/run legitimacy path
replaceable execution means
no folder-derived authority
no projection-derived persistence
```
