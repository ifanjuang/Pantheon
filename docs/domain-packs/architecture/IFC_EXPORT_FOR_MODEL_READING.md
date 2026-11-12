# IFC export for the model reading

Status: operating guidance, candidate. Owner: Project Anatomy domain pack.

The model reading (`implementation/mvp_vertical/model_reading.py`) reads the
current index of each model piece of an affaire once and publishes, beside the
Anatomy projection, the levels, spaces, openings, walls and neighbours a screen
or Hermes needs. It trusts geometry first and treats what a model declares as
clues, because models are rarely exported to the letter of the IFC schema. This
page says what the reading does with an imperfect model, and what to set in the
authoring tool so the reading becomes exact.

## What the reading does with an imperfect model

| Common situation | What the reading does |
|---|---|
| Exterior doors and French windows modelled in a window family; openings in load-bearing walls modelled in a door family | The nature of an opening is deduced from geometry: exterior when only one side has a space and that side is outside the building outline; door or French window when the sill is at floor level and the height is at least 1.90 m; a full-height opening narrower than 0.60 m is a full-height window. The IFC class and the declared type stay visible as clues. |
| A door opening onto a stair or a corridor that has no space | The empty side lies inside the level's outline: the opening is interior, towards an unmodelled room, not exterior. |
| An opening without a door or window in a wall between two spaces | A free opening (passage, bay), at least 0.50 m wide and 1.80 m high. |
| Rooms of one volume separated by a room separation line, without a wall | Spaces touching without a wall or door between them are open onto each other. |
| `Pset_WallCommon.IsExternal` set by wall type, `LoadBearing` never ticked | Geometry decides exterior; a property false everywhere is treated as not filled in. The difference is summarised once (declared against observed), not reported element by element. |
| Furniture, decoration, planting, generic objects | Not read; an agency file may also ignore type-name prefixes (`MVP_MODEL_CONVENTIONS`). |
| Storey elevations in absolute altitude, geometry relative | Sills are measured from the floor of the adjacent space. |

Every side, façade and neighbour is a geometric deduction and is said to be one.
A façade named from a model north left at its default is flagged as to be
confirmed before any comparison with elevations named by orientation.

## Every element, one engine

Besides spaces, walls and openings, the reading describes every building element
the same way (columns, beams, members, footings, slabs, roofs, stairs, railings,
coverings, plates): IFC class, predefined type, declared type, level, measured
length, width and height, orientation, the space holding it and its grid
position. What an element is comes from the category profile
(`registries/architecture_category_profile.registry.json`): IFC classes,
predefined types, type-name patterns and geometric conditions, first match by
priority; the door and window rules are entries like any other. The words of
the categories present are published with the reading, so designations such as
"poteaux", "garde corps R01" or "poutres séjour" work for any category.

Sizes of doors and windows are measured from geometry (along the host wall and
in height): families often carry their real sizes in custom parameters and leave
the IFC ones at a default. Declared sizes, from the IFC attributes or from family
parameters by name, stay visible, and a difference over 5 cm is pointed out.
An agency names its own size parameters in the conventions file.

## Overlaying an engineer's model without shared coordinates

Engineers often export from their own origin (no site, another origin, sometimes
a slight rotation), so their columns and beams cannot inherit the architect's
rooms and grid lines. During the preparation of a new model index
(`anatomy_export.align_structural_models`, `model_alignment.py`), each structural
model is laid on the architect's model with the most rooms:

1. height: the engineer's ground floor (a level named RDC, R00 or ground floor,
   else the lowest non-foundation level) on the architect's lowest floor;
2. rotation: the dominant wall directions of both models, tried at the four
   quarter turns;
3. position: the core of the engineer's points on the architect's rooms, then
   refined so they fall on the architect's walls;
4. score: the share of the engineer's points on an architect wall, with the
   margin over the next best candidate.

The overlay is applied only when probable (score of at least 60 % and margin of
at least 15 points). Elements then carry the architect's level, room (or the
rooms on either side for a post inside a wall) and grid position, marked as
obtained by overlay. The overlay is recomputed when either model changes and
stays "to be confirmed": a human confirms it once per pair of indices. Shared
coordinates, or an agreed common origin such as the intersection of two grid
lines at level 0.00, remain the reliable way.

## Anatomy sources

Which files the readings rest on is a human choice made on each file's card in
the Workspace (`anatomy_source` in the card corrections): add the file as a
complement, or replace another source (by default the previous index of the
same piece), with its role (reference, complement, control), discipline, use,
scope, the alignment known at export (shared coordinates, agreed origin, none),
a note, and whether to consolidate now. The Workspace owns that declaration;
the agency side only reads it.

Consolidation (`agency consolidate --code X`, or an export when the card asks
for it) reads the declared sources, overlays the engineers' models, and
publishes each source's state in `<CODE>.json` (`anatomy_sources`) for the
Cockpit and Hermes:

| State | Meaning |
|---|---|
| en attente | declared, not consolidated yet (or file or declaration changed since): not read |
| activée | consolidated without problem; a well-indexed drawing is "activée (index and text, no geometric alignment)" |
| avertissement | consolidated with minor inconsistencies: model quality to improve, overlay to confirm, size gaps, index read from the file name or not read |
| erreur | cannot be brought together: unreadable model, uncertain overlay without shared coordinates, insufficient quality, missing file |
| remplacée | replaced by a source whose consolidation succeeded |
| inactive | switched off on its card: not read |

A replacement takes effect only when the new source is `activée` or in
`avertissement`; otherwise the old source stays active and the new one says why.
In the validated Anatomy nothing is erased: values from a replaced source are
superseded through a reviewed batch. A confirmed overlay is attached to the
pair of model indices and falls at the next index. While no file of an affaire
declares anything, every current model piece is read as before.

### Workspace contract

What the Workspace Cockpit writes, in its own database, and the agency reads
read-only:

- on a file card, `anatomy_source` inside the card corrections
  (`workspace_document_metadata_overrides.overrides_json`), an object:

  ```json
  {"active": true, "mode": "complément | remplacement", "replaces": "<path of the replaced file>",
   "role": "référence | complément | contrôle", "discipline": "…", "usage": "conception | permis | DCE | exé | DOE",
   "perimeter": "…", "declared_alignment": "coordonnées partagées | origine convenue | aucun",
   "note": "…", "consolidate_now": true, "set_by": "…", "set_at": "<UTC>",
   "alignment_confirmed": {"by": "…", "at": "<UTC>", "reference_fingerprint": "<from the published overlay>"}}
  ```

  Unknown values fall back to defaults (complement); texts are cut at 300
  characters. The correction endpoint must accept this one object field besides
  its strings and lists. Model files (IFC, and DWG later) must appear as file
  cards for the declaration to be possible;
- on a project card, the "Consolider les sources" button adds a row to
  `workspace_anatomy_consolidation_requests (workspace, project_code,
  requested_at, requested_by)`.

What the agency publishes and the Workspace displays: `anatomy_sources` in
`<CODE>.json` (one line per file: state, reasons, reading, overlay, replacement,
last consolidation). A timer runs `agency consolidate-pending`: a project card
request consolidates every declared source of the affaire; a changed card
consolidates the sources that ask for it now; each request is handled once,
remembered on the agency side, never written back to the Workspace. The card
compares its own request time with the published last consolidation to show
"demandée" or "faite".

## File sheets and the project core

The Anatomy has two layers. Each activated file has a **file sheet**: what this
file says. Each project has a **core**: what the project keeps. The sheets are
the plug-and-play part; the core holds what crosses files.

```text
FILE SHEET (one per activated file)         CORE (one per project)
"what this file says"                       "what the project keeps"
identity: fingerprint, path, piece, index   nodes: rooms, walls, lots…
declaration (from the Workspace card)       shared vocabulary
state and reasons                           validated facts, each citing its files
alignment, typed by the file's nature       questions between files
body: what was read                         history (replacements)
Hermes proposals about this file
```

| Nature | Body | Alignment |
|---|---|---|
| IFC model | rooms, openings, walls, elements by category, minimal geometry, quality | 3D overlay: rotation, offsets, score, confirmed or not |
| PDF drawing | index and text | level and scale (later) |
| Section / elevation | index and text | section mark / façade (later) |
| Specification (CCTP) | lots (later) | lot, discipline |
| Quote | lot, company, amounts to confront (later) | lot |
| Photo | date, room proposed by Hermes (later) | room |

Three rules keep it light:

1. **What is computed is keyed by the file's fingerprint.** An unchanged file is
   never read twice: deactivating and reactivating a source, or coming back to an
   earlier index, finds its sheet again. A changed file gets a new sheet.
2. **Comparisons are keyed by the pair of fingerprints** (an engineer's overlay
   on the architect's model, later drawing against drawing or drawing against
   model) and kept while the pair is the same.
3. **The project file stays small.** `<CODE>.json` carries the core, one line per
   source and the questions; a sheet is read on demand (`get_project` focus
   `fichier <name>`). A local model then reads whole what it is given.

Where things live: the truth of a source is on its file. What a human enters
(declaration, corrections, overlay confirmation) is on the Workspace card; what
is computed (reading, alignment, state) and Hermes' proposals are published by
the agency and shown on the card. The project's list of sources is a view
rebuilt at each consolidation, never edited; each consolidation that brings a
source in, or that was requested, keeps a snapshot (files, fingerprints, states) of what the state of
the affaire rested on, the last twenty kept. A file moved in the Workspace keeps
its declaration, found again by its content digest.

Hermes analyses and enriches both layers by proposals only: about a file ("this
specification describes lot 04", "this photo shows the kitchen") or about the
core ("room 3 of the model is the kitchen of the drawing", "remember that…",
"confirm the overlay"). Proposals go through the existing candidate path and a
human validates them; Hermes writes neither a sheet nor the core. One task, one
sheet: the size a local model holds.

Status: fingerprint-keyed model sheets, the drawing sheet (index and text),
consolidation snapshots, moved files and the `fichier` focus are implemented on
the agency side. The Cockpit card display and actions, the other natures and
Hermes proposals are not implemented yet.

## Model quality and re-export

Each reading carries a quality level (`bonne`, `à améliorer`, `insuffisante`),
the checks behind it, the declared-against-observed notes and, when needed, a
re-export advice. `get_project` puts it in its summary; Hermes then answers with
what is read, says what is missing and proposes a re-export citing the advice,
without inventing.

## What to set in the authoring tool (Revit)

| Setting | Why |
|---|---|
| Export in IFC4 (Reference View) rather than IFC2X3 | Richer, better defined classes and properties. |
| Set the project true north | Façades named by orientation match the elevations. |
| Export space boundaries (1st level) | "This wall bounds this room" becomes direct instead of computed. |
| Export the Revit property sets (phase created, phase demolished) | Existing and new elements are known directly. |
| Fill the instance Mark of doors and windows, with the drawings' nomenclature | One key shared by model, drawings, specifications and quotes. |
| Use `IfcExportAs` and `IfcExportType` in families | An exterior door kept in a window family is exported as an `IfcDoor`; an opening in a load-bearing wall as an opening element; the predefined type (door, French window, skylight) is explicit. The families stay as they are. |
| Set wall function (interior / exterior) and the structural flag on load-bearing walls | `Pset_WallCommon.IsExternal` and `LoadBearing` become reliable. |
| Name and number every room; export grids in both directions | Room sheets and grid positions (on line B, between 2 and 3). |

Standard properties are read where they are reliable and map to the property
profile: `Pset_WallCommon` (`IsExternal`, `LoadBearing`, `FireRating`,
`AcousticRating`, `ThermalTransmittance`), `Pset_WindowCommon` and
`Pset_DoorCommon` (`IsExternal`, `FireRating`, `ThermalTransmittance`).

## Next: an agency IDS

An IDS file (buildingSMART Information Delivery Specification) can state the
agency's model requirements (every wall has its load-bearing function, every
door and window its mark, every space a name and a number) and check each new
index; IfcOpenShell's `ifctester` and the catalogued IFClite runtime can run it.
The checks above are the first, built-in step.

```text
model reading != model copied into the Anatomy
declared source != consolidated source
file sheet != project core
declared property != observed fact
quality advice != approval of the model
```
