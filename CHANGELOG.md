# Changelog

## Unreleased - public repository start (2026-10-14)

- Public history starts from a reviewed snapshot of the private Pantheon-Next
  repository at `40f2a1ae` plus its five then-open pull requests.
- Removed `ai_logs/` and its index/path tooling; provenance links now point to
  the private Pantheon-Next archive.
- Real project data pseudonymized; real case examples removed.
- Agency- and host-specific identifiers genericized (`vault-read`,
  `vault-search`, `project-context`, `hindsight-project`, `AGENCY_PROJECTS`);
  host names, NAS paths and LAN addresses replaced by placeholders.
- Archive issue/PR references qualified as `Pantheon-Next#<n>`.
- Project Anatomy model §25 (frontière `ProjectClaim` / APU) is now a decision,
  and records that phase codes and source kinds will move to governed
  vocabulary registries with an add-only local agency file.
- Project Anatomy `source_kind` is now a governed vocabulary registry
  (`registries/architecture_source_kind_profile.registry.json`) instead of a
  closed list in the schema, extended add-only by an agency file named by
  `PANTHEON_SOURCE_KIND_OVERLAY`. New kinds: `document`, `email`, `cad_drawing`;
  the Document Structure fragment writer labels written documents `document`
  instead of `other`. The validator and the owner check the declaration; the
  database checks the shape only. The registry is carried in the built package
  with its digest. An installed owner is upgraded in place.
- Phase codes are now a governed vocabulary registry
  (`registries/architecture_phase_profile.registry.json`) instead of a closed
  list repeated in five Project Anatomy and proof-register schemas. `ESQ` is
  declared; each code carries a category (mission element, project stage or
  non-project scope marker). An agency may add phases through an add-only file
  named by `PANTHEON_PHASE_OVERLAY`. The APU validator and the owner refuse an
  undeclared code; the registry is carried in the built package with its digest.
- Phases are declared per project as it advances: ProjectClaim `phase` (card
  field `phases`), one claim per phase with a required effective date, checked
  against the phase vocabulary (scope markers refused). The Project Anatomy
  Cockpit projection reports claims established at a phase the project has not
  declared, without refusing them. The SQL read cache now projects every list
  claim type generically instead of special-casing parcels.
- The card's current phase is compared with the declared phases: a card phase
  the project has not declared is reported on the Project claims read
  (`phase_consistency`) and on the card verso, never refused or corrected. A
  phase declared again is listed once in both the Python and SQL projections.
- Phase aliases: a registry code may list other spellings, and the agency file
  may add its own (`aliases`) without redefining a repository code or alias.
  Both registry readers (validation server and owner) apply the same rules.
  `DPC` (building-permit filing, an agency project stage) is declared with the
  aliases `PC` and `PERMIS` and added to the card phase values. A declaration
  given by an alias is stored as its code with the entered spelling kept. The
  disposable-database phase check now runs from `implementation/` without
  `PYTHONPATH`.
- IFC observation: `observe-ifc` reads storeys and spaces (surfaces from Qto
  quantities or the space footprint) of one model index, reconciles them with
  the Project Anatomy by GlobalId and deposits only the difference as a batch:
  `+ objet`, `= rattache` (known object, including ones first observed on a
  drawing), `~ remplace` (changed surface), `- retrait` (absent from the index).
  Batch review now includes identity matches. Optional `ifc` extra
  (ifcopenshell).
- APU object lifecycle: Observation Bundles may carry new-object and retirement
  candidates; reviewed (`accept_object_candidate`, `accept_retirement`), prepared
  (`add_object`, `retire_object`), authorized and applied through the existing
  chain, recording `object_added` / `object_retired` (whose writer was missing).
  A retired object is kept with its history. Batch review orders new objects,
  then claims, then retirements. Guarded migrations upgrade existing databases.
- Anatomy on the affaire card: the implementation publishes each Project's
  Anatomy projection as `<MVP_ANATOMY_EXPORT_DIR>/<CODE>.json`
  (`pantheon.anatomy.v1`) after `store-reviewed-dossier` and `apu-batch`
  (regenerate with `export-anatomy`); the Workspace Cockpit reads it through
  `WORKSPACE_ANATOMY_DIR` and shows levels, spaces, ouvrage state and values on
  the back of the affaire card, read-only. The projection now keeps relation
  qualifiers.
- APU batch review: `apu_batch.preview_batch` / `apply_batch` and the CLI
  `apu-batch` let one human approval cover all claim candidates of one
  Observation Bundle. The preview's digest binds every candidate and its accept
  or reject decision; applying replays the existing per-candidate chain (review,
  write command, authorization, application) in one transaction, all or
  nothing. No new table or schema.
- Model reading: `model_reading` reads the current index of each model piece
  of an affaire once (cached by file fingerprint) and `export-anatomy`
  publishes it beside the Anatomy (`<CODE>.maquette-<piece>.json`): levels,
  spaces, doors and windows with their host wall, the space on each side,
  exterior or not, façade and grid position, walls with length, thickness,
  composition, sides, façade, grid position and junctions, and the neighbours
  (spaces linked by a door or sharing a wall). Sides and façades are computed
  by geometry and said to be deductions; a façade named from a default model
  north is flagged as to be confirmed. `get_project(code, focus)` returns the
  sheet of one room or element from it. CLI `read-model --file` prints a
  summary. A reading, never a source: nothing enters the Anatomy.
- Current state reading generalized after a dry run on five affaires: only
  project pieces are followed (drawings, models, written pieces of the design
  and consultation, recognised by name), everything else in an affaire folder
  (minutes, litigation, chats, statutes...) is counted, not followed; piece
  names drop dates written with dots, noise words and the words repeated
  across an affaire's names (client, address, project title). `get_project`
  puts the open questions first, adds a synthesis written from the published
  state, the origin of each date (card, title block, file name, PDF creation)
  and the project description and phase, with a rule not to add anything that
  is not in the answer.
- Hermes routing to the live project state: the `get_project` description and
  the policy server instructions call it the live project-state source, to use
  first for where an affaire stands or the current index of a document, and the
  `project-context` Skill (core route, point 8) now covers the current index of
  a drawing, model or written document and forbids inferring an index, version
  or phase from a file name. A test keeps the tool and the Skill on the same
  words. Observed on IA00: without this, the governed profile listed files and
  inferred indices from their names.
- Where an affaire stands, for Hermes: the read-only MCP tool `get_project(code)`
  reads the file the implementation already publishes for the Workspace Cockpit
  (`<PANTHEON_ANATOMY_DIR>/<CODE>.json`) and returns a compact summary: current
  index of each piece and the open questions when the file carries them, then
  levels, spaces, surfaces, state of the work, surface totals by state, sources
  and reading rules. Indices and numbers come from the file so a local model
  quotes them instead of computing or recalling them. No database access; never
  evidence or a decision.
- Consolidation requests from the Workspace: `agency consolidate-pending`
  (for a timer) reads, read-only, the project card requests
  (`workspace_anatomy_consolidation_requests`) and the changed `anatomy_source`
  cards, consolidates those affaires once per request and remembers what it
  handled on the agency side; a requested consolidation is always dated, even
  when every source was up to date, so the card shows it done. The Workspace contract (the `anatomy_source`
  object, the request table, what is published back) is documented.
- File sheets and the project core: model sheets are named by the model file's
  fingerprint, so deactivating, reactivating or coming back to an earlier index
  reads nothing again, and sheets nothing refers to are removed. A drawing
  source's sheet carries its index and text. Each consolidation that brings a
  source in keeps a snapshot of what the affaire's state rested on (last
  twenty). A file moved in the Workspace keeps its declaration through its
  content digest. `get_project` answers `fichier <name>` with a source's sheet
  and gives the last consolidation date. Direction documented: per-file sheets,
  a small project core, Hermes enriching both by proposals only.
- `get_project` summary lighter for a local model: each model's quality gives
  short labels of what to correct (`à_corriger`) instead of the full export
  advice, and `focus="qualité"` gives every model's checks, full advice to
  cite, declared against observed and overlay.
- One confidence scale for every value: validé (confirmed by a human), lu
  (written in the source), déduit (computed from the source), estimé (brought
  together across sources). Each piece's current index says it (from where the
  index was read: card, title block, file name, none), model answers carry the
  legend and mark overlay-placed rows `estimé`, a source's overlay is `validé`
  once confirmed; Hermes qualifies an answer by its weakest value.
- Changes between two indices of a model (`model_diff`): each model is compared
  with the previous index of its piece, element by element through the IFC
  GlobalIds the authoring tool keeps, on the readings (rooms, openings, walls,
  elements by category), once per pair of fingerprints. `get_project` gives
  one line per model and `focus="changements <maquette>"` the detail. Two
  current models sharing most identifiers raise the question "one model under
  two names: which one is authoritative?".
- Index order checked by dates: indices follow each other, and a known date
  (card, title block read by the preflight, file name; never the PDF creation
  date) checks it. A lower index dated after the current one (indices
  restarted at a new phase, a wrong index) becomes a question; the current
  index is not changed automatically.
- From a control of Hermes' answers: rooms are found through usual synonyms
  ("salon" for "Séjour", "salle de bain" for "SDB"); "du BET" or "archi" in a
  focus keeps only that discipline's models; a room or element not found gives
  the rooms and the advice to retry instead of a dead end; an answer spanning
  several models summarises each beyond 12 rows, and the piece list stops at 30
  with a filter hint. The "one model under two names" question gives each
  index's date, which one is more recent, and speaks of shared IFC identifiers
  so it is not mistaken for the overlay score.
- Hermes skills `drawing-reading` and `model-reading`: how to read a drawing
  (identify it from the title block, grid lines, levels, legend, tables,
  rooms, walls and partitions, openings; a written dimension is read, a scaled
  measurement is deduced and only when no dimension answers) and how to answer
  about a model from the published readings (which focus for which question,
  confidence scale, positions, engineers' overlays, changes between indices,
  quality and re-export). Short main files for a local model, details in
  references; agency conventions in a reference an installation may replace.
- Question/action publication contract: each published question carries a
  stable identifier, the files it concerns and a proposed action (mark the
  project reference, correct an index, remove a reference, activate a source as
  a replacement). The consuming Cockpit UI and write endpoint are not part of
  this change.
  The Anatomy's seven rules for an AI (deterministic readings, per-file sheets,
  short answers, one confidence scale, questions not decisions, proposals
  validated by a human, one owner per information) are written once.
- Summarised selections give distributions over every element (counts by
  grid position, size ranges) and say the 8-row extract is a sample: a control
  showed Hermes generalising positions and sections from the extract alone.
- The summary names each model's discipline and file, and the "one model under
  two names" question starts with the discipline ("Maquettes structure : …"):
  a bench showed Hermes taking an engineer's file for the architect's model and
  tying the engineers' question to the architect's changes. Change lines give a
  total per kind ("éléments : 197 changés (143 ajoutés, …)") so it is quoted,
  not added up (the bench showed a wrong sum).
- The `get_project` tool description, read with every tool list, now names the
  project's Anatomy and its vocabulary (« anatomie du projet », « sources
  anatomiques »), says it is the first call for any question about an affaire's
  building, lists the focuses (rooms, elements by category and place with « du
  BET », changes, quality, sources, files), forbids searching the web for an
  affaire and asks for one retry on "not found". A bench showed « sources
  anatomiques » read as medical anatomy and searched on the web.
- `get_project` tells Hermes to start with the summary (models with discipline,
  index and file, open questions, changes, quality) and to answer from it when
  it suffices, and to open documents only when asked to verify or when the
  answer is not there, offering to dig further rather than reading at length:
  a bench showed 7 focus calls for an index already in the summary, and 27 to
  68 calls reading documents for questions the summary answered.
- From a full reading of a Hermes bench (42 runs): the governed profile now
  says to claim an action done only when its tool confirms it, that a project
  fact asserted by the user is a proposal, and that a request to choose or
  record gets the elements while the human decides (Hermes had answered
  "Retenu" after a failed memory write, and decided when asked to choose). A
  room sheet groups its exterior openings by façade (two windows had been
  swapped between façades). An element is designated between two rooms
  (« cloison entre la chambre 3 et la SDB »), and « cloison » falls back on
  interior walls, said so. Open questions are put first only when they concern
  the answer. The "one model under two names" question says its shared
  identifiers have nothing to do with the overlay score.
- Trade vocabulary and habits rather than case rules: a `project-context`
  reference gives, by trade (terrassement and VRD, gros œuvre, charpente and
  ossature, couverture, façades and isolation, menuiseries, plâtrerie,
  plomberie, CVC, électricité, extérieurs), the usual words and abbreviations
  and which document or model discipline answers, how architecture, structure
  and fluids models differ, and standards to read in the library; an unknown
  term is looked up in the library first. `model-reading` gains a method for a
  fact stated by the user: compare it with the reading, say whether it agrees
  or why it may not (model north at default…), and treat it as a proposal to
  validate, never « retenu ». Each model in a multi-model answer names its
  discipline.
- The governed profile says a factual question on an affaire is not governed
  work (answer with `get_project`), and keeps the governed method for
  consequential work: in benches, simple questions (a model index) loaded the
  governed method, request intake and activity projection skills and called
  classification and routing tools before reading the summary.
- Memory reuse and verification offer: an answer from memory ends with one
  short offer to check further, naming the source that would confirm it; what
  the conversation already read is cited instead of reopened; an earlier
  session or remembered passage is a lead, checked against `get_project` when
  it concerns an affaire (newer index, newer reading); differently worded
  questions are recognised by subject; memory keeps preferences and
  conventions, project facts go to the card for validation.
- The `get_project` summary lists the architect's model first, and the status
  of an affaire without a validated Anatomy says that answers come from the
  pieces and model readings listed: a bench showed Hermes taking the first
  model listed (an engineer's) as the architect's, and reading « Anatomie non
  encore installée » as « no index available ».
- The "one model under two names" question gives the model file's own date
  when no date was read on a card or title block, said « date du fichier », so
  it can still tell which one is more recent.
- Card proposals: `prepare_card_proposal` (read-only MCP tool) checks the
  corrections a discussion found for a document card (date, index, issuer,
  title, summary…, each with its source and a confidence never « validé ») and
  returns a `pantheon-card-proposal` block that Hermes copies into its answer;
  the Cockpit shows it as a checklist on the card and saves only what the
  operator accepts. The project-context skill tells Hermes to propose instead
  of announcing a change.
- Anatomy sources (`anatomy_sources`): the files an affaire's readings rest on
  are declared on their Workspace card (`anatomy_source`: complement or
  replacement, role, discipline, use, scope, declared alignment, consolidate
  now), read read-only. Consolidation (`agency consolidate --code`, or an
  export when the card asks for it) reads them, overlays the engineers' models
  and publishes each source's state (en attente, activée, avertissement,
  erreur, remplacée, inactive) with its reasons, reading, quality and overlay
  in `<CODE>.json`. A replacement happens only when the new source succeeds.
  Only consolidated, usable sources are read; without any declaration the
  former behaviour stays. An agency-owned record next to the projection keeps
  what was consolidated. `get_project` lists the sources, one line each, and
  answers the `sources` focus.
- Overlay of engineer models without shared coordinates (`model_alignment`):
  during the preparation of a new model index, each structural model is laid
  on the architect's (height by the ground floors, rotation by dominant wall
  directions at the four quarter turns, position from the building core
  refined onto the architect's walls), scored by the share of its points on
  architect walls and its margin over the next candidate, applied only when
  probable and marked to be confirmed. Its elements then inherit the
  architect's level, rooms and grid position. Model readings keep a minimal
  geometry (wall ends, element points, room outlines, grid lines, floors) for
  this. `get_project` answers engineer elements by grid line or room through
  the overlay, merges a category across models, gives each model's overlay in
  the summary, and tells Hermes to say an overlay is estimated.
- Model quality by discipline: a model with only load-bearing elements is a
  structural model, for which missing spaces, marks and space boundaries are
  set aside rather than failed; a new check asks for shared coordinates (a
  georeferenced site or a map conversion), first in the export advice, so
  architect and engineer models can overlay. `get_project` gives the quality
  of every published model and shows declared-against-measured size gaps on
  designated elements.
- Category profile `architecture@1`
  (`registries/architecture_category_profile.registry.json`) and one reading
  engine for every element: what a model element is (opening natures, walls,
  columns, beams, members, footings, slabs, roofs, stairs, railings,
  coverings, plates; furniture and generic objects counted, not read) comes
  from declarative rules (IFC classes, predefined types, type-name patterns,
  exterior side, sill, height, width, thickness, orientation), first match by
  priority, with synonyms; agencies may add categories (add-only). The model
  reading describes every element the same way with a spatial index, measures
  opening sizes from geometry and points out declared sizes (IFC or custom
  family parameters) that differ. `get_project` designations use the category
  words of the reading ("poteaux", "garde corps R01"), room sheets list what a
  room contains, the summary counts elements by category per model, and long
  selections give counts by level and room with an extract.
- Model reading made rigorous on imperfect models
  (`docs/domain-packs/architecture/IFC_EXPORT_FOR_MODEL_READING.md`): the
  nature of an opening is deduced from geometry (exterior side outside the
  level outline, sill, height, width) with the IFC class and declared type as
  clues, so exterior doors modelled in window families and door families in
  load-bearing walls are read right; a missing space inside the outline is an
  unmodelled room, not the outside; free openings and spaces open onto each
  other are read; sills are measured from the adjacent floor; standard
  properties are read where reliable, and declared against observed is
  summarised once. Each reading carries a quality level with re-export advice;
  `get_project` shows it, names openings by their nature (a `porte` may be a
  French window in a window family), and tells Hermes to answer with what is
  read and propose a re-export when the model falls short. Agency habits may be
  set in a local file (`MVP_MODEL_CONVENTIONS`).
- An affaire is published before its Anatomy is installed: `export-anatomy`
  writes its pieces and model reading with an empty Anatomy marked
  `not_installed`, and `export_all` covers every Project with a code (a code
  that cannot name a file is skipped). The current-state reading no longer
  raises a question for a drawing and its model under one index (two formats
  of one piece) and admits numbered engineer indices (`Ind 0`, `IND9`). The
  model reading also reads grid lines exported in `WAxes`, the third axis list
  of an IFC grid, where Revit may put one direction.
  `get_project(code, focus)` also selects `file M`, `façade sud` or a level
  (`R01`), with the architect's model read first, so reverse questions are
  answered by the tool instead of the model.
  A designation such as `cloison file 5` or `fenêtre façade sud chambre 1`
  returns the one element it names, or the candidates with the question to ask
  the user instead of choosing.
  Without focus, `get_project` answers with a summary of a few kilobytes
  (questions, synthesis, models, rooms); the full lists come with `focus`
  (`pièces`, optionally filtered, `devis`, `locaux`), and a focus answer
  carries only a short header. A real answer of 38 KB had to be paged by Hermes.
  It also understands what Hermes was seen typing: a lower-case affaire code,
  `n°` before a room number, and a plural element word (`fenêtres`), which
  lists every matching element instead of asking which one.
- Property profile `architecture@1`
  (`registries/architecture_property_profile.registry.json`): the vocabulary of
  attribute keys, so an object gains properties as the project advances
  (identity, position including grid lines, geometry, function, composition,
  performance, state, quantity), each with its facet, value type and unit, in
  French. Advisory: an undeclared key is reported, never refused; an agency may
  add properties through `PANTHEON_PROPERTY_OVERLAY` (add-only).
  `export-anatomy` publishes the label, unit and facet of each property an
  affaire uses, and lists undeclared keys.
- Current state of an affaire's documents: `project_pieces` groups the files of
  an affaire into pieces (one drawing, model or written document across
  indices) and gives the latest index of each, from what the Workspace Cockpit
  already read on the title block or the human corrected on the document card,
  plus the IFC models of the affaire folder (ARCHIVES skipped). Index rule: A,
  B, C successive, C1/C2 variants of C; a file without index keeps an uncertain
  position placed by its date. Two contents under one index, several variants
  of the latest index, or an unindexed newer file become questions. Quotes are
  set apart for confrontation. A reading, not a register: `export-anatomy`
  publishes it in the same `<CODE>.json` as the Anatomy (`pieces`), and the CLI
  `pieces --code` prints it. Configured by `MVP_WORKSPACE_STATE_DB` and
  `MVP_AFFAIRES_ROOT`.
- Phase orientation: `registries/architecture_phase_orientation.registry.json`
  projects the agency domain pack phase map (candidate deliverables, minimum
  evidence, gate per phase block) and the gate risk of the index effect matrix,
  in French. The Cockpit card verso shows the card phase's main subjects in a
  folded section, and the read-only MCP tool `get_phase_orientation` gives them
  to Hermes. Orientation only: no status, no completeness check, nothing
  required. A conformance test keeps the registry aligned with both documents.
- Project Anatomy relation profile `architecture@1` (candidate registry under
  `registries/`): the APU validator now reports undeclared or deprecated
  relation types, inadmissible endpoints and out-of-vocabulary controlled
  qualifiers as `vocabulary_errors`, and fails closed when the profile cannot
  be read. Dossiers using off-doctrine types such as `opens_into` now fail
  validation; the Cockpit demo fixture uses `architecture.opens_to`.
- Project Anatomy progressive claim writes (candidate implementation, not
  deployed): after the reviewed dossier import, an Observation Bundle attribute
  or relation claim candidate can be added, or can replace one claim on the same
  subject and key, through review (`accept_claim_candidate`), write command
  (`add_claim` / `supersede_claim`), human authorization and application. Claims
  stay append-only and candidate; replacements are recorded in
  `agency_apu_claim_supersessions` and `get_project_anatomy` lists only claims
  in force plus `superseded_claims`. Identity relations stay out of this path.
  APU write authorizations are now ordered by write time (`clock_timestamp()`),
  so a rejection written after an authorization always wins.

- Workspace Cockpit multi-vault (catch-up of the state running on the
  reference node): one coordinator producer for Affaires and Bibliotheque with
  a shared SQLite index and processing queue (preflight, OCR, Hindsight lanes,
  per-lane/per-document pause, retry/continue), metadata preflight (date, index,
  issuer candidates with page and evidence), retained OCR derivatives, worker
  observability and a read-only OTEL span log. Node values (roots, mounts,
  banks, state database, vision model) are bindings outside Git. The unused
  per-file raw-text representation of #64 is retired.

## 0.1.66 - 2026-09-10

Hermes-first test checkpoint after the post-0.1.65 convergence cycle. This
heading records the repository state selected for controlled runtime testing.
It does not claim a published tag, installed deployment, provider adoption,
professional validation or production authorization.

### Added

- Project-context and exact-document routing for agency professional work, with
  explicit project continuity, alias/identity separation and the distinction
  `mentioned != exact source present != relevant content inspected`.
- ProjectClaim provenance, temporal-read and conflict-candidate structures,
  plus project/document identity and workspace source-materialization
  qualification paths.
- Context-admission and external-context candidate surfaces for Hermes, with
  bounded retrieval and source/data exposure rules.
- Qualification material for PAIR + Unsloth, Obsidian/Hindsight workspace
  composition and related runtime/source boundaries.

### Changed

- Hermes integration converged on adaptive runtime selection: Pantheon bounds
  legitimacy, scope, data exposure, effect ceilings and approvals while Hermes
  may choose qualified tools, skills, plugins, MCP capabilities, models and
  delegation inside that admitted boundary.
- Boundary-profile vocabulary and placement were migrated across governance,
  architecture-domain, examples, assets, templates and Hermes profile
  documentation, reducing duplicated authority prose and retired-owner drift.
- Workspace, memory, Evidence, exact-source and governed-identity distinctions
  were tightened so retrieval, filesystem organization, derivatives and
  runtime success cannot silently acquire authority.
- CI now enforces additional authority/boundary consistency, AI-log index
  currentness and qualification contracts introduced during the convergence
  cycle.

### Test checkpoint

The selected source checkpoint is `main@bc2ac9a80c662f252ebf3749775c00f061edcd58`
before this version-only release PR. Open experimental work such as Google
Drive provider qualification remains outside this checkpoint until separately
rebased, reviewed and admitted.

```text
checkpoint versioned != tag published
green CI             != runtime qualified
runtime qualified     != effect authorized
test deployment       != production adoption
```

## 0.1.65 - 2026-09-02

Consequential-mutation inventory closed and one chokepoint gap wired. This
heading records an implementation candidate checkpoint and does not claim a
published tag, installed service, live Hermes enforcement, activation or
production authorization.

### Added

- The consequential-mutation entry-point inventory now enumerates and has
  individually reviewed all 92 discovered mutation entry points under
  `implementation/mvp_vertical`; the unreviewed ceiling moves from a bound on
  a shrinking backlog (21) to a rule (0) — a newly discovered entry point must
  be reviewed when it is added.
- `human_access.bind_oidc_identity`, the write that makes an external OIDC
  identity able to act as a governed principal, now routes through
  `policy_gate.enforce_consequential` when a decision point is supplied, with
  the decision expectation bound to a digest of the exact binding
  (`principal_ref`, `issuer`, `subject`, `valid_until`) rather than to its
  name. The only production path (`mvp-vertical bind-oidc-identity`) fails
  closed without a configured decision point unless
  `MVP_POLICY_ENFORCEMENT=disabled` is declared explicitly.
- `test_semantic_order_is_total_when_distances_tie` and
  `test_a_pending_gate_is_still_absent_from_the_code_it_names`: regression
  tests that plant the defect they guard against instead of waiting to
  observe it, and assert an absence rather than a surviving fragment.

### Fixed

- `mvp_vertical.store.retrieve_scoped` ordered semantic hits on vector
  distance alone at both call sites, so equal-distance rows could return in
  either order between two identical calls. Both queries now carry the same
  tiebreak (`source_ref`, `source_digest`, `chunk_no`) the lexical retrieval
  path already used.
- `apu_write_preparation.apply_authorized_write_command` read the latest
  write authorization outside the transaction that applies the command, so a
  `reject_application` committing in the gap did not block the apply. Both
  `apply_authorized_write_command` and `append_authorization` now take the
  command row `FOR UPDATE` before reading or writing the decision.
- `store.ingest` accepted a `replace_dossier` parameter it never read, while
  both call sites passed `False` believing it protected the dossier from
  replacement; removed. The protection is the digest-scoped `DELETE`, named
  where it actually lives.
- `project_change_variants.select_variant_for_change_candidate`'s replay
  branch looked its selection disposition up by the current call's
  idempotency key after testing and discarding the disposition id already on
  the candidate row, so a replay under a different key raised as if the
  disposition did not exist. It now looks the disposition up by that id.

### Changed

- The mutation inventory's pending-gate anchor changed from a literal code
  fragment expected to remain present to a normalized-body digest and a
  reachability check against `enforce_consequential`, so a repair is detected
  by the absence of the gap rather than by a fragment that survives the
  repair. Required-gate ceiling: 9 -> 5 (`store_reviewed_dossier`,
  `publish_knowledge`, `complete_edit_request`, `apply_edit_request`,
  `act_working_information` remain).
- Reviewed Ubuntu release targets refreshed for the current bootstrap
  candidate under `deployment/ubuntu/`.

### Boundary clarification

Reviewing an entry point and wiring one gate change what this repository can
say about its own consequential-write surface. They do not change adoption,
deployment or professional validation status.

```text
entry point reviewed  != entry point authorized
gate reachable         != gate observed enforced in a live deployment
identity bound          != identity granted access
green CI               != adoption
implemented            != installed
```

## 0.1.64 - 2026-07-22

Read-only policy transport checkpoint. This heading records an implementation
candidate and does not claim a published tag, installed service, live Hermes
enforcement, activation or production authorization.

### Added

- `PantheonPolicyService`, a transport-neutral application facade shared by MCP
  and HTTP projections.
- `pantheon-policy-api`, an authenticated internal FastAPI adapter with separate
  liveness/readiness, request classification, deterministic candidate-work
  preflight, consultation, candidate preparation, validation, provided-evidence
  verification and Context Pack planning/validation routes.
- A hardened candidate `Dockerfile.policy-api` and `compose.policy-api.yaml` for
  `ai-net`, with no host port, a read-only checkout/filesystem, dropped Linux
  capabilities and no Docker socket.
- HTTP acceptance tests for fail-closed authentication, policy parity, K4 gate
  behavior, request-size limits, legacy-route refusal and Context Pack schema
  validation.
- `mcp-server/docs/HTTP_API_CONTRACT.md` and a candidate Hermes enforcement
  blueprint under `templates/hermes/connection/`.

### Changed

- MCP tools now call the same application facade as the HTTP adapter rather than
  wiring policy modules independently.
- The package exposes optional `http` dependencies and the
  `pantheon-policy-api` console entry point.
- Repository status and authority maps distinguish MCP consultation, HTTP
  policy/preflight data, Hermes enforcement and human decision.
- `VERSION`, this changelog head and package metadata advance together to
  `0.1.64`; the repository root remains non-distributable.
- The `mcp-server` module migrates to the `mcp` Python SDK 2.x line (`mcp>=2,<3`):
  the stdio server now uses `mcp.server.MCPServer` (the v2 successor to the
  removed `mcp.server.fastmcp.FastMCP`). Read-only tools, resources and the
  end-to-end stdio conformance harness are unchanged; the surface stays
  side-effect-free.

### Compatibility posture

- `POST /domain/approval/classify` remains a temporary classification alias and
  has no approval effect.
- `GET /runtime/context-pack` and `GET /domain/snapshot` fail explicitly with
  `501 contract_not_defined`; their ambiguous semantics are not invented.

### Boundary clarification

The API never authorizes external or canonical effects in V0. Gate references
remain caller-provided, unverified signals. Hermes remains the Policy
Enforcement Point and execution runtime; OpenWebUI exposes; the human decides.

```text
MCP consultation != HTTP enforcement
classification != authorization
provided gate reference != validated decision
ready != safe
runtime_success != evidence
implementation present != activated
```

## 0.1.63 - 2026-07-21

Repository-efficiency consolidation checkpoint. This heading records the
repository and MCP-package state after PRs Pantheon-Next#424 through Pantheon-Next#428. It is not a
published release: no `v0.1.63` tag is claimed.

### Added

- `pantheon-verify <family> <evidence>` as one static read-only CLI for install,
  observability, backup, exposure and update verification; the five historical
  command names remain compatible.
- Fail-closed duplicate-identifier detection for the Architecture Project
  Understanding dossier checker, with direct positive and negative tests.
- A current predecessor-independence guard that rejects active Pantheon-OS
  remotes, checkout paths, environment variables and vendored snapshots.
- A reusable runtime-boundary language guard extracted from GitHub Actions YAML.

### Changed

- The governance read path and roadmap now prioritize current status, ownership,
  blockers and exit criteria instead of repeating document inventories.
- `base_metier/architecte/` is explicitly qualified as an external professional
  corpus and adapter proving area, not an internal Pantheon RAG or runtime.
- Active governance documents use `Register Candidate` and `Registre Probatoire
  entry` where the governed record is meant, while Hermès retains runtime-memory
  ownership.
- AI intervention logs are limited to one durable trace per coherent material PR;
  mechanical corrections do not require an autonomous log.
- Governance CI no longer maintains completed-migration bookkeeping. It checks
  the present invariant that Pantheon Next is independent from its predecessor.
- `VERSION`, this changelog head and MCP package metadata advance together to
  `0.1.63`; the repository root remains deliberately non-distributable.

### Fixed

- Duplicate APU identifiers can no longer overwrite an earlier declaration
  silently in the dossier-wide reference index.
- Update evidence now uses the same schema-backed fail-closed validation path as
  install, observability, backup and exposure evidence.
- The large inline runtime-language program and two migration-era assertions were
  removed from the active workflow without removing current governance, APU, MCP,
  root-test or packaging checks.

### Validation posture

Each consolidation PR was refreshed onto the successive `main` state and passed
Governance CI plus Obsolete Authority Consistency before squash merge. The final
CI rewrite validated itself, including root tests, APU referential integrity,
MCP unit/end-to-end tests, wheel construction and clean-install metadata checks.

### Boundary clarification

No live runtime inventory, network probe, installer, scheduler, queue, provider
router, plugin manager, external action, update execution, automatic approval or
automatic register admission is introduced.

```text
installed != approved
healthy != safe
update_available != update_authorized
runtime_success != evidence
binding_selected != dependency_adopted
checkpoint recorded != tag published
```

### Earlier entries

- Versions `0.1.42` through `0.1.62` remain preserved in the immutable parent
  snapshot [`cc927ec:CHANGELOG.md`](https://github.com/ifanjuang/Pantheon-Next/blob/cc927ec93191e1fbbec148c1971714e89ba27488/CHANGELOG.md).
