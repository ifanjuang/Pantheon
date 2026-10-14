# Card Stack visual language

Status: illustrative design guidance — documented non-implemented.
Boundary profile: candidate_support_note.
Owner: `docs/governance/CARD_STACK_MODEL.md`.

This guide translates the existing Card Stack projection grammar into a bounded visual system. It creates no new governed object, lifecycle, status vocabulary, renderer, resolver, runtime, approval engine, memory engine or external action.

## Shared anatomy

Every expanded card uses the same reading order:

1. written object kind;
2. exact owner-defined status;
3. title and scoped summary;
4. consequence or risk treatment;
5. essential metadata;
6. dominant relation;
7. bounded review affordance.

A compact card keeps only object kind, title, exact status and one decisive qualifier. Compact means intentionally reduced markup; it must not be a clipped expanded card.

## Non-colour identity

Card families remain distinguishable when colour is unavailable.

| Projection | Structural marker | Required written distinction |
|---|---|---|
| Source | solid left rule | original, received, retrieved or observed |
| Evidence Candidate | double inset rule | reliance status and conflict posture |
| Candidate Output | top bracket | candidate or draft; never deliverable by implication |
| Action Candidate | arrow notch | prepared/proposed and authorization posture |
| Gate | heavy frame | threshold, blocking reason and consequence level |
| Human Decision | split status band | recorded status and current applicability separately |
| Trace | timeline rail | observed event/result and explicit non-evidence warning |
| Reference | dashed frame | reusable/advisory and non-executable |

Colour is supplemental. Text, border pattern, icon shape and anatomy carry meaning.

## Status grammar

No aggregate badge may collapse independent axes.

```text
process posture
!= governance maturity
!= authorization posture
!= evidence posture
!= operational posture
```

Human Decision projections must expose at least:

```text
recorded: yes | no
current: yes | no | unresolved
expires_at: value | none
revoked: yes | no
superseded_by: reference | none
scope: exact bounded scope
```

A card must never infer `current` from `recorded`.

## Compact and expanded variants

### Compact

Use for secondary depth, sibling summaries and mobile decks.

```text
kind
status
short title
one decisive qualifier
```

Compact cards do not hide an open Gate or consequential warning. When those exist, the warning remains visible or the card expands.

### Expanded

Use for the principal review item, open Gate, decision surface or contested Evidence Candidate.

```text
kind + status
scope
summary
risk/consequence
provenance
relations
history/currentness
next safe review action
```

## Scene and global navigation

```text
project selector or Constellation
= change global Project Space

primary tabs or rail
= change Scene

vertical order
= read Deck depth

horizontal group
= move between siblings at the same level

tap or Enter
= open governed detail

bounded menu
= expose review intents or prepare an Action Candidate
```

Top and bottom controls must not duplicate the same navigation meaning. Global-space navigation remains visually separate from Scene navigation.

## Interaction semantics

Real controls use native elements:

- links for navigation;
- buttons for local disclosure or bounded menus;
- `aria-current` for the active Scene;
- `aria-expanded` for detail disclosure;
- visible `:focus-visible` treatment;
- meaningful labels that describe review intent, not execution.

Forbidden labels include ambiguous commands such as `Run`, `Approve now`, `Send` or `Install` when the control only prepares or reviews a candidate.

Preferred labels:

```text
Open details
Inspect provenance
Compare support
Review blocking reasons
Prepare action candidate
Open decision record
```

## Cluster boundary

`Cluster` is a local visual grouping device only. It may group sibling cards by source family, review concern or relation type.

```text
Cluster != governed object
Cluster != stored workflow
Cluster != authorization scope
Cluster != graph node by default
```

## Static prototype coverage

The companion `visual-language.html` demonstrates:

- all eight required card families;
- explicit compact and expanded markup;
- written non-colour status distinctions;
- recorded/current decision separation;
- expiry, revocation and supersession fields;
- semantic links and disclosure buttons;
- visible keyboard focus;
- separate global and Scene navigation;
- bounded action-menu intent without execution.

## Implementation status

```text
implemented:
- this illustrative guide;
- static HTML prototypes.

partial:
- bounded read-only projections elsewhere in the repository.

documented non-implemented:
- production renderer;
- design tokens package;
- Scene/Deck state engine;
- Current Decision Resolver;
- authenticated OpenWebUI integration;
- Hermes handoff integration.
```

## Invariants

```text
card projection != object ownership
visual distinction != governance status
Gate != Decision
Action Candidate != execution
recorded != current
UI interaction != Hermes command
prototype present != production implementation
```