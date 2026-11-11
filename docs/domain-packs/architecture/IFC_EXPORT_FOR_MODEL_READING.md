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
declared property != observed fact
quality advice != approval of the model
```
