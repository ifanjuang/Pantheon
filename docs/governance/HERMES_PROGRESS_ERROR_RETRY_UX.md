# Pantheon Next — Hermes Progress, Error, Diagnosis and Bounded Retry UX

Status: candidate support specification — documented non-implemented.
Boundary profile: candidate_support_note.

This document specializes the external-run observation rules used by:

- `DOCUMENT_LIFECYCLE_GOVERNANCE.md`;
- `DOCUMENT_PRODUCTION_LIFECYCLE.md`;
- `HERMES_AUTHORED_CARD_REVIEW_UX.md`;
- `KNOWLEDGE_NAVIGATION_UX.md`;
- `docs/domain-packs/architecture/PROJECT_NAVIGATION_UX.md`.

It defines how the Cockpit should display measurable progress, explicit errors, Hermes diagnosis and bounded retry behavior without making Pantheon a queue, scheduler, worker, repair engine, provider router, installer or automatic approval system.

It implements no polling service, callback receiver, SSE stream, retry worker, exception classifier, log search, Hermes Skill, Cockpit component, queue, scheduler, provider fallback, model switch, configuration mutation or repair runtime.

```text
Hermes reports execution state.
Pantheon governs what may be attempted, retried, changed or escalated.
The Cockpit displays the observed state without inventing progress or success.
```

## 1. Purpose

The Cockpit should not display only a generic `En cours` when Hermes can expose more precise progress.

The preferred order is:

```text
measurable percentage and unit
-> current step and completed steps
-> indeterminate running state
```

When a run fails, the Cockpit must display an explicit error rather than remaining indefinitely in an in-progress state.

Hermes may automatically diagnose errors and retry only within a bounded, pre-authorized repair policy.

```text
error detected != root cause confirmed
root cause proposed != remediation authorized
retry started != problem corrected
fallback available != fallback authorized
runtime recovered != output validated
```

## 2. Progress display hierarchy

### 2.1 Quantified progress

The Cockpit displays a percentage only when Hermes exposes a measurable numerator and denominator or an explicit runtime-calculated percentage with a declared method.

Examples:

```text
OCR — 18 / 42 pages — 43 %
Chunking — 67 / 120 chunks — 56 %
Embeddings — 840 / 1 000 vectors — 84 %
Upload — 38 / 90 MB — 42 %
Archive copy — 2 / 5 artifacts — 40 %
```

Candidate payload:

```yaml
progress:
  mode: quantified
  percent: 42.86
  completed: 18
  total: 42
  unit: pages
  method: executor_measured
  reported_by: hermes
  reported_at:
```

The Cockpit must not derive a percentage from elapsed time alone.

```text
45 seconds elapsed != 45 % complete
three steps completed out of six != 50 % complete
```

unless the execution contract explicitly declares equivalent step weights and Hermes reports that method.

### 2.2 Step progress

When no valid percentage exists, Hermes should expose the current step and step statuses.

```text
Source captured              completed
Context understood           completed
OCR                          running
Markdown normalization       pending
Summary                      pending
Chunking                     pending
Embeddings                   pending
Index publication            pending
```

Candidate payload:

```yaml
progress:
  mode: steps
  current_step: ocr
  steps:
    - step: source_capture
      status: completed
    - step: context_understanding
      status: completed
    - step: ocr
      status: running
    - step: markdown_normalization
      status: pending
```

### 2.3 Indeterminate progress

When Hermes exposes only a running state, the Cockpit displays an indeterminate progress indicator and the last observed state.

```text
Traitement Hermès en cours
Étape détaillée non exposée par le runtime
Dernière mise à jour : 18:42:16
```

It must not fabricate a percentage.

### 2.4 Overall and per-step progress

An overall percentage may be displayed only when Hermes explicitly exposes it.

A per-step percentage may coexist with an overall percentage:

```yaml
run_progress:
  percent: 64
  method: hermes_pipeline_weighted_progress_v1

step_progress:
  step: embeddings
  percent: 35
  completed: 350
  total: 1000
  unit: chunks
```

Pantheon records the reported method. The Cockpit identifies the percentage as runtime-reported rather than an independent Pantheon measurement.

## 3. Progress freshness

Every progress observation must carry a timestamp.

```yaml
progress_observation:
  external_run_id:
  reported_status:
  reported_progress:
  reported_at:
  observed_by_pantheon_at:
  freshness: fresh | stale | unreachable | unknown
```

Candidate display rules:

```text
fresh
= normal progress display

stale
= keep last value but show “Dernière mise à jour il y a …”

unreachable
= display “Hermès inaccessible — état réel inconnu”

unknown
= no reliable external status available
```

```text
progress stopped updating != execution failed
Hermes unreachable != run cancelled
last reported 82 % != currently 82 % with certainty
```

A stale progress bar must not continue animating as though new work were observed.

## 4. Error model

A run error should expose, where available:

```yaml
run_error:
  error_id:
  external_run_id:
  step:
  error_class:
  error_code:
  user_message:
  technical_message_ref:
  occurred_at:
  retryable_candidate:
  last_successful_step:
  partial_output_refs: []
  diagnosis_status:
  remediation_status:
```

### 4.1 Error classes

Candidate classes:

```text
transient_infrastructure
source_access
source_integrity
unsupported_format
extraction_failure
ocr_failure
layout_failure
model_runtime_failure
resource_exhaustion
timeout
network_failure
rate_limit
configuration_failure
binding_unavailable
permission_or_policy_block
output_validation_failure
archive_failure
chunking_failure
embedding_failure
index_publication_failure
retrieval_verification_failure
unknown
```

The Cockpit should show a human-readable message first, with technical details available on demand.

Example:

```text
ERREUR — Embeddings interrompus

720 chunks sur 1 000 ont été traités.
Cause candidate : mémoire GPU insuffisante.
Dernière étape réussie : chunking.
Diagnostic Hermès : en cours.
```

### 4.2 Partial success

A failure in one step does not erase successful prior steps.

```text
archive succeeded + indexing failed
!= complete failure
```

The Cockpit may display:

```text
Indice A archivé
Chunking terminé
Embeddings en erreur
Indexation non publiée
```

The ordinary finalized appearance must depend on the finalization bundle declared for that card.

## 5. Hermes automatic diagnosis

Hermes may automatically inspect available logs, error codes, runtime state and output manifests after a failure.

Candidate operation:

```text
diagnose_run_error
```

Candidate result:

```yaml
error_diagnosis:
  diagnosis_id:
  error_id:
  status: running | candidate_ready | inconclusive | failed
  probable_causes:
    - cause:
      confidence_band:
      supporting_refs: []
  proposed_remediations:
    - remediation_type:
      parameters:
      risk_class:
      requires_new_authorization:
  created_by_binding:
  binding_version:
```

Hermes diagnosis is a candidate interpretation.

```text
Hermes probable cause != confirmed root cause
log pattern matched != remediation safe
```

The Cockpit should distinguish:

```text
Diagnostic en cours
Cause probable identifiée
Diagnostic non concluant
Diagnostic impossible
```

## 6. Automatic retry policy

Automatic retry is permitted only under a bounded policy recorded before or at execution authorization.

Candidate policy:

```yaml
retry_policy:
  automatic_retry_enabled: true
  maximum_attempts: 3
  retryable_error_classes:
    - transient_infrastructure
    - timeout
    - network_failure
    - rate_limit
  backoff_strategy: exponential
  maximum_total_retry_duration:
  same_binding_required: true
  same_model_version_required: true
  same_data_scope_required: true
  same_execution_location_required: true
  parameter_adjustments_allowed: []
  fallback_chain_ref:
  human_confirmation_after_attempt:
```

### 6.1 Safe automatic retries

Typical candidates for automatic retry:

- temporary network failure;
- service timeout;
- rate limit after declared backoff;
- temporary binding unavailability;
- interrupted upload or download with integrity verification;
- idempotent index publication retry;
- transient database connection loss;
- executor restart where the operation is resumable and idempotent.

### 6.2 Controlled repair attempts

A policy may authorize narrowly defined repair attempts, for example:

```text
retry OCR for the same failed page
reduce batch size for embeddings
resume from the last verified chunk
recreate one missing derivative
retry archive copy after checksum mismatch
```

Such adjustments must be explicitly allowlisted.

```yaml
parameter_adjustments_allowed:
  - operation: embeddings
    field: batch_size
    allowed_direction: decrease_only
    minimum: 1
  - operation: ocr
    field: failed_page_retry
    allowed_value: true
```

### 6.3 Retries requiring a new gate

Hermes must not automatically:

- switch to an unapproved binding;
- switch model or model version;
- change from local to remote execution;
- transmit data to a new provider;
- install or update a dependency;
- modify system configuration;
- expand project or Knowledge scope;
- weaken validation requirements;
- discard warnings;
- overwrite prior outputs;
- alter the validated document content;
- publish a partially verified index as complete.

These actions require a new bounded request and applicable Pantheon gate.

```text
fallback binding known != fallback authorized
remote provider available != data transfer authorized
update may fix error != update authorized
```

## 7. Retry lifecycle

Candidate lifecycle:

```text
error detected
-> error displayed
-> automatic diagnosis when available
-> retry eligibility evaluated against recorded policy
-> automatic retry or repair attempt when authorized
-> progress resumes with attempt number visible
-> success, repeated failure or escalation
```

Candidate attempt record:

```yaml
retry_attempt:
  attempt_id:
  external_run_id:
  parent_attempt_id:
  attempt_number:
  trigger: automatic_policy | human_request | operator_request
  triggering_error_id:
  remediation_applied:
  binding_id:
  binding_version:
  parameter_delta:
  started_at:
  completed_at:
  outcome: succeeded | failed | cancelled | partial
  output_refs: []
```

Every attempt remains visible. Hermes does not erase failed attempts after recovery.

## 8. Cockpit UX

### 8.1 Running card

When percentage is available:

```text
Finalisation — Indice A
64 %

Embeddings : 350 / 1 000 chunks
Tentative 1 / 3
Dernière mise à jour : 18:42
```

When percentage is unavailable:

```text
Finalisation — Indice A
Hermès traite actuellement les embeddings
Progression chiffrée non exposée
```

### 8.2 Error card

```text
ERREUR
Indice A — finalisation incomplète

Étape : embeddings
Progression atteinte : 72 %
Erreur : mémoire GPU insuffisante
Diagnostic Hermès : cause probable identifiée

Nouvelle tentative automatique : prévue dans 30 s
Tentative 2 / 3
```

Actions may include:

```text
Voir le diagnostic
Voir les détails techniques
Relancer maintenant
Annuler les nouvelles tentatives
Demander une autre solution
Ouvrir les sorties partielles
```

### 8.3 Exhausted retries

When automatic retries are exhausted:

```text
ÉCHEC APRÈS 3 TENTATIVES

Hermès n’a pas pu terminer les embeddings.
Les éléments déjà archivés restent disponibles.
L’indexation demeure bloquée.

[Voir le diagnostic]
[Demander une solution à Hermès]
[Relancer avec validation]
```

### 8.4 Successful recovery

```text
Traitement repris après une erreur temporaire
Tentative 2 réussie
```

Recovery does not hide the incident history.

## 9. User-requested remediation

When the automatic policy cannot repair the failure, the user may ask Hermes to propose another solution.

The Cockpit sends a structured request containing:

```yaml
remediation_request:
  error_id:
  external_run_id:
  current_attempt:
  user_instruction:
  allowed_scope:
  forbidden_changes:
  available_partial_outputs: []
```

Hermes may propose:

- retry with an allowlisted parameter adjustment;
- resume from the last verified checkpoint;
- process only failed pages or chunks;
- request a corrected source;
- propose a different approved profile;
- propose a fallback binding requiring approval;
- request operator intervention;
- declare the error not automatically repairable.

Hermes does not apply a consequential remediation merely because it proposed it.

## 10. Idempotence and checkpoints

Automatic retry should be enabled only for operations whose repeat behavior is understood.

```text
retryable
= idempotent, resumable or safely compensatable
```

Candidate checkpoints:

- captured source hash;
- processed page set;
- normalized Markdown hash;
- completed chunk identifiers;
- completed embedding identifiers;
- archived artifact checksums;
- published index generation identifier.

A retry should resume from the last verified checkpoint when possible rather than restarting every completed step.

```text
resume from verified checkpoint
!= trust unverified partial output
```

## 11. Card finalization interaction

For a Hermes-authored Draft Card, finalization may include:

```text
validated Markdown freeze
rendering
sectorization
archive
chunking
embeddings
index publication
retrieval verification
```

Each step may expose a percentage independently.

The card becomes ordinary only according to the declared required finalization set.

Example:

```yaml
finalization_bundle:
  required_for_normal_appearance:
    - validated_markdown_freeze
    - sectorization
    - archive
    - chunking
    - embeddings
    - index_publication
  optional_or_deferred:
    - retrieval_verification
```

If embeddings fail after archive succeeds:

```text
Indice A archivé
Finalisation partielle
Embeddings en erreur
Carte normale non encore activée
```

A project policy may declare indexing optional. In that case the card may become ordinary after the required non-indexing steps complete, while the indexing error remains visible separately.

## 12. Status axes

Candidate orthogonal axes:

```yaml
external_run_status:
  lifecycle: requested | authorized | submitted | running | completed | failed | cancelled
  progress_mode: quantified | steps | indeterminate | unavailable
  observation_freshness: fresh | stale | unreachable | unknown
  diagnosis: not_requested | running | candidate_ready | inconclusive | failed
  retry: not_allowed | eligible | scheduled | running | exhausted | succeeded | cancelled
  result_quality: not_checked | review_required | accepted | rejected
```

A single `status: error` field is insufficient for the complete UX, but the primary user-facing state should remain concise.

## 13. Responsibility split

### Cockpit

The Cockpit:

- displays Hermes-reported progress and units;
- displays explicit error states;
- shows diagnosis and retry posture;
- exposes attempt history and partial outputs;
- captures a user request to retry, stop retries or seek another solution;
- does not invent progress or root cause;
- does not execute retries itself.

### Pantheon

Pantheon governs:

- allowed retry classes;
- maximum attempts;
- allowable parameter adjustments;
- binding, model, provider and data-scope boundaries;
- whether fallback requires a new gate;
- trace and checkpoint requirements;
- finalization conditions;
- escalation and human-decision requirements.

Pantheon does not run the retry loop, poll worker or diagnose logs itself.

### Hermes

Hermes may:

- report progress;
- expose measurable units;
- report errors and partial outputs;
- inspect available runtime diagnostics;
- produce a probable-cause candidate;
- retry idempotent operations under the approved policy;
- resume from verified checkpoints;
- propose a different remediation.

Hermes must not:

- fabricate progress;
- hide failed attempts;
- exceed the maximum retry count;
- change binding, model, provider or data scope without authorization;
- install or update software automatically;
- mutate Pantheon configuration directly;
- mark an output professionally valid because the retry succeeded.

### Human or operator

The human or operator decides when:

- the diagnosis is inconclusive;
- a new binding, model or provider is proposed;
- configuration or infrastructure must change;
- a source must be corrected;
- partial output may be accepted;
- the finalization bundle must change;
- repeated failure requires abandonment or escalation.

## 14. Capability Slot

```yaml
capability_slot: external_run_progress_diagnosis_and_bounded_retry
abstract_function: >-
  expose measurable external execution progress, explicit errors, candidate
  diagnosis and bounded retry attempts without making Pantheon the execution or
  repair runtime.
candidate_binding:
  executor: Hermes
  operations:
    - get_run_status
    - get_run_progress
    - diagnose_run_error
    - retry_run
    - resume_run
    - request_cancel
implementation_status: documented non-implemented in Pantheon Next
installation_status: not installed by this document
health_status: to verify
activation_status: not authorized by this document
pantheon_gates:
  - retry policy authorized
  - remediation remains in scope
  - fallback binding authorized when applicable
  - data posture unchanged or newly approved
  - finalization result reviewable
```

## 15. Acceptance criteria

The candidate specification is coherent when:

1. the Cockpit shows a percentage only when Hermes exposes a valid measured percentage or numerator/denominator;
2. the measurement method and unit remain available;
3. the Cockpit falls back to steps or indeterminate progress without fabrication;
4. stale and unreachable observations are visible;
5. a failed run becomes an explicit error state;
6. successful prior steps and partial outputs remain visible;
7. Hermes may automatically diagnose the error when diagnostics are available;
8. diagnosis remains a candidate, not a confirmed fact by default;
9. automatic retry is governed by a recorded bounded policy;
10. retry count, attempt history and remediation applied remain visible;
11. transient and idempotent failures may retry automatically;
12. model, binding, provider, execution location or data-scope changes require explicit authorization unless already covered by a reviewed fallback policy;
13. Hermes cannot install, update or reconfigure itself through this retry flow;
14. automatic retry success does not validate the professional output;
15. failed finalization does not produce false ordinary card appearance;
16. a user may stop further retries or request a different solution;
17. exhausted retries escalate visibly;
18. Pantheon remains governance and not retry runtime.

## 16. Final decision candidate

```text
When Hermes exposes measurable progress, the Cockpit displays the reported
percentage and its real unit. Otherwise it displays the current step or an
indeterminate state without inventing a number.

When execution fails, the Cockpit displays an explicit error, successful partial
steps, the diagnosis posture and the retry posture.

Hermes may automatically inspect the failure and retry only the idempotent,
allowlisted operations covered by a bounded Pantheon retry policy. Any change of
binding, model, provider, data scope, configuration, installation or consequential
finalization condition requires a new governed decision.
```
