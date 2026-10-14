# Cockpit CSS clean-slate rebuild

## Decision

The Cockpit visual layer is rebuilt from one current CSS architecture. Historical V2/V3 styles are not wrapped, versioned or retained as fallbacks after cutover.

The JavaScript navigation, CockpitSnapshot contract, renderer DOM, schemas, editors, provenance, status and authorization semantics remain unchanged unless a separate reviewed change proves that a DOM adjustment is required.

```text
CSS rebuild != Cockpit architecture rewrite
visual projection != semantic model
UI status != authorization
```

## CSS modules

```text
styles/
  cockpit.css
  cards.css
  families.css
  editors.css
```

The split follows stable technical responsibilities rather than card catalogue entries.

### `cockpit.css`

Authority for:

- local reset and global tokens;
- viewport and fixed shell;
- header, menus, navigation and Hermès dock;
- Swiper host geometry;
- global responsive rules;
- global z-index and motion boundaries.

It contains no Project, Knowledge, Skills or Tool palette.

### `cards.css`

Authority for:

- the common card geometry;
- front, back and flip;
- card header, identity, body, metadata and actions;
- the shared three-blob primitive;
- the 12 px corner and 12 px top-band primitives;
- common back-border behaviour;
- common card state presentation.

It contains no business-family palette.

### `families.css`

Authority for declarative visual variables only:

- level: `pack`, `booster`, `card`;
- family: Pantheon, Affaires, Knowledge, Skills, Tools;
- kind: Project, Work, Folder, Information, Decision and other visible kinds;
- family palettes, gradients and blob compositions;
- project-accent inheritance.

It must not redefine shell, Swiper, card dimensions or shared content geometry.

### `editors.css`

Authority for:

- schema editor;
- Contacts and Information editors;
- ProjectClaim surfaces;
- forms, overlays, modals and edit actions.

## Cascade hierarchy

The four files share one explicit layer order:

```css
@layer reset, tokens, shell, navigation, cards, families, states, editors, responsive;
```

Responsibility order:

```text
reset
→ tokens
→ Cockpit structure
→ common card primitive
→ family variables and signatures
→ states
→ editors
→ responsive adaptation
```

No selector should rely on accidental stylesheet order.

## Card axes

The visual model separates four independent axes:

```text
level   → pack | booster | card
family  → pantheon | affaires | knowledge | skills | tools
kind    → project | work | folder | information | decision | ...
status  → active | review | blocked | ...
```

Project colour is a fifth contextual value exposed as `--project-accent`; it is not a status.

Example:

```html
<article
  class="v2-card"
  data-level="card"
  data-family="affaires"
  data-kind="work"
  data-status="active"
  style="--project-accent:#d75a28"
>
```

The existing class names may remain during the DOM-preserving rebuild. New CSS filenames and selectors carry no V2/V3 version labels.

## Scope to retire

The canonical page must stop loading the historical visual cascade once equivalent coverage exists:

- `styles/index.css`
- `styles/v2.css`
- `styles/v2_refinement.css`
- `styles/v2_swiper.css`
- `styles/v2_shell_controls.css`
- `styles/v3_living_cards.css`
- `styles/v3_geometry.css`
- `styles/v3_collections.css`
- transitional family and token files introduced before consolidation;
- editor-specific historical files once their rules are migrated.

No historical stylesheet remains loaded as a fallback after cutover.

## Visual grammar retained

- Pack / Booster / Card hierarchy.
- Pantheon: three organic CSS outline blobs, cyan / yellow / magenta.
- Affaires: three filled organic blobs.
- Project booster: white surface and project-colour blob composition.
- Work: white surface with a 12 × 12 px project-colour corner.
- Folder: white surface with a 12 px project-colour top band.
- Knowledge and Skills: full-card gradients with no card border on the front.
- General-card backs: 4 px coloured border.
- Business/project-card backs: 1 px coloured border.
- No shadows, glow, paper texture, hover animation or swipe animation.

## Migration sequence

1. Inventory current DOM classes, editor surfaces and computed responsibilities.
2. Build `cockpit.css` and reproduce shell, navigation and Swiper geometry.
3. Build `cards.css` and reproduce the common front/back card contract.
4. Build `families.css` with level, family, kind and project-accent variables.
5. Build `editors.css` and migrate all edit surfaces.
6. Replace the canonical stylesheet list in one cutover commit.
7. Delete retired styles and stale tests immediately after cutover.
8. Verify demo/live, mobile/desktop, keyboard, flip, swipe, nested descent, New card and editor interactions.

There is no `data-cockpit-css="next"`, no CSS version selector and no dual production cascade.

## Acceptance

- exactly four canonical Cockpit stylesheets;
- one visible CSS authority per responsibility;
- no old stylesheet loaded by the canonical page;
- no V2/V3 naming in new stylesheet filenames;
- no family-specific shell, Swiper or card-size override;
- no renderer dependency on stylesheet filenames;
- no Swiper API outside MotionAdapter;
- bounded mounted projections remain unchanged;
- demo and live use the same visual entry point;
- full CI green plus browser verification at representative mobile and desktop widths.
