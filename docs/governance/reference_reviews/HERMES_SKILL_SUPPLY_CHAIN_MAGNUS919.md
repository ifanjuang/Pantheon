# Hermes Skill Supply Chain — magnus919/agent-skills

Status: external reference — to verify.

Reviewed source: `https://github.com/magnus919/agent-skills`
Review date: 2026-07-26

## Purpose

This review evaluates `magnus919/agent-skills` as an external source of Hermes-compatible skills and uses Haystack to test the separation between source discovery, skill review and capability binding.

```text
Skill Source
!= Skill Candidate
!= Capability Binding
!= Installed Skill
!= Approved Skill
!= Activated Skill
!= Task-authorized Skill
```

The review installs nothing, activates nothing and adopts no framework dependency.

## Boundary

```text
exposed_by: OpenWebUI or another cockpit may display source, binding and lifecycle state.
executed_by: Hermes owns discovery, loading, installation and execution when separately configured.
governed_by: Pantheon governs placement, status, scope, evidence expectations, installation proposals, activation and consequential gates.
approved_by: human review where installation, activation, sensitive scope, breaking updates or consequential effects require it.
forbidden: Pantheon as skill hub, plugin manager, installer, updater, runtime, automatic trust authority or automatic approval engine.
```

## Source classification

`magnus919/agent-skills` is retained as an external Hermes skill-source candidate.

```text
source available != install instruction
source reviewed != every contained skill reviewed
skill discovered != skill selected
update detected != update authorized
```

Recommended source posture:

```yaml
skill_source:
  source_id: magnus919-agent-skills
  upstream: https://github.com/magnus919/agent-skills
  source_kind: repository
  trust_status: external
  discovery_allowed: true
  auto_install: false
  auto_update: false
```

A future source review may qualify provenance, licence, maintainer activity and supply-chain risk. That still would not approve each skill in the repository.

## Skill candidate shape

Candidate support shape only; not an executable schema:

```yaml
skill_candidate:
  skill_id:
  source_id:
  upstream_path:
  capability_slot:
  binding_target:
  permissions_required:
  network_behavior:
  filesystem_behavior:
  external_effects:
  sensitive_data_surface:
  install_status:
  health_status:
  update_status:
  activation_status:
  task_authorization_status:
  rollback_expectation:
  review_status:
```

Installation, health, approval, activation and task authorization remain separate axes.

## Haystack arbitration

Haystack and a Haystack skill are two different objects:

```text
Haystack
= external framework / candidate Hermes-side binding

skill: haystack
= instructions/competence allowing Hermes to work with Haystack
```

The review initially left open whether Haystack should sit under the existing `document_parsing_rag_ingestion` slot or whether a separate tool-agnostic capability was justified.

The distinction is now useful independently of Haystack.

A governed document vertical contains separable effects:

```text
document source management
-> extraction / parsing
-> retrieval over already-extracted governed material
-> filtering / ranking / reranking
-> context assembly with provenance
-> Hermes candidate answer
-> Evidence Pack Candidate
-> human review
```

Retrieval remains useful when extraction has already happened, when the corpus is not managed by RAGFlow, and when the selected retrieval engine is replaced. Therefore the abstract capability does not depend on the Haystack product name.

Recommended candidate slot:

```text
knowledge_retrieval_pipeline
```

Abstract function:

```text
retrieve within declared corpus and scope
apply metadata / project / dossier filters
rank and rerank candidates
assemble provenance-linked context
return bounded retrieval candidates and capability gaps
```

The candidate slot does not own source management, document extraction, truth, Evidence admission, canonical memory or approval.

## Relationship to existing slots

```text
document_source_management
  -> optional Paperless-ngx binding

core document extraction / parsing
  -> Docling and OCR candidates

knowledge_retrieval_pipeline
  -> Haystack candidate
  -> LlamaIndex watch / comparison
  -> LangChain watch / comparison

document_parsing_rag_ingestion
  -> RAGFlow remains the integrated-product candidate

bounded_workflow_runtime
  -> LangGraph remains the existing candidate behind Hermes
```

This does not demote RAGFlow. It separates an integrated ingestion/RAG product from a smaller replaceable retrieval capability.

## Candidate binding posture

```text
knowledge_retrieval_pipeline:
  preferred_binding: unbound
  candidate_bindings:
    - Haystack
  watchlist_bindings:
    - LlamaIndex
    - LangChain
  install_status: absent / not established
  health_status: unknown
  update_status: unknown
  activation_status: unavailable
  approval_status: not approved by this review
```

Haystack is not selected as preferred merely because its upstream framework currently supports RAG, retrieval, reranking, pipelines and agent-oriented composition.

## Lifecycle

```text
External Skill Source
-> discovery observation
-> Skill Candidate
-> Capability Slot classification
-> binding review
-> installation proposal
-> human gate where required
-> Hermes installation
-> health/version observation
-> sandbox activation
-> scoped activation
-> task authorization remains separate
```

Pantheon may display and govern the lifecycle state. Hermes or an operator performs lifecycle operations.

## OpenWebUI projection

A future cockpit may expose:

```text
Capability Slot
candidate / selected binding
skill source
install status
health status
version
update status
activation scope
approval state
risk level
rollback expectation
task authorization state
```

Controls such as `propose install`, `propose update`, `request benchmark` and `request activation` are requests or gates, not an installer implementation.

## Decision

```text
magnus919/agent-skills:
  placement: external Hermes skill-source candidate
  install: no
  activate: no
  auto_update: no

knowledge_retrieval_pipeline:
  status: candidate capability distinction
  reason: durable function independent of any single product

Haystack:
  placement: candidate binding for knowledge_retrieval_pipeline
  preferred: no
  installed: not established
  approved: no

LlamaIndex:
  placement: watch / compare for knowledge_retrieval_pipeline

LangChain:
  placement: watch / compare for knowledge_retrieval_pipeline and broader component use

LangGraph:
  placement: unchanged bounded_workflow_runtime candidate

RAGFlow:
  placement: unchanged document_parsing_rag_ingestion candidate
```

## Non-equivalences

```text
skill_source_reviewed != every_skill_reviewed
skill_discovered != skill_selected
skill_selected != skill_installed
skill_installed != skill_approved
skill_healthy != skill_safe
skill_active != task_authorized
framework_available != dependency_adopted
binding_candidate != preferred_binding
update_available != update_authorized
runtime_success != evidence
```
