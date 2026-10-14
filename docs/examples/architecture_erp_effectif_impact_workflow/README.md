# Architecture workflow — ERP occupancy / effectif impact review

Status: fictional example — educational support only.
Boundary profile: documentation_only.

This example shows how Pantheon can govern a professional workflow where a client email and an attached document may change project assumptions.

It is not implementation.

It is not architectural, contractual, insurance, structural, fire-safety or regulatory advice.

It does not validate any real ERP position, drawing, width, alarm requirement, classification or notice.

```text
The Registre Probatoire proves.
The human decides.
```

## User request

```text
The client sent a new structural / project note with a changed occupancy assumption.
What are the impacts on the project?
```

The request looks simple.

It may be consequential because the answer can affect:

- fire-safety assumptions;
- circulation and stair dimensions;
- accessibility coordination;
- structural coordination;
- cost and schedule;
- the architect's contractual scope;
- external communication with the client, contractor, control office or authority.

## Surface answer pattern

The user should see a short, useful answer first:

```text
I found a new attached document that appears to change the occupancy assumption.

Before treating it as approved, I need to verify:
1. whether this document is the latest project version;
2. whether the changed effectif replaces the previous registered assumption;
3. whether your current mission includes the fire-safety / ERP impact review;
4. whether you want a client-facing draft or an internal impact note only.

Candidate impacts detected:
- stair and circulation review;
- fire-safety notice update;
- alarm / equipment visibility check;
- possible cost and planning effect;
- possible need for client confirmation or mission adjustment.
```

No final conclusion is allowed at this stage.

## Under-the-hood workflow

```text
email received
→ attachment extracted
→ OCR / PDF cleanup
→ document classified
→ index / date / author / assumption extracted
→ project lookup
→ contract / mission scope check
→ latest plan retrieval
→ previous fire-safety notice retrieval
→ Registre Probatoire check
→ Hermes runtime memory check
→ plan vision analysis
→ stair / circulation / exit zones isolated
→ candidate impact matrix
→ annotated PDF candidate
→ blocking questions
→ User Decision Gate
```

## Modules / skills / tools

| Capability | Layer | Status of result |
|---|---|---|
| Email reader | connector / execution runtime | source candidate |
| Attachment extractor | execution runtime | source candidate |
| OCR | execution runtime | extracted text candidate |
| PDF cleanup / optimization | execution runtime | preparation only |
| Document classifier | execution runtime | classification candidate |
| Version detector | execution runtime | version candidate |
| Notion project lookup | cockpit / connector view | project view candidate |
| Contract scope checker | governed review | scope candidate |
| Plan retrieval | connector / execution runtime | source candidate |
| Vision plan analysis | execution runtime | interpretation candidate |
| Stair / zone isolation | execution runtime | geometry / location candidate |
| PDF annotation | execution runtime | visual candidate artifact |
| Impact matrix builder | execution runtime | Result Candidate |
| Evidence Pack builder | governed output shape | Evidence Pack Candidate |
| Question generator | execution runtime | blocking / non-blocking questions |
| Draft email generator | execution runtime | draft-only candidate |

## Evidence expectations

Minimum Evidence Pack Candidate:

```text
source email reference
sender / received date
attachment filename
attachment apparent date / index
extracted occupancy assumption
previous occupancy assumption from Registre Probatoire or project record
latest plan source and index
previous notice source and index
contract / mission scope reference
vision plan snapshots or page references
annotated PDF candidate reference
uncertainties
contradictions
blocking questions
```

## Typical contradictions

```text
runtime memory: client seemed to prefer the new assumption
Registre Probatoire: previous effectif still approved

email attachment: note index B
project folder: plan index C but notice index A

Notion project view: notice in scope
contract check: notice scope not explicit

vision plan: alarm not visible
project memory: alarm was discussed orally
```

Contradiction is not failure.

It is a governance signal.

## Capability gaps

Typical stop conditions:

```text
latest_plan_unconfirmed
previous_notice_absent
contract_scope_unclear
effectif_not_approved
room_function_unknown
recipient_unconfirmed
external_transmission_requested_without_approval
```

The safe result is not silence.

The safe result is a visible gap:

```text
capability_gap:
  missing: latest approved plan version
  needed_for: fire-safety impact review
  blocked_effect: client-facing confirmation
  safe_fallback: internal candidate impact note only
  required_human_or_admin_action: confirm latest plan / approve scope
```

## Candidate impact matrix

| Impact area | Candidate signal | Status |
|---|---|---|
| Occupancy / effectif | changed in incoming attachment | to verify |
| Stair | may need dimensional review | to verify |
| Circulation | may need width / route review | to verify |
| Fire-safety notice | likely needs update if assumption confirmed | to verify |
| Alarm / equipment | not clearly visible on plan | gap |
| Room function | one local appears undetermined | gap |
| Cost | potential project effect | candidate |
| Schedule | potential coordination effect | candidate |
| Contract | scope may need confirmation | blocking |

## Annotated PDF candidate

The runtime may prepare an annotated PDF candidate showing:

```text
- page / plan reference;
- stair zone;
- circulation zone;
- unknown local;
- equipment / alarm location not visible or not found;
- source label;
- candidate status watermark.
```

The annotation is not proof by itself.

It is a review aid.

## Safe user-facing output status

```text
answer_status: to_verify
runtime_task_status: partial_success
governance_result_status: candidate
external_action_status: not_sent
memory_status: candidate_only
registre_status: unchanged
user_decision_gate: required
```

## Safe draft email

```text
Bonjour,

Nous avons bien reçu la nouvelle pièce transmise, qui semble modifier l’hypothèse d’effectif prise en compte dans le dossier.

Avant de confirmer ses incidences sur le projet, nous devons vérifier :

1. que cette pièce constitue bien la dernière hypothèse validée ;
2. que l’effectif indiqué remplace l’hypothèse précédemment retenue ;
3. les conséquences éventuelles sur les circulations, l’escalier, la notice de sécurité et le coût des adaptations ;
4. le périmètre exact de notre intervention sur cette vérification.

À ce stade, nous pouvons préparer une note d’impact candidate, mais nous ne pouvons pas confirmer définitivement les conséquences sans validation de ces points.

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

It does not implement email retrieval, OCR, computer vision, PDF annotation, Notion access, ERP rule checking, Registre Probatoire storage, automatic memory promotion, approval or external transmission.
