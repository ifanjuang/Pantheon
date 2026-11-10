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
from typing import Any, Iterable

SCHEMA = "pantheon.model_reading.v1"
FACADES = ("nord", "est", "sud", "ouest")
PROBES = (0.35, 0.6, 0.9)  # metres from a wall or opening axis, tried in order on each side
GRID_TOLERANCE = 0.15      # metres: an element closer than this to a grid line is on it


class ModelReadingError(ValueError):
    pass


# ---------- pure geometry, testable without a model ----------

def facade(vx: float, vy: float, north_deg: float = 0.0) -> str:
    """Façade an outward direction faces, the model's north being north_deg clockwise from +Y."""
    angle = (math.degrees(math.atan2(vx, vy)) - north_deg) % 360
    return FACADES[int((angle + 45) // 90) % 4]


def side_spaces(center: tuple[float, float], normal: tuple[float, float], z: float,
                spaces: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    """Id of the space on each side of an axis (normal side first), probing outward."""
    from shapely.geometry import Point

    found = []
    for sign in (1, -1):
        hit = None
        for distance in PROBES:
            point = Point(center[0] + sign * distance * normal[0], center[1] + sign * distance * normal[1])
            hit = next((s["id"] for s in spaces if s["z"][0] - 0.3 <= z <= s["z"][1] + 0.3 and s["poly"].contains(point)), None)
            if hit:
                break
        found.append(hit)
    return found[0], found[1]


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


def neighbours(openings: Iterable[dict[str, Any]], walls: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pairs of spaces linked by a door, or sharing a wall."""
    pairs: dict[tuple[str, str, str], list[str]] = {}
    for item, how in [(o, "porte") for o in openings if o["kind"] == "porte"] + [(w, "mur") for w in walls]:
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

    axes: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {}
    for grid in model.by_type("IfcGrid"):
        matrix = util_placement.get_local_placement(grid.ObjectPlacement)
        for axis in list(grid.UAxes or []) + list(grid.VAxes or []):
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

    def located(item: dict[str, Any], center, axis_dir, z) -> None:
        normal = (-axis_dir[1], axis_dir[0])
        a, b = side_spaces((float(center[0]), float(center[1])), normal, z, geo)
        item["sides"] = [a, b]
        if bool(a) != bool(b):
            sign = -1 if a else 1  # outward = towards the side without a space
            item["exterior"] = True
            item["facade"] = facade(sign * normal[0], sign * normal[1], north)
        else:
            item["exterior"] = False
        item["grid"] = grid_position((float(center[0]), float(center[1])), axes, axis_dir)

    openings = []
    for cls, kind in (("IfcWindow", "fenêtre"), ("IfcDoor", "porte")):
        for element in model.by_type(cls):
            try:
                verts, _ = mesh(element)
            except Exception:
                continue
            host = next((void.RelatingBuildingElement for rel in element.FillsVoids or []
                         for void in rel.RelatingOpeningElement.VoidsElements or []), None)
            _, axis_dir = frame(host or element)
            center = (verts.min(axis=0) + verts.max(axis=0)) / 2
            item = {"id": element.GlobalId, "kind": kind, "type": type_name(element), "level": level(element),
                    "width_m": round(float(element.OverallWidth or 0) * scale, 3) or None,
                    "height_m": round(float(element.OverallHeight or 0) * scale, 3) or None,
                    "wall": host.GlobalId if host is not None else None}
            located(item, center, axis_dir, float(verts[:, 2].min()) + 1.0)
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
        mid = origin[:2] + np.array(axis_dir) * (length or 0) / 2
        item = {"id": wall.GlobalId, "type": type_name(wall), "level": level(wall),
                "length_m": round(length, 2) if length else None, "thickness_m": thickness, "composition": layers,
                "junctions": junctions.get(wall.GlobalId, [])}
        located(item, mid, axis_dir, float(origin[2]) + 1.0)
        walls.append(item)

    return {
        "north": {"angle_deg": round(north, 1), "set_in_model": north_set},
        "levels": levels,
        "spaces": spaces,
        "grid_lines": sorted(axes),
        "openings": openings,
        "walls": walls,
        "neighbours": neighbours(openings, walls),
        "limits": [
            "Côtés, façades et voisinages calculés par la géométrie : déductions, à confirmer.",
            "Façades nommées d'après le nord de la maquette"
            + ("" if north_set else ", laissé par défaut : orientation à confirmer avant toute comparaison avec des élévations."),
        ],
    }


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
