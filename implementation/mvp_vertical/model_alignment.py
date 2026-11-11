"""Overlay an engineer's model on the architect's when they share no coordinates.

Engineers often export from their own origin: no georeferenced site, another
origin, sometimes another rotation. Their columns and beams then cannot inherit
the architect's rooms and grid lines. This module estimates the transformation
from the minimal geometry each model reading keeps, during the preparation of a
new model index:

- height: the engineer's ground floor (the lowest level that is not a
  foundation level) is laid on the architect's lowest floor;
- rotation: the dominant wall directions of both models, tried at the four
  quarter turns (a house is often nearly symmetric);
- position: bounding boxes first, then refined so the engineer's points fall on
  the architect's walls;
- score: the share of the engineer's columns, footings and wall ends lying on
  an architect wall, with the margin over the next best candidate.

The result is an estimate, never a fact: it says how good it is, is applied only
when it is probable, and waits for a human confirmation. Shared coordinates or an
agreed common origin at export remain the reliable way.
"""

from __future__ import annotations

import math
from typing import Any

TOLERANCE = 0.20       # metres: a point this close to an architect wall is on it
PROBABLE_SCORE = 0.60  # share of points on walls for a probable overlay
PROBABLE_MARGIN = 0.15
FOUNDATION_WORDS = ("fond", "found", "semelle", "radier")
NEAR_ROOM = 0.35  # metres: an element inside a wall belongs to the rooms this close


def dominant_angle(segments: list[list[float]]) -> float | None:
    """Main wall direction in [0, 90) degrees, weighted by length."""
    weights: dict[int, float] = {}
    for x1, y1, x2, y2, *_ in segments:
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 0.5:
            continue
        bucket = int(round(math.degrees(math.atan2(y2 - y1, x2 - x1)) % 90)) % 90
        weights[bucket] = weights.get(bucket, 0.0) + length
    if not weights:
        return None
    best = max(weights, key=weights.get)
    # refine on the neighbouring buckets
    total = sum(weights.get((best + d) % 90, 0.0) for d in (-1, 0, 1))
    return (sum(((best + d) % 90) * weights.get((best + d) % 90, 0.0) for d in (-1, 0, 1)) / total) if total else float(best)


def rotate(points: list[tuple[float, float]], degrees: float) -> list[tuple[float, float]]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in points]


GROUND_WORDS = ("rdc", "r00", "r0 ", "rez", "ground", "niveau 0", "n0")


def ground_floor(floors: dict[str, float]) -> float | None:
    """The ground floor: a level named so (RDC, R00, rez-de-chaussée), else the lowest non-foundation one."""
    named = [z for name, z in floors.items() if any(w in f"{name.lower()} " for w in GROUND_WORDS)]
    if named:
        return min(named)
    kept = [z for name, z in floors.items() if not any(w in name.lower() for w in FOUNDATION_WORDS)]
    return min(kept) if kept else (min(floors.values()) if floors else None)


def _core_box(points: list[tuple[float, float]], share: float = 0.05) -> tuple[tuple[float, float], tuple[float, float]]:
    """Bounding box of the points without the outer 5 % on each side (isolated elements far away)."""
    xs, ys = sorted(p[0] for p in points), sorted(p[1] for p in points)
    cut = int(len(points) * share)
    return (xs[cut], ys[cut]), (xs[-1 - cut], ys[-1 - cut])


def _segments_index(segments: list[list[float]]):
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    lines = [LineString([(s[0], s[1]), (s[2], s[3])]) for s in segments]
    return lines, STRtree(lines)


def _nearest_offsets(points, lines, tree, reach: float):
    """For each point near an architect wall, the vector to the nearest point of that wall."""
    from shapely.geometry import Point
    from shapely.ops import nearest_points

    offsets = []
    for x, y in points:
        p = Point(x, y)
        candidates = [lines[i] for i in tree.query(p.buffer(reach))]
        if not candidates:
            continue
        line = min(candidates, key=p.distance)
        if p.distance(line) <= reach:
            q = nearest_points(line, p)[0]
            offsets.append((q.x - x, q.y - y))
    return offsets


def _score(points, lines, tree) -> float:
    from shapely.geometry import Point

    hits = 0
    for x, y in points:
        p = Point(x, y)
        if any(p.distance(lines[i]) <= TOLERANCE for i in tree.query(p.buffer(TOLERANCE))):
            hits += 1
    return hits / len(points) if points else 0.0


def align(architect: dict[str, Any], engineer: dict[str, Any]) -> dict[str, Any]:
    """Transformation laying the engineer's geometry on the architect's, with its quality.

    Both arguments are the ``geometry`` sections of two model readings.
    """
    walls = list((architect.get("walls") or {}).values())
    if len(walls) < 4:
        return {"verdict": "impossible", "reason": "la maquette d'architecture n'a pas assez de murs lus"}
    eng_walls = list((engineer.get("walls") or {}).values())
    eng_points = [(p[0], p[1]) for p in (engineer.get("points") or {}).values()] + \
                 [(w[0], w[1]) for w in eng_walls] + [(w[2], w[3]) for w in eng_walls]
    if len(eng_points) < 6:
        return {"verdict": "impossible", "reason": "la maquette du BET n'a pas assez d'éléments lus"}

    arch_floor, eng_floor = ground_floor(architect.get("floors") or {}), ground_floor(engineer.get("floors") or {})
    dz = round(arch_floor - eng_floor, 3) if arch_floor is not None and eng_floor is not None else None

    lines, tree = _segments_index(walls)
    a_arch = dominant_angle(walls)
    a_eng = dominant_angle(eng_walls)
    base = (a_arch - a_eng) if a_arch is not None and a_eng is not None else 0.0
    # Start from the building, not the site: the architect's rooms when there are some (site walls,
    # hedges and fences widen the walls' extent), the core of the engineer's points (a gate far away).
    room_points = [tuple(c) for coords in (architect.get("spaces") or {}).values() for c in coords]
    if room_points:
        arch_xs, arch_ys = [p[0] for p in room_points], [p[1] for p in room_points]
    else:
        arch_xs = [v for w in walls for v in (w[0], w[2])]
        arch_ys = [v for w in walls for v in (w[1], w[3])]
    arch_center = ((min(arch_xs) + max(arch_xs)) / 2, (min(arch_ys) + max(arch_ys)) / 2)

    candidates = []
    for quarter in range(4):
        rotation = (base + 90 * quarter) % 360
        turned = rotate(eng_points, rotation)
        lo, hi = _core_box(turned)
        dx, dy = arch_center[0] - (lo[0] + hi[0]) / 2, arch_center[1] - (lo[1] + hi[1]) / 2
        for reach in (2.0, 1.0, 0.5, 0.3, 0.3):  # refine: move by the median offset to the nearest walls
            moved = [(x + dx, y + dy) for x, y in turned]
            offsets = _nearest_offsets(moved, lines, tree, reach)
            if len(offsets) < 3:
                break
            ox = sorted(o[0] for o in offsets)[len(offsets) // 2]
            oy = sorted(o[1] for o in offsets)[len(offsets) // 2]
            dx, dy = dx + ox, dy + oy
        score = _score([(x + dx, y + dy) for x, y in turned], lines, tree)
        candidates.append({"rotation_deg": round(rotation, 2), "dx": round(dx, 3), "dy": round(dy, 3), "score": round(score, 3)})

    candidates.sort(key=lambda c: -c["score"])
    best, second = candidates[0], candidates[1]
    margin = round(best["score"] - second["score"], 3)
    probable = best["score"] >= PROBABLE_SCORE and margin >= PROBABLE_MARGIN and dz is not None
    return {
        **best, "dz": dz, "second_score": second["score"], "margin": margin,
        "points": len(eng_points), "verdict": "probable" if probable else "incertain",
        "method": "sols, directions de murs (quatre quarts de tour), emprises puis ajustement sur les murs",
        "status": "à confirmer",
    }


def transform(point: tuple[float, float, float], alignment: dict[str, Any]) -> tuple[float, float, float]:
    x, y = rotate([(point[0], point[1])], alignment["rotation_deg"])[0]
    return x + alignment["dx"], y + alignment["dy"], point[2] + (alignment.get("dz") or 0.0)


def place(engineer_reading: dict[str, Any], architect_reading: dict[str, Any], alignment: dict[str, Any]) -> int:
    """Give the engineer's elements the architect's room and grid position; returns how many found a room."""
    from shapely.geometry import Point, Polygon

    from .model_reading import grid_position

    arch = architect_reading.get("geometry") or {}
    names = {s["id"]: (s["name"], s.get("level")) for s in architect_reading.get("spaces") or []}
    floors = sorted((z, level) for level, z in (arch.get("floors") or {}).items())
    outlines = {sid: Polygon(coords) for sid, coords in (arch.get("spaces") or {}).items() if len(coords) >= 4}
    axes = {tag: ((a[0], a[1]), (a[2], a[3])) for tag, a in (arch.get("axes") or {}).items()}
    points = (engineer_reading.get("geometry") or {}).get("points") or {}
    found = 0
    for element in engineer_reading.get("elements") or []:
        raw = points.get(element["id"])
        if not raw:
            continue
        x, y, z = transform((raw[0], raw[1], raw[2]), alignment)
        level = next((lvl for floor, lvl in reversed(floors) if z >= floor - 0.3), floors[0][1] if floors else None)
        space = next((sid for sid, poly in outlines.items() if names.get(sid, (None, None))[1] == level and poly.contains(Point(x, y))), None)
        element["via_recalage"] = {"niveau_archi": level, "files": grid_position((x, y), axes)}
        if space:
            element["via_recalage"]["local"] = names[space][0]
            found += 1
        else:  # a post inside a wall: the rooms on either side
            near = sorted({names[sid][0] for sid, poly in outlines.items()
                           if names.get(sid, (None, None))[1] == level and poly.distance(Point(x, y)) <= NEAR_ROOM})
            if near:
                element["via_recalage"]["locaux_voisins"] = near
                found += 1
    return found
