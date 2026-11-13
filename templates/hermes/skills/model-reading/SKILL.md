---
name: model-reading
description: "Use for questions about a building as modelled (IFC from Revit or another tool): rooms, walls, openings, columns and any element, their level, room, façade, grid line and size, what changed since the previous index, the engineers' models overlaid on the architect's, model quality and re-export advice. Answer from the published model readings through get_project focuses, never from the raw IFC; quote values with their confidence."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: templates/hermes/SKILLS.md
  related_skills: [project-context, drawing-reading]
---

# Reading a model

The agency reads each current model index once and publishes what it found
(rooms, openings, walls, every element, grid lines, quality, overlay, changes).
Hermes asks that reading; it does not open the IFC file. Values come from the
tool and are quoted, not recomputed.

## 1. Ask the right focus

`get_project(code)` gives the summary (models, quality, changes, questions).
Then one focus per question:

| Question | Focus |
|---|---|
| A room: what it contains, its walls, doors, windows, neighbours | room name (« cuisine », « chambre 1 R01 ») |
| Elements of a kind in a place | category + place: « poteaux du BET séjour », « cloisons R01 », « fenêtres façade sud » |
| One element | category + grid lines / façade / room: « cloison file 5 », « porte-fenêtre séjour » |
| Everything on a grid line, a façade, a level | « file C », « façade sud », « R00 » |
| What changed since the previous index | « changements <maquette> » |
| Model quality and export advice | « qualité » |
| Which files the readings rest on | « sources », « fichier <nom> » |

Words people use work (« salon » finds the Séjour). « du BET » / « archi » keeps
one discipline's models. When the tool answers « not found », retry **once**
with a name from the list it returns, before any other source.

## 2. Say how sure each value is

Every answer carries a confidence: **validé** (confirmed by a human), **lu**
(declared in the model), **déduit** (computed from geometry: nature of an
opening, sides, façades, sizes, rooms), **estimé** (engineer elements placed
through the overlay on the architect's model, before confirmation). Qualify the
answer by its weakest value; never present déduit or estimé as lu.

## 3. Positions

- Grid lines: « sur la file C », « entre 3 et 4 », as the tool gives them.
- Façades are named from the model's north; when the model's north was left
  at its default, say façades are to be confirmed before comparing with
  elevations named by orientation.
- Left / right / behind are deductions: give the clue (façade, grid lines) and
  the assumption (north up on the plan).

## 4. Engineers' models

Engineers often export without shared coordinates. The agency overlays their
model on the architect's (rotation, offsets, score, margin); elements placed so
are **estimé** until a human confirms the overlay. Quote the score; ask for
confirmation when the answer depends on it. Two current models sharing most
identifiers are one model under two names: ask which one holds, never choose.

## 5. Changes between indices

Elements keep their identifier from one export to the next, so changes are
read element by element (rooms renamed or resized, openings and walls changed,
elements added or removed). A change can come from the modelling (a room
drawn, a family changed) as well as from the project: say so before drawing a
conclusion. A comparison declared « non fiable » (identifiers not kept) is not
a list of changes.

## 6. Quality and re-export

When the model's quality is « à améliorer » or « insuffisante », answer with
what is read, say what is missing, and propose a re-export citing the advice
given by focus « qualité » (shared coordinates, true north, space boundaries,
marks, IFC4, IfcExportAs). Never invent what the model does not hold.

## 7. A fact stated by the user

When the user states or asks to remember a project fact (« la cuisine donne au
nord »), compare it with the reading first. Agreeing: say so and on what. Disagreeing:
say what the reading shows and the likely cause (model north left at default,
another index, a room drawn otherwise). Either way it is a proposal for the human to
validate on the card, never « retenu » or « noté ».

## 8. When to open a drawing instead

For written dimensions, sections, reinforcement, notes, legends, or when no
model is read: use `drawing-reading`. When model and drawing disagree, give
both with their sources and ask.

Trade words and disciplines: `project-context/references/trade-vocabulary.md`.
Agency conventions when the installation provides them:
[references/agency.md](references/agency.md).

```text
model reading != model approved
déduit != lu
estimé != confirmed
```
