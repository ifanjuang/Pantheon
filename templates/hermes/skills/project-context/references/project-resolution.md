# Project resolution

Operational reference for `project-context`. This file helps Hermes keep a stable working referent during agency professional work. It does not create governed project identity, durable memory, source authority or authorization.

## Select the conversation-local target

When the question depends on one affaire/project, determine which project the user is talking about from the conversation before widening retrieval:

1. the project explicitly named or selected by the user in the current request;
2. the project explicitly selected by the user earlier in the current conversation, when nothing since has changed the target;
3. recent conversation context when it identifies one project without material ambiguity.

User statements take precedence over earlier assistant wording.

Do not invent a project merely to make the task easier. When several candidates remain plausible, preserve them as a bounded candidate set. Ask for targeted clarification only when choosing between them would materially change the answer, permitted action or consequence. Otherwise continue only from facts shared by the supported candidates and expose the uncertainty.

## Resolve and confirm identity proportionally

Conversation context can select the intended working target without proving a governed project identity. When exact project identity matters, use Hindsight only as a discovery/continuity lead and confirm the candidate against admitted workspace/source material or an existing governed project identity when available.

```text
conversation target != governed identity
Hindsight lead != source confirmation
retrieval match != identity admission
```

A source-backed or governed identity is stronger confirmation than Hindsight recall. Do not let a remembered alias or prior assistant wording override a conflicting admitted source silently.

## Maintain conversational continuity

Once an affaire/project is sufficiently grounded, keep it as the conversation-local working referent for elliptical follow-ups such as "où en est-on ?", "quand a-t-on déposé le permis ?" or "quels plans avons-nous ?".

Reconsider that working referent when:

- the user explicitly selects another project;
- another project is explicitly named as the new target;
- material source evidence makes the current referent uncertain or contradictory.

The third case reopens resolution; it does not authorize an automatic switch to another project. Preserve the candidate set or request targeted clarification when the distinction matters.

Do not treat continuity as governed persistence. A conversation-local working referent is not a Pantheon identity record or memory-promotion decision.

## Treat aliases as leads, not identity

A client name, person, street, commune, operation name, building name, internal code or folder label may identify a project candidate. None is sufficient by itself when more than one dossier remains plausible.

Use aliases to discover candidate workspace material, then prefer an exact source identity, document reference or currently governed project identity when one is available.

An alias observed in a document or conversation may be reused as a search lead. Do not promote it into a permanent alias mapping merely because retrieval succeeded once.

```text
alias match != governed identity
folder name != governed identity
Hindsight recall != source confirmation
conversation continuity != durable persistence
```

## Confirm business facts from sources

Hindsight may recover a project name, chronology hint, actor or prior conversational statement. It does not prove the underlying professional fact.

When a material answer depends on that fact, confirm it against the admitted `AFFAIRES` source material when available. If only conversational/Hindsight context supports the statement, label that limitation rather than silently presenting it as a confirmed dossier fact.
