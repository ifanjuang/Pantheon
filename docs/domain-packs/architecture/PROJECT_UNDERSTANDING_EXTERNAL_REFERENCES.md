# Architecture Project Understanding — External References

Status: candidate / to verify — external reference register (candidate-only, non-canonical).
Boundary profile: candidate_support_note.

This document is an **external reference register** for the Architecture Project
Understanding work. It lists standards, libraries, tools, datasets and research
that may **inspire** adapters, examples, benchmarks or non-normative notes.

It is documentation only. It adds no runtime, no schema, no dependency, and adopts
no external tool as canonical. Every entry is candidate / to verify until audited
(licence, maintenance, security, read-only vs write, Hermes/local compatibility,
output quality).

## Placement rule

External repositories may inspire adapters, examples, benchmarks, or non-normative
notes. They must not:

- define Pantheon doctrine;
- become core dependencies;
- perform automatic canonization;
- mutate Revit / IFC / PDF / project memory without approval;
- replace Pantheon evidence, decision, and approval registers.

Every adapter must output, through the chokepoint:

```text
Task Contract in
→ Result Candidate + Evidence Pack Candidate out
```

Identity note: an external identifier (IFC GlobalId, Revit ElementId, source
label) is a **source / evidence**, never the internal `stable_id`. Internal
project identity is owned by the project object model, not by any external tool.

## 1. openBIM standards / doctrinal inspiration

- **IFC / buildingSMART** — BIM vocabulary: objects, relations, properties,
  quantities, interoperable exchange. Major external reference, not a canonical
  Pantheon model. Limit: IFC is too complex and heterogeneous to become our single
  internal structure.
- **IDS / buildingSMART IDS** — inspiration for information requirements, not for
  spatial understanding. Machine-readable requirements on objects, classifications,
  materials, properties and values in an IFC. Future inspiration for
  `information_requirement`. Limit: covers alphanumeric information, not spatial
  reasoning, orientation, site interfaces or details.
- **BCF / buildingSMART BCF** — inspiration for issues, coordination, location,
  clashes, comments, statuses. openBIM standard for issue management, by file or
  web service. Limit: describes coordination topics, not the project itself.
- **ISO 19650** — inspiration for information management over the asset lifecycle:
  exchange, naming, status, versioning and responsibilities. Reference for
  documentary discipline. Limit: avoid turning it into a bureaucratic apparatus;
  borrow the status/versioning posture, not the full process machinery.

## 2. IFC / BIM libraries and viewers

- **IfcOpenShell / IfcDiff / Bonsai (formerly BlenderBIM)** — best open-source IFC base (Python/C++);
  IfcDiff compares two IFC models (added / removed / changed) across geometry,
  properties, containers, aggregations and classifications. Priority candidate for
  a future `ifj-ifc-spatial-reader`. Limit: do not replace internal `stable_id`
  with IFC GlobalId; GlobalId is a source/evidence, not our project identity.
- **IfcOpenShell repository** — IFC library, geometry engine, plus Bonsai, BCF,
  bSDD, ifctester, ifcpatch, ifcmcp, ifcquery submodules. Central openBIM
  reference. Limit: ifcmcp or any IFC-editing tool is an external runtime, never
  Pantheon core.
- **xBIM Toolkit / XbimEssentials** — .NET alternative to read, create, view and
  query IFC, with geometry/topology operations. Reference if the runtime ecosystem
  becomes C#/.NET. Limit: less natural if the first runtime is Python/Hermes.
- **web-ifc** — IFC read/write in JavaScript/WASM, useful for web viewer and light
  querying. Candidate viewer/browser adapter. Limit: pre-alpha status per its
  README; experimentation, not a critical source.
- **Autodesk/revit-ifc** — Autodesk open-source IFC import/export for
  Revit/Navisworks; announces a release for Revit 2027. Reference to understand
  Revit IFC export, not a primary adapter. Limit: a Revit/IFC ecosystem component,
  not a Pantheon project reader.

## 3. AEC object models / adapters

- **BHoM** — strong inspiration for a software-agnostic AEC object model: schemas,
  functions, conversions and adapters, reachable from Revit, Grasshopper, Excel.
  Strong inspiration for our Architecture Project Object Model. Limit: do not
  import BHoM as-is; borrow the object/adapter separation.
- **BHoM Adapter** — architecture pattern: an adapter converts and exchanges data
  between the object model and external software. Placement reference; exactly our
  Project Understanding Base ↔ adapters (Revit / IFC / PDF / JPG) logic.
- **Speckle** — inspiration for versioned objects, connectors, viewer, controlled
  publication. Reference for system/versioning/viewer. Limit: must not become our
  canonical memory; it may inspire connectors, not govern project truth.

## 4. Spatial graph / topology / navigation

- **TopologicPy** — inspiration for topological graphs, rooms, paths, obstacles,
  circulation, connections, navigation graphs. Research / spatial-reasoning
  reference. Limit: algorithmic inspiration, not a single canonical vocabulary.
- **IfcLLM** — recent research: IFC converted into relational and topological-graph
  representations for natural-language queries. Priority conceptual reference. It
  confirms combining relational + graph, not SQL-only or graph-only.
- **BIM adaptive exploration / ifc-bench v2** — recent research showing BIM
  heterogeneity makes static approaches fragile; the benchmark covers many tasks
  across many IFC models. Method/benchmark reference. Implication: our adapters
  must explore and normalize, not assume clean models.

## 5. Revit / MCP / local bridge

- **Bimwright rvt-mcp v1.1.0** — current preferred external runtime candidate for
  read-only Revit qualification. Relevant properties: per-tool read-only filtering,
  read-only removal of arbitrary C# `send_code`, local per-session authentication,
  explicit per-instance targeting, and refusal of silent rebinding after a Revit
  restart. Revit 2022–2027 support. Limit: broad write/toolbaker surfaces exist
  upstream and remain non-admitted; runtime-local history is not Pantheon Memory.
- **Horizun Revit MCP v2.1.5** — fallback qualification candidate and live-evidence
  baseline. Broad typed Revit coverage with published multi-version probe evidence.
  Limit: only a bounded read-only subset is considered; Python, save/sync/delete/
  purge, modeling and delivery surfaces are outside the first Pantheon slice.
- **Pantheon Revit W0** — internal contract/freshness oracle, not automatically the
  production runtime. It anchors document/view/selection freshness, requested scope
  vs observed coverage, partial-coverage refusal and Observation Bundle semantics.
  Live convergence should select one runtime and remove redundant execution paths.
- **Autodesk Revit MCP 2027 (official)** — reference/watch candidate for local Revit
  reading, not the current preferred binding. Any future reassessment must preserve
  the same Task Contract, coverage, identity and effect boundaries.
- **revit-mcp-next** — architecture/reference watch for typed contracts, bounded
  operations and preview/apply patterns. Do not adopt without live production proof.
- **mcp-servers-for-revit** — technical reference MCP → Revit bridge. Technical
  audit, not a dependency. Risk: permissive write surfaces.
- **shuotao/REVIT_MCP_study** — advanced reference for architect/MEP/structure/
  fire-safety profiles, but too agentic. Technical audit / idea source. Risk: mixes
  tools, SOPs, skills, doctrine and actions.
- **Nonica Revit MCP / AI Connector** and similar small bridges — watch only unless
  they demonstrate a stronger contract, security or maintenance advantage than the
  current candidates.
- **BIBIM Revit/Dynamo AI Agent** — critical watch, not a Pantheon base; executes
  Revit/Dynamo tasks. Risk: action execution, auto-fix, code generation and external
  service coupling.

## 6. Vector PDF / plan drawing extraction

- **PyMuPDF** — PDF vector extraction: lines, rectangles, curves, paths, text.
  Priority candidate for `ifj-pdf-plan-reader`. Use: walls/partitions/dimensions/
  axes/lines from CAD/BIM-exported PDFs.
- **pdfplumber** — text/coordinates/tables/title-blocks/schedules extraction.
  Complementary candidate. Use: room names, dimensions, joinery tables,
  title-blocks, legends.
- **OpenCV** — registration, contours, Hough lines, image diff, zone detection,
  index-to-index alignment. Algorithmic tool, not a doctrinal reference.
- **LayoutParser / PaddleOCR** — OCR, layout, title-blocks, tables, legends, scans.
  Image/OCR candidates. Limit: OCR yields candidate text only, never truth.

## 7. Floorplan AI / raster → graph

- **CubiCasa5K** — dataset + floorplan-image baseline (thousands of annotated plans,
  many categories, polygonal annotations). Floorplan-AI benchmark / reference.
  Limit: older stack; useful as dataset, not necessarily a modern runtime.
- **DeepFloorPlan** — historical inspiration for walls/rooms/doors/windows/room
  types. Old reference. Limit: old stack; not production.
- **FloorPlanCAD** — CAD/SVG vector floorplan dataset reference. Potential
  benchmark. Limit: possibly stalled, to verify.
- **Raster2Seq** — priority research reference: turns raster plan images into
  labelled polygonal sequences for rooms, doors and windows, with geometry +
  semantics. Priority watch. Limit: integrate only after verifying repo, licence,
  model weights, reproducibility.
- **FloorplanVLM** — vision-language floorplan watch. Research to monitor. Limit:
  not production without code and tests.

## 8. Performance / future analysis (out of MVP)

- **Ladybug / Honeybee** — future inspiration for daylight, energy, solar exposure,
  orientation, glazed surfaces. Future extension. Limit: not useful for the
  immediate understanding core.
- **EnergyPlus / Radiance / OpenStudio (via Honeybee)** — simulation, not project
  understanding. Future adapter/domain extension.

## 9. IDS / assisted generation

- **Ishigaki-IDS / Ishigaki-IDS-Bench** — recent research on IDS generation and
  benchmarking; shows LLMs still struggle to produce valid IDS XML aligned with IFC
  vocabularies, and a specialized model improves validation pass rate. Research
  watch. Implication: information requirements must stay governed and validated, not
  freely generated.

## Repository decision

- Repo state: candidate references plus selected adapter/runtime qualification work.
- Authority: external reference / candidate-only; none of these tools is canonical
  project truth, Evidence, Memory or execution authorization.
- Current Revit decision: **qualify rvt-mcp first**, retain Horizun as fallback and
  live-evidence baseline, and use Pantheon W0 as contract/freshness oracle.
- Exit criterion: same-fixture live receipts, one production runtime selected, then
  redundant production execution paths removed.
- IFC and other external references remain subject to licence, maintenance,
  security, read-only/write, local compatibility and output-quality review.

## Governance references

- docs/governance/AUTHORITY_INDEX.md
- docs/governance/CAPABILITY_PLACEMENT.md
- docs/governance/EVIDENCE_PACK.md
- docs/governance/TASK_CONTRACTS.md
- docs/governance/EXTERNAL_TOOLS_POLICY.md
