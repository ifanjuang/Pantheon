# Obsidian / Hindsight Historical Reference Implementation

Status: historically qualified optional reference — not the selected productive AFFAIRES topology and not a Pantheon architecture owner, dependency or mandatory binding.

Authority note: generic memory selection remains owned by `HERMES_CAPABILITY_BINDINGS.md` and the machine-checkable `catalog/bindings/external-runtime-memory-unbound.yaml`. Generic source, Knowledge, Evidence and Project identities remain owned by their existing Pantheon contracts.

Qualification record: Pantheon-Next #655, Pantheon-Next#659, Pantheon-Next#660, Pantheon-Next#714 and merged qualification slices including Pantheon-Next#703, Pantheon-Next#725 and Pantheon-Next#726.

## Purpose

Preserve the demonstrated Obsidian / synchronization / retrieval composition as historical capability evidence without turning those products into Pantheon prerequisites or the current AFFAIRES target.

```text
Obsidian / Markdown
-> Self-hosted LiveSync / CouchDB
-> filesystem vault mirror
-> hindsight-obsidian-sync
-> Hindsight
-> bounded Hermes consumers
```

This composition has real qualification evidence and working regression coverage. The selected professional AFFAIRES route now uses the direct NAS-mounted Workspace topology owned by `docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md`; Pantheon-Next#660 and Pantheon-Next#659 track its remaining operational qualification.

A user may instead use Hermes-native context/files/memory only, another note workspace, another synchronization mechanism, another retrieval engine or another memory provider when the same boundaries are preserved.

```text
recommended reference != mandatory dependency
working and qualified != architecture authority
```

## Responsibility split

```text
Markdown workspace
= human-authored working material

synchronization transport
= convergence between representations

filesystem mirror
= synchronized file representation

Hindsight
= derived retrieval / associative memory in this reference profile

Hermes
= runtime consumption, reasoning and candidate generation

Pantheon
= governed identity, provenance, Evidence, authorization and durable professional status
```

```text
workspace != governed Project
folder != governed identity
sync success != professional approval
retrieved != truth
memory != Evidence
```

## Qualified observations

The repository has demonstrated, with bounded synthetic qualification:

- Self-hosted LiveSync CLI materialization through CouchDB into a filesystem vault;
- create/edit/rename/delete convergence in the qualified headless daemon composition;
- Hermes filesystem read/create/anchored-patch compatibility against a bounded vault;
- Hermes-originated file changes converging through LiveSync in the synthetic Q3 path;
- `hindsight-obsidian-sync` as a separate producer from Hermes runtime writes;
- Hindsight recall through Hermes with source/path provenance in the Q5 separation test;
- Hindsight bank isolation and bounded read surfaces in the Pantheon-Next#655 qualification campaign.

These observations prove compatibility for the tested revisions only.

```text
qualification proof != production adoption
runtime success != authorization
bank isolation != access control
```

## Qualified synchronization topology

The working Pantheon-Next#703 topology is preserved as part of this reference recommendation:

```text
native Obsidian clients
        |
        | Self-hosted LiveSync
        v
CouchDB synchronization state
        |
        | one long-running Self-hosted LiveSync CLI daemon
        v
dedicated local LiveSync DB
        |
        v
dedicated filesystem vault mirror
        |
        | designated hindsight-obsidian-sync producer
        v
Hindsight
```

The qualified daemon seam used the reviewed Self-hosted LiveSync `1.0.18` release line (`self-hosted-livesync-cli` `1.0.18-cli`). It demonstrated create, edit, rename-as-delete+create and delete convergence with distinct daemon database and filesystem-vault paths.

The repeated one-shot `sync` + `mirror` composition was explicitly rejected after it left a stale path during rename. The demonstrated durable topology therefore uses one long-running daemon per mirror rather than polling unrelated one-shot commands.

Obsidian Web/Docker is not part of the synchronization or ingestion chain. Obsidian Web remains optional UI only and must not become a second filesystem writer, synchronization owner or Hindsight producer.

The preserved regression invariants are:

```text
external_runtime_memory.preferred_binding = unbound
synchronization qualified != Hindsight ingestion authorized
filesystem materialized != Evidence
vault path != governed identity
optional UI != infrastructure owner
```

Those are behavioral constraints of the qualified reference, not requirements that every replacement provider use CouchDB, LiveSync, banks or filesystem mirrors.

## Current reference topology

The qualified agency reference used trust-domain banks rather than one bank per project:

```text
agency
agency-projects
agency-sandbox
```

Project/folder tags were used for narrower retrieval scope.

That topology is a provider-specific implementation choice, not a Pantheon identity model.

```text
bank != Project
folder/tag != Pantheon scope authority
```

Other providers may express isolation through namespaces, collections, tenants, stores or different mechanisms.

## Source rule

Original professional material keeps its existing source identity.

Examples:

```text
PDF -> source/document owner
email -> source/message owner
photo -> source/image owner
model -> source representation owner
Markdown note -> workspace source note when intentionally authored
```

Hindsight in this reference implementation is a derivative index/memory, not the canonical store for professional source bytes.

## Retrieval rule

Retrieval should remain bounded by the active task/source scope.

The reference Hindsight profile used strict bank/tag/folder constraints to prevent silent cross-project widening. A replacement retrieval engine must preserve the same behavioral invariant even if its API is different.

```text
specific target
-> bounded retrieval inside authorized scope
-> explicit widening only when requested/authorized
```

## Producer rule

The qualified durable-workspace path separates file mutation from Hindsight ingestion:

```text
Hermes or human edits source Markdown
!= direct durable Hindsight write

source Markdown
-> designated ingestion producer
-> derived Hindsight state
```

The Q5 qualification specifically demonstrated that Hermes file writes did not appear in Hindsight until the designated `hindsight-obsidian-sync` reconcile step ran.

That separation remains useful qualification evidence because it keeps the workspace source and the derived retrieval/memory index legible. The productive AFFAIRES route now preserves the same authority distinction through one direct-NAS Workspace producer instead of this LiveSync path. A replacement stack must avoid ambiguous concurrent authorities.

## Hermes-native alternative

No external workspace/retrieval stack is required when Hermes-native facilities are sufficient.

Current Hermes can use:

```text
project/context files
explicit file/folder references
MEMORY.md / USER.md
session history/search
```

Those facilities remain Hermes runtime state/context. They do not become Pantheon Evidence or governed Knowledge automatically.

Choosing another path does not erase the historical qualification evidence of this Obsidian/Hindsight stack. For professional AFFAIRES, however, the direct NAS route has superseded it as the selected productive topology.

## Optional Hermes Obsidian skill and second-brain behavior

An Obsidian skill exposed to Hermes is a runtime operation surface for reading, searching and preparing writes against a Markdown workspace. A second-brain package is a richer optional behavior profile for recall, linking, synthesis, health checks and knowledge maintenance. Neither is a Pantheon prerequisite, workspace owner, memory authority or manifest authority.

The reviewed external `eugeniughelbur/obsidian-second-brain` project advertises a Hermes adapter and an optional Obsidian MCP access path. This is a compatibility signal only. Pantheon has not adopted, installed or qualified that package through this document.

If such a package is selected, the intended layering is:

```text
Hermes Obsidian capability
= bounded workspace access and candidate operations

optional second-brain behavior
= knowledge recall, links, synthesis and vault-health assistance

Pantheon workspace/manifest owners
= identity, manifestability, provenance, approval and consequential-write rules
```

The workspace remains usable without either layer. Existing folder organization remains valid, and a selected skill must discover and respect workspace-local conventions rather than bootstrap or impose its own folder map, frontmatter schema or propagation rules.

Second-brain behavior may operate more freely only inside an explicitly designated, reconstructible knowledge area. Its upstream-style automatic rewriting, cross-note propagation, contradiction reconciliation or proactive saving must not silently touch professional source material, admitted Evidence, governed status, document identity or other consequential records.

### Minimal maintenance behavior

When selected, the optional second-brain profile should prefer maintenance of existing knowledge over note proliferation.

```text
search-before-create

durable information candidate
-> search relevant notes inside the authorized workspace scope
-> patch / enrich / link the natural existing note when one exists
-> create a new note only when no suitable existing note exists
```

This is workspace behavior, not a new Pantheon Knowledge object or lifecycle. Search remains bounded by the active task/context scope. It does not introduce a note-per-concept topology, fixed folder layout, frontmatter schema or automatic propagation rule.

Conversation consolidation is explicit by default. An instruction such as `consolidate this discussion`, `add this to the workspace knowledge`, `update our notes on this topic`, or equivalent unambiguous workspace-persistence intent may turn only the durable delta of the conversation into workspace edits:

```text
conversation / Result Candidate
-> select durable delta only
-> search existing notes
-> patch / enrich / link existing notes
-> create a new note only if needed
```

Ambiguous retention wording such as `keep this` or `remember this` does not by itself select workspace persistence. The intended destination must be resolved before a durable workspace write.

Consolidation is not transcript export and does not make the conversation, summary or workspace note Evidence, canonical memory, approved professional status or source truth. A second-brain profile may suggest consolidation, but must not silently persist ordinary conversation material or treat repeated recall as promotion.

For manifests, the boundary is narrower:

```text
discover / read / lint manifest          = allowed bounded assistance
propose manifest creation or correction  = candidate only
define manifest semantics                = existing Pantheon owner
silently mutate manifest or move files   = forbidden
```

`docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md` owns the candidate manifest UX and local health posture. A second-brain package may consume that contract; it does not replace it. A missing manifest remains neutral unless an explicit qualification rule requires one.

### Distilled maintenance patterns without a parallel knowledge system

The reviewed external `Ar9av/obsidian-wiki` project demonstrates additional useful maintenance patterns, including staged writes, source-delta tracking, statement provenance labels and whole-vault equilibrium checks. Pantheon does not adopt or install that package through this document.

Most of those responsibilities are already owned elsewhere in Pantheon and must not be duplicated here. Reusable Knowledge already has visible `generated_unreviewed`, `needs_review`, `reviewed` and `superseded` states, exact optimistic versions, idempotent write semantics, source references and digests. The workspace-manifest candidate already owns manifestability and local package health. Hindsight already owns derived retrieval in this reference profile.

Therefore an optional Obsidian behavior must not import `_staging`, `.manifest.json`, a trust ledger, a required frontmatter lifecycle or a second retrieval index as Pantheon requirements.

```text
upstream staging directory != Pantheon review owner
upstream manifest != governed workspace identity
upstream trust ledger != Evidence or approval authority
upstream lifecycle != Pantheon Knowledge lifecycle
upstream graph query != replacement for bounded Hindsight retrieval
```

Two patterns remain useful because they add behavior without adding authority.

First, a **report-only workspace audit** may inspect the authorized knowledge area for candidate duplicate notes, unresolved or malformed wikilinks/embeds, stale summaries or source references, contradictory statements, orphaned material and useful missing cross-links. Its default output is findings only. It must not auto-fix, rename, merge, archive, relink or rewrite professional material. Any accepted correction follows the existing write posture and exact task scope.

```text
audit finding != defect confirmed
audit clean != professionally current
duplicate candidate != merge authorization
contradiction candidate != source adjudication
link repair candidate != filesystem mutation authority
```

A later maintenance pass may compare report-only results across the relevant checks and state that no checked maintenance action is currently proposed. That local equilibrium is a workspace-health observation only; it is not truth, review completion, Evidence admission or authorization.

Second, narrative workspace material may expose lightweight statement posture such as `extracted`, `inferred` or `ambiguous` when this improves human legibility. These are descriptive annotations only. They do not introduce a new Pantheon provenance schema, Claim status, Evidence class, lifecycle or confidence authority. Where an existing Pantheon contract already carries source/provenance or claim semantics, the existing owner must be consumed rather than mirrored in frontmatter.

```text
extracted annotation != source truth
inferred annotation != accepted Claim
ambiguous annotation != governed conflict state
workspace annotation != Evidence provenance owner
```

These patterns intentionally stop short of automatic contradiction reconciliation or whole-vault rewriting. The current external `obsidian-wiki` implementation also has open edge cases around reserved staging paths and Obsidian link forms; that reinforces the Pantheon posture that maintenance starts as report-only and professional writes remain bounded by existing owners.

This preserves a small default:

```text
Hermes-native files/context
-> optional Obsidian workspace capability
-> optional second-brain behavior
-> optional report-only maintenance
-> optional Hindsight-derived recall
```

Each layer is independently optional. Installing one does not authorize or require the next.

## Optional Obsidian authoring and document-assembly UX

Obsidian plugins may also provide local authoring ergonomics without becoming part of the workspace, memory or governance architecture. The reviewed external `Sadsnake1/word-smith` plugin is classified in this category only.

Its useful patterns include focused writing, manuscript/document organization, preview and compilation/export. These capabilities may improve human authoring of Markdown material and can inform future document-assembly UX, but Pantheon does not adopt, install, bind or qualify Word-Smith through this document.

```text
Word-Smith
= optional Obsidian authoring / document-assembly UX

Word-Smith
!= Pantheon architecture owner
!= document identity or professional-status owner
!= Evidence producer
!= memory / retrieval provider
!= synchronization owner
```

Word-Smith-local structure, ordering, flags, goals or history remain plugin/workspace state. In particular, `ws-structure.md` must not become authority for Pantheon document identity, governed order, applicability, approval or status. A successful local export similarly does not establish professional approval or Evidence.

```text
plugin organization != governed document structure
plugin metadata != Pantheon authority
export success != professional approval
```

The intended layering is therefore:

```text
Pantheon governance / document contracts
-> Markdown workspace
-> optional Obsidian authoring UX such as Word-Smith
```

The plugin remains replaceable. No Word-Smith-specific schema, registry binding, storage layer or runtime component should be introduced unless a later demonstrated requirement cannot be satisfied through existing document/workspace contracts.

## Hindsight posture

Hindsight is the currently recommended external retrieval/memory provider because the repository contains real integration and separation tests for it.

It is not mandatory.

The `external_runtime_memory` Capability Binding remains `unbound` unless a separate selection decision changes it. Hermes native memory can remain the only runtime memory.

If Hindsight is selected for both workspace retrieval and runtime memory, those responsibilities must remain scoped distinctly rather than being collapsed merely because one product can serve both.

## Security and production gaps

Historical qualification observed limitations including unauthenticated Hindsight API/MCP exposure on the tested LAN path. Pantheon-Next#659 retains the hardening/operational qualification work for that specific deployment.

Those gaps matter when this reference implementation is selected. They are not Pantheon-wide infrastructure requirements.

## Replacement rule

A replacement workspace, sync layer, retrieval engine or memory provider is acceptable when it preserves the relevant contracts:

```text
source provenance remains visible
scope does not silently widen
runtime state does not become Evidence
a provider write does not become authorization
projection does not become persistence
folder/provider namespace does not become governed identity
```

Do not reproduce Obsidian/Hindsight-specific bank, tag or folder conventions in generic Pantheon contracts.

## Final classification

```text
Obsidian                 = historically qualified optional workspace; not selected AFFAIRES route
Self-hosted LiveSync     = historically qualified optional synchronization path
CouchDB                  = synchronization state in that historical reference
filesystem mirror        = historical qualified materialization pattern; not selected AFFAIRES route
hindsight-obsidian-sync  = historical designated producer for this reference only
Hindsight                = selected derived retrieval/memory candidate; live AFFAIRES qualification remains open
Hermes native facilities = valid zero-extra-provider alternative
Hermes Obsidian skill    = optional runtime workspace capability
second-brain behavior    = optional knowledge-maintenance profile, subordinate to workspace governance
Word-Smith               = optional Obsidian authoring / document-assembly UX
Pantheon                 = provider-agnostic governance boundary
```

This file preserves what has been demonstrated by the earlier composition. It remains useful as optional capability evidence and replacement criteria, while the direct NAS AFFAIRES topology is the selected productive target.
