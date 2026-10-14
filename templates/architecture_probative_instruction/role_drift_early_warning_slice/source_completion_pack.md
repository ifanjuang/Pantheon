# Source Completion Pack — Role Drift Early Warning

Status: template — source completion pack candidate, documented non-implemented.

This pack replaces ChatGPT-project-context patterns with original project sources before any external communication.

It is not a project record, not proof, not legal review, not an insurance act and not an external communication.

## 1. Required source inventory

| Source | Required? | Why it matters | Locator to fill |
|---|---:|---|---|
| Architecture mission contract | Yes | Confirms MOE scope and exclusions. |  |
| Amendments / additional missions | If applicable | Determines whether role changed. |  |
| Company market / accepted quote | Yes | Defines contractor scope. |  |
| Extra quote / variation request | If applicable | Determines whether extra work was justified and accepted. |  |
| Meeting minutes / site reports | Yes | Establishes chronological alerts and instructions. |  |
| Client written decisions | Yes | Establishes MOA validation or refusal. |  |
| Contractor emails | If applicable | Establishes delay, default, quote, reservation or response. |  |
| Photos / site observations | If applicable | Supports visible facts. |  |
| Reception / OPR / reserve list | If applicable | Determines reception and reserve status. |  |
| Payment situations / fee invoices | If applicable | Avoids mixing payment and technical approval. |  |
| Replacement contractor quote | If applicable | Separates corrective works from original contract. |  |
| Insurance / professional warning source | If applicable | Triggers senior review. |  |

## 2. Admission test for each source

```text
source_id:
title:
date:
index:
author / issuer:
recipient:
status: draft | issued | received | validated | superseded | unknown
source_type: contract | amendment | quote | mail | report | photo | reception | payment | other
authority_class: project_controlled | project_source_candidate | derived | chatgpt_context | unknown
locator:
relevant_excerpt_or_observation:
limitation:
```

## 3. Role questions to resolve

```text
1. Who made the decision?
2. Who gave the instruction?
3. Was the MOE copied only, or asked to validate?
4. Was the contractor's scope clear?
5. Was the extra work priced and accepted?
6. Was the point recorded before reception?
7. Was it reserved at reception if still open?
8. Was the MOE mission changed by amendment?
9. Is a replacement contractor correcting the original contractor's work?
10. Is the answer likely to affect payment, reception, reserve lifting or mission scope?
```

## 4. Source-based status update

After source completion, update:

```text
source_basis: chatgpt_project_context_candidate | partial_project_sources | complete_project_sources
risk_level: Bas | Moyen | Haut | Critique
mission_scope_reading:
role_chain_complete: yes | no | uncertain
external_effect_possible: true | false | uncertain
output_status: result_candidate | needs_human_arbitrage | blocked | approved_for_external_transmission
```

## 5. Gate condition before external response

External response may only move from candidate to approved when all are true:

```text
- dates checked;
- original sources inspected;
- names and personal data minimized if used as example;
- mission scope checked;
- role chain stated;
- wording avoids admission and accusation;
- reviewer approves final text;
- recipient list is intentional.
```

## 6. Current default status

```text
source_basis:
  chatgpt_project_context_candidate

risk_level:
  Haut by default when role drift is detected

output_status:
  needs_human_arbitrage

external_transmission:
  blocked

allowed_next_action:
  collect and inspect sources

forbidden_next_action:
  send the reminder candidate as final
```
