# Communication Pattern Registry

Status: registry — candidate-only, documented non-implemented.

This registry lists communication pattern candidates created from architecture probative instruction work.

It is not a library of approved emails. It does not authorize external transmission.

## Registry rules

```text
A registry row records a candidate.
A registry row does not approve wording.
A registered candidate must still be source-checked and reviewed before any case use.
Rejected patterns stay visible to prevent unsafe reuse.
```

## Fields

| Field | Meaning |
|---|---|
| pattern_id | Stable identifier for the candidate. |
| title | Human-readable title. |
| folder | Classification folder. |
| status | wording_fragment / draft_candidate / pattern_candidate / approved_for_internal_use / rejected / obsolete. |
| recipient_class | project_owner / contractor / BET / administration / insurer_or_counsel / internal / mixed. |
| professional_act | inform / clarify / request / remind / alert / record / reserve / refuse / propose / escalate / prepare_reception / close_point / other. |
| project_phase | Phase or broad context. |
| risk_level | Bas / Moyen / Haut / Critique. |
| source_basis | example_only / chatgpt_project_context_candidate / partial_project_sources / complete_project_sources. |
| external_gate | human_review_required / source_pack_required / senior_review_required / insurer_or_counsel_review_required. |
| related_slice | Source slice or template family. |
| forbidden_uses | Main prohibited uses. |

## Current registry

| pattern_id | title | folder | status | recipient_class | professional_act | project_phase | risk_level | source_basis | external_gate | related_slice | forbidden_uses |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `PAT-COMM-0001` | Project-owner role boundary reminder | `01_client_moa` | `pattern_candidate` | `project_owner` | `clarify / remind` | `DET / AOR / dispute_watch` | `Haut` | `chatgpt_project_context_candidate` | `source_pack_required + human_review_required` | `role_drift_early_warning_slice` | Do not use as admission, blame allocation, legal position, payment decision or reserve closure. |
| `PAT-COMM-0002` | Contractor open-items source request | `02_contractors` | `pattern_candidate` | `contractor` | `request / record` | `DET / AOR / GPA` | `Moyen` | `chatgpt_project_context_candidate` | `human_review_required` | `role_drift_early_warning_slice` | Do not use as formal notice, liability finding or reserve closure. |
| `PAT-COMM-0003` | Role-chain reminder MOA / MOE / contractor | `06_role_drift_risk` | `pattern_candidate` | `mixed` | `clarify / alert` | `DET / AOR / dispute_watch` | `Haut` | `chatgpt_project_context_candidate` | `source_pack_required + human_review_required` | `role_drift_early_warning_slice` | Do not use when an official challenge or counsel/insurer trigger exists without senior review. |
| `PAT-COMM-0004` | Pre-reception open-items reminder structure | `05_reception_reserves_gpa` | `pattern_candidate` | `project_owner` | `prepare_reception / alert` | `AOR` | `Haut` | `example_only` | `source_pack_required + human_review_required` | `professional_risk_review_layer` | Do not use as reception decision, reserve closure or legal advice. |
| `PAT-COMM-0005` | PRO / DCE non-EXE footer candidate | `03_bet_control` | `pattern_candidate` | `BET / contractor / mixed` | `clarify` | `PRO / DCE / EXE_VISA` | `Haut` | `partial_project_sources` | `source_pack_required + human_review_required` | `pro_exe_responsibility_slice` | Do not use as EXE validation, BET review replacement or contractor instruction. |
| `PAT-COMM-0006` | PRO / EXE boundary mail candidate | `03_bet_control` | `draft_candidate` | `BET / contractor / mixed` | `clarify / request` | `PRO / DCE / EXE_VISA` | `Haut` | `partial_project_sources` | `source_pack_required + human_review_required` | `pro_exe_responsibility_slice` | Do not send without project-source completion and architect approval. |
| `PAT-COMM-0007` | Internal professional-risk review cartouche | `07_internal_review` | `pattern_candidate` | `internal` | `record / alert` | `dispute_watch` | `Haut` | `example_only` | `human_review_required` | `professional_risk_review_layer` | Do not treat as legal advice, insurer advice or project proof. |
| `PAT-COMM-0008` | Rejected: vague validation wording | `08_rejected_or_obsolete` | `rejected` | `mixed` | `other` | `any` | `Haut` | `example_only` | `not_applicable` | `communication_patterns` | Never use wording that implies validation without source, role and gate. |

## Next registry actions

```text
1. Add one metadata file per registered pattern before reuse.
2. Convert only reviewed recurring drafts to pattern_candidate.
3. Keep project-specific drafts as draft_candidate.
4. Move unsafe formulations to rejected_or_obsolete with rejection reason.
```
