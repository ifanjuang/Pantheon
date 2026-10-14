# Architecture Evidence Tree Candidate — PRO / EXE Responsibility Slice

Status: template — candidate output, non-executable.

This file records the reviewable evidence tree for one PRO / EXE responsibility question.

It is not proof, not approval, not VISA, not EXE validation and not memory.

## 1. Question instructed

```text
question:
professional_act:
project_phase:
mission_scope:
output_status:
```

## 2. Candidate claim table

| Claim | Source support | Phase reading | Responsibility reading | Risk | Required gate |
|---|---|---|---|---|---|
| | | | | | |

## 3. Source items

```text
source_items:
  - source_ref:
    source_type:
    authority_class:
    index_or_date:
    issuer:
    recipient:
    locator:
    observation:
    limitation:
    supersession_risk: yes | no | unknown
```

## 4. Responsibility chain

```text
requester:
producer_of_current_document:
producer_of_execution_document:
calculation_owner:
checker:
decision_owner:
executor:
recipient:
party_bearing_consequence:
unknowns:
```

## 5. Contradictions and tensions

```text
contradictions:
  - tension:
    source_a:
    source_b:
    affected_output:
    required_arbitrage:
```

Typical tensions:

```text
plan looks EXE but phase is PRO;
drawing dimension is precise but mission excludes EXE;
contractor asks for final dimensions but contractor owns EXE;
BET note is available but not issued for direct execution;
client asks the agency to validate what belongs to the company or BET;
cartouche lacks non-EXE disclaimer;
mail wording says validate while intended act is comment / coordination.
```

## 6. Risk classification

```text
risk_level: low | medium | high | critical
external_effect_possible: true | false | unknown
why:
forbidden_wording_found:
unsafe_interpretation:
```

## 7. Candidate conclusion

```text
candidate_conclusion:
status: result_candidate | to_verify | needs_human_arbitrage | blocked
confidence_note:
```

## 8. Safe wording candidate

```text
safe_wording_candidate:
```

## 9. Human gate

```text
decision_needed: accepted | refused | to_verify | to_arbitrate
approval_needed_before_external_transmission: yes | no
reviewer:
review_date:
final_decision:
```
