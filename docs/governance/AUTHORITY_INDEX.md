# Pantheon Next — Authority Index

Status: active support doctrine — authority map, repository status vocabulary and sensitive-path guardrail.

This document is a governance index.

It does not implement a runtime, schema, test, operation, platform component, Docker configuration, environment setting, approval engine, memory engine, scheduler, queue, provider router, plugin manager or external action.

```text
Optional compatible runtime client       -> runtime interaction
Hermes Agent                             -> external execution runtime
Runtime adapter / Hermes                 -> PEP for consequential effects
Pantheon Cockpit                         -> governed Cards, status, Evidence gaps and decisions
Pantheon policy service                  -> bounded deterministic PDP interface
Pantheon Next                            -> governance, authority and PDP semantics
Human                                    -> consequential decision when required
```

## Purpose

Pantheon Next already distinguishes doctrine, support doctrine, candidates, references, examples and implementation artifacts.

This index makes that distinction explicit so future work does not silently promote a draft, discussion, example, tool note, schema candidate or implementation artifact into authority.

It answers one practical question:

```text
What status does this repository item have, and what may it decide?
```

## Authority classes

### Canonical doctrine

Canonical doctrine defines binding Pantheon governance rules.

A document is canonical when it governs consequential decisions such as truth status, memory status, approval, evidence, scope, external action, role procedure or professional-domain boundaries.

Canonical doctrine overrides candidates, examples, discussions, comments, implementation notes and external references.

### Active support doctrine

Active support doctrine coordinates, clarifies or operationalizes canonical doctrine without replacing it.

It may define placement rules, indexes, checklists, interpretation guides, status maps, review methods, prompt placement rules, bridge boundaries, template discipline or activation semantics.

Support doctrine must remain compatible with canonical doctrine.

### Candidate / to verify

Candidate material proposes a useful orientation but is not yet promoted.

It may be referenced, reviewed or tested.

It must not be treated as binding doctrine until explicit review promotes it.

### Validation-only

Validation-only material tests coherence, audits a position or records a reconciliation.

It may support a decision.

It does not create doctrine by itself.

### External reference

External references describe tools, ecosystems, standards, architectural patterns or adjacent frameworks.

They may inform Pantheon.

They do not govern Pantheon.

### Implementation artifact

Implementation artifacts include executable or machine-checked material such as schemas, tests, code, platform components, operations procedures, Docker files and packaging files.

They may instantiate doctrine.

They must not silently redefine doctrine.

### Voluntarily absent

A voluntarily absent item is excluded by doctrine.

This is an active status, not a gap.

Examples include internal execution runtime, hidden scheduler, autonomous approval engine, automatic memory promotion engine or unrestricted plugin manager when such items would collapse governance into execution.

### Obsolete / refused

Obsolete or refused material has been superseded, rejected or moved outside scope.

It must not be reused as authority unless explicitly reinstated.

## Promotion rule — the referent (B-5)

A candidate does not become active doctrine by age or repetition. Promoting a
`candidate` to `active` (or `implemented`) requires a **referent** — at least one of:

- a schema that encodes it;
- a test that exercises it;
- an end-to-end example that runs it;
- a read-only verification surface (`mcp-server/`) that checks it;
- an explicit, dated human decision with a durable repository referent.

For the human-decision form, a bounded referent such as `PR #<n>` or `issue #<n>`
may be used. The referent identifies where the human decision is recorded; a PR,
issue, merge, green CI result or automation output does not become a human
decision merely by existing.

Without a referent, the material stays a note or a candidate; it is not promoted.
This keeps the doctrine growing only where it anchors to something executable or
explicitly decided (arbitration B-5). The rule governs promotion; it does not
demote existing entries by itself.

### Candidacy aging signal

The promotion rule says how a candidate leaves that state. It says nothing about
a candidate that never leaves it, and the repository currently cannot tell a
candidate deliberately kept as one from a candidate nobody has revisited.

`.github/scripts/check_candidacy_aging.py` reports that difference. It is a
signal, not a gate: age promotes nothing, and the check does not fail on age. It
derives each candidate's start from the commit history rather than a written
date, and reports a candidate whose start predates this repository as
`imported` instead of giving it a fabricated age.

A document may restart its own clock by recording a dated human review, in the
same header block as `Status:`, citing a bounded decision referent in this
repository:

```text
Candidacy reviewed: <ISO date> (PR #<n>)
Candidacy reviewed: <ISO date> (issue #<n>)
```

For a PR or issue marker, the checker validates the bounded reference
syntax but does not infer human authority from GitHub state. The cited discussion
must contain the explicit human review. Existence, merge, CI success or automation
output alone is not review and does not authorize promotion.

The line is optional and adds no authority by itself — it records that a human
looked, when, and where that decision is recorded.

## Current authority map

A row whose path is a directory (ending in `/`) or a glob (containing `*`) is a **grouped row**: it indexes every governance document it matches, so individual members are covered without a separate row. The read-only coverage check honors grouped rows declared in this index and in the registered sub-indexes — a candidate under `docs/governance/reference_reviews/`, `docs/governance/rites/` or matching `docs/governance/DATA_PLATFORM_*.md` is considered indexed by its group. Coverage is visibility only; it does not promote a member's authority class.

Detailed rows live in the sub-indexes listed in the Sub-index map below. This master file keeps only the rows that anchor the map itself:

A sub-index under `docs/governance/authority/` that is itself registered in this file (its path cited here) extends the coverage corpus: a candidate row may live in a registered sub-index instead of this table. An unregistered file under `authority/` extends nothing — this master index remains the sole interpreter and the single registration point (decomposition plan step PR C, approved 2026-07-05).

| Path or area | Authority class | Repo state | Notes |
|---|---|---|---|
| `docs/governance/AUTHORITY_INDEX.md` | active support doctrine | implemented as documentation | Authority vocabulary, rules and sub-index map. This file remains the single authority interpreter; sub-indexes only list placement. |
| `docs/governance/authority/` | candidate support maps | implemented as documentation / awaiting review | Grouped row for the six sub-indexes per `AUTHORITY_INDEX_DECOMPOSITION_PLAN.md`. All six are populated; they list placement only and must not override this index's vocabulary. |
| `docs/governance/SOURCE_RETRIEVAL_IMPLEMENTATION_COVERAGE.md` | validation-only | documented implementation inventory | Observational doctrine-to-implementation coverage map for source ingestion and retrieval. It adds no runtime, authority object, adoption or activation. |

## Sub-index map

Sub-indexes decompose the Current authority map by area, per `docs/governance/AUTHORITY_INDEX_DECOMPOSITION_PLAN.md`. All six sub-indexes are populated; each area's detailed rows live in its sub-index, and rows were moved verbatim without changing any authority class or repo state. The read-only coverage check (`.github/scripts/check_index_coverage.py`) reads this file plus the sub-indexes under `docs/governance/authority/`, so a candidate document is indexed when it appears in a table row of either — a prose mention does not count; indexing is a deliberate row. A sub-index may only list where documents sit; it must not override the authority vocabulary, promotion rule, placement test, tool naming rule, terminology boundary rule or sensitive-path guardrail defined here.

| Area | Sub-index | Authority class | Rule |
|---|---|---|---|
| Governance kernel | `docs/governance/authority/GOVERNANCE_AUTHORITY_INDEX.md` | candidate support map | Must not override authority vocabulary. |
| Architecture domain | `docs/governance/authority/ARCHITECTURE_AUTHORITY_INDEX.md` | candidate support map | Domain-specific map only. |
| Runtime adapters | `docs/governance/authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md` | candidate support map | Adapter placement only. |
| Implementation artifacts | `docs/governance/authority/IMPLEMENTATION_ARTIFACTS_AUTHORITY_INDEX.md` | candidate support map | Protected-path status visibility; it relaxes no protected path. |
| External references | `docs/governance/authority/EXTERNAL_REFERENCES_AUTHORITY_INDEX.md` | candidate support map | Non-authoritative unless distilled. |
| Obsolete / absent | `docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md` | candidate refusal/absence map | Does not reinstate refused material. |

## Bootstrap stub rule

Historical bootstrap stubs may appear in roadmap, migration or discussion material before a concrete governed document exists.

They remain:

```text
candidate / stub reference
repo state: documented non-implemented
```

until this authority index explicitly promotes a concrete path.

A roadmap mention, filename placeholder or removed `STATUS.md` stub list does not make the item canonical, implemented, active support doctrine or voluntarily absent.

Declared historical stubs are recorded in `docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md`; this rule stays here and governs how those records are read.

## Placement test

For any capability, module, template, skill, connector, workflow or data platform component, ask:

```text
If this goes wrong, can it produce a false truth,
an unapproved external effect,
a wrong memory,
an invalid approval,
an illegitimate scope expansion,
or an unauthorized action?
```

If the answer is no, it is a feature and belongs in the appropriate tool or runtime.

If the answer is yes, Pantheon governs the decision through rules, status, evidence, memory, approval and scope.

Execution remains outside Pantheon unless a separately approved implementation artifact exists.

```text
Governing is not implementing.
```

## Tool naming rule

Generic governance documents should use abstract roles:

- exposure surface;
- execution runtime;
- observability layer;
- connector gateway;
- data registry;
- administration cockpit.

Specific product names belong in bindings, adapters, integration notes, reference reviews or other non-generic documents whose subject is the tool relationship.

## Terminology boundary rule

`TERMINOLOGY_BOUNDARIES.md` defines controlled terms, reserved runtime words, public aliases and progressive cleanup rules.

New governance writing should prefer:

```text
Case / Affaire
Situation
Method / Méthode
Approach / Démarche
Contract / Contrat
Scope / Périmètre
Corpus
Source
Connaissance
Context / Contexte
Capability / Capacité
Competence / Compétence
Guide de compétence
Ressource de compétence
Template
Assertion
Evidence / Preuve
Gate / Seuil
Approval / Approbation
Register / Registre
Recall / Rappel
Trace
Role / Rôle
Handoff / Relais
Surface
```

Runtime and host-system words remain reserved unless explicitly qualified:

```text
Runtime
Workflow
Skill
Tool
Plugin
Job
Action
State
Run
Node
Edge
Checkpoint
Thread
Queue
Scheduler
Worker
```

This terminology rule does not rename schemas or existing fields by itself. It governs future language and progressive cleanup proposals.

## Domain pack rule

A domain pack is a governed professional method.

It does not advise, validate, approve, execute, send or memorize by itself.

Common envelope:

```text
Task Contract in
-> module
-> Result Candidate + Evidence Pack Candidate out
```

The method lives in Pantheon.

Display may live in the exposure surface.

Execution may live in the execution runtime.

Final truth, approval, memory and external-action status remain governed.

## External runtime memory adapter rule

External runtime memory may store, recall, rank, summarize, checkpoint or trace.

It may propose:

```text
Register Candidates
Evidence Pack Candidates
Trace References
Runtime State References
Review Queue signals
```

It must not produce:

```text
Registre Probatoire entries
validated truth
approval
scope decisions
external-action authorization
Pantheon runtime state
```

Any adapter or product-specific review remains documented non-implemented until a separate approved implementation exists outside Pantheon.

## Data platform rule

The data platform remains candidate unless explicitly promoted.

Principle:

```text
The database records.
The workflow proposes.
The evidence supports.
The approval validates.
The human decides.
```

A data platform must not turn Pantheon into an ERP, runtime, scheduler, queue, approval engine or memory engine.

## Sensitive-path guardrail

This index is allowed to live under `docs/governance/`.

It must not require modification of:

- `schemas/`;
- `tests/`;
- `pyproject.toml`;
- `operations/`;
- `platform/`;
- `CLAUDE.md`;
- `mcp-server/`;
- GitHub Actions / CI scripts;
- Docker files;
- `.env` files.

Those paths require explicit approval in their own work package.
