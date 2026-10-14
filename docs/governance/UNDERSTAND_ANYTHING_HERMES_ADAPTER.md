# Understand-Anything Hermes Adapter

Status: support doctrine — Hermes Skill Candidate specification, not implemented.
Boundary profile: candidate_support_note.

This document defines how Understand-Anything may be considered as a bounded Hermes-side structural analysis capability.

It does not install Understand-Anything.

It does not install Hermes skills.

It does not create a Pantheon runtime, plugin manager, tool runtime, GraphRAG runtime, knowledge graph runtime, scheduler, queue, provider router, automatic memory promotion mechanism or OpenWebUI extension.

## Purpose

Understand-Anything may be useful when a user or reviewer needs to understand the structure of a repository, documentation set or knowledge base before producing a patch, review, onboarding note, architecture analysis or impact assessment.

Pantheon may govern this through a Hermes Skill Candidate called:

```text
understand_anything_structural_analysis
```

The capability exists to produce structural evidence candidates.

It must not become a source of truth.

## Classification

```text
capability_type: External Structural Intelligence Tool
execution_layer: Hermes Agent
exposure_layer: OpenWebUI
validation_layer: Pantheon Next
status: optional_skill_candidate
installation_state: not_installed_by_pantheon
memory_state: non_canonical
```

## Scope

Allowed scope:

```text
repository structure review
documentation structure review
knowledge-base relationship review
diff impact review
onboarding guide candidate
architecture overview candidate
business-domain mapping hypothesis
```

Excluded scope:

```text
Canonizing repository architecture
Canonizing business process truth
Installing skills automatically
Installing repository hooks automatically
Promoting generated graph output to memory
Using the graph as GraphRAG runtime
Using the dashboard as cockpit authority
Mutating Pantheon doctrine without approval
```

## Required Task Contract

Any Understand-Anything execution for Pantheon-governed work requires a Task Contract when it touches a repository, documentation set, professional dossier, protected governance area or memory-sensitive output.

Recommended Task Contract type:

```text
STRUCTURAL_ANALYSIS
```

Minimal Task Contract fields:

```text
Identity
Intent
Scope
Roles
Constraints
Approvals
Expected Evidence
Allowed Outputs
Forbidden Outputs
Memory Rules
Risk Notes
```

### Example Task Contract outline

```text
Identity:
  id: TC-STRUCTURAL-ANALYSIS-[date]-[short-scope]
  owner_role: ATHENA
  creation_source: OpenWebUI user request

Intent:
  Produce a structural analysis candidate for the authorized repository or documentation scope.

Scope:
  included:
    - named repository, branch or documentation folder
    - selected subdirectories if applicable
  excluded:
    - unrelated repositories
    - secrets
    - runtime credentials
    - generated caches unless explicitly authorized
    - Registre Probatoire entry mutation

Roles:
  ATHENA: structure and task decomposition
  ARGOS: source, provenance and version check
  THEMIS: risk and approval boundaries
  HEPHAISTOS: tool execution candidate
  APOLLO: readability and delivery-readiness review
  ZEUS: status arbitration if graph interpretation affects doctrine, memory or protected output

Constraints:
  - read-first posture
  - no automatic installation by Pantheon
  - no automatic repository hook
  - no automatic graph commit
  - no memory promotion
  - no doctrine mutation
  - no external transmission

Approvals:
  - C0 for read-only review of supplied public repository material
  - C2 or higher when output influences a patch, governance file or implementation decision
  - C3 or higher when doctrine interpretation or protected governance files are affected
  - C4 or higher for installation, hook, credential, provider or trust-boundary change

Expected Evidence:
  - repository or documentation source reference
  - branch, commit or version when available
  - tool output artifact reference
  - summary of deterministic structural findings
  - summary of LLM-inferred findings
  - limitations and uncertainty
  - forbidden-output confirmation

Allowed Outputs:
  - Structural Analysis Report Candidate
  - Diff Impact Report Candidate
  - Onboarding Guide Candidate
  - Evidence Pack Candidate
  - Capability Gap
  - User Decision Gate Candidate

Forbidden Outputs:
  - Registre Probatoire entry
  - doctrine mutation
  - automatic install plan execution
  - repository hook installation
  - automatic graph commit
  - unreviewed patch merge
  - GraphRAG runtime proposal as implementation

Memory Rules:
  - no memory by default
  - Register Candidate only if explicitly requested and evidence-linked
  - generated graph is not memory
  - repeated structural finding is not memory

Risk Notes:
  - static graph may be incomplete
  - semantic interpretation may be wrong
  - business-domain mapping is hypothesis
  - generated graph may become stale
  - dashboard can create false authority
```

## Allowed Hermes-side commands

Allowed only when the Task Contract authorizes them and the tool is already installed in the Hermes sandbox:

```text
understand project within authorized scope
open dashboard for review
ask scoped questions about graph
explain specific file or function
produce diff impact report
produce onboarding guide candidate
produce domain map hypothesis
produce knowledge-base relationship map hypothesis
```

This document intentionally avoids operational command syntax.

Operational syntax must be verified against current official project documentation before use.

## Forbidden Hermes-side actions

Hermes must not:

```text
install Understand-Anything without explicit approval
enable automatic graph update hooks by default
commit generated graph artifacts by default
write to Pantheon governance files because the graph suggests it
promote graph findings into a Registre Probatoire entry
broaden scope beyond the Task Contract
access unrelated OpenWebUI Knowledge Bases
use graph output as proof without Evidence Pack review
use the dashboard as cockpit authority
hide tool limitations from the Evidence Pack
```

## Evidence Pack Candidate format

An Understand-Anything run may return an Evidence Pack Candidate with this shape:

```text
Identity:
  evidence_pack_id:
  linked_task_contract:
  produced_by: Hermes Agent / Understand-Anything Skill Candidate
  status: candidate

Sources:
  - repository_url_or_identifier:
  - branch_or_commit:
  - included_paths:
  - excluded_paths:
  - documentation_scope:

Actions:
  - structural analysis performed
  - dashboard or graph artifact produced
  - diff impact checked, if applicable
  - domain or knowledge map generated, if applicable

Artifacts:
  - knowledge_graph_reference:
  - dashboard_reference:
  - summary_report_reference:
  - diff_report_reference:
  - onboarding_report_reference:

Findings:
  deterministic_structural_findings:
  semantic_interpretation_findings:
  domain_hypotheses:
  dependency_or_impact_notes:

Risks:
  - partial visibility
  - stale graph risk
  - LLM interpretation risk
  - false authority risk
  - scope mismatch risk

Reviews:
  ATHENA:
  ARGOS:
  THEMIS:
  HEPHAISTOS:
  APOLLO:
  ZEUS:

Register Candidates:
  - none by default

Approval State:
  status: under_review
  required_level:
  user_decision_gate:
```

## OpenWebUI workflow

OpenWebUI may expose the workflow as a visible cockpit sequence:

```text
1. User requests structural analysis.
2. OpenWebUI shows the proposed scope.
3. Pantheon frames or revises a Task Contract.
4. User approves the task boundary when required.
5. Hermes executes the external structural analysis tool in its own sandbox.
6. Hermes returns artifacts and an Evidence Pack Candidate.
7. OpenWebUI displays the graph, summary, limitations and governance status.
8. Pantheon classifies the output as candidate, under review, rejected, deferred or approved for a narrow use.
9. User Decision Gate opens if graph interpretation affects protected work, installation, memory or doctrine.
10. Only separately approved outputs may influence delivery or memory.
```

OpenWebUI may display:

```text
Task Contract
scope summary
artifact references
graph dashboard link
Evidence Pack Candidate
risk notes
review status
User Decision Gate options
```

OpenWebUI must not display the graph as canonical architecture truth.

## Role activation guidance

Suggested role viewpoints:

| Trigger | Roles |
|---|---|
| simple repository orientation | ATHENA + HEPHAISTOS |
| source/provenance uncertainty | ATHENA + ARGOS + HEPHAISTOS |
| patch or diff impact | ATHENA + HEPHAISTOS + APOLLO |
| protected governance files | ATHENA + ARGOS + THEMIS + HEPHAISTOS + ZEUS |
| memory or doctrine implication | ARGOS + THEMIS + ZEUS |
| user-facing delivery | APOLLO + IRIS + required approval |

These are governance viewpoints.

They are not a runtime role team.

## User Decision Gate template

Open a User Decision Gate when the graph output creates a decision beyond analysis.

```text
Discord detected

Object of conflict:
The generated graph suggests a structural or business-domain conclusion that may affect repository mutation, doctrine, memory or protected workflow design.

Role positions:
- ATHENA: graph helps structure the repository view, but scope may be incomplete.
- ARGOS: graph source, branch and generated artifact need provenance.
- THEMIS: generated relationships are not approval and must not mutate doctrine or memory.
- HEPHAISTOS: tool output is usable as an artifact candidate.
- APOLLO: summary may be useful for review if limitations stay visible.
- ZEUS: human decision required if the graph influences protected work.

Options:
1. Continue as draft-only structural analysis.
2. Request more source/provenance evidence.
3. Authorize a narrow patch or documentation proposal.
4. Reject graph-based conclusion as insufficient.
5. Open a separate Register Candidate review.

Recommended procedure:
Use the graph as candidate evidence only. Do not promote, commit or install anything automatically.

Decision effects:
- output: candidate unless separately approved
- evidence: may support an Evidence Pack Candidate
- approval: required for protected impact
- memory: none by default
- transmission: blocked unless separately authorized
```

## Activation and deactivation

Recommended status lifecycle:

```text
detected
candidate
sandbox_enabled
project_enabled
task_authorized
suspended
rejected
```

Activation means only:

```text
eligible for task-bound Hermes execution under a Task Contract
```

Activation does not mean:

```text
installed by Pantheon
approved globally
available for all projects
authorized to mutate repositories
allowed to create memory
```

## Security posture

The capability touches repository structure and may expose source code, documentation topology, business-domain concepts, hidden dependencies and generated artifacts.

Minimum security posture:

```text
read-only first
sandbox before project use
no secrets in context
no credential files in scope
no generated graph publication by default
no external sharing without approval
review installer and dependencies before any installation
record artifacts and risks in Evidence Pack Candidate
```

## Examples

See:

```text
docs/examples/understand_anything_structural_analysis/
```

Those examples are fictional and non-executable.

They show the expected shape of a `STRUCTURAL_ANALYSIS` Task Contract and an Evidence Pack Candidate without installing, running, committing or canonizing any external graph output.

## Final rule

```text
Understand-Anything may be a microscope.
It must not become the memory, the judge, the cockpit or the runtime.
```