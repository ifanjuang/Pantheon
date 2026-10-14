# Architecture decision — memory versus Registre Probatoire

Status: fictional example — educational support only.
Boundary profile: documentation_only.

This example shows why Pantheon must distinguish runtime memory from the Registre Probatoire when a professional asks a consequential project question.

It is not implementation.

It is not architectural, legal, contractual or financial advice.

It does not validate any real project decision.

```text
The Registre Probatoire proves.
The human decides.
```

## Scenario

An architect asks the system:

```text
Prepare an email to the client confirming that we validate the zinc option and can launch the contractor.
```

Hermes runtime memory recalls several useful signals:

```text
- The client seemed to prefer zinc during the last design discussion.
- A working budget around 170000 was mentioned in conversation.
- Contractor X was considered a likely candidate.
```

Those statements are useful context.

They are not proof.

## Registre Probatoire check

The system must resolve consequential claims against the Registre Probatoire before drafting a message that could commit the architect externally.

The Registre Probatoire currently contains:

```text
- Last approved option: material choice still to arbitrate.
- Approved budget ceiling: 150000, not 170000.
- Contractor appointment: no signed order, no approved launch instruction.
- Administrative condition: ABF feedback still pending.
```

## Conflict

```text
Hermes memory says: zinc likely preferred.
Registre Probatoire says: zinc not approved.

Hermes memory says: 170000 discussed.
Registre Probatoire says: 150000 approved ceiling.

Hermes memory says: Contractor X likely.
Registre Probatoire says: no contractor launch approved.
```

The conflict is not a failure.

It is exactly the point of the governance layer.

## Required governance result

The system must not send or prepare a definitive confirmation email.

It should return:

```text
answer_status: to_verify
consequence_level: K3 or K4 depending on contractual wording
approval_ceiling: C3 or C4 before external transmission
runtime_memory_status: recall_candidate_only
registre_status: contradiction_found
external_action_status: blocked_until_human_decision
```

## Safe draft

The safe output is a draft that exposes the uncertainty rather than committing the architect:

```text
Bonjour,

À ce stade, nous pouvons confirmer que l’option zinc reste l’hypothèse privilégiée, sous réserve de validation définitive de votre part et de confirmation des incidences budgétaires.

Avant tout lancement auprès de l’entreprise, merci de confirmer expressément :

1. le choix définitif de l’option zinc ;
2. le budget plafond retenu ;
3. l’autorisation de solliciter l’entreprise pour chiffrage ou engagement ;
4. la conduite à tenir en attente du retour ABF.

Bien à vous,
```

Output status:

```text
draft_only
not_sent
requires_user_decision_gate
```

## Notion / database mirror

A Notion database or another cockpit may mirror the Registre Probatoire fields for review:

```text
claim
scope
certainty E0-E4
source date
received date
exhibits
citation
status
approval reference
supersession state
```

But the mirror does not make the entry probative.

```text
Notion may record and expose synchronized views.
Pantheon governs whether a record is probative.
```

If Notion contains a row that conflicts with the Registre Probatoire, the correct result is a review signal, not silent overwrite.

## Why this matters

Without the Registre check, the system would transform a remembered preference into a client commitment.

That is the dangerous collapse Pantheon prevents:

```text
remembered preference
-> confident draft
-> external commitment
-> professional liability
```

Pantheon inserts the missing procedure:

```text
remembered preference
-> Registre Probatoire check
-> contradiction surfaced
-> User Decision Gate
-> human decision
-> only then: possible external act
```

## Boundary

This example is documentary only.

It does not implement a Notion sync, database schema, runtime memory adapter, email sender, approval engine, Registre Probatoire storage or external action.

It shows the desired governance behavior.
