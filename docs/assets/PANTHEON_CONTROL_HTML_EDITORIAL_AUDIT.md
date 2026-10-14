# Pantheon Control — HTML editorial audit

Date: 2026-07-03

Status: editorial audit — static prototype only.

## Purpose

This audit prepares a global cleanup of the Pantheon Control HTML prototype.

Goal:

```text
keep only what is useful, clear, consequential and readable;
remove redundant pages, chapters, words and mock interactions;
make the prototype simple, direct and professionally understandable.
```

Boundary:

```text
No runtime behavior.
No approval engine.
No memory engine.
No connector execution.
No scheduler.
No queue.
No external action.
No automatic validation.
```

## Editorial rule

A page stays only if it helps the user understand or decide something consequential:

```text
source;
evidence;
status;
memory;
skill;
scope;
approval;
external action;
professional responsibility.
```

A page should be reduced, merged or removed if it mainly repeats that the prototype has no effect, shows mock buttons without strong governance value, or looks like operational infrastructure without a clear professional decision.

## Page classification

| Page | Decision | Reason | Action |
|---|---|---|---|
| `index.html` + `pages/home-manifest.js` | keep | Main explanation of the professional problem and role split. | Tighten language, keep as manifesto. |
| `modules.html` | keep, reduce | Useful to explain stack usage, but too many cards at equal level. | Reorganize into 4 families: interface, execution, memory/search, observation/automation. |
| `evidence.html` | keep | Core Pantheon value: proof, status, risk, decision. | Keep. Simplify labels and remove ornamental wording. |
| `discussion.html` | keep, reduce | Strong value: branches, refused hypotheses, decision visibility. | Keep as decision branch page. Reduce buttons and repeated warnings. |
| `drafting.html` | keep or merge | Useful but close to discussion. | Either keep as “Rédaction candidate” or merge into decision workflow after first cleanup. |
| `skills.html` | keep, rewrite | Skills are important but current page is too thin. | Rewrite as skills = governed reusable methods, not buttons to activate. |
| `references.html` | keep, reduce | Useful support center for reference material. | Keep. Shorten doctrine sentence and reduce card noise. |
| `observability.html` | keep, reduce | Useful to show that trace is not proof. | Keep one clear Langfuse panel and remove secondary clutter. |
| `services.html` | merge | Overlaps with modules, machines and installations. | Merge into a single Infrastructure page. |
| `machines.html` | merge | Useful only as infrastructure context. | Merge into Infrastructure; remove standalone page from nav. |
| `installations.html` | merge / hide | Too operational and long; risk of implying install planning. | Move to Infrastructure or Admin/Bootstrap, hidden from main nav. |
| `files.html` | merge | Files are source intake, not a separate primary chapter. | Merge into Evidence / Sources. Remove standalone page. |
| `surveillance.html` | remove or merge | Too light and risks implying automatic controls. | Remove from nav; merge useful journal content into Observability or Dashboard. |
| `deck.html` | keep for prototype only | Important UX experiment, but not a primary governance chapter. | Rename as UX prototype or move lower in nav. |

## Recommended target navigation

Preferred visible navigation after cleanup:

```text
Pilotage
- Accueil
- Preuves & statuts
- Décisions
- Rédaction candidate

Méthodes
- Skills & mémoire
- Références
- Modules & usages

Infrastructure
- Services, machines & observabilité
- Prototypes UX
```

Pages to remove from primary navigation:

```text
surveillance.html
files.html
machines.html
installations.html
```

These pages should not be deleted immediately unless their content is safely merged.

## Content cuts by type

### Cut repeated safety phrases

Remove repeated variants of:

```text
Aucun changement réel.
Demande candidate.
Documenté non implémenté.
Aucune exécution.
```

Keep the warning once per page, ideally in the lede or a boundary note.

### Cut weak buttons

Remove or reduce buttons that only say:

```text
Préparer configuration
Préparer ajout
Préparer retrait
Préparer réveil
Utiliser comme source
Activer
```

These are useful only if attached to a visible decision, risk, source or approval path.

### Replace technical phrasing

Replace product/runtime language with professional language except on modules/infrastructure pages.

Examples:

```text
runtime -> outil d’exécution
adapter -> liaison outil
candidate -> proposition à vérifier
canonical memory -> mémoire validée
external effect -> action envoyée ou engagement externe
```

### Keep strong governance sentences

Keep and sharpen distinctions like:

```text
Une trace décrit l’exécution ; elle ne valide pas le résultat.
Une source retrouvée n’est pas une preuve.
Une mémoire retrouvée n’est pas une mémoire validée.
Une réponse bien écrite peut rester inutilisable.
Préparer un message n’est pas l’envoyer.
```

## First implementation batch

Recommended first batch:

1. Rewrite `home-manifest.js` more tightly.
2. Rewrite `modules.html` into 4 grouped families.
3. Simplify `services.html`, `machines.html`, `installations.html` into one new `infrastructure.html` page.
4. Remove `surveillance.html`, `files.html`, `machines.html`, `installations.html` from `nav.js` after merging useful content.
5. Keep old files for one pass, then delete only after verifying no navigation dependency remains.

## Repo state

```text
Documented non-implemented.
Static prototype audit only.
No HTML deletion or rewrite performed in this audit step.
```
