"""Reading of an affaire's current model: elements, their position and their neighbours.

The model is the source of detail; this module reads it, it does not copy it into
the Project Anatomy. For the current index of each model piece it computes once
what a screen or Hermes needs to answer "which room does the kitchen open onto",
"which wall is on grid line B", "which windows are on the west façade":

- levels and spaces (name, number, level, surface);
- doors and windows: host wall, the space on each side, exterior or not, façade,
  size, type, position against the grid lines;
- walls: level, length, thickness, composition, the space on each side, façade
  when exterior, grid position, the walls they join and how;
- neighbours: spaces linked by a door, spaces sharing a wall.

Sides and façades are computed by geometry (models seldom export space
boundaries), so they are deductions: each reading says so. A façade is named from
the model's own north; when the model keeps the default north, the reading says
so too, and the orientation must be confirmed before it is compared with
elevations named by orientation.

The result is a reading, never a source: nothing is stored in the Anatomy and
nothing is approved. It is written to one file per model piece next to the
Anatomy projection and recomputed only when the model file changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import os
from typing import Any, Iterable

SCHEMA = "pantheon.model_reading.v1"
CONVENTIONS_ENV = "MVP_MODEL_CONVENTIONS"  # local agency file: type prefixes to ignore, modelling habits
FACADES = ("nord", "est", "sud", "ouest")
PROBES = (0.35, 0.6, 0.9)  # metres from a wall or opening axis, tried in order on each side
GRID_TOLERANCE = 0.15      # metres: an element closer than this to a grid line is on it
# Names of size parameters families often carry instead of (or besides) the IFC ones; an agency adds its own
# in the conventions file ("size_parameters": {"width": [...], "height": [...]}).
SIZE_PARAMETERS = {"width": ("largeur", "largeur brute", "largeur tableau", "width", "rough width", "l"),
                   "height": ("hauteur", "hauteur brute", "hauteur tableau", "height", "rough height", "h")}
SIZE_TOLERANCE = 0.05  # metres between a declared size and the measured one before it is pointed out
# Element classes read besides spaces, walls and openings; the category profile says what each one is.
GENERIC_CLASSES = ("IfcColumn", "IfcBeam", "IfcMember", "IfcFooting", "IfcSlab", "IfcRoof", "IfcStair", "IfcStairFlight",
                   "IfcRailing", "IfcCovering", "IfcPlate", "IfcBuildingElementProxy", "IfcFurnishingElement")


class ModelReadingError(ValueError):
    pass


# ---------- pure geometry, testable without a model ----------

def facade(vx: float, vy: float, north_deg: float = 0.0) -> str:
    """Façade an outward direction faces, the model's north being north_deg clockwise from +Y."""
    angle = (math.degrees(math.atan2(vx, vy)) - north_deg) % 360
    return FACADES[int((angle + 45) // 90) % 4]


def side_spaces(center: tuple[float, float], normal: tuple[float, float], z: float,
                spaces: list[dict[str, Any]], tree: Any = None) -> tuple[str | None, str | None]:
    """Id of the space on each side of an axis (normal side first), probing outward.

    With ``tree`` (a shapely STRtree over the spaces' footprints) only nearby spaces are tested.
    """
    from shapely.geometry import Point

    found = []
    for sign in (1, -1):
        hit = None
        for distance in PROBES:
            point = Point(center[0] + sign * distance * normal[0], center[1] + sign * distance * normal[1])
            candidates = [spaces[i] for i in tree.query(point)] if tree is not None else spaces
            hit = next((s["id"] for s in candidates if s["z"][0] - 0.3 <= z <= s["z"][1] + 0.3 and s["poly"].contains(point)), None)
            if hit:
                break
        found.append(hit)
    return found[0], found[1]


def envelope(polygons: list[Any]) -> Any:
    """Footprint of one level from its spaces, holes filled: an area inside it without a space is unmodelled, not outside."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    merged = unary_union([p.buffer(0.6) for p in polygons]).buffer(-0.6)
    parts = getattr(merged, "geoms", [merged])
    return unary_union([Polygon(part.exterior) for part in parts if not part.is_empty and hasattr(part, "exterior")])


def grid_position(point: tuple[float, float], axes: dict[str, tuple[tuple[float, float], tuple[float, float]]],
                  direction: tuple[float, float] | None = None) -> str | None:
    """'sur la file B ; entre 2 et 3': for each family of parallel grid lines, on one or between two."""
    if not axes:
        return None
    families: dict[int, list[str]] = {}
    for tag, (_, d) in axes.items():
        families.setdefault(round(math.degrees(math.atan2(d[1], d[0])) % 180 / 5) * 5 % 180, []).append(tag)
    parts = []
    for tags in families.values():
        ref = axes[tags[0]][1]
        normal = (-ref[1], ref[0])

        def offset(tag: str) -> float:
            (ax, ay), _ = axes[tag]
            return (point[0] - ax) * normal[0] + (point[1] - ay) * normal[1]

        ranked = sorted(tags, key=offset)
        on = [t for t in ranked if abs(offset(t)) < GRID_TOLERANCE]
        parallel = direction is None or abs(abs(direction[0] * ref[0] + direction[1] * ref[1]) - 1) < 0.02
        if on and parallel:
            parts.append(f"sur la file {on[0]}")
            continue
        before = [t for t in ranked if offset(t) < 0]
        after = [t for t in ranked if offset(t) > 0]
        if before and after:
            parts.append(f"entre {after[0]} et {before[-1]}")
        elif before or after:
            parts.append(f"au-delà de la file {before[-1] if before else after[0]}")
    return " ; ".join(parts) or None


def classify(features: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """First category whose clues all hold, by priority; None when no rule recognises the element.

    A clue the element does not have (no sill for a beam, no exterior side for a slab) fails the
    rule that asks for it: no rule guesses.
    """
    ifc_class = features.get("ifc_class") or ""
    type_name = _fold_text(features.get("type_name"))
    for rule in rules:
        match = rule.get("match") or {}
        if "classes" in match and ifc_class not in match["classes"]:
            continue
        if "predefined_types" in match and features.get("predefined_type") not in match["predefined_types"]:
            continue
        if "type_name_patterns" in match and not any(_fold_text(p) in type_name for p in match["type_name_patterns"]):
            continue
        if "exterior" in match and features.get("exterior") is not match["exterior"]:
            continue
        if "orientation" in match and features.get("orientation") != match["orientation"]:
            continue
        bounds_ok = True
        for name in ("sill", "height", "width", "thickness"):
            value = features.get(name)
            low, high = match.get(f"{name}_min"), match.get(f"{name}_max")
            if (low is not None or high is not None) and value is None:
                bounds_ok = False
            elif (low is not None and value < low) or (high is not None and value > high):
                bounds_ok = False
        if bounds_ok:
            return rule
    return None


IDS_ENV = "MVP_MODEL_IDS"  # an agency's own IDS file; otherwise the default one shipped here
DEFAULT_IDS = Path(__file__).with_name("model_requirements") / "default.ids"


def check_requirements(model: Any) -> dict[str, Any] | None:
    """The model checked against the IDS (buildingSMART Information Delivery Specification).

    None when ifctester is not installed or no IDS can be read: the reading never depends on it.
    """
    try:
        from ifctester import ids
    except ImportError:
        return None
    configured = os.environ.get(IDS_ENV, "").strip()
    path = Path(configured) if configured and Path(configured).is_absolute() else DEFAULT_IDS
    try:
        spec = ids.open(str(path))
        spec.validate(model)
    except Exception:  # an unreadable IDS or a validation failure never blocks the reading
        return None
    rows = []
    for item in spec.specifications:
        applicable, failed = len(item.applicable_entities), len(item.failed_entities)
        if applicable:
            rows.append({"exigence": item.name, "applicables": applicable, "en_échec": failed})
    return {"ids": spec.info.get("title") or path.name, "ids_agence": bool(configured),
            "exigences": rows, "respectées": sum(1 for r in rows if not r["en_échec"]), "total": len(rows)}


def load_rules() -> list[dict[str, Any]]:
    """Category rules from the profile; empty (and the reading falls back) when it cannot be read."""
    try:
        from . import apu_vocabulary
        return apu_vocabulary.categories()
    except Exception:  # an unreadable profile never blocks the reading
        return []


def opening_nature(ifc_class: str, *, exterior: bool, sill_m: float | None, height_m: float | None,
                   declared_type: str | None = None, declared_external: bool | None = None,
                   width_m: float | None = None, rules: list[dict[str, Any]] | None = None) -> tuple[str, list[str]]:
    """What an opening is, from geometry first, with the clues used.

    The family a modeller picked is a clue, not a fact: agencies often model
    exterior doors in a window family and openings in load-bearing walls in a
    door family. Exterior or interior comes from the spaces on each side; door
    or window from the sill and the height.
    """
    clues = [f"classe IFC {ifc_class}", "extérieur (géométrie)" if exterior else "intérieur (géométrie)"]
    full_height = sill_m is not None and sill_m <= 0.10 and (height_m or 0) >= 1.9
    if sill_m is not None:
        clues.append(f"allège {sill_m:.2f} m".replace(".", ","))
    rule = classify({"ifc_class": ifc_class, "exterior": exterior, "sill": sill_m, "height": height_m, "width": width_m,
                     "type_name": declared_type}, [r for r in (rules if rules is not None else load_rules())
                                                   if set((r.get("match") or {}).get("classes") or []) & {"IfcWindow", "IfcDoor"}])
    if rule is not None:
        nature = rule["label"]
    elif exterior:  # fallback when the category profile cannot be read
        too_narrow = width_m is not None and width_m < 0.6
        nature = ("fenêtre toute hauteur" if too_narrow else ("porte extérieure" if ifc_class == "IfcDoor" else "porte-fenêtre")) \
            if full_height else "fenêtre"
    else:
        nature = "porte intérieure" if ifc_class == "IfcDoor" or full_height else "châssis intérieur"
    declared = _fold_text(declared_type)
    if declared_type:
        clues.append(f"type déclaré « {declared_type} »")
    if exterior and any(word in declared.split() for word in ("int", "int.", "interieur", "interieure")):
        clues.append("le type déclaré dit intérieur, la géométrie dit extérieur")
    if declared_external is not None and declared_external != exterior:
        clues.append("la propriété IsExternal contredit la géométrie")
    return nature, clues


def _fold_text(text: Any) -> str:
    table = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    return str(text or "").lower().translate(table)


def open_neighbours(geo: list[dict[str, Any]], linked: set[frozenset[str]], *, gap: float = 0.04,
                    min_length: float = 0.5) -> list[dict[str, Any]]:
    """Spaces of one volume: they touch (no wall between) and are not already linked by a wall or a door."""
    pairs = []
    for i, a in enumerate(geo):
        for b in geo[i + 1:]:
            if frozenset((a["id"], b["id"])) in linked or not (a["z"][0] < b["z"][1] - 0.5 and b["z"][0] < a["z"][1] - 0.5):
                continue
            shared = a["poly"].buffer(gap / 2).intersection(b["poly"].buffer(gap / 2))
            if shared.is_empty:
                continue
            # Length of the contact strip: the long side of its smallest enclosing rectangle.
            corners = list(shared.minimum_rotated_rectangle.exterior.coords)
            length = max(math.dist(corners[i], corners[i + 1]) for i in range(len(corners) - 1)) - gap
            if length >= min_length:
                pairs.append({"spaces": sorted((a["id"], b["id"])), "via": "ouvert", "elements": [],
                              "longueur_m": round(length, 1)})
    return pairs


EXPORT_ADVICE = {
    "schema": "Exporter en IFC4 (Reference View) plutôt qu'en IFC2X3.",
    "north": "Régler le nord géographique du projet dans Revit avant l'export.",
    "space_boundaries": "Cocher l'export des limites d'espace (space boundaries, 1er niveau).",
    "phases": "Exporter les jeux de propriétés Revit pour transmettre la phase de création et de démolition.",
    "marks": "Renseigner le paramètre Marque (repère) des portes et fenêtres et l'exporter.",
    "spaces": "Nommer et numéroter tous les locaux avant l'export.",
    "external": "Régler la fonction (intérieur / extérieur) des types de murs ; à défaut, IfcExportAs / Pset_WallCommon.IsExternal.",
    "load_bearing": "Cocher « porteur » (structural) sur les murs porteurs, exporté dans Pset_WallCommon.LoadBearing.",
    "classes": "Utiliser IfcExportAs / IfcExportType dans les familles pour exporter portes et fenêtres dans leur vraie classe.",
    "coordinates": "Exporter en coordonnées partagées (même point de base que la maquette d'architecture, site géoréférencé), "
                   "ou convenir d'une origine commune (par exemple l'intersection de deux files au niveau 0,00), "
                   "pour superposer les maquettes archi et BET.",
}


def discipline(counts: dict[str, int]) -> str:
    """Architecture when spaces or doors and windows are modelled; structure when only load-bearing elements are."""
    if counts.get("spaces") or counts.get("openings"):
        return "architecture"
    if counts.get("structure"):
        return "structure"
    return "autre"


def quality(checks: dict[str, bool | None], model_discipline: str = "architecture") -> dict[str, Any]:
    """Model quality from named checks (True passes, False fails, None unknown), with export advice.

    Checks that do not apply to the model's discipline (spaces, marks, space boundaries for a structural
    model) are set aside rather than failed.
    """
    if model_discipline != "architecture":
        checks = {name: (None if name in {"spaces", "marks", "space_boundaries", "external"} else ok)
                  for name, ok in checks.items()}
    important = ("spaces", "north", "phases", "marks", "space_boundaries", "coordinates")
    failed = [name for name, ok in checks.items() if ok is False]
    blocking = "spaces" in failed
    level = "insuffisante" if blocking else ("à améliorer" if failed else "bonne")
    order = ["spaces", "coordinates", "north", "phases", "marks", "space_boundaries", "schema", "external", "load_bearing", "classes"]
    advice = [EXPORT_ADVICE[name] for name in sorted(failed, key=lambda n: order.index(n) if n in order else len(order))
              if name in EXPORT_ADVICE]
    return {"niveau": level, "discipline": model_discipline, "contrôles": {name: ok for name, ok in checks.items()},
            "réexport_conseillé": blocking or sum(1 for name in failed if name in important) >= 2,
            "conseils_export": advice}


def neighbours(openings: Iterable[dict[str, Any]], walls: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pairs of spaces linked by a door or a free opening, or sharing a wall."""
    pairs: dict[tuple[str, str, str], list[str]] = {}
    for item, how in [(o, "porte" if o["kind"] == "porte" else "baie libre") for o in openings if o["kind"] in {"porte", "baie libre"}] + \
            [(w, "mur") for w in walls]:
        a, b = item.get("sides") or (None, None)
        if a and b and a != b:
            key = (*sorted((a, b)), how)
            pairs.setdefault(key, []).append(item["id"])
    return [{"spaces": [a, b], "via": how, "elements": ids} for (a, b, how), ids in sorted(pairs.items())]


# ---------- extraction from the model ----------

def read(path: Path) -> dict[str, Any]:
    """Read one IFC model; heavy (geometry), so callers use ensure() and its cache."""
    try:
        import ifcopenshell
        import ifcopenshell.geom as ifc_geom
        import ifcopenshell.util.element as util_element
        import ifcopenshell.util.placement as util_placement
        import ifcopenshell.util.unit as util_unit
        import numpy as np
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
    except ImportError as exc:  # pragma: no cover - optional extra
        raise ModelReadingError("model reading needs the ifc extra (ifcopenshell, shapely)") from exc

    model = ifcopenshell.open(str(path))
    scale = util_unit.calculate_unit_scale(model)
    settings = ifc_geom.settings()
    settings.set("use-world-coords", True)

    def mesh(element):
        shape = ifc_geom.create_shape(settings, element)
        return (np.array(shape.geometry.verts).reshape(-1, 3), np.array(shape.geometry.faces).reshape(-1, 3))

    def level(element) -> str | None:
        # Elements are contained in a storey; spaces are usually aggregated under it.
        parent = util_element.get_container(element) or util_element.get_aggregate(element)
        while parent is not None and not parent.is_a("IfcBuildingStorey"):
            parent = util_element.get_aggregate(parent)
        return parent.Name if parent is not None else None

    def frame(element):
        matrix = util_placement.get_local_placement(element.ObjectPlacement)
        x = matrix[:2, 0] / (np.linalg.norm(matrix[:2, 0]) or 1)
        return matrix[:3, 3] * scale, (float(x[0]), float(x[1]))

    north, north_set = 0.0, False
    for context in model.by_type("IfcGeometricRepresentationContext"):
        if not context.is_a("IfcGeometricRepresentationSubContext") and getattr(context, "TrueNorth", None):
            dx, dy = context.TrueNorth.DirectionRatios[:2]
            north = math.degrees(math.atan2(dx, dy)) % 360
            north_set = abs(north) > 1e-6
            break

    levels = [{"name": s.Name, "elevation": round(float(s.Elevation or 0) * scale, 3)}
              for s in sorted(model.by_type("IfcBuildingStorey"), key=lambda s: float(s.Elevation or 0))]
    elevation = {level["name"]: level["elevation"] for level in levels}
    rules = load_rules()
    conventions = load_conventions()
    ignored = tuple(p.lower() for p in conventions.get("ignored_type_prefixes") or [])

    def pset(element, name: str) -> dict[str, Any]:
        return util_element.get_psets(element).get(name) or {}

    size_names = {kind: {_fold_text(n) for n in names} | {_fold_text(n) for n in (conventions.get("size_parameters") or {}).get(kind, [])}
                  for kind, names in SIZE_PARAMETERS.items()}

    def declared_sizes(element) -> dict[str, float]:
        """Sizes the model declares: the IFC attributes, then family parameters by name (system or custom)."""
        found: dict[str, float] = {}
        for attribute, kind in (("OverallWidth", "width"), ("OverallHeight", "height")):
            value = getattr(element, attribute, None)
            if isinstance(value, (int, float)) and value > 0:
                found[f"{kind} ({attribute})"] = round(float(value) * scale, 3)
        for set_name, properties in util_element.get_psets(element).items():
            for key, value in properties.items():
                folded = _fold_text(key)
                for kind, names in size_names.items():
                    if folded in names and isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
                        metres = float(value) * scale if float(value) > 20 else float(value)  # millimetres or metres
                        found.setdefault(f"{kind} ({key})", round(metres, 3))
        return found

    def sill(element_level: str | None, bottom: float, sides: list[str | None]) -> float | None:
        """Height of the bottom of an opening above the floor of the space beside it (or of its storey)."""
        floors = [s["z"][0] for s in geo if s["id"] in sides]
        reference = min(floors) if floors else elevation.get(element_level)
        if reference is None:
            return None
        value = bottom - reference
        return round(value, 2) if -0.5 < value < 5 else None  # storeys in absolute altitude, geometry relative

    spaces, geo = [], []
    for space in model.by_type("IfcSpace"):
        try:
            verts, faces = mesh(space)
        except Exception:
            continue
        poly = unary_union([p for f in faces if (p := Polygon(verts[f][:, :2])).is_valid and p.area > 1e-6]).buffer(0)
        name = space.LongName or space.Name or space.GlobalId
        spaces.append({"id": space.GlobalId, "name": name, "number": space.Name if space.LongName else None,
                       "level": level(space), "area_m2": round(poly.area, 2)})
        geo.append({"id": space.GlobalId, "poly": poly, "z": (float(verts[:, 2].min()), float(verts[:, 2].max()))})

    from shapely.strtree import STRtree

    tree = STRtree([s["poly"] for s in geo]) if geo else None
    # Minimal geometry kept with the reading, so models can be overlaid without reading the IFC again.
    geometry: dict[str, Any] = {"walls": {}, "points": {}, "spaces": {}, "floors": {}}
    for space_item, shape_item in zip(spaces, geo):
        outline = shape_item["poly"].simplify(0.05)
        rings = list(getattr(outline, "geoms", [outline]))
        if rings and hasattr(rings[0], "exterior"):
            geometry["spaces"][space_item["id"]] = [[round(x, 2), round(y, 2)] for x, y in rings[0].exterior.coords]
        if space_item["level"]:
            floor = round(shape_item["z"][0], 3)
            geometry["floors"][space_item["level"]] = min(geometry["floors"].get(space_item["level"], floor), floor)

    def space_at(x: float, y: float, z: float) -> str | None:
        from shapely.geometry import Point
        point = Point(x, y)
        candidates = [geo[i] for i in tree.query(point)] if tree is not None else []
        return next((s["id"] for s in candidates if s["z"][0] - 0.3 <= z <= s["z"][1] + 0.3 and s["poly"].contains(point)), None)

    axes: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {}
    for grid in model.by_type("IfcGrid"):
        matrix = util_placement.get_local_placement(grid.ObjectPlacement)
        # Revit may export one direction of grid lines in WAxes, the third axis list: read all three.
        for axis in list(grid.UAxes or []) + list(grid.VAxes or []) + list(getattr(grid, "WAxes", None) or []):
            points = [np.array([*p.Coordinates[:2], 0, 1], dtype=float) for p in axis.AxisCurve.Points]
            a, b = (matrix @ points[0])[:2] * scale, (matrix @ points[-1])[:2] * scale
            length = float(np.linalg.norm(b - a))
            if axis.AxisTag and length > 0 and axis.AxisTag not in axes:
                axes[axis.AxisTag] = ((float(a[0]), float(a[1])), (float((b - a)[0] / length), float((b - a)[1] / length)))

    def type_name(element) -> str | None:
        element_type = util_element.get_type(element)
        if element_type is not None and element_type.Name:
            return element_type.Name
        psets = util_element.get_psets(element)
        return (psets.get("Pset_WindowCommon") or psets.get("Pset_DoorCommon") or psets.get("Pset_WallCommon") or {}).get("Reference")

    from shapely.geometry import Point as _Point

    footprints: dict[tuple[float, float], Any] = {}

    def footprint(z: float):
        """Envelope of the spaces whose height range holds z."""
        group = [s for s in geo if s["z"][0] - 0.3 <= z <= s["z"][1] + 0.3]
        key = (min((s["z"][0] for s in group), default=0.0), max((s["z"][1] for s in group), default=0.0))
        if key not in footprints:
            footprints[key] = envelope([s["poly"] for s in group]) if group else None
        return footprints[key]

    def located(item: dict[str, Any], center, axis_dir, z) -> None:
        normal = (-axis_dir[1], axis_dir[0])
        a, b = side_spaces((float(center[0]), float(center[1])), normal, z, geo, tree)
        item["sides"] = [a, b]
        if bool(a) != bool(b):
            sign = -1 if a else 1  # outward = towards the side without a space
            probe = _Point(float(center[0]) + sign * 0.6 * normal[0], float(center[1]) + sign * 0.6 * normal[1])
            outline = footprint(z)
            if outline is not None and outline.contains(probe):
                item["exterior"] = False  # inside the building: a stair or circulation without a space
                item["unmodelled_side"] = True
            else:
                item["exterior"] = True
                item["facade"] = facade(sign * normal[0], sign * normal[1], north)
        else:
            item["exterior"] = False
        item["grid"] = grid_position((float(center[0]), float(center[1])), axes, axis_dir)

    openings, ignored_count = [], 0
    for cls, kind in (("IfcWindow", "fenêtre"), ("IfcDoor", "porte")):
        common = "Pset_WindowCommon" if cls == "IfcWindow" else "Pset_DoorCommon"
        for element in model.by_type(cls):
            declared_type = type_name(element)
            if ignored and str(declared_type or "").lower().startswith(ignored):
                ignored_count += 1
                continue
            try:
                verts, _ = mesh(element)
            except Exception:
                continue
            host = next((void.RelatingBuildingElement for rel in element.FillsVoids or []
                         for void in rel.RelatingOpeningElement.VoidsElements or []), None)
            _, axis_dir = frame(host or element)
            center = (verts.min(axis=0) + verts.max(axis=0)) / 2
            # Measured, not declared: families often carry their real sizes in custom parameters.
            along = np.dot(verts[:, :2], np.array(axis_dir))
            measured_width = round(float(along.max() - along.min()), 3)
            measured_height = round(float(verts[:, 2].max() - verts[:, 2].min()), 3)
            declared = declared_sizes(element)
            item = {"id": element.GlobalId, "kind": kind, "type": declared_type, "level": level(element),
                    "width_m": measured_width or None, "height_m": measured_height or None,
                    "wall": host.GlobalId if host is not None else None}
            if declared:
                item["declared_sizes"] = declared
            located(item, center, axis_dir, float(verts[:, 2].min()) + 1.0)
            item["grid"] = grid_position((float(center[0]), float(center[1])), axes)
            properties = pset(element, common)
            item["sill_m"] = sill(item["level"], float(verts[:, 2].min()), item["sides"])
            item["nature"], item["clues"] = opening_nature(
                cls, exterior=item["exterior"], sill_m=item["sill_m"], height_m=item["height_m"],
                declared_type=declared_type, declared_external=properties.get("IsExternal"), width_m=item["width_m"],
                rules=rules)
            for key, field in (("ThermalTransmittance", "uw_declared"), ("FireRating", "fire_rating")):
                if properties.get(key) not in (None, ""):
                    item[field] = properties[key]
            for label, value in declared.items():
                measured = measured_width if label.startswith("width") else measured_height
                if measured and abs(value - measured) > SIZE_TOLERANCE:
                    item["clues"].append(f"dimension déclarée {label} = {value:.2f} m, mesurée {measured:.2f} m".replace(".", ","))
            openings.append(item)

    # Openings without a door or window in a wall between two spaces: free openings (passages, bays).
    for void in model.by_type("IfcOpeningElement"):
        if void.HasFillings or not void.VoidsElements:
            continue
        host = void.VoidsElements[0].RelatingBuildingElement
        if not host.is_a("IfcWall"):
            continue
        try:
            verts, _ = mesh(void)
        except Exception:
            continue
        _, axis_dir = frame(host)
        along = abs(np.dot(verts[:, :2] - verts[0, :2], np.array(axis_dir)))
        width, height = float(along.max() - along.min()), float(verts[:, 2].max() - verts[:, 2].min())
        if width < 0.5 or height < 1.8:
            continue  # ducts, reservations, small cuts
        center = (verts.min(axis=0) + verts.max(axis=0)) / 2
        item = {"id": void.GlobalId, "kind": "baie libre", "nature": "baie libre", "level": level(host),
                "width_m": round(width, 2), "height_m": round(height, 2), "wall": host.GlobalId,
                "clues": ["percement sans menuiserie dans un mur"]}
        located(item, center, axis_dir, float(verts[:, 2].min()) + 1.0)
        if not all(item["sides"]):
            continue  # a free opening counts between two spaces
        item["grid"] = grid_position((float(center[0]), float(center[1])), axes)
        openings.append(item)

    junctions: dict[str, list[dict[str, str]]] = {}
    for rel in model.by_type("IfcRelConnectsPathElements"):
        a, b = rel.RelatingElement.GlobalId, rel.RelatedElement.GlobalId
        how = f"{rel.RelatingConnectionType}-{rel.RelatedConnectionType}".lower()
        junctions.setdefault(a, []).append({"with": b, "how": how})
        junctions.setdefault(b, []).append({"with": a, "how": how})

    walls = []
    for wall in model.by_type("IfcWall"):
        origin, axis_dir = frame(wall)
        length = None
        for rep in (wall.Representation.Representations if wall.Representation else []):
            if rep.RepresentationIdentifier == "Axis" and rep.Items and rep.Items[0].is_a("IfcPolyline"):
                pts = rep.Items[0].Points
                length = abs(float(pts[-1].Coordinates[0]) - float(pts[0].Coordinates[0])) * scale
        material = util_element.get_material(wall)
        layers, thickness = None, None
        if material is not None and material.is_a("IfcMaterialLayerSetUsage"):
            items = material.ForLayerSet.MaterialLayers
            thickness = round(sum(float(l.LayerThickness) for l in items) * scale, 3)
            layers = " + ".join(f"{l.Material.Name if l.Material else '?'} {float(l.LayerThickness) * scale * 100:.0f} cm" for l in items)
        if not length:  # no exported axis: take the long side of the wall's footprint
            try:
                wall_verts, _ = mesh(wall)
                along = np.dot(wall_verts[:, :2] - origin[:2], np.array(axis_dir))
                origin = np.array([*(origin[:2] + np.array(axis_dir) * float(along.min())), float(wall_verts[:, 2].min())])
                length = float(along.max() - along.min()) or None
            except Exception:
                pass
        mid = origin[:2] + np.array(axis_dir) * (length or 0) / 2
        if length:
            end = origin[:2] + np.array(axis_dir) * length
            geometry["walls"][wall.GlobalId] = [round(float(v), 3) for v in (*origin[:2], *end, origin[2])]
        item = {"id": wall.GlobalId, "type": type_name(wall), "level": level(wall),
                "length_m": round(length, 2) if length else None, "thickness_m": thickness, "composition": layers,
                "junctions": junctions.get(wall.GlobalId, [])}
        located(item, mid, axis_dir, float(origin[2]) + 1.0)
        properties = pset(wall, "Pset_WallCommon")
        item["declared"] = {key: properties[key] for key in ("IsExternal", "LoadBearing") if key in properties}
        rule = classify({"ifc_class": wall.is_a(), "exterior": item["exterior"], "thickness": thickness,
                         "type_name": item["type"]}, rules)
        if rule is not None:
            item["category"], item["label"] = rule["id"], rule["label"]
        for key, field in (("ThermalTransmittance", "u_declared"), ("FireRating", "fire_rating"),
                           ("AcousticRating", "acoustic_rating")):
            if properties.get(key) not in (None, ""):
                item[field] = properties[key]
        walls.append(item)

    # Every other building element, described the same way; the category profile names it.
    from shapely.geometry import MultiPoint

    elements, ignored_by_category = [], {}
    generic = [e for cls in GENERIC_CLASSES for e in model.by_type(cls, include_subtypes=False)]
    if model.schema.upper().startswith("IFC4"):
        generic += model.by_type("IfcGeographicElement")
    for element in generic:
        declared_type = type_name(element)
        features = {"ifc_class": element.is_a(), "predefined_type": str(getattr(element, "PredefinedType", "") or "") or None,
                    "type_name": declared_type}
        rule = classify(features, rules)
        if rule is not None and rule.get("ignore") or (ignored and str(declared_type or "").lower().startswith(ignored)):
            key = rule["label"] if rule is not None else "ignoré par convention"
            ignored_by_category[key] = ignored_by_category.get(key, 0) + 1
            continue
        try:
            verts, _ = mesh(element)
        except Exception:
            continue  # aggregates without own geometry (a roof made of slabs)
        rectangle = MultiPoint([tuple(v) for v in verts[:, :2]]).minimum_rotated_rectangle
        corners = list(getattr(rectangle, "exterior", rectangle).coords) if hasattr(rectangle, "exterior") else []
        sides = sorted(math.dist(corners[i], corners[i + 1]) for i in range(min(2, len(corners) - 1))) if len(corners) > 2 else [0.0, 0.0]
        width, length = (sides + [0.0, 0.0])[:2]
        height = float(verts[:, 2].max() - verts[:, 2].min())
        features.update(orientation="vertical" if height > 2 * max(length, 0.01) else "horizontal",
                        width=round(width, 3), height=round(height, 3), thickness=round(min(width, height), 3))
        rule = classify(features, rules)
        center = (verts.min(axis=0) + verts.max(axis=0)) / 2
        geometry["points"][element.GlobalId] = [round(float(v), 3) for v in (center[0], center[1], verts[:, 2].min(), verts[:, 2].max())]
        item = {"id": element.GlobalId, "ifc_class": element.is_a(), "type": declared_type, "level": level(element),
                "category": rule["id"] if rule else None, "label": rule["label"] if rule else f"élément ({element.is_a()})",
                "length_m": round(length, 2), "width_m": round(width, 2), "height_m": round(height, 2),
                "orientation": features["orientation"],
                "space": space_at(float(center[0]), float(center[1]), float(center[2])),
                "grid": grid_position((float(center[0]), float(center[1])), axes)}
        elements.append(item)

    for item in walls + elements:  # levels without spaces (structural models): the lowest element bottom
        if item.get("level") and item["level"] not in {s["level"] for s in spaces}:
            bottom = (geometry["walls"].get(item["id"]) or [None] * 5)[4] if item in walls else (geometry["points"].get(item["id"]) or [None] * 3)[2]
            if bottom is not None:
                geometry["floors"][item["level"]] = min(geometry["floors"].get(item["level"], bottom), bottom)
    geometry["axes"] = {tag: [round(a[0], 3), round(a[1], 3), round(d[0], 5), round(d[1], 5)] for tag, (a, d) in axes.items()}

    linked = {frozenset(pair["spaces"]) for pair in neighbours(openings, walls)}
    pairs = neighbours(openings, walls) + open_neighbours(geo, linked)

    # Declared against observed: the model's own properties, kept only where the geometry agrees.
    declared_external = [w for w in walls if isinstance(w["declared"].get("IsExternal"), bool)]
    agree = sum(1 for w in declared_external if w["declared"]["IsExternal"] == w["exterior"])
    load_bearing = [w["declared"].get("LoadBearing") for w in walls if "LoadBearing" in w["declared"]]
    notes = []
    if declared_external and agree < len(declared_external):
        notes.append(f"{sum(1 for w in declared_external if w['declared']['IsExternal'])} murs déclarés extérieurs, "
                     f"{sum(1 for w in walls if w['exterior'])} le sont par la géométrie : la géométrie fait foi.")
    if load_bearing and not any(load_bearing):
        notes.append("Fonction porteur jamais renseignée (tous les murs à « non ») : traitée comme non renseignée.")
        for wall_item in walls:
            wall_item["declared"].pop("LoadBearing", None)
    contradicted = sum(1 for o in openings if any("contredit" in c or "dit intérieur" in c for c in o.get("clues", [])))
    if contradicted:
        notes.append(f"{contradicted} ouvertures dont la famille ou les propriétés contredisent la géométrie : nature déduite de la géométrie.")
    if ignored_count:
        notes.append(f"{ignored_count} éléments ignorés selon les conventions de l'agence.")

    def has_property(elements, words: tuple[str, ...]) -> bool:
        for element in elements:
            for properties in util_element.get_psets(element).values():
                if any(any(w in str(k).lower() for w in words) and v not in (None, "") for k, v in properties.items()):
                    return True
        return False

    sample_walls = model.by_type("IfcWall")[:20]
    checks = {
        "spaces": bool(spaces) and all(s["name"] and s["name"] != s["id"] for s in spaces),
        "schema": model.schema.upper().startswith("IFC4"),
        "north": north_set,
        "space_boundaries": bool(model.by_type("IfcRelSpaceBoundary")),
        "phases": has_property(sample_walls, ("phase",)),
        "marks": has_property(model.by_type("IfcWindow") + model.by_type("IfcDoor"), ("mark", "marque")),
        "external": (agree >= 0.8 * len(declared_external)) if declared_external else None,
        "load_bearing": any(load_bearing) if load_bearing else None,
        # Shared coordinates: a georeferenced site or a map conversion lets models of several authors overlay.
        "coordinates": any(site.RefLatitude for site in model.by_type("IfcSite"))
                       or bool(model.schema.upper().startswith("IFC4") and model.by_type("IfcMapConversion")),
    }
    model_discipline = discipline({
        "spaces": len(spaces),
        "openings": len(model.by_type("IfcWindow")) + len(model.by_type("IfcDoor")),
        "structure": sum(len(model.by_type(c)) for c in ("IfcColumn", "IfcBeam", "IfcFooting", "IfcMember")),
    })

    return {
        "north": {"angle_deg": round(north, 1), "set_in_model": north_set},
        "levels": levels,
        "spaces": spaces,
        "grid_lines": sorted(axes),
        "openings": openings,
        "walls": walls,
        "neighbours": pairs,
        "elements": elements,
        "ignored": ignored_by_category,
        "categories": category_words(rules, {o.get("nature") for o in openings} | {w.get("label") for w in walls}
                                     | {e.get("label") for e in elements} | {"baie libre"}),
        "ifc_schema": model.schema,
        "declared_vs_observed": notes,
        "discipline": model_discipline,
        "quality": {**quality(checks, model_discipline),
                    **({"exigences": requirements} if (requirements := check_requirements(model)) else {})},
        "geometry": geometry,
        "limits": [
            "Côtés, façades et voisinages calculés par la géométrie : déductions, à confirmer.",
            "Façades nommées d'après le nord de la maquette"
            + ("" if north_set else ", laissé par défaut : orientation à confirmer avant toute comparaison avec des élévations."),
        ],
    }


def category_words(rules: list[dict[str, Any]], labels: set[Any]) -> dict[str, list[str]]:
    """The words people use for each category label present in this reading (for designations)."""
    words: dict[str, list[str]] = {}
    for rule in rules:
        if rule["label"] in labels and not rule.get("ignore"):
            words.setdefault(rule["label"], [])
            words[rule["label"]] = sorted(set(words[rule["label"]]) | {_fold_text(s) for s in rule.get("synonyms") or []})
    return words


def load_conventions() -> dict[str, Any]:
    """The agency's modelling habits, from a local file kept outside the repository; empty when absent."""
    configured = os.environ.get(CONVENTIONS_ENV, "").strip()
    if not configured:
        return {}
    try:
        data = json.loads(Path(configured).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


# ---------- cache and publication ----------

def fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"size:{stat.st_size}:mtime:{int(stat.st_mtime)}"


def ensure(path: Path, out_file: Path, *, piece: str, index: str | None = None) -> dict[str, Any]:
    """Read the model into out_file unless it already holds this exact file; never raises on a bad model."""
    try:
        stamp = fingerprint(path)
    except OSError:
        return {"piece": piece, "status": "absent"}
    status = {"piece": piece, "index": index, "file": out_file.name}
    try:
        current = json.loads(out_file.read_text(encoding="utf-8"))
        if current.get("source", {}).get("fingerprint") == stamp:
            return {**status, "status": "cached"}
    except (OSError, ValueError):
        pass
    try:
        reading = read(path)
    except Exception as exc:  # a damaged or unsupported model must not block the Anatomy
        return {**status, "status": "unreadable", "error": type(exc).__name__}
    document = {"schema": SCHEMA, "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": {"piece": piece, "index": index, "file": path.name, "fingerprint": stamp}, **reading}
    out_file.parent.mkdir(parents=True, exist_ok=True)
    partial = out_file.with_name(f".{out_file.name}.partial")
    partial.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    partial.replace(out_file)
    return {**status, "status": "read"}
