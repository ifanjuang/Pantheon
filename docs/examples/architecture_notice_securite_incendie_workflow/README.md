# Architecture workflow — governed ERP fire-safety notice preparation

Status: fictional example — educational support only.
Boundary profile: documentation_only.

This example shows how Pantheon can govern the preparation of a candidate ERP fire-safety notice without treating the AI output as regulatory validation or external authorization.

It is not implementation.

It is not architectural, legal, fire-safety, regulatory, insurance or engineering advice.

It does not validate any real ERP classification, notice, plan, alarm requirement, evacuation path, local risk category or administrative filing.

```text
The Registre Probatoire proves.
The human decides.
```

## User request

```text
Prepare the fire-safety notice for project X.
```

The system must not immediately draft the notice.

It must first run a governed dossier preflight.

## Practitioner-facing path

```text
request
→ mission / contract check
→ latest plans and project data
→ missing information
→ plan review and candidate observations
→ draft notice candidate
→ questions to ask
→ User Decision Gate before transmission
```

## Preflight checks

The system should check:

```text
1. Is fire-safety notice preparation included in the current mission?
2. Is the latest plan version confirmed?
3. Are the project identity, address and client data confirmed?
4. Are ERP type, category and effectif known or still assumptions?
5. Are the relevant existing notices, previous submissions or authority comments available?
6. Is there a known control office, fire-safety office, mairie / instruction contact or other confirmed recipient?
7. Does the user ask for an internal draft or an external transmission package?
```

If a point is missing, the system may continue only as candidate work.

## Under-the-hood workflow

```text
Task Contract
→ contract / mission scope check
→ project lookup
→ latest plan retrieval
→ Notion / project database view
→ Registre Probatoire check
→ previous notice / administrative file retrieval
→ OCR / document extraction
→ vision plan analysis
→ rooms / exits / stairs / circulations / equipment detection
→ local function ambiguity check
→ evidence gaps
→ candidate notice outline
→ questions to architect / client
→ draft-only email
→ User Decision Gate
```

## Modules / skills / tools

| Capability | Layer | Result status |
|---|---|---|
| Contract scope checker | governed review | scope candidate |
| Project lookup | cockpit / connector | project data candidate |
| Notion project view | cockpit / connector | synchronized view candidate |
| Plan retrieval | connector / runtime | source candidate |
| Version detector | runtime | version candidate |
| OCR / document extraction | runtime | extracted text candidate |
| Plan vision analysis | runtime | interpretation candidate |
| Room / local classifier | runtime | candidate classification |
| Stair / circulation detector | runtime | candidate observation |
| Equipment visibility checker | runtime | candidate observation |
| Evidence Pack builder | governed output shape | Evidence Pack Candidate |
| Notice outline generator | runtime | Result Candidate |
| Missing-info question generator | runtime | candidate questions |
| Contact lookup | connector / runtime | recipient candidate |
| Draft email generator | runtime | draft-only candidate |

## Evidence expectations

The Evidence Pack Candidate should contain:

```text
contract / mission reference
project identity source
address source
client source
latest plan reference and index
plan confirmation status
ERP type / category / effectif source or assumption status
previous notice / administrative file reference
room function table
unknown rooms / local functions
stairs / circulation / exits observation references
fire-safety equipment observation references
recipient source if any
missing information list
candidate notice version
review status
```

## Typical gaps

```text
mission_scope_unclear
latest_plan_unconfirmed
ERP_type_unknown
category_unknown
effectif_unknown
room_function_unknown
alarm_not_visible_on_plan
previous_notice_absent
recipient_unconfirmed
external_transmission_not_approved
```

## Example alert

```text
Candidate alert:

One room on the plan has no determined function in the available project data.
The plan review also does not clearly identify the expected alarm / equipment location for that area.

The system cannot determine whether this has regulatory, cost or layout consequences without human review and confirmation of the room function.
```

This is not a regulatory conclusion.

It is a governance alert.

## Candidate question set

The system should avoid asking everything.

It should surface blocking questions first:

```text
1. Confirm the latest plan version to use.
2. Confirm whether the fire-safety notice is within the current mission or requires an additional scope decision.
3. Confirm ERP type, category and effectif, or identify the source to use.
4. Define the function of the undetermined local.
5. Confirm whether the output should remain internal or be prepared for external review.
```

Non-blocking questions can be grouped separately.

## Candidate outputs

| Output | Status |
|---|---|
| Notice outline | Result Candidate |
| Missing information list | to verify |
| Room / local table | candidate |
| Plan observations | candidate |
| Annotated plan extract | candidate review aid |
| Contact / recipient list | candidate only |
| Draft email | draft-only, not sent |
| Register Candidate | possible only after human validation |

## Safe notice status

```text
notice_status: candidate
regulatory_validation_status: not_validated
external_action_status: not_sent
approval_required: true
user_decision_gate: required before transmission
```

## Safe draft email

```text
Bonjour,

Nous préparons la notice de sécurité incendie du projet sur la base des pièces actuellement disponibles.

Avant finalisation ou transmission, plusieurs points doivent être confirmés :

1. la dernière version des plans à prendre en compte ;
2. le type, la catégorie et l’effectif retenus pour l’ERP ;
3. la fonction du local non déterminé sur le plan ;
4. le périmètre exact de notre intervention pour cette notice ;
5. le destinataire éventuel de la version de travail.

À ce stade, la notice peut être préparée comme document candidat, mais elle ne doit pas être considérée comme validée ni transmise sans arbitrage.

Bien à vous,
```

Output status:

```text
draft_only
not_sent
approval_required
```

## Boundary

This example is documentary only.

It does not implement plan analysis, ERP classification, regulatory validation, Notion sync, contact lookup, email sending, Registre Probatoire storage or approval.
