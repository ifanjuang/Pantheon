# Run 001 — Expected Outputs

Status: expected output scaffold — fictional MVP.

This file lists the expected candidate artifacts for the first manual run.

No output listed here is approval, validation, payment order, contractor instruction, legal advice, accounting advice, insurer confirmation or Registre Probatoire entry.

## Expected candidate artifacts

```text
00_task_contract_candidate.md
01_context_pack_candidate.md
02_document_form_check_candidate.md
03_progress_match_candidate.md
04_justification_matrix_candidate.md
05_lot_scope_check_candidate.md
06_cross_lot_allocation_candidate.md
07_insurance_coverage_candidate.md
08_risk_flags_candidate.md
09_result_candidate_note.md
10_notion_finance_observation_candidate.md
11_review_card_candidate.md
11_review_card_candidate.json
```

## Expected verdict shape

```text
The extra works quote must not be accepted in its current form.
The structural item may belong to another lot and insurance coverage is not demonstrated.
Request detailed breakdown, lot allocation clarification, OS / avenant status and insurance confirmation before any decision.
```

## Expected decision gate

```text
User Decision Gate required before:
- replying to the enterprise;
- accepting the quote;
- rejecting the quote definitively;
- writing a validated Notion finance record;
- instructing another enterprise;
- requesting execution.
```

## Expected risk flags

```text
missing_OS_or_avenant;
amount_breakdown_missing;
wrong_lot_candidate;
insurance_scope_gap;
technique_not_confirmed;
structural_validation_missing;
formal_client_approval_missing;
external_action_requested;
```
