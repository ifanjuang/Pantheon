# Evidence Pack Candidate Example — Structural Analysis

Status: fictional example — non-executable.

This example shows how a structural-analysis result could be represented as an Evidence Pack Candidate after Hermes uses an external tool such as Understand-Anything under a governed Task Contract.

It does not prove anything by itself.

It does not approve any output.

It does not create memory.

It does not authorize repository mutation.

## Identity

```text
evidence_pack_id: EP-STRUCTURAL-ANALYSIS-EXAMPLE-001
linked_task_contract: TC-STRUCTURAL-ANALYSIS-EXAMPLE-001
status: candidate
produced_by: Hermes Agent external structural-analysis capability
review_state: under_review
approval_state: not_approved
memory_state: none
```

## Sources

```text
source_type: repository
repository: fictive/example-repository
branch: main
commit: unknown_in_example
included_paths:
  - README.md
  - docs/
  - src/
  - tests/
excluded_paths:
  - .env
  - secrets
  - credentials
  - private client data
  - generated caches
```

## Actions summary

```text
read authorized repository scope
produced structural graph candidate
produced architecture overview candidate
produced documentation hotspot candidate
separated deterministic findings from semantic interpretation
recorded limitations and risks
```

No repository mutation occurred.

No generated graph was committed.

No memory was promoted.

No external transmission occurred.

## Artifacts

```text
structural_graph_candidate: artifact reference only, not included in this example
dashboard_candidate: artifact reference only, not a cockpit authority
summary_report_candidate: included as summarized findings below
diff_impact_candidate: not produced in this example
onboarding_candidate: not produced in this example
```

## Deterministic structural findings

These findings would be based on static structure if the external tool produced them.

```text
finding_001:
  claim: repository contains separate documentation, source and test areas
  support: observed path groups in authorized scope
  status: candidate_evidence

finding_002:
  claim: documentation appears separate from source implementation
  support: docs/ and src/ are distinct path groups
  status: candidate_evidence

finding_003:
  claim: tests are present in a dedicated path group
  support: tests/ exists in authorized scope
  status: candidate_evidence
```

## Semantic interpretation findings

These findings are interpretive and require more caution.

```text
interpretation_001:
  claim: documentation may need alignment with source structure
  support: inferred from graph relation candidate
  status: hypothesis
  limitation: requires human review of actual files

interpretation_002:
  claim: onboarding could start from README then docs then source entry points
  support: generated tour candidate
  status: usable_for_draft
  limitation: not validated against developer workflow
```

## Domain hypotheses

```text
domain_hypothesis_001:
  claim: repository may contain a separation between public documentation and implementation details
  status: hypothesis
  risk: could be wrong if docs are stale or partial
```

No business-domain claim is validated by this Evidence Pack Candidate.

## Risks and limitations

```text
risk_001:
  type: partial_visibility
  note: only authorized paths were included
  mitigation: request broader scope only if needed and approved

risk_002:
  type: semantic_interpretation_risk
  note: LLM summaries may overstate relationships
  mitigation: preserve distinction between deterministic structure and interpretation

risk_003:
  type: false_authority
  note: dashboard and graph can look more authoritative than they are
  mitigation: label artifacts as candidate and require review before use

risk_004:
  type: staleness
  note: generated graph may become stale after repository changes
  mitigation: record branch or commit before relying on result

risk_005:
  type: memory_drift
  note: repeated structural findings may be mistaken for memory
  mitigation: no memory output by default
```

## Role review candidates

```text
ATHENA:
  status: ok_with_reserve
  note: structure is useful for orientation, but scope remains limited

ARGOS:
  status: source_insufficient
  note: commit reference is unknown in this fictional example

THEMIS:
  status: approval_required
  note: any repository mutation, installation or graph commit would require separate approval

HEPHAISTOS:
  status: ready_for_review
  note: artifact candidate could be produced externally, but this example did not execute anything

APOLLO:
  status: ok_with_reserve
  note: output is readable if candidate status and limitations remain visible

ZEUS:
  status: proceed_as_draft
  note: no delivery, memory or mutation should proceed from this candidate alone
```

## User Decision Gate

Not required for draft-only review.

Would be required if the user asks to:

```text
install external tool
commit graph artifact
rewrite protected governance files
promote a structural finding to memory
use domain graph as business authority
merge or deploy a patch
```

## Register Candidates

```text
none
```

Reason:

```text
structural graph output is not memory
generated summaries are not memory
candidate evidence is not memory
```

## Approval state

```text
approval_required_for_delivery: true
approval_required_for_repository_mutation: true
approval_required_for_memory: true
current_approval_level: none
current_status: candidate_under_review
```

## Output status

```text
Structural Analysis Report Candidate: usable_for_draft_only
Evidence Pack Candidate: under_review
Registre Probatoire entry: not_created
Repository Mutation: not_authorized
External Transmission: not_authorized
```

## Final rule

```text
The graph may help review the repository.
It does not decide what the repository is.
It does not approve what should change.
It does not remember anything by itself.
```
