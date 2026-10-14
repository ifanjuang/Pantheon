# Task Contract — PRO / EXE Responsibility Slice

Status: template — candidate input, non-executable.

Use this contract before instructing any question where a PRO, DCE, EXE or VISA boundary may be confused.

## 1. Case metadata

```text
case_ref:
project_ref:
project_phase:
phase_certainty: known | uncertain | disputed
mission_scope_ref:
contract_ref:
reviewer_role:
review_date:
```

## 2. Trigger

```text
trigger_type: incoming_mail | outgoing_mail_draft | plan_note | BET_note | contractor_question | client_question | site_question | visa_comment | other
trigger_summary:
requested_action:
intended_output: internal_note | mail_candidate | plan_footer_candidate | visa_comment_candidate | question_list | refusal_candidate | other
external_recipients:
```

## 3. Sources to inspect

```text
source_documents:
  - source_id:
    title:
    type: plan | mail | contract | CCTP | DPGF | BET_note | quote | meeting_minutes | site_report | other
    index_or_date:
    issuer:
    recipient:
    status: draft | issued | received | validated | superseded | unknown
    locator:
    limitation:
```

## 4. Mission and responsibility boundaries

```text
architect_mission_includes:
  - design_coordination
  - PRO
  - DCE
  - ACT
  - VISA
  - DET
  - AOR
  - other
architect_mission_excludes:
  - EXE_production
  - structural_calculation
  - contractor_method_statement
  - final_execution_dimensions
  - other
specialist_roles:
  BET_structure:
  BET_fluids:
  bureau_de_controle:
  contractor:
  supplier:
```

## 5. Risk check

Mark each item:

```text
could_be_read_as_execution_instruction: yes | no | uncertain
could_be_read_as_final_dimension_validation: yes | no | uncertain
could_shift_contractual_responsibility: yes | no | uncertain
could_commit_client_or_agency_externally: yes | no | uncertain
could_conflict_with_contract_scope: yes | no | uncertain
could_conflict_with_BET_or_contractor_scope: yes | no | uncertain
```

## 6. Forbidden wording found

```text
forbidden_wording:
  - bon pour execution
  - plan d'execution
  - dimensions definitives
  - valide
  - conforme
  - visa favorable
  - prepercement
  - a realiser
  - synthese complete
  - sans reserve
  - other:
```

## 7. Required output

```text
output_status: result_candidate | to_verify | needs_human_arbitrage | blocked
required_output:
  - source_inventory
  - responsibility_reading
  - contradiction_list
  - risk_classification
  - safe_wording_candidate
  - evidence_tree_candidate
human_gate_required: yes
```

## 8. Non-negotiable boundary

```text
No automatic external transmission.
No execution drawing production.
No structural calculation.
No contractor EXE validation.
No memory promotion.
No approval without human decision.
```
