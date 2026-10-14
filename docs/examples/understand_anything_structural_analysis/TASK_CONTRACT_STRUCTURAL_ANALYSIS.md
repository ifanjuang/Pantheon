# Task Contract Example — Structural Analysis

Status: fictional example — non-executable.

This is an illustrative Task Contract for a hypothetical Hermes-side structural analysis using an external tool such as Understand-Anything.

It does not authorize execution.

It does not install a skill.

It does not define command syntax.

It does not mutate a repository.

## Identity

```text
contract_id: TC-STRUCTURAL-ANALYSIS-EXAMPLE-001
contract_type: STRUCTURAL_ANALYSIS
status: draft_example
owner_role: ATHENA
creation_source: OpenWebUI user request
scope_type: repository
approval_state: not_approved
```

## User request

```text
Help me understand this repository before I decide whether to reorganize the documentation or propose a patch.
```

## Intent

Produce a structural-analysis candidate for the authorized repository scope.

The result should help the user review repository organization, likely impact zones and possible documentation cleanup areas.

The result must remain candidate-only.

## Scope

### Included

```text
repository: fictive/example-repository
branch: main
paths:
  - README.md
  - docs/
  - src/
  - tests/
```

### Excluded

```text
excluded:
  - .env
  - secrets
  - credentials
  - private client data
  - unrelated repositories
  - generated caches
  - deployment configuration not needed for review
  - Registre Probatoire entry
  - doctrine mutation
```

## Role viewpoints

```text
ATHENA:
  structure the task and identify analysis boundaries

ARGOS:
  verify source scope, branch, provenance and evidence status

THEMIS:
  check risk, approval boundaries, protected areas and memory implications

HEPHAISTOS:
  prepare the external structural-analysis candidate through Hermes if authorized

APOLLO:
  review clarity, completeness and delivery-readiness of the resulting report

ZEUS:
  arbitrate if graph interpretation affects protected files, doctrine, memory or repository mutation
```

These are governance viewpoints.

They are not runtime agents.

## Constraints

```text
read_only_first: true
automatic_installation_allowed: false
automatic_repository_hook_allowed: false
automatic_graph_commit_allowed: false
automatic_memory_promotion_allowed: false
doctrine_mutation_allowed: false
repository_mutation_allowed: false
external_transmission_allowed: false
```

## Approval expectations

```text
C0:
  allowed for read-only analysis of authorized, non-sensitive repository material

C2:
  required if the result is used to prepare a patch candidate or documentation rewrite candidate

C3:
  required if the result affects governance doctrine or protected governance documents

C4:
  required before any external tool installation, repository hook, credential access or trust-boundary change
```

This example remains unapproved.

## Expected evidence

The resulting Evidence Pack Candidate should include:

```text
source repository reference
branch or commit reference when available
included and excluded scope
structural graph artifact reference if generated
summary of deterministic structural findings
summary of semantic or LLM-inferred findings
risk notes
limitations
approval state
memory state
```

## Allowed outputs

```text
Structural Analysis Report Candidate
Diff Impact Report Candidate
Onboarding Guide Candidate
Evidence Pack Candidate
Capability Gap
User Decision Gate Candidate
```

## Forbidden outputs

```text
Registre Probatoire entry
doctrine mutation
repository mutation
automatic graph commit
automatic repository hook
automatic skill installation
unreviewed patch merge
GraphRAG runtime
knowledge graph runtime
external transmission
```

## Memory rules

```text
memory_output: none_by_default
memory_candidate_allowed: only_if_explicitly_requested_and_evidence_linked
canonical_memory_allowed: false
```

Generated graphs, summaries, repeated findings and dashboard views must not become memory by themselves.

## Risk notes

```text
static graph may be incomplete
semantic interpretation may be wrong
business-domain mapping is hypothesis
graph may become stale
dashboard may create false authority
tool output may hide scope gaps
```

## Completion criteria

The task is complete only if the output remains reviewable and candidate-labeled:

```text
scope recorded
sources recorded
assumptions recorded
risks recorded
candidate outputs labeled
memory default is none
approval state explicit
forbidden actions not performed
```

## Final status

```text
produced_status: draft_example_only
execution_status: not_executed
approval_status: not_approved
memory_status: none
```
