---
name: visual-focus
description: "Use when a user identifies a bounded region of an image, PDF page, drawing or frame that Hermes should inspect in context. Prefer Hermes' native region zoom when the authorized runtime exposes it; preserve source, locator, coverage, provenance and uncertainty."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: templates/hermes/SKILLS.md
  related_qualification: "Pantheon-Next#613"
  reviewed_upstream_surface: "Hermes Agent 0.20.6 / v2026.8.27: vision_analyze.region"
---

# Visual focus (governed candidate)

Non-executable Hermes skill candidate. Pantheon governs; Hermes executes outside the repository under an authorized Task Contract.

## Purpose

Let the user tell Hermes exactly where to look without creating another image-analysis, crop, annotation or identity system.

```text
exact visual source
-> bounded focus
-> Hermes native region zoom when available
-> context-preserving analysis candidate
```

## Native Hermes seam

Reviewed Hermes Agent `0.20.6` / `v2026.8.27` already exposes:

```text
vision_analyze(
  image_url=...,
  question=...,
  region=[x1, y1, x2, y2]
)
```

`region` uses original-image pixel coordinates and is cropped before downscaling, so the focused detail keeps the available resolution budget. Hermes also preserves crop/scale information for mapping back to the original image.

```text
reviewed upstream surface != installed runtime
runtime capability available != task-authorized
```

## Modes

- `human_focus` — use a user-selected `[x1, y1, x2, y2]` with native `vision_analyze.region` when available;
- `context_compare` — inspect whole visible source and focused region when surroundings matter;
- `grounded_focus` — optional capability gap only: an independently authorized grounding/segmentation tool may propose a region, then Hermes analyzes it through the same region seam.

If the user already selected the region, no grounding model is needed. A model-derived region requires traceable tool/model identity and localization method; if that provenance is unavailable, report a grounded-focus provenance gap instead of treating the localization as a qualified candidate.

## Required context

Resolve when available:

- exact source reference and digest/version;
- page, sheet, frame or equivalent locator;
- inspection question;
- original-image region coordinates;
- selection origin: `human` or `model`;
- allowed visual runtime/tool surface;
- scope, coverage and data-transmission limits.

If the exact source cannot be resolved, report the limitation rather than treating a derived crop or screenshot as authoritative.

## Method

1. Keep source and focus separate. A viewer may convert pointer/drag input into original-image coordinates; that UI supplies a region but owns no analysis or authority.
2. Inspect the whole visible source first when context can change interpretation.
3. Reuse `vision_analyze.region` for the focused inspection instead of adding another crop/VLM bridge.
4. If semantic localization or mask-level precision is materially necessary, treat it as an optional capability need; do not add an undeclared provider. For model-derived focus, preserve required localization provenance or return an explicit gap.
5. Separate visible observation, interpretation/inference, ambiguity, missing viewpoint/source and professional question candidate.

```text
crop != source
region != stable object identity
```

## Return posture

Return, when available:

- source reference and exact digest/version;
- page/sheet/frame locator;
- region in original-image coordinates;
- selection origin;
- observed scope and missing context;
- visible observations separated from interpretation;
- uncertainty / alternatives when material;
- runtime/model provenance available from the executed analysis path.

For model-derived localization, tool/model identity and localization method are required; missing provenance is a gap, not permission to emit an untraceable grounded region.

Reuse existing Result Candidate / Observation Bundle / Evidence Pack Candidate paths when required. This Skill creates no persistence owner or source-specific candidate envelope.

## Required boundaries

```text
human selection != professional conclusion
crop != source
region != stable object identity
bbox or mask != governed geometry
visible != complete
not visible != absent
apparent defect != contractual non-conformity
model inference != Evidence
grounding confidence != verification
runtime success != result validity
runtime success != Evidence
tool available != task-authorized
```

A partial or unknown visual field must not support absence inference outside the actually observed scope.

## Forbidden effects

This Skill must not by itself:

- modify or supersede the source;
- persist annotations/masks as canonical project state;
- create stable identity from source-local geometry;
- approve professional, contractual, compliance, payment or reserve conclusions;
- promote output to Evidence or a Registre Probatoire entry;
- transmit private source pixels externally without explicit authorization for that destination;
- install, activate or adopt a visual provider;
- trigger a consequential external action.

## Escalation

Report a bounded gap instead of guessing when the source/version is unresolved, the selected region is too imprecise, wider context is missing, resolution/coverage is insufficient, model-derived localization provenance is missing, or grounding/segmentation is required but unavailable or unauthorized.

## Final rule

```text
The focus tells Hermes where to look.
Hermes already owns the region zoom when available.
Pantheon still decides what may become governed truth.
```
