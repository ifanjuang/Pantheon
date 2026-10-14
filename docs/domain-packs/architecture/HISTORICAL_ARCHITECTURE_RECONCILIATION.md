# Historical Architecture Reconciliation

Status: validation-only trace — documented non-implemented.
Boundary profile: validation_only_trace.
Scope: historical `architecture_fr` domain material versus the current Pantheon Next architecture-domain direction.

This note compares inherited `architecture_fr` domain material with the current Pantheon Next governance baseline.

It does not import a retired runtime by bulk copy.

It does not create a runtime, API endpoint, schema, test, operation, platform component, OpenWebUI configuration, Hermes skill, memory engine, approval engine or external action.

## Purpose

Pantheon Next is doctrinally stronger than its historical predecessor.

The historical predecessor was operationally richer for the architecture domain.

The useful move is not migration.

The useful move is distillation.

This document records what was accepted, refused, verified or arbitrated before inherited architecture-domain material entered Pantheon Next.

## Sources reviewed

Pantheon Next active and support sources reviewed:

```text
docs/governance/STATUS.md
docs/governance/MODULAR_DOMAIN_REORIENTATION.md
docs/governance/CAPABILITY_PLACEMENT.md
docs/governance/DOMAIN_PACK_SPEC.md
docs/governance/AUTHORITY_INDEX.md
docs/governance/MODULES.md
docs/governance/OPENWEBUI_INTEGRATION.md
docs/domain-packs/architecture/AGENCY_DOMAIN_PACK.md
docs/governance/KNOWLEDGE_TAXONOMY.md
docs/governance/SKILL_LIFECYCLE.md
docs/governance/ADAPTERS_AND_BINDINGS.md
docs/governance/REPOSITORY_REVIEW_WATCHER.md
docs/governance/TARGET_ARCHITECTURE.md
GitHub issue #7 and its arbitration comment
```

Historical sources reviewed:

```text
README.md
docs/governance/STATUS.md
domains/architecture_fr/domain.md
domains/architecture_fr/rules.md
domains/architecture_fr/knowledge_policy.md
domains/architecture_fr/output_formats.md
knowledge/registry.example.yaml
docs/governance/OPENWEBUI_INTEGRATION.md
```

## Migration boundary

Issue #7 arbitrated the now-completed historical migration posture:

```text
No bulk-copy from the predecessor runtime.
Condense by default.
Do not silently integrate a historical document that is better than current doctrine.
Propose a Next doctrine update first.
Do not migrate obsolete or contradictory content by default.
Defer diagrams and images.
Use reviewed historical material only as non-authoritative source material.
```

This reconciliation follows that posture.

It is not the Phase C migration playbook.

It is not a substitute for a future PR that actually distills one accepted item into the architecture domain pack.

## Finding

The old `architecture_fr` package contained several useful professional controls that are not fully visible in the current Pantheon Next architecture pack.

The current `AGENCY_DOMAIN_PACK.md` is stronger as an abstract architecture-agency data and evidence model.

The old `architecture_fr` package is stronger as a daily professional working frame for:

```text
CCTP / DPGF / CCAP / devis review
client and third-party message safety
source freshness
project-source priority
architecture output formats
OpenWebUI Knowledge mapping
architecture skill and workflow candidates
```

These elements should be distilled into Pantheon Next only when they remain compatible with the current rule:

```text
A domain pack is a governed professional method.
It does not advise, validate, approve, execute, send or memorize by itself.
```

## Accepted for distillation

### 1. Architecture source policy

The historical predecessor had a useful architecture-specific source discipline:

```text
official and primary sources
professional and technical references
project-controlled sources
secondary and contextual sources
fetch-before-cite rule
freshness rule for regulatory and normative references
project-source priority over generic templates
```

Decision Zeus: accepted.

Repository state: documented non-implemented.

Target: distill into the architecture domain pack source-policy section.

Boundary:

```text
Search result = lead.
Read source = possible evidence.
Evidence Pack = trace.
```

The source-policy material must remain method and evidence discipline.

It must not become a retrieval runtime, vector database, web crawler, automatic regulatory checker or source-of-truth replacement.

### 2. Architecture output format catalogue

The historical predecessor defined useful governed output formats:

```text
note
lettre
email
rapport
resume
cctp_review
dpgf_review
client_message_draft
quote_vs_cctp_analysis
evidence_summary
```

Each format carried:

```text
default approval level
output status
mandatory sections
Evidence Pack expectations
forbidden patterns
```

Decision Zeus: accepted.

Repository state: documented non-implemented.

Target: non-executable architecture output-format section or template catalogue.

Boundary:

```text
The format is a contract.
The status is honest.
The Evidence Pack is the trace.
The user remains the legal author of any external output.
```

A format is a frame, not a prompt runtime.

### 3. OpenWebUI Knowledge registry blueprint

The historical predecessor had a useful YAML example mapping Knowledge Bases to:

```text
domain
source tier
reliability level
privacy level
project scope
freshness policy
allowed use
forbidden use
Evidence Pack requirement
memory-candidate behavior
```

Decision Zeus: accepted as blueprint only.

Repository state: documented non-implemented.

Target: `templates/` or adapter-facing documentation.

Boundary:

```text
The blueprint lives in Pantheon.
The adapter lives in the tool.
The dependency always points to Pantheon.
```

The real OpenWebUI configuration must live outside Pantheon.

OpenWebUI Knowledge may expose and organize sources.

It must not become canonical memory, approval, Registre Probatoire, doctrine or unrestricted Hermes access.

### 4. Architecture skill and workflow candidates

The historical predecessor named practical candidates:

```text
quote_vs_cctp_review
cctp_review
dpgf_review
notice_architecturale_check
client_message_safety
chantier_situation_review
delai_penalite_analysis
plu_constraint_check
erp_sdis_check
re2020_compliance_summary
```

Decision Zeus: accepted as capability candidates only.

Repository state: documented non-implemented.

Target: map each candidate to the current skill lifecycle:

```text
declared
validated
admitted
preflighted
task-authorized
suspended
superseded
retired
```

No skill becomes active by migration.

No workflow becomes executable by migration.

### 5. Architecture communication boundary

The historical predecessor correctly treated external professional messages as high-risk when they can bind the architect.

The following outputs should remain C4 by default when directed to a third party or when they carry contractual, regulatory, financial, professional-responsibility or dispute implications:

```text
client email
client letter
contractor email
BET / bureau de contrôle / SPS message
ABF / instructeur / authority message
insurance / MAF / expert / legal-facing message
```

Decision Zeus: accepted.

Repository state: documented non-implemented.

Target: keep architecture external communication behind explicit User Decision Gate.

Boundary:

```text
Hermes drafts.
Pantheon governs status and approval.
The user signs and sends.
```

## Refused

### 1. Bulk migration of `domains/architecture_fr`

Decision Zeus: refused.

Reason: contradicts issue #7 and current Pantheon Next migration discipline.

Repository state: non applicable.

### 2. Runtime/API material from the historical predecessor

Decision Zeus: refused inside Pantheon Next.

Includes:

```text
runtime endpoints
execution APIs
installer logic
scheduler
queue
router
Docker / NAS deployment
operations setup
```

Such material may be reconsidered only as an adapter or external runtime implementation outside Pantheon.

### 3. Memory folders as canonical Pantheon memory

Decision Zeus: refused.

The former structure is useful as vocabulary history:

```text
memory/session
memory/candidates
memory/project
memory/system
```

But it must not become the Registre Probatoire.

Current rule remains:

```text
Knowledge informs.
Context bounds.
Evidence supports.
Memory persists.
Doctrine governs.
```

### 4. Active skills or workflows inherited from OS

Decision Zeus: refused.

Any inherited skill or workflow starts as candidate only.

Runtime success, historical presence or repeated use does not grant admission.

### 5. OpenWebUI mapping as authority

Decision Zeus: refused.

OpenWebUI may expose and organize.

It does not govern, validate, approve, remember or authorize.

## To verify

### 1. Role vocabulary

The historical predecessor used additional architecture-domain roles:

```text
HECATE
CHRONOS
HESTIA
MNEMOSYNE
DEMETER
PROMETHEUS
```

Decision Zeus: to verify.

Question: should these remain internal review angles, be folded into existing roles, or stay domain-specific aliases?

Risk: role sprawl and confusion between role viewpoint, Hermes profile and autonomous agent.

### 2. Source tiers and reliability levels

The historical predecessor used T0-T5 and R0-R5 style source and reliability tiers.

Pantheon Next has broader evidence, certainty and approval axes.

Decision Zeus: to verify.

Question: map historical tiers to current axes or keep them as architecture-domain aliases?

Risk: competing classification systems.

### 3. Workflow Event ledger

The historical predecessor centered governance around workflow events.

Pantheon Next now has:

```text
Evidence Packs
Run Trace View
Outcome Observation Candidates
Registre Probatoire
impact review
register links
Repository Review Watcher
```

Decision Zeus: to verify.

Question: rename the old idea to `Governance Event`, or absorb it into trace and evidence doctrine?

Risk: treating runtime state as evidence or memory.

### 4. `architecture_fr` identifier

Decision Zeus: to verify.

Question: keep `architecture_fr` as internal pack id, or expose a more general public label while retaining the id internally?

Risk: overfitting to one jurisdiction versus losing the useful French MOE specificity.

## To arbitrate

### A. Target document

Options:

```text
1. Fold accepted material into AGENCY_DOMAIN_PACK.md.
2. Create DOMAIN_PACK_RECONCILIATION.md.
3. Create DOMAIN_PACK_SPEC.md aligned with DOMAIN_PACK_SPEC.md.
```

Recommendation: start with this validation-only note, then create a proper `DOMAIN_PACK_SPEC.md` only after arbitration.

### B. Output formats location

Options:

```text
1. Section inside architecture domain pack.
2. Dedicated candidate doc.
3. Non-executable templates under templates/.
```

Recommendation: start inside the architecture pack. Split only if the catalogue becomes too long or starts behaving like runtime prompt material.

### C. Knowledge registry location

Options:

```text
1. templates/knowledge_registry_architecture.example.yaml
2. docs/domain-packs/architecture/KNOWLEDGE_REGISTRY_BLUEPRINT.md
3. external adapters repository
```

Recommendation: blueprint in Pantheon, runnable mapping outside Pantheon.

## Proposed next PR after this note

A later PR may distill one accepted item at a time.

Recommended order:

```text
1. Architecture source policy.
2. Architecture output format catalogue.
3. Knowledge registry blueprint.
4. Architecture capability candidate list.
5. Role vocabulary reconciliation.
```

Each PR should remain small, reviewable and non-executable.

No protected path should be touched unless separately approved.

## Boundary

This document does not modify:

```text
schemas/
tests/
operations/
platform/
Docker files
.env files
pyproject.toml
CLAUDE.md
```

It does not implement anything.

It does not promote any historical material into doctrine by itself.

It classifies the useful material so a later PR can distill it cleanly.

## Final rule

The historical predecessor provided useful architecture-domain material.

Pantheon Next decides what becomes doctrine.

The accepted pieces become candidates.

The refused pieces stay outside.

The verified pieces may become support doctrine.

The arbitrated pieces require Zeus decision.

The human decides.
