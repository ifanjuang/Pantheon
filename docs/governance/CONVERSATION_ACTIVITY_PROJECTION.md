# Conversation Activity Projection

Status: candidate support doctrine — compact conversation projection of observable governed work. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

## Objective

Expose meaningful progress from Pantheon-governed Hermes work in chat surfaces without turning the chat into a technical log and without exposing hidden chain-of-thought.

The user-facing grammar separates identity from the observable description:

```text
[icon] [name] · [semantic label]
[brief observable rationale]

```

The blank line after the description separates successive milestones. Color is optional presentation enrichment only; meaning must remain complete through icon, name, semantic label and text.

Examples:

```text
🦉 Athena · Analyse / structuration
Le C2 est plus ancien que le DCE. Je vérifie si son estimation reste cohérente avec le périmètre actuel.

⚙ Hermes · Exécution
C2 et CCTP retrouvés. Je poursuis sur les dernières pièces identifiées.

⚖ Themis · Risque / conformité
Cette réponse engage une information financière : validation humaine nécessaire.

```

The same dual-label rule applies when a Rite or governed Space becomes materially relevant.

```text
🔁 Concordance des Sources · Rite de vérification
Les pièces financières ne portent pas toutes le même périmètre. Leur concordance doit être qualifiée avant de conclure.

🏛 Agora · Espace de délibération
Deux lectures restent défendables. La divergence est rendue visible pour décision plutôt que lissée automatiquement.

```

This is a projection of observable work, not a new reasoning system, workflow engine, role system, Rite system, Space system or authority layer.

## Existing authority reused

This projection reuses rather than duplicates:

- `ROLE_DIALOGUE_TRACE.md` for observable role moves and safe rationale summaries;
- `GOVERNANCE_COLLEGE.md` for Pantheon Role jurisdictions and plain-language responsibilities;
- `docs/governance/rites/README.md` and the Rite catalogue for governed methods;
- `EVOLUTION_OF_ROLES_RITES_AND_SPACES.md` for the distinction between Roles, Rites, governed Spaces and presentation structures;
- Task Contracts for intent, owner role, scope, constraints and evidence expectations;
- Role Signals for declared role-to-role governance signals;
- Workflow Manifests for governed phases and entry/exit conditions;
- Hermes integration/runtime contracts for external execution boundaries;
- `HERMES_PROGRESS_ERROR_RETRY_UX.md` for measurable runtime progress, errors and retries when Hermes exposes them.

A conversation activity line does not replace any of those objects and is not itself Evidence, approval, memory or authorization.

## Semantic identity rule

The symbolic name must never be the only explanation when the semantic function is known.

```text
Athena
!= sufficient user explanation

Athena · Analyse / structuration
= preferred compact display
```

Presentation labels explain current responsibility without redefining the underlying object.

```text
symbolic name != semantic authority
presentation label != new Role
presentation label != new Rite
presentation label != new governed Space
```

Owner documents remain authoritative for identity, jurisdiction, lifecycle and status. The projection may shorten a semantic label for readability but must not invent a new responsibility.

### Roles

Recommended compact presentation derived from the current Governance College:

```text
🦉 Athena · Analyse / structuration
🔎 Argos · Sources / traçabilité
⚖ Themis · Risque / conformité
☀ Apollo · Clarté / synthèse
🛠 Hephaistos · Fabrication / production
📨 Iris · Transmission / adaptation
⚡ Zeus · Arbitrage / statut
🧠 Mnemosyne · Continuité / mémoire
```

Hermes remains distinct because it is an external execution runtime, not a Pantheon Role:

```text
⚙ Hermes · Exécution
```

Adapters may expose other bounded runtime or boundary identities only when their underlying status is already defined elsewhere. A presentation label must not promote an adapter into a Pantheon Role.

### Rites

A Rite is a governed method, not an actor. When a Rite materially affects current progression, display its governed name plus a short method label.

```text
🔁 Divergence Contrôlée · Rite d'exploration
🔁 Autocritique Contradictoire · Rite de critique
🔁 Concordance des Sources · Rite de vérification
🔁 Prémisses Cachées · Rite d'explicitation
🔁 Refondation de Session · Rite de recadrage
```

The label is explanatory only.

```text
rite visible != rite authorized
rite selected != rite running
rite completed != output approved
```

### Governed Spaces

A governed Space is a durable distinction between kinds of activity. Show it only when it materially explains where activity or deliberation belongs.

```text
🏛 Agora · Espace de délibération
📁 Project Space · Espace projet
📚 Governance Reference Space · Référentiel de gouvernance
```

The exact visible label follows the active owner when a localized product label already exists.

```text
space visible != space owns object
space displays status != space owns status
new screen != new governed Space
```

Scenes, Decks and Constellations remain presentation structures and must not be presented as governed Spaces merely because they are visible.

## Runtime separation

```text
Pantheon constrains legitimacy and status.
Hermes performs admitted runtime work outside Pantheon.
Observable runtime/governance events may be projected into a conversation.
The channel renders the projection.
The human remains the decision authority at applicable gates.
```

Therefore:

```text
conversation line != chain-of-thought
conversation line != Evidence
conversation line != approval
role badge != autonomous authority
rite badge != runtime execution
space badge != persistence authority
Hermes success != Pantheon validation
channel delivery != action authorization
```

## What the projection should make understandable

The projection is not primarily an activity monitor. Its purpose is to make governed transformation understandable.

At any meaningful point, the user should be able to answer five questions:

```text
Why this step?
What does it rely on?
What changed?
What still blocks progress?
Who or what must act next?
```

The most valuable visible changes are changes in legitimacy, evidence coverage, contradiction, risk, authorization posture and decision state.

### Trigger / why now

When useful, expose the observable condition that caused a meaningful change of responsibility or method.

```text
🦉 Athena · Analyse / structuration
Le DCE est plus récent que le C2. Cette version plus récente déclenche une vérification du périmètre financier.

```

The trigger is an observable reason summary, never hidden chain-of-thought.

### Information legitimacy ladder

Pantheon should make it possible to understand how an information item changes status without implying certainty that has not been established.

```text
retrieved
-> source identified
-> scope/version qualified
-> corroborated or contradicted
-> usable with stated limits
-> Evidence Pack Candidate when applicable
-> human-approved only at the applicable gate
```

The renderer may expose the current relevant stage, but must not manufacture intermediate states merely for visual progression.

```text
retrieved != true
source identified != Evidence
corroborated != approved
Evidence Pack Candidate != Evidence
runtime success != authorization
```

### Material alternatives and discarded paths

When a branch materially affected the result, the user may be shown the retained and rejected alternatives with a short observable reason.

```text
Voies examinées
✓ conserver C2 comme repère historique
✕ présenter 120 k€ comme coût actuel arrêté — périmètre trop ancien
→ recalcul depuis le DCE actuel — encore ouvert
```

Do not expose scratchpad branches, token-level alternatives or internal model deliberation. Only project alternatives that correspond to observable governed choices, evidence differences, scope differences or explicit decisions.

### Material tensions

A material tension may be exposed when it explains why Pantheon does not immediately converge.

```text
⚡ Tension active · rapidité ↔ fiabilité financière
Athena considère l'enveloppe exploitable pour cadrer ; Themis limite son usage pour une affirmation destinée au client.
```

A tension is not a theatrical debate. It must correspond to distinct governed responsibilities or a real unresolved trade-off.

### Coverage instead of synthetic confidence

Do not invent a generic AI confidence percentage.

Prefer observable coverage indicators:

```text
Sources attendues : 3/3 retrouvées
Version applicable : vérifiée
Contradictions : 1 ouverte
Evidence : candidate
Validation : requise
```

A percentage may be shown only when a runtime or governed procedure actually measures a defined quantity, such as pages processed. Measured progress is not epistemic confidence.

### Current holder and next action

The user should be able to see where the task currently waits.

```text
Pantheon  cadrage ✓
Hermes    recherche ✓
Athena    analyse ✓
Themis    réserve ✓
Utilisateur  décision requise ←
```

This is a projection of current state, not a new scheduler, queue or ownership engine.

### What Pantheon changed

When governance materially changes the deliverable, a compact before/after explanation may make Pantheon's contribution explicit.

```text
Avant contrôle
« budget actuel ≈ 120 k€ »

Après contrôle
« 120 k€ = enveloppe haute d'un état antérieur ; coût actuel à recalculer depuis le DCE »
```

This comparison must be grounded in observable source/status changes. It must not exaggerate Pantheon's contribution or imply that Pantheon independently established truth.

## Progressive disclosure

Conversation surfaces should remain calm. Additional detail belongs behind progressive disclosure when the channel supports it.

### Level 1 — conversation

Show only meaningful milestones:

- identity and semantic function;
- concise observable description;
- material blocker or decision request;
- optional small status when it changes interpretation.

### Level 2 — event detail

An expanded event may show:

- trigger;
- objective or Task Contract reference;
- source references and version/scope status;
- evidence posture;
- contradiction/tension;
- Rite or governed Space if materially active;
- approval posture;
- next action;
- produced candidate/artifact references.

### Level 3 — Cockpit / audit

The Cockpit may expose the broader trace, project graph, role/rite/space context, Evidence Pack Candidates, approvals, artifacts and bounded runtime trace references according to their existing owners.

Progressive disclosure does not change authority:

```text
more visible detail != more authority
projection != persistence
expanded trace != Evidence
```

### Opt-in trace mode

The user may turn on a conversation trace mode, for example to test or understand
behavior. It is off by default, ends with the session and does not change the
calm default above.

While it is on, each skill, tool, Rite, work posture or Space actually used gets
one line, including for simple requests: an icon, the mechanism name and a
half-sentence naming the observable trigger, for example
`🔁 Rite Prémisses Cachées — la question affirme une valeur à vérifier`.

The same identity rules apply. A Pantheon Role line appears only when a governed
object returned to the run records that viewpoint; a mechanism that was merely
available is not listed. The reason is an observable trigger, not hidden
chain-of-thought. Trace lines are model-authored declarations; the runtime's own
tool display and session record remain the factual trace.

```text
trace line != runtime receipt
trace mode on != authority
reason shown != private reasoning
```

## Presentation and color

The stable textual grammar is:

```text
[icon] [name] · [semantic function]
[description]

```

Color may enrich interfaces that support it, but must never carry unique governance meaning.

Recommended presentation hierarchy:

- first line may receive an identity/family accent;
- description remains normal body text;
- risk/blocking/decision state may receive an accessible status accent;
- Telegram or plain-text channels remain fully understandable without color.

Do not assign a unique semantic meaning solely through hue. Icons, labels and text remain authoritative for presentation meaning.

## Minimal projection

Do not create a parallel canonical event model merely for chat.

When a compatible `trace_event` exists, the conversation renderer should consume only the fields needed for display and resolve labels from existing owner doctrine or presentation registries.

```yaml
conversation_projection:
  trace_event_ref: trace-123
  visible_identity:
    kind: role
    id: ATHENA
    name: Athena
    semantic_label: Analyse / structuration
  event_type: review
  summary: >-
    Le C2 est plus ancien que le DCE. Je vérifie si son estimation
    reste cohérente avec le périmètre actuel.
  conversation_visibility: visible
```

For a Rite or Space, the same display shape may be derived without asserting a new persisted schema.

These examples describe presentation projection only. No new persisted field is required until a concrete runtime producer demonstrates that existing trace/event and owner surfaces cannot provide the necessary identity safely.

## Progressive delivery

Conversation activity is intended to arrive progressively when meaningful work milestones occur.

```text
meaningful step
-> observable event
-> safe summary
-> resolve visible identity + semantic label
-> channel projection
```

The projection should not wait for the final answer when the runtime can safely expose an intermediate milestone. It also must not publish every tool call, token, retry or retrieval attempt.

### Publishable milestones

A chat surface may show a line when one of these materially changes:

- responsibility or visible Role;
- Rite invocation, material result or closure;
- governed Space when it clarifies a deliberation or activity boundary;
- source/evidence coverage or legitimacy state;
- important finding or contradiction;
- material alternative accepted/rejected;
- bounded delegation or return from research;
- approval or governance posture;
- blocking uncertainty;
- user decision required;
- task completion.

### Suppressed noise

Do not project by default:

- repeated semantic searches;
- individual low-level tool calls;
- unchanged Role/Rite/Space metadata repeated on every line;
- retries with no user-relevant state change;
- raw connector payloads;
- raw prompts;
- private reasoning;
- internal token/context management;
- duplicate status messages.

A burst of runtime operations may therefore produce one conversation line.

## Summary style

Target one or two short sentences: observation + consequence/next move.

Good:

```text
🦉 Athena · Analyse / structuration
Le C2 est antérieur au DCE actuel. Je vérifie les écarts de périmètre avant de retenir son estimation.

```

Too thin:

```text
🦉 Athena · Analyse / structuration
Analyse en cours.
```

Too detailed: a transcript of internal model deliberation, intermediate scoring, hidden prompt state or scratchpad.

## Channel neutrality

The same projection may be rendered by Telegram, WhatsApp, OpenWebUI, a Hermes WebUI or another admitted chat surface.

The channel must not invent governance semantics. Transport-specific formatting may differ; identity and semantic status must not.

```text
same governed event
-> Telegram line
-> OpenWebUI line
-> cockpit timeline entry
```

## Relationship with Role Signals

Do not overload `role_signal.schema.yaml` for general runtime progress.

Role Signals are declared governance communications between Pantheon Roles. Hermes runtime progress, Rite projection, Space projection, source retrieval and generic activity are broader than that contract.

```text
Role Signal != conversation activity
conversation activity != Role Signal
```

## Compatibility with Hermes progress UX

`HERMES_PROGRESS_ERROR_RETRY_UX.md` already owns measurable runtime progress, explicit errors, diagnosis and bounded retry display. This conversation projection must not duplicate those semantics.

When useful, a compact activity line may summarize the latest meaningful runtime observation:

```text
⚙ Hermes · Exécution
OCR : 18/42 pages traitées. La progression est mesurée par le runtime ; aucune conclusion documentaire n'est encore tirée.

```

Quantified progress remains runtime-reported progress, not Pantheon-measured truth.

## Compatibility with Hermes adaptive execution

Hermes may adaptively select qualified tools, skills, plugins, MCP capabilities, retrieval providers, models or bounded delegation inside the admitted task boundary.

The conversation projection describes the meaningful outcome or next move, not a frozen tool path. Changing tools without changing user-relevant state should normally produce no new conversation line.

If a new mechanism changes data exposure, effect ceiling, approval posture, source scope or another governed boundary, that change is significant and may be projected.

## Failure and user-question behavior

When work cannot continue safely:

```text
⛔ Athena · Analyse / structuration
Les pièces retrouvées se contredisent sur le montant. Je ne peux pas conclure sans une source plus récente.

```

When only the user can resolve the remaining ambiguity:

```text
❓ Athena · Analyse / structuration
Les documents permettent deux lectures. Souhaites-tu conserver l'enveloppe C2 ou recalculer depuis le DCE actuel ?

```

A user question is a real workflow boundary, not a cosmetic progress message.

## Initial acceptance scenario — Roseraie

A controlled test should verify the following observable sequence without requiring every internal call to be displayed:

```text
1. Professional financial request enters the governed path.
2. Pantheon classification is observable as consulted/qualified, not as blanket approval.
3. Athena identifies the need for current financial sources.
4. Hermes retrieves the exact C2 and current DCE/CCTP sources through the admitted agency retrieval path.
5. Retrieval is visibly distinct from source qualification.
6. Athena records the material date/scope difference.
7. Concordance des Sources may be projected if a governed Rite is actually invoked and materially changes the review.
8. Themis or the applicable governance review qualifies the professional/financial delivery boundary.
9. If evidence is sufficient, a Result Candidate is prepared; otherwise a user/source gap is shown.
10. The chat receives only meaningful compact activity lines plus the final candidate response.
```

Expected compact shape:

```text
🦉 Athena · Analyse / structuration
Je vérifie d'abord quelles pièces financières sont actuellement applicables.

⚙ Hermes · Exécution
C2 et DCE retrouvés. Le DCE est postérieur et décrit un périmètre plus précis.

🔁 Concordance des Sources · Rite de vérification
Les périmètres diffèrent. Je conserve l'écart visible avant toute conclusion financière.

⚖ Themis · Risque / conformité
Information financière destinée au client : la réponse reste candidate jusqu'à validation humaine.

```

An expanded view should additionally be able to explain the trigger, source status, contradiction, approval posture, current holder and what Pantheon materially changed.

## Implementation order

1. Keep `ROLE_DIALOGUE_TRACE` as the conceptual trace authority; do not create a competing canonical event family.
2. Reuse canonical Role, Rite and governed Space identities and resolve short semantic labels at presentation time.
3. Identify the smallest existing Hermes/runtime progress hook able to emit meaningful milestones.
4. Map milestones to safe summaries and observable state changes without exposing hidden reasoning.
5. Add deduplication/throttling so repeated operations or unchanged identity metadata do not flood chat.
6. Add progressive disclosure where the target UI supports expansion; preserve plain-text fallback.
7. Render the same projection through the active gateway/chat adapter.
8. Add the Roseraie controlled test covering Pantheon classification, agency retrieval, source comparison, optional Rite/Space projection, approval boundary and progressive delivery.

If Hermes exposes no suitable progress/event hook, return a Capability Gap and implement the smallest adapter at the Hermes boundary rather than adding execution logic to Pantheon.

## Completion criteria

This feature is complete only when a controlled live run demonstrates that:

- activity arrives progressively rather than only at final response;
- identity header and description are separated by a line break, with a blank line between milestones;
- a visible Pantheon identity shows both its governed name and a plain semantic label;
- color is optional and no governance meaning depends on it;
- Rite and governed Space labels appear only when actually relevant;
- Hermes remains visibly identified as runtime execution rather than a Pantheon Role;
- the user can understand why a material step happened, what it relied on, what changed, what remains blocked and who acts next;
- retrieval can visibly progress through qualification without being represented as truth;
- material contradictions and tensions can remain visible rather than being silently flattened;
- coverage indicators are observable and no synthetic confidence percentage is invented;
- a material before/after may explain what governance changed;
- summaries are concise and contain no hidden reasoning;
- low-level tool noise is suppressed;
- Rite completion is not represented as output approval;
- Space projection is not represented as persistence or authority;
- Hermes execution is not represented as approval;
- a blocking ambiguity can route to the user;
- Telegram/chat transport does not acquire governance authority;
- the final result remains subject to the existing Pantheon gates.

## Current status

This document defines the converged projection contract only.

It does not claim that Hermes currently emits these events or that Telegram/OpenWebUI currently streams them. Those runtime capabilities must be verified against the installed Hermes version and gateway before implementation is described as complete.
