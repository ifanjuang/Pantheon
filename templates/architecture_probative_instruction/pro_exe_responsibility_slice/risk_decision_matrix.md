# Risk Decision Matrix — PRO / EXE Responsibility Slice

Status: template — candidate decision aid, documented non-implemented.

This matrix helps classify the risk level of a PRO / DCE / EXE / VISA boundary question before drafting or transmitting anything.

It does not approve, validate, send, issue a VISA, produce EXE, promote memory or create a project record.

```text
Risk classification is not decision.
Decision remains human.
External transmission remains gated.
```

## Core test

Ask:

```text
Could this wording, drawing, note or response be read as:
- final execution production;
- technical validation;
- contractor/BET substitution;
- instruction to execute;
- approval of dimensions, calculations, assemblies or methods;
- responsibility transfer to the agency?
```

If yes or uncertain, use this matrix.

## Risk bands

| Risk | Situation | Required posture | Minimum output status | Gate |
|---|---|---|---|---|
| Bas | Internal discussion only; no final dimension; no external recipient; no phase ambiguity. | Note internally, preserve uncertainty. | `result_candidate` | Internal review only. |
| Moyen | External recipient possible; document status known; no final technical validation wording; responsibility chain mostly clear. | Draft cautious wording; avoid EXE language. | `needs_human_arbitrage` | Architect approval before send. |
| Haut | PRO / DCE document could be read as EXE; dimensions or technical notes present; contractor/BET/client in copy; mission boundary relevant. | Source pack required; safe wording required; no final validation. | `needs_human_arbitrage` | Architect approval + source completion before send. |
| Critique | Explicit demand for final dimensions, calculation, EXE validation, instruction to execute, disputed responsibility, claim, insurance, legal or payment implication. | Stop candidate drafting unless sources are complete; consider external counsel / BET / bureau de controle route. | `blocked` or `to_arbitrate` | Zeus/human arbitration; no send until resolved. |

## Automatic escalation triggers

Escalate one level when any of these appear:

```text
bon pour execution;
plan d'execution;
dimensions definitives;
valide / validé;
conforme;
visa favorable;
prepercement / prépercement;
a realiser / à réaliser;
sans reserve;
synthese complete;
client in copy;
contractor asks for final answer;
BET absent or ambiguous;
cartouche lacks non-EXE disclaimer;
plan index / phase unknown;
contract scope unknown;
claim / dispute / insurance context;
payment or reserve impact.
```

## Downgrade conditions

Do not downgrade unless all apply:

```text
source documents are identified;
phase is clear;
mission scope is clear;
recipient understands the document status;
no final technical dimension is being validated;
no execution method is being instructed;
no claim, reserve, payment or reception effect exists;
human reviewer approves the wording.
```

## Decision rule

```text
Bas:
  internal note possible.

Moyen:
  mail_candidate possible, but approval required.

Haut:
  source_completion_pack mandatory before external wording.

Critique:
  no external wording until arbitration; consider legal/BET/bureau-de-controle review.
```

## Output label

Every slice output should carry:

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
Do not treat a cautious footer as legal protection by itself.
Do not treat a mail candidate as approval.
Do not treat a BET mention as BET validation.
Do not treat a plan index as phase proof if the cartouche or contract contradicts it.
Do not send because the wording sounds careful.
```
