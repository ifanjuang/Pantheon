# Editorial Language

Status: active support doctrine — public-facing language and vocabulary.

This document defines how Pantheon Next should speak to non-technical professionals.

It is an editorial guide.

It does not define runtime behavior.

It does not add implementation.

It does not replace governance doctrine.

When technical placement must be explained, inherit it from `HERMES_INTEGRATION.md`: compatible runtime clients are optional interaction surfaces, Hermes/the external runtime executes admitted work, Pantheon Cockpit projects governed state, and Pantheon retains governance authority. Public-facing copy should not turn a client or UI into the governance owner.

## Core editorial problem

Pantheon Next is conceptually strong, but it can become too abstract if it speaks like a system architecture.

A practitioner does not first care about runtime boundaries, agentic patterns, schemas or governance primitives.

A practitioner first cares about practical failures:

```text
a well-written email that validates too much
a source treated as proof too early
a contradiction hidden by a clean summary
a draft mistaken for a deliverable
a new rule that makes an active dossier fragile
a memory reused outside its proper scope
```

Public-facing language should therefore start from situations, not architecture.

## Preferred editorial posture

Prefer:

```text
show the professional risk
show the status
show what Pantheon blocks or preserves
show the human decision
```

Avoid:

```text
explaining the whole architecture first
using AI-industry vocabulary as the hook
presenting Pantheon as more automation
promising automatic proof, compliance or safety
```

## Main public message

The strongest public-facing message is:

```text
Pantheon frames the dossier flow: what enters, what is sent to AI, what leaves, and what remains.
```

French version:

```text
Pantheon cadre les flux du dossier : ce qui entre, ce qui est transmis à l’IA, ce qui sort et ce qui reste.
```

This is clearer for practitioners than the more doctrinal sentence:

```text
AI opens possibilities. Roles organize tensions. Evidence constrains. The human decides. Only the validated remains.
```

The doctrinal sentence may remain in governance documents, but it should not be the first public-facing slogan.

## Verb choices

Use different verbs depending on audience and location.

| Context | Preferred verb | Reason |
|---|---|---|
| Public README | frame / cadrer | clear, practical, non-runtime, non-absolute |
| Internal doctrine | govern / gouverner | strong governance meaning, but more abstract |
| Professional result | master / maîtriser | good for `controlled dossier` / `dossier maîtrisé`, but avoid overpromising total control |
| Status handling | qualify / qualifier | precise for source, evidence, output and memory statuses |
| Visual metaphor | channel / canaliser, filter / filtrer | useful for gates, ports and flows |
| Technical administration | administer / administrer | useful for statuses, not ideal as headline slogan |

Recommended public formulation:

```text
Pantheon frames the dossier flow.
It qualifies sources, reduces context to what is necessary, conditions outputs and bounds memory.
```

French:

```text
Pantheon cadre les flux du dossier.
Il qualifie les sources, réduit le contexte au nécessaire, conditionne les sorties et borne la mémoire.
```

Use `administer` only in secondary wording:

```text
Pantheon administers dossier statuses, not professional decisions.
```

French:

```text
Pantheon administre les statuts du dossier, pas les décisions professionnelles.
```

## Alternative formulations

```text
Pantheon stops fluent AI from becoming an unsafe professional act.
Pantheon turns AI output into a reviewable dossier path.
Pantheon keeps sources, doubts, contradictions and validation visible.
Pantheon helps professionals use AI without abandoning dossier method.
Pantheon does not make AI decide. It makes the decision path reviewable.
```

French:

```text
Pantheon évite qu’une réponse IA fluide devienne un acte professionnel risqué.
Pantheon transforme une sortie IA en chemin de dossier relisible.
Pantheon garde visibles les sources, les doutes, les contradictions et la validation.
Pantheon aide les professionnels à utiliser l’IA sans abandonner la méthode du dossier.
Pantheon ne fait pas décider l’IA. Il rend le chemin de décision relisible.
```

## Vocabulary to prefer

| Prefer | Why |
|---|---|
| dossier | speaks to professional work |
| source | concrete input |
| evidence / preuve | review support, not truth by itself |
| assumption / hypothèse | shows uncertainty |
| contradiction | strong practitioner signal |
| risk / risque | professional relevance |
| draft / brouillon | prevents premature authority |
| candidate output / sortie candidate | clear non-final status |
| deliverable / livrable | professional output |
| validated / validé | human decision signal |
| review / revue | professional process |
| decision / décision | keeps human authority |
| memory candidate / mémoire candidate | useful but not final |
| scoped memory / mémoire bornée | prevents overgeneralization |
| watch alert / alerte de veille | useful for regulatory change |
| affected assumption / hypothèse affectée | clearer than abstract knowledge drift |
| decision gate / seuil de décision | concrete escalation |
| review angle / angle de revue | avoids agent confusion |
| governance magistrature / magistrature de gouvernance | narrative, non-runtime |
| minimum necessary context / contexte minimal nécessaire | shows both quality and reduced exposure |

## Vocabulary to avoid or restrict

| Avoid or restrict | Reason | Better wording |
|---|---|---|
| agent | suggests autonomous runtime | role, review angle, profile when execution-side |
| multi-agent | suggests hidden debate or runtime | governance college, separated viewpoints |
| meta-agent | still suggests agency | governance role, magistrature |
| orchestrator | suggests runtime | coordination, procedure, framing |
| workflow engine | suggests execution | dossier path, review path |
| automated validation | forbidden meaning | human validation, explicit approval |
| automatic proof | false promise | evidence candidate, reviewable support |
| opposable dossier | legal overpromise | controlled, traceable, reviewable or mastered dossier |
| safe AI | overbroad promise | safer use, reviewable use |
| compliant by design | overpromise | compliance review support |
| audit automatic | overpromise | audit-ready trace, reviewable trail |
| truth | too strong | status, evidence state, validated claim |
| reliable memory | too strong | scoped and approved memory |
| smart memory | vague | Register Candidate / a Registre Probatoire entry |
| plugin marketplace | forbidden drift | watched external skill pattern |
| skill approval by popularity | false authority | governed skill watchlist |

## Titles that work better

Use titles that create an immediate professional situation.

Strong recommended titles:

```text
Pantheon in 60 seconds
What Pantheon frames
The risk: AI answers well, sometimes too well
Four fears, four responses
The email that commits too much
When a rule changes, which dossiers are touched?
From raw AI to a controlled dossier
A source is not proof
Useful disagreement, human decision
A draft is not a deliverable
No memory without validation
Cloud or local: choose according to the dossier
Worked dossiers: architect, lawyer, doctor
Eight review angles, one human decision
Not another tool: a dossier method
The vocabulary in plain language
What Pantheon is not
One formula
```

French recommended titles:

```text
Pantheon en 60 secondes
Ce que Pantheon cadre
Le risque : l’IA répond bien, parfois trop bien
Quatre peurs, quatre réponses
Le mail qui engage trop
Quand une règle change, quels dossiers sont touchés ?
De l’IA brute au dossier maîtrisé
Une source n’est pas une preuve
Désaccords utiles, décision humaine
Un brouillon n’est pas un livrable
Aucune mémoire sans validation
Cloud ou local : choisir selon le dossier
Dossiers déroulés : architecte, avocat, médecin
Huit regards, une décision humaine
Pas un outil de plus : une méthode de dossier
Le vocabulaire en clair
Ce que Pantheon n’est pas
En une formule
```

## Syntax principles

### Use short declarative sentences

Prefer:

```text
A draft is not a deliverable.
A source is not proof.
A useful output is not memory.
```

Avoid long stacked abstractions.

### Prefer status pairs

Good Pantheon language often uses contrasts:

```text
Found source ≠ proof.
Complete dossier ≠ useful context.
Draft ≠ deliverable.
Validated output ≠ memory.
Watch alert ≠ dossier update.
Impact suspected ≠ conclusion.
```

These pairs are memorable and enforce doctrine.

### Use professional verbs

Prefer:

```text
frame
check
review
mark
block
escalate
validate
reject
defer
archive
supersede
qualify
condition
bound
```

French:

```text
cadrer
vérifier
revoir
marquer
bloquer
escalader
valider
rejeter
différer
archiver
remplacer / rendre obsolète
qualifier
conditionner
borner
```

Avoid vague verbs:

```text
enable
leverage
optimize
orchestrate
empower
streamline
```

### Say what changes in practice

Every public-facing section should answer at least one of these questions:

```text
What could go wrong?
What does Pantheon preserve?
What does Pantheon block?
What must the professional decide?
What becomes evidence?
What remains only candidate?
What may become memory?
What context is actually necessary?
```

## Safer replacement phrases

| Before | After |
|---|---|
| governance-first AI layer | professional method around AI |
| agentic orchestration | external execution under a bounded mission |
| multi-agent debate | separated review angles |
| autonomous arbitration | procedural arbitration |
| evidence automation | evidence preparation and review |
| validated output | output validated by the professional |
| canonical memory | approved, scoped memory |
| RAG source of truth | searchable document source |
| regulatory intelligence | watch alert and affected-assumption review |
| dossier opposable | traceable, reviewable or mastered dossier |
| full dossier context | minimum necessary context |

## French replacement phrases

| À éviter | À préférer |
|---|---|
| agent | rôle, angle de revue, profil Hermes si exécution |
| méta-agent | rôle de gouvernance, magistrature |
| orchestration agentique | cadrage, coordination, chemin de revue |
| dossier opposable | dossier maîtrisé, traçable, relisible |
| preuve automatique | support de preuve, preuve candidate, élément à revoir |
| validation automatique | validation humaine, approbation explicite |
| mémoire fiable | mémoire validée, bornée, reliée à des preuves |
| IA sécurisée | usage IA encadré, exposition réduite, revue visible |
| conformité automatique | support de revue de conformité |
| workflow intelligent | chemin de dossier, chemin de revue |
| contexte complet du dossier | contexte minimal nécessaire |

## Public-facing hierarchy

A public README should lead with:

```text
1. concrete risk
2. concrete example
3. dossier flow
4. minimum necessary context
5. sources, evidence, contradictions
6. human decision
7. memory control
8. technical boundary only after that
```

It should not lead with:

```text
1. architecture
2. runtime boundary
3. roles
4. external frameworks
5. schemas
6. integrations
```

Those topics matter, but not first.

## Recommended first-screen text

English:

```text
Pantheon Next helps professionals use AI on serious dossiers without letting a fluent answer become an unsafe professional act.

Pantheon frames the dossier flow: what enters, what is sent to AI, what leaves, and what remains.

It gives the AI enough context to work properly, but not the whole dossier exposed unnecessarily.
Nothing leaves without status.
Nothing remains without validation.
```

French:

```text
Pantheon Next aide les professionnels à utiliser l’IA sur des dossiers sérieux sans laisser une réponse fluide devenir un acte professionnel risqué.

Pantheon cadre les flux du dossier : ce qui entre, ce qui est transmis à l’IA, ce qui sort et ce qui reste.

Il donne à l’IA assez de contexte pour travailler correctement, mais pas tout le dossier exposé inutilement.
Rien ne sort sans statut.
Rien ne reste sans validation.
```

## Final editorial rule

```text
Do not sell Pantheon as more AI.
Show Pantheon preventing a professional mistake that fluent AI could make easier.
```
