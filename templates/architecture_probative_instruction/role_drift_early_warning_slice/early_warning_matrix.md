# Early Warning Matrix — Role Drift

Status: template — candidate decision aid, documented non-implemented.

This matrix classifies early role-drift signals before drafting a response or reminder.

It does not decide responsibility, send a message, create a project record, validate proof or promote memory.

## Core test

Ask:

```text
Could this situation create confusion about:
- who decides;
- who validates;
- who executes;
- who pays;
- who receives;
- who lifts reserves;
- who carries contractor failure;
- whether the MOE mission has been silently extended?
```

## Risk bands

| Risk | Situation | Required posture | Minimum output status | Gate |
|---|---|---|---|---|
| Bas | Clarification request; no external consequence; sources mostly clear. | Answer factually, cite source gaps. | `result_candidate` | Internal review. |
| Moyen | Direct quote changes, unclear extra works, missing validation, bypassed channel. | Recall roles and request source completion. | `needs_human_arbitrage` | Architect review before send. |
| Haut | Payments, penalties, reserves, reception, replacement contractor or unfinished works are involved. | Build source pack; draft cautious reminder only. | `needs_human_arbitrage` or `to_arbitrate` | Architect review + source completion. |
| Critique | Official challenge, quantified demand, reception dispute, major defect or possible mission extension. | Stop spontaneous response; prepare evidence pack; use senior review. | `blocked` | Human arbitration. |

## Escalation triggers

```text
unpaid fees linked to defects;
contractor default;
replacement contractor correcting prior works;
client directly instructs contractor while expecting MOE validation;
unclear extra works;
reception without clear reserves;
reserve lifting mixed with payment;
MOE asked to perform synthesis, EXE, quote analysis or reinforced site follow-up outside mission;
financial or work situation signed outside mission perimeter.
```

## Downgrade conditions

Do not downgrade unless all apply:

```text
source documents are identified;
dates are verified;
mission scope is checked;
roles are explicit;
no payment / reception / reserve consequence is hidden;
the draft avoids admission and blame language;
human reviewer approves the wording.
```

## Decision rule

```text
Bas:
  internal note or short factual answer possible.

Moyen:
  role reminder candidate possible; approval required.

Haut:
  source completion pack mandatory before external wording.

Critique:
  no external wording until arbitration.
```

## Output label

Every role-drift output should carry:

```text
risk_level:
external_effect_possible:
source_completion_required:
human_gate:
allowed_next_action:
forbidden_next_action:
```

## Forbidden shortcuts

```text
Do not answer because the facts seem obvious.
Do not write "validé" if the project owner has not validated.
Do not turn a role reminder into an accusation.
Do not let a copied email become tacit approval.
Do not let quote review become full consultation mission.
Do not let reserve comments become reception decision.
Do not let situation review extend the mission perimeter.
```
