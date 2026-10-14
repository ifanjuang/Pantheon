# Fictional CR Chantier Deliberation — Walkthrough

Status: example candidate — non-executable, fictional data.

This walkthrough exercises `docs/governance/ITERATIVE_DELIBERATION_LIFECYCLE.md` on
one architecture CR chantier (site report) run. It is the validation scenario
requested in PR Pantheon-Next#231 review: 10 corrections, 1 old pinned constraint, 1 factual
correction, 1 backtrack, 1 contradiction, 1 draft, 1 finalization, 1 candidate
email, 1 Notion gate.

It promotes nothing. All names, values and sources are invented.

## Setup

```text
Project: extension maison Dupont (fictional)
Subject: CR visite de chantier du 2026-06-20
Workflow: site-visit report drafting
Ledger: opened at turn 1 (constraint_decision_ledger_candidate)
```

## Turn-by-turn routing

Each turn is classified by the turn taxonomy and routed at the lowest sufficient
cost. Only a few turns tick the governance clock.

| # | Architect turn | Class | Route | Touches consequence |
|---|---|---|---|---|
| 1 | "Prépare un CR de la visite du 20/06. Ne nomme jamais l'entreprise de gros œuvre par son nom." | scope + **pinned constraint** | open ledger; record `C-001: never name the gros-œuvre firm` (scope: subject, status active) | constraint only |
| 2 | "La réserve sur l'étanchéité, mets-la en premier." | structural correction | revision v1→v2 (reorder); diff only | no |
| 3 | "Le terme 'malfaçon' est trop fort, écris 'réserve à lever'." | cosmetic/wording | ephemeral; no governed object | no |
| 4 | "La surface du palier, c'est 4,20 m², pas 4,80." | **factual correction** | revision; re-bind Evidence `E-002` to source; **cascade** to any draft sentence using 4,80 | yes (assertion) |
| 5 | "Ajoute aussi un point sur la conformité PMR de la rampe." | **scope extension** | **gate the contract** (mission), not the output; Themis warns: PMR conformity may imply a responsibility statement | yes (responsibility) |
| 6 | System question: "La pente de rampe mesurée est-elle disponible, ou à relever ?" (batched with one other blocking question) | consultative facet | ledger `Gap G-001`; no gate | no |
| 7 | "Finalement, enlève le point PMR, on le traitera à part." | **backtrack** | revert the turn-5 scope extension; pointer to snapshot; `C-001` untouched; contract returns to prior scope | no |
| 8 | "Mets une conclusion qui dit que le chantier est conforme." | **contradiction** | conflicts with turn 4 reserve still open; ledger `X-001` surfaces the contradiction (Athena); human must resolve — last turn does not win | yes (would overstate) |
| 9 | "Bon, envoie-moi un CR brouillon." | draft request | produce **Draft Output Card**, status `draft_allowed` / candidate; not transmissible | no (candidate) |
| 10 | "Reformule l'intro, plus sobre." | cosmetic | ephemeral; draft revision, diff only | no |
| 11 | "OK, finalise le CR." | **finalization** | opens a **diff-review gate** over the delta since draft; `C-001` checked (firm not named); `X-001` must be resolved first | yes |
| 12 | "Prépare un mail au client avec le CR." | **candidate email** | **Action Card** `mail candidate` + a **separate transmission gate**; nothing sent | yes (external) |
| 13 | "Et garde le CR validé dans Notion." | **Notion write** | **Promotion Card** → Register Candidate + a **separate Notion gate**; not written until the gate is passed | yes (canonical memory) |

## What the ledger held at finalization

```text
C-001  never name the gros-œuvre firm        active     scope: subject
E-002  palier surface = 4.20 m2 (was 4.80)    candidate  corrected at turn 4
G-001  rampe slope: to measure                open       blocks PMR if reopened
X-001  "chantier conforme" vs open reserve     open       human must resolve
D-001  PMR treated separately                  held       reopen if client asks
```

## Where the governance clock actually ticked

```text
Turn 5  : contract gate (scope/responsibility) — cheap, early.
Turn 8  : contradiction surfaced — blocked an overstatement.
Turn 11 : diff-review gate on finalize.
Turn 12 : separate transmission gate (email candidate).
Turn 13 : separate Notion / Register gate.
```

Eight of thirteen turns carried zero governance friction. The constraint from
turn 1 survived ten turns because it lived in the ledger, not in fungible chat
history — the conversational form of the no-partial-read rule.

## What was promoted

```text
Nothing automatically.
The CR stays a candidate until the diff-review gate passes.
The email is not sent until the transmission gate passes.
The Notion entry is not written until the Register gate passes.
The human decides at each gate.
```

## Boundary

This is a fictional example. It creates no runtime, no email send, no Notion
write, no schema and no memory promotion. It illustrates routing and gates only.
