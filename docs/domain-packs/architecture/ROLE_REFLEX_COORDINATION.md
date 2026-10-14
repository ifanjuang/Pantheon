# Architecture Role Reflex Coordination

Status: candidate — coordination model for role-owned reflexes, consultations, rites and Zeus arbitration inside architecture-domain approaches.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement an agent loop, workflow engine, micro-workflow runtime, router, scheduler, queue, message bus, UI, memory engine, approval engine, rite runner, role executor, checker, sender or external action.

It defines a non-executable coordination model for how a main architecture approach may be enriched by role-owned reflexes without becoming an usine a gaz.

## Purpose

A main approach may reveal many small situations while it progresses.

Examples:

```text
site report finalization reveals a line that sounds like an instruction;
CCTP drafting reveals a missing structural source;
material choice reveals a conflict between PLU, client preference and economy;
invoice review reveals a wrong-lot or insurance concern;
email drafting reveals forbidden responsibility wording;
photo analysis reveals insufficient evidence.
```

These do not require creating a new full workflow each time.

They require small governed reactions:

```text
role-owned reflex;
role consultation;
rite request;
Zeus arbitration;
tactic;
gate;
return to the main approach.
```

## Core rule

```text
The approach advances.
Situations surface.
Roles detect consequence-domain risks.
Roles emit reflexes.
Reflexes may trigger consultation, rite request or Zeus arbitration.
The result enriches the current approach without becoming a hidden runtime.
```

## Vocabulary

### Main approach

The primary governed handling of the user request.

Examples:

```text
Site Report Finalization Approach;
CCTP from Plan Approach;
Material Choice Approach;
Invoice / Quote Review Approach;
Document Summary Approach;
Client Response Approach.
```

### Micro-démarche

A bounded local sub-handling that appears during a main approach.

A micro-démarche is not a runtime workflow.

It is a visible local reasoning and governance packet.

Examples:

```text
check whether this CR line is a duplicate;
check whether this phrase implies instruction;
check whether an insurance activity covers the proposed work;
ask for a missing source;
prepare two safe reply postures;
```

### Role-owned reflex

A triggered signal emitted by a role when its consequence domain is threatened.

Examples:

```text
Themis -> mission-boundary warning;
Athena -> contradiction warning;
Mnemosyne -> duplicate-memory warning;
Hermes -> handoff-boundary warning;
Zeus -> status-promotion caution.
```

### Role consultation

A role may request another role's view when the situation touches another consequence domain.

Consultation is bounded and visible.

It must not create a hidden multi-agent loop.

### Rite request

A role may request a rite when a tension is recurring, structured or cross-domain.

A rite organizes tensions. It is not a runtime workflow.

### Zeus arbitration

Zeus is invoked when a status decision is required.

Examples:

```text
block or proceed;
remain candidate or open gate;
reformulate or refuse;
ask source or infer low-risk;
write candidate or prohibit memory write;
external action allowed only after approval;
```

## Coordination pattern

```text
Main Approach
-> Situation surfaces
-> Detect relevant consequence domain
-> Role-owned reflex fires
-> Optional role consultation
-> Optional rite request
-> Optional Zeus arbitration
-> Tactic / warning / gate / missing information
-> Candidate updated
-> Return to Main Approach
```

This is a conceptual governance pattern, not an executable graph.

## Consultation rule

A role may consult another role only if the other role's domain is materially touched.

Examples:

```text
Themis consults Athena when limitation wording must stay factually accurate.
Themis consults Iris when a boundary reply needs safe external wording.
Mnemosyne consults Athena when a recalled point conflicts with a current source.
Hermes consults Zeus when an execution handoff may create external effect.
Hephaestus consults Themis when a deliverable may imply validation.
```

Consultation should normally be limited to 1-3 roles.

If more roles are needed, request a rite or Zeus arbitration instead of expanding silently.

## Rite request rule

A rite may be requested when:

```text
tensions recur across several cases;
several roles disagree;
a decision pattern should be stabilized;
a boundary cannot be resolved by one tactic;
the same warning appears repeatedly during a main approach;
```

A rite should expose the tension and organize the decision.

It must not become hidden execution.

## Zeus arbitration rule

Invoke Zeus when a status or approval ceiling must be decided.

Examples:

```text
candidate vs validated;
internal draft vs external reply;
missing source vs allowed low-risk assumption;
Notion candidate vs validated write;
simple warning vs formal notice candidate;
within mission vs mission complement required;
```

Zeus arbitration remains governance. It does not send, approve automatically, write memory automatically or execute.

## Anti-usine-a-gaz limits

```text
Do not consult all roles by default.
Do not invoke Zeus for every wording issue.
Do not request a rite for a one-off tactic.
Do not turn every reflex into a new approach.
Do not let consultations loop.
Do not hide role disagreements.
Do not deepen beyond Workflow Depth Policy unless the consequence requires it.
```

## Example — site report line

```text
Main Approach: Site Report Finalization.
Situation: proposed CR line says “the enterprise must reprise the support before installation”.
Role-owned reflex: Themis emits mission-boundary / instruction-risk warning.
Consultation: Athena checks whether the wording states a fact or prescribes execution.
Consultation: Mnemosyne checks whether the point already exists in a previous CR.
Tactic: reformulate as a factual observation and request enterprise clarification.
Gate: user validation before CR transmission.
Return: CR Draft Candidate updated.
```

## Example — material choice

```text
Main Approach: Material Choice.
Situation: user considers replacing submitted brick with timber cladding.
Role-owned reflex: Athena emits contradiction warning if PC notice says brick.
Role-owned reflex: Themis emits regulatory / mission-boundary warning if external advice is implied.
Consultation: Hermes checks whether a mairie / ABF communication handoff is requested.
Zeus arbitration: decide whether this remains internal option, client arbitration note, or external inquiry candidate.
Return: Material Choice Candidate updated with status and missing checks.
```

## Example — invoice / quote review

```text
Main Approach: Invoice / Quote Review.
Situation: quote includes work possibly outside the enterprise lot.
Role-owned reflex: Athena emits wrong-lot suspicion.
Role-owned reflex: Themis emits responsibility / contractual boundary warning.
Consultation: Mnemosyne checks prior CRs, OS or avenants.
Procedure: insurance certificate review may be requested.
Zeus arbitration: candidate status remains blocked until lot scope and insurance gap are resolved.
Return: Invoice Review Candidate updated.
```

## Output trace

When useful, the first-layer card may show:

```text
Method objects used:
Triggered role reflexes:
Consulted roles:
Rite requested: yes / no
Zeus arbitration: none / needed / completed candidate
Tactic applied:
Gate:
```

This trace should be short.

Detailed role dialogue should be second-layer, not default output.

## Relationship with Architecture Method Taxonomy

This document depends on `METHOD_TAXONOMY.md`.

It respects:

```text
Approaches handle work.
Disciplines constrain work.
Strategies choose routes.
Procedures order steps.
Tactics handle local moves.
Roles guard consequence domains.
Reflexes interrupt with necessary cadrage.
Some reflexes are owned by roles.
Gates expose decisions.
The architect decides.
```

## Relationship with Workflow Depth Policy

Role reflex coordination must obey `WORKFLOW_DEPTH_POLICY.md`.

```text
Fast: one visible warning or one question.
Normal: bounded role consultation if context matters.
Deep: role consultation, rite request or Zeus arbitration when consequence requires it.
```

## Final rule

```text
A reflex enriches the method only when a situation requires it.
A role may consult another role, request a rite or invoke Zeus.
The enrichment remains visible, bounded and candidate.
No hidden micro-workflow.
No automatic authority.
The architect decides.
```
