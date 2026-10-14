# Pantheon Cockpit — Knowledge Navigation UX

Status: candidate support specification — documented non-implemented as dedicated UX; co-located Category navigation foundation exists.
Boundary profile: candidate_support_note.

This document owns the **Cockpit UX specialization for navigating reusable Knowledge**. It no longer defines a parallel persisted folder model.

Current responsibility split:

- `CATEGORY_CLASSIFICATION_MODEL.md` owns hierarchical `Category` records, `CategoryAssignment`, recursion and stable classification identity;
- `DOCUMENT_LIFECYCLE_GOVERNANCE.md` owns source intake, capture, document/Knowledge publication and retention boundaries;
- `DOCUMENT_PRODUCTION_LIFECYCLE.md` owns generated-draft review and sectorization;
- `HERMES_PROGRESS_ERROR_RETRY_UX.md` owns runtime progress, error and bounded-retry display rules;
- this document owns how those objects are **presented and navigated** in the `Connaissances` surface.

```text
Category persisted != folder UI
folder UI != physical directory
CategoryAssignment != source ownership
Card projection != persisted business record
Knowledge visible != Evidence
runtime success != approval
projection != persistence
```

## 1. Current implementation boundary

A bounded co-located foundation already exists under `implementation/`:

```text
Connaissances
-> root Categories
-> Category Card
-> child Collection
-> child Category Cards / assigned entity Cards
```

The current implementation uses the generic `collection_read` contract and preserves one owner identity across multiple Category presentations. Knowledge without a Category remains visible through its applicable Project/owner collection.

Therefore:

```text
Category-backed hierarchical navigation = implemented foundation
persisted knowledge_folder backend        = superseded / must not be added
dedicated Knowledge visual/action UX      = documented non-implemented
breadcrumb/search UX                      = to verify
create/move/link/archive UI                = to verify
file/URL deposit UX                       = to verify
```

Implementation presence does not establish product adoption or production activation.

## 2. Folder is a UI alias for Category navigation

The Cockpit may use the familiar word `folder` when it improves comprehension.

The governed backend concept is `Category`, not a second `knowledge_folder` object.

```text
UI folder
= presentation of a Category as a navigation container

UI folder membership
= projection of CategoryAssignment
```

The following former candidate objects are retired as independent backend concepts:

```text
knowledge_folder
knowledge_folder_item_link
```

Their useful semantics are already carried by:

```text
knowledge_folder.parent_folder_id
-> Category.parent_category_id

knowledge_folder_item_link
-> CategoryAssignment
```

Do not persist a parallel Folder tree for Knowledge navigation.

The UI alias must preserve these non-equivalences:

```text
Cockpit folder != NAS/filesystem directory
Cockpit move != source-byte relocation
folder membership != source ownership
folder deletion/retirement != source deletion
Category != Tag
Category != Project ownership
Category != authorization
```

## 3. Navigation contract

The `Connaissances` surface should support a simple hierarchical read path:

```text
Connaissances
├── breadcrumb
├── current Category title / description
├── search and filters
├── primary actions
├── child Category containers
└── Knowledge/item Cards
```

The hierarchy is recursive and has no product-specific fixed depth. Backend parent/cycle integrity belongs to `CATEGORY_CLASSIFICATION_MODEL.md`; this document only requires that the UI render the resulting hierarchy coherently.

Recommended default human organization may use broad first-level families such as:

```text
Référentiels
Responsabilité
Méthodologie
Techniques
Réglementations
```

These are defaults, not immutable taxonomy or physical directories.

### Breadcrumb

Nested navigation should expose the current Category path.

Example:

```text
Connaissances / Réglementations / Urbanisme / PLU et PLUi
```

Requirements:

- ancestors are navigable;
- current container is explicit;
- long paths collapse responsively;
- mobile preserves parent/current context;
- a search result can reveal its Category path;
- a proposed move/link shows source and destination context before confirmation.

Breadcrumb context does not change permissions, source provenance or classification authority.

## 4. Visual grammar

The remaining distinctive responsibility of this document is the object-family visual grammar.

### Category container

A Category projected as a navigation container should use a **gradient-filled card surface**.

```text
background = controlled gradient fill
role       = container / navigation
icon       = Category/folder affordance
text       = accessible high contrast
```

The gradient communicates object family only.

```text
gradient fill != approved
gradient fill != active binding
gradient fill != high confidence
gradient fill != Evidence
gradient fill != lifecycle status
```

### Knowledge item

A reusable Knowledge item should remain visually in the same card family while using a **neutral interior with a strong gradient outline** rather than a gradient-filled surface.

```text
Category container = filled gradient
Knowledge item      = gradient outline, neutral fill
```

The exact CSS technique is not governed here. Accessibility and semantic distinction matter more than implementation mechanism.

### Status separation

Lifecycle, processing, access and review states use badges/icons/text separate from the container/item grammar.

```text
fill/outline = object family
badge/icon   = lifecycle or access state
```

This prevents visual styling from implying truth, approval, Evidence or authorization.

## 5. Item presentation and actions

A Knowledge Card should prioritize:

- title;
- concise summary/type;
- source/provenance cue;
- update/review information when material;
- applicable Category path/context;
- source-access posture when material.

Candidate actions may include:

```text
Open
View sources
Download original
Move / reclassify
Add to another Category
Edit metadata
Request processing
Review
Archive
```

Action availability must come from current owner policy/state. A Card does not infer an action merely because it can display one.

```text
Card visible != action authorized
Category assignment != task authorization
UI control present != consequential write permitted
```

## 6. Move, link and archive semantics

The UX must distinguish organizational classification from source/persistence effects.

```text
Move
= change Category assignment posture

Add to another Category
= add another bounded presentation of the same owner identity
```

A single item may appear in several Categories without duplicating source bytes or business identity.

Archive/removal vocabulary must remain explicit:

```text
remove Category assignment
archive Category
archive Knowledge item
delete source capture
```

These are separate operations.

Retiring a Category must not silently delete assigned Knowledge or original sources. Exact persistence rules remain owned by the corresponding Category, Knowledge and source lifecycles.

## 7. Source and document intake handoff

This document does not duplicate the document lifecycle.

When the user adds a file, URL or connector source from the Knowledge surface, the UX captures a requested destination/context and hands the source to `DOCUMENT_LIFECYCLE_GOVERNANCE.md`.

```text
file / URL / connector input
-> governed source intake
-> preserved source capture
-> processing when required
-> Knowledge/document candidate
-> human/review gates where required
-> Category assignment when admitted
```

Required non-equivalences are inherited from the lifecycle owner:

```text
file received != Knowledge published
same filename != same source
same hash != automatic merge
processing completed != reviewed
Knowledge published != Evidence admitted
```

A visible provisional/intake Card may project current state, but it is not the source object itself.

## 8. Produced-document handoff

Generated or materially rewritten documents remain governed by `DOCUMENT_PRODUCTION_LIFECYCLE.md`.

The Knowledge UX may expose a draft/review Card and intended Category destination, but it must preserve:

```text
draft generated != content reviewed
reviewed version N != later version N+1 reviewed
sectorization proposed != sectorization approved
archived != distributed
```

The UX must not convert Hermes completion into retained/final Knowledge automatically.

## 9. Progress and failure display

Progress, errors, diagnosis and retry semantics are owned by `HERMES_PROGRESS_ERROR_RETRY_UX.md`.

The Knowledge surface may project those observations but must not invent them.

```text
executor-measured percentage -> may display percentage
step observation              -> may display steps
running only                  -> indeterminate display
no fresh observation          -> unknown/stale, not fabricated progress
```

```text
runtime recovered != output validated
retry available != retry authorized
```

## 10. Search and filters

Candidate search scopes:

```text
Current Category
Current Category and descendants
All Knowledge
Selected Categories
```

Useful filters may include:

- Knowledge/source type;
- date;
- lifecycle/review state;
- Project origin;
- access posture;
- author/organization;
- tags;
- language.

Search is retrieval/navigation. It does not change CategoryAssignment, Evidence status, source authority or permissions.

## 11. Permissions and access

Category visibility and source access are independent.

```text
Category visible != every source downloadable
Knowledge Card visible != confidential source visible
classification != authorization
```

The UI should explain when material:

- whether the Card is visible;
- whether source detail is visible;
- whether original download is allowed;
- why an action is restricted.

Linking an item into a broader Category must never bypass owner/source permissions.

## 12. Responsive and accessibility requirements

The Category/Knowledge distinction must not rely on color alone.

Category containers require a semantic container/navigation affordance and accessible name. Knowledge items require an item-type cue and explicit status/action labels.

Minimum expectations:

- sufficient contrast over gradients;
- visible keyboard focus;
- semantic labels/icons in addition to fill/outline;
- non-color status indicators;
- screen-reader meaningful names;
- reduced-motion compliance;
- no essential action hidden behind hover only;
- mobile alternative to drag-and-drop.

## 13. Responsibility boundary

### Classification owner

`CATEGORY_CLASSIFICATION_MODEL.md` owns:

- Category identity and hierarchy;
- parent/cycle integrity;
- CategoryAssignment;
- classification persistence;
- recursive Category/Collection semantics.

### Document/Knowledge lifecycle owners

They own:

- source capture and retention;
- intake/classification lifecycle;
- Knowledge publication;
- produced-document review and sectorization;
- archive/distribution distinctions.

### Cockpit Knowledge UX

This document owns:

- human navigation grammar;
- breadcrumb/search/filter posture;
- Category-container vs Knowledge-item presentation;
- interaction wording for move/link/archive intent;
- permission/access visibility;
- responsive/accessibility requirements.

### Hermes

Hermes may process through separately admitted capabilities and report observations. It does not decide classification authority, final publication, source access, Evidence admission or archive consequences.

## 14. Current acceptance posture

Already established by the co-located foundation:

- root `Connaissances` can expose root Categories;
- Category hierarchy can recurse through generic Card/Collection reads;
- the same owner identity can appear in several Category contexts without duplication;
- unclassified Knowledge need not disappear from its Project/owner context.

Still to verify as dedicated product UX:

- breadcrumb behavior;
- search/filter behavior across Category scopes;
- create/rename/reclassify/link/archive controls;
- file/URL/connector intake controls;
- gradient-filled Category container treatment;
- gradient-outline Knowledge item treatment;
- responsive/mobile implementation;
- accessibility implementation;
- permission-aware action presentation.

## Final rule

```text
Category owns the logical hierarchy.
The Cockpit may call that hierarchy folders for human navigation.
Cards project owner records; they do not become the records.
Filled gradient identifies a Category container, not status.
Gradient outline identifies a Knowledge item, not truth.
Source, review, progress, archive and permission rules remain with their existing owners.
```