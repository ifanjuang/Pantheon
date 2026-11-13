---
name: drawing-reading
description: "Use to read an architectural or engineering drawing (PDF plan, section, elevation, detail, site plan) to answer a bounded question or check a value: identify the drawing first, then read only what the question needs (grid lines, levels, rooms and areas, tables, legend, walls and partitions, openings, dimensions). A written dimension is read; a scaled measurement is deduced. Creates no truth or approval."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: templates/hermes/SKILLS.md
  related_skills: [project-context, model-reading, visual-focus]
---

# Reading a drawing

A drawing answers a question; it is not read whole. Keep the user's question,
read the part of the drawing that answers it, cite where, and say how sure.

For the building as modelled (rooms, elements, positions, sizes, changes
between indices), ask the project-state source first (`get_project` with a
focus, see `model-reading`). Open the drawing for what models do not hold
(dimensions written by the designer, sections, reinforcement, notes, legends,
tables), when no model is read, when the user asks to check on the drawing, or
to cite it.

## 1. Identify the drawing before reading it

Find it first: `get_project` with focus « plans » lists the current drawings,
latest first, each with the `project_ref` and `source_path` the document reader
takes; open only the one that shows what is asked (plan de niveau for a room,
façade for an elevation), searching the room or mark as text. Do not guess paths.

From the title block (cartouche): project, drawing title, nature (plan de
niveau, coupe, façade/élévation, détail, plan masse, plan de situation,
structure, réseaux), level shown, phase, index, date, scale, issuer. The
current index of a piece comes from `get_project`, never from the file name.
When the drawing read is not the current index, say so.

## 2. Find the references

- **Grid lines (files)**: letters one way, numbers the other. Place everything
  by them, as the models do: « sur la file C », « entre 3 et 4 ».
- **Levels**: level name (RDC, R+1 / R00, R01), altimetry (0,00, NGF), floor
  and ceiling heights on sections.
- **North arrow** on plans; **section marks** (A-A, 1-1) linking plans and
  sections; elevations named by orientation or by side (« façade rue »).
  Without a north arrow, a direction is an assumption: say it.

## 3. Read what the question needs

Detailed checklist: [references/reading-checklist.md](references/reading-checklist.md).

- **Legend first** when hatches or colours matter: existing / to demolish /
  new, materials, insulation, fire ratings.
- **Tables on the drawing** (surfaces, door and window schedules, finishes):
  quote them as written; they often answer directly.
- **Rooms**: name, number, area written in the room.
- **Walls**: exterior walls (thick, layered) against interior partitions (thin);
  load-bearing walls by hatch or structure drawing.
- **Openings**: symbol, mark (repère), sill and height on sections or tables,
  side and façade.

## 4. Dimensions

Rules: [references/dimensions-and-measuring.md](references/dimensions-and-measuring.md).

- A **written dimension (cote)** is read: quote it with its chain and units.
- **Measure only when no dimension answers**, after checking the scale on a
  known written dimension of the same view; give the result rounded with its
  uncertainty, marked **déduit (mesuré à l'échelle)**. Never measure when a
  written dimension exists; never measure a drawing marked « ne pas mesurer ».

## 5. How to look

Read the PDF's own text first (`read_vault_pdf_pages`): exported drawings carry
room names, areas, dimensions, grid labels and title blocks as text. Look at the
image (`read_vault_pdf_figures`, or a zoom on a region with `visual-focus`)
when the answer is graphic: a hatch, a symbol, a position. Name the page and the
zone (« page 2, quart supérieur gauche, entre les files B et C »).

## 6. Answer

- Cite drawing, index, page and zone for each value.
- Confidence: **lu** (written on the drawing), **déduit** (measured, inferred
  from a symbol or a position), never more. A drawing is not validated by being
  read.
- When drawing and model disagree, give both with their sources and ask which
  one holds; do not choose.
- When the drawing is ambiguous (two partitions could be meant, a mark
  unreadable), ask the user, naming the candidates.
- When the drawing cannot answer, say what would (another drawing, the model, a
  section).

Agency conventions (naming, levels, grid lines, title blocks) when the
installation provides them: [references/agency.md](references/agency.md).

```text
drawing read != drawing validated
measured on a drawing != written dimension
file name != current index
```
