# Architecture Source Policy

Status: candidate support doctrine — architecture_fr source policy.  
Repository state: documented non-implemented.  
Domain pack target: `architecture_fr`.  
Origin: distillation from `HISTORICAL_ARCHITECTURE_RECONCILIATION.md` after PR Pantheon-Next#151.
Boundary profile: candidate_support_note.

This document defines how sources enter, constrain and support architecture-domain work in Pantheon Next.

It does not validate any source by itself.

It does not create a retrieval runtime, RAG system, web crawler, vector database, OpenWebUI Knowledge configuration, Hermes skill, regulatory checker, evidence engine, memory engine, approval engine or external action.

## Purpose

Architecture work carries professional, contractual, regulatory and liability consequences.

A fluent answer with the wrong version of a rule, the wrong project document, the wrong site constraint or the wrong technical assumption can become dangerous if it is treated as usable truth.

This policy defines how `architecture_fr` treats sources before they can support:

```text
project facts
regulatory statements
technical statements
cost or scope statements
client-facing drafts
contractor-facing drafts
authority-facing drafts
insurance or dispute-facing material
Register Candidates
Evidence Pack Candidates
```

## Scope

This policy covers the French architecture practice domain first.

It applies to professional architecture-agency work such as:

```text
urban planning and permit review
PLU / SPR / ABF / servitude analysis
ERP and accessibility questions
fire-safety and SDIS-facing material
RE2020 / energy / renovation framing
CCTP / DPGF / CCAP / devis review
BET / geotechnical / bureau de contrôle coordination
site, chantier, reservations, claims and reception material
client / contractor / authority / insurer communication drafts
```

It is a policy for source treatment.

It is not legal advice, architectural validation, engineering validation, code compliance certification, insurance advice or administrative authorization.

## Core rule

```text
A source is not proof because it was found.
A source becomes usable only when its authority, date, scope, version and relation to the task are explicit.
```

The minimum safe sequence is:

```text
search result or uploaded item
-> source lead
-> opened / read / inspected source
-> source candidate
-> evidence item candidate
-> Evidence Pack Candidate
-> human review / decision / approval if consequential
```

A search result snippet, RAG chunk, OCR extract, model recollection, pasted quote or connector preview must not be treated as final evidence.

## Source states

Architecture work must distinguish the following states.

| State | Meaning | May support a conclusion? |
|---|---|---|
| `source_lead` | A possible source was found or mentioned. | No. |
| `source_candidate` | The source was opened, read or inspected enough to identify content, date, scope and authority. | Only cautiously. |
| `evidence_item_candidate` | A specific passage, figure, drawing, decision, clause or observation has been selected and bounded. | Yes, as candidate support. |
| `evidence_pack_candidate` | Multiple evidence items are assembled with tensions, assumptions and missing pieces. | Yes, pending review. |
| `validated_evidence` | The professional has reviewed and accepted it within scope. | Yes, within the validated scope only. |

Transport success is not source validation.

A connector successfully returning a document only proves access to that document. It does not prove that the document is current, authoritative or applicable.

## Source authority classes

These classes are domain-policy labels.

They do not replace the general Pantheon axes for consequence, approval, memory or evidence.

### S0 — Project-controlled validated source

Examples:

```text
signed contract
validated client instruction
approved programme
validated plan revision
signed meeting minutes
permit decision or formal authority correspondence
approved estimate or market document
survey / bornage / geotechnical report / BET report attached to the project
site report issued under the project perimeter
```

Use:

```text
primary for project facts and project scope
primary for what was decided in the project
primary for chronology when dated and traceable
```

Limits:

```text
may be superseded by a later project revision
may not override regulation
may not validate technical matters outside its author scope
```

Rule:

```text
Latest validated project source wins for project facts, unless a contradiction or supersession is unresolved.
```

### S1 — Official statutory or regulatory source

Examples:

```text
Code de l'urbanisme
Code de la construction et de l'habitation
Code du patrimoine
Code de l'environnement
Legifrance official text
Service-public official explanatory page
official local planning document when published by the competent authority
formal administrative decision
prefecture / ministry / competent authority publication
```

Use:

```text
primary for legal or regulatory framing
mandatory for consequential regulatory claims
```

Limits:

```text
must be current or explicitly dated
must be checked against local or project-specific rules when relevant
may require legal, administrative or specialist interpretation
```

Rule:

```text
No consequential regulatory statement may rely only on memory or a secondary summary when an official source should exist.
```

### S2 — Local authority, local planning and instruction source

Examples:

```text
PLU / PLUi / règlement graphique / règlement écrit
SPR / PSMV / AVAP / heritage perimeter material
ABF opinion or exchange
urbanisme service email or instruction note
SDIS or accessibility service exchange
DDT / mairie / métropole / instruction-platform item
```

Use:

```text
primary for local applicability and instruction context
stronger than generic national summaries for local constraints
```

Limits:

```text
must identify locality, zone, parcel, perimeter, date and version
informal exchange is not equivalent to formal decision
local interpretation can conflict with later formal instruction
```

Rule:

```text
Local project constraints require local-source identification, not only generic rule recall.
```

### S3 — Normative, technical and professional source

Examples:

```text
DTU / NF / Eurocodes / rules of art
CSTB or professional technical publications
Ordre des architectes guidance
MAF guidance
bureau de contrôle doctrine or checklist
manufacturer technical documentation
product certification and declaration documents
```

Use:

```text
support for technical framing
support for professional-responsibility framing
support for risk identification and questions to specialists
```

Limits:

```text
may be paywalled, copyrighted, partial or context-specific
manufacturer documentation supports product claims, not general compliance
professional guidance is not automatically law
technical validation may require BET, bureau de contrôle or enterprise note
```

Rule:

```text
Technical sources may frame a question or risk, but they do not replace specialist calculation, execution design, product-specific certification or professional validation.
```

### S4 — Specialist project source

Examples:

```text
BET structure note
geotechnical report
thermal study
acoustic study
fluid or fire-safety note
surveyor report
asbestos / lead / diagnostic report
enterprise execution detail or note de calcul
```

Use:

```text
primary inside the author's discipline and stated scope
strong support for technical assumptions in project work
```

Limits:

```text
valid only within date, scope, hypothesis and mission limits
may conflict with architecture, client, site or regulatory constraints
must not be generalized beyond the report
```

Rule:

```text
A specialist source is authoritative only inside its mission perimeter.
```

### S5 — Secondary, contextual or illustrative source

Examples:

```text
blog article
forum or social media post
commercial explainer
AI-generated summary
undated checklist
training note without source trail
non-official synthesis
```

Use:

```text
orientation
vocabulary aid
lead to a better source
non-consequential context
```

Limits:

```text
not sufficient for regulatory, contractual, financial or liability-sensitive claims
not sufficient for source-of-truth project facts
```

Rule:

```text
Secondary sources may help find the right question. They do not close the question.
```

## Consultation policy — project vault, professional library and LLM wiki

Choose sources according to the question, **not a mandatory sequence of searches**. This specializes the existing `SOURCE_INGESTION_RETRIEVAL_MODEL.md` and `KNOWLEDGE_TAXONOMY.md`; those owners retain source identity, provenance, retrieval and Knowledge status rules.

| Question | Useful first source | When to expand |
|---|---|---|
| Project facts or chronology | Admitted project vault original, including its current revision | Conflicting project sources or missing decision history |
| Professional method or general explanation | Existing Knowledge note/wiki, or professional reference library | Applicable technical or contractual claim requires inspecting the underlying original |
| Regulatory or DTU applicability | Current official text or admitted complete standard/edition | Local applicability, supersession, project-specific constraints |
| Project tested against a rule | Both project source and professional reference | Material missing assumptions or conflicting sources |

The **LLM wiki** is a navigable/editorial view of **existing Knowledge Items**, not a new source-of-truth database or a mandatory mirror of original PDFs. A generated note can aid discovery with its current review status; conclusions that depend materially on its content should inspect the cited sources.

Use exact reads before broad retrieval when an admitted source is already known. Hindsight/memory may locate a source but does not validate it. Expand consultation when the stakes, missing context or contradictions justify it; a simple orientation answer need not open every reference.

Source changes may feed the existing Knowledge revision/recompile proposal path (Pantheon-Next#1121); they do not silently rewrite notes. No extra wiki index, source graph, or automatic publication authority is created. Agency-specific vault names and bindings are supplied externally, not mandated by this domain policy.

## Fetch-before-cite rule

```text
Search result = lead.
Opened source = candidate.
Selected passage = evidence item candidate.
Evidence Pack = trace.
Human validation = usable professional status.
```

A result must not cite or rely on a source unless the relevant source content was actually opened, read, inspected or extracted.

For PDFs, scans, drawings, tables, maps and figures, the evidence must identify the inspected page, sheet, view, extract, drawing reference or figure.

For retrieved web material, the result must identify:

```text
source title
publisher or authority
URL or connector reference
date published / date accessed / date of document when available
version or update signal when available
relevant passage or section
task relation
```

For project files, the result must identify:

```text
project name or dossier scope
document title
revision index or date
issuer / author
validated / draft / received / superseded status when known
specific page, sheet, clause or section
```

## Freshness and supersession

Architecture sources have different freshness behavior.

| Source family | Freshness rule |
|---|---|
| Official regulations | Use current official source or explicitly state date uncertainty. |
| PLU / local planning | Check local document version, zone, parcel and date. |
| Project plans | Latest validated revision wins; old revisions become history. |
| Client instructions | Latest explicit validated instruction wins; ambiguous informal instructions remain to verify. |
| BET / specialist reports | Valid inside mission, date and assumptions; newer reports or revisions supersede older ones. |
| Product documentation | Check product reference, certification and current manufacturer data. |
| Cost data | Treat as volatile; date and source quality must be explicit. |
| Case law / administrative doctrine | Treat as specialist or legal-sensitive; do not overstate without qualified review. |

When freshness cannot be checked, the output status must be at least:

```text
to_verify
```

If the source is likely obsolete, superseded or version-conflicted, the result must expose that as a tension, not smooth it into a confident answer.

## Project-source priority

For project facts, project-controlled sources outrank generic sources.

Examples:

```text
A validated plan outranks a generic assumption about surface.
A signed meeting minute outranks an inferred client intention.
A formal permit decision outranks a remembered instruction timeline.
A bornage or surveyor source outranks a visual assumption about boundary.
A BET note outranks a generic structural intuition inside the BET scope.
```

But project sources do not override external constraints.

Examples:

```text
A client instruction does not override planning rules.
A contractor claim does not override contract scope by itself.
A sketch does not override a formal permit if they conflict.
A generic product datasheet does not override project-specific execution limits.
```

If project-source priority and external-rule priority conflict, the answer must classify the tension.

## Claim types and minimum source support

| Claim type | Minimum support |
|---|---|
| Project fact | S0 or S4 when technical; otherwise explicitly marked assumption. |
| Regulatory claim | S1 plus S2 when local applicability matters. |
| Local planning claim | S2 with zone, parcel, date and version when available. |
| Technical claim | S3 or S4; consequential validation stays with specialist/professional. |
| Cost claim | dated source, scope and uncertainty range; never timeless truth. |
| External communication | source-backed draft plus status and approval gate. |
| Insurance / dispute chronology | dated project records and explicit uncertainty. |
| Memory / Register Candidate | Evidence Pack Candidate and explicit scope. |

## Contradiction handling

The system must surface contradictions such as:

```text
old PLU versus current PLU
client instruction versus signed contract
contractor statement versus CCTP
plan revision conflict
BET assumption versus architect design intent
informal urbanisme exchange versus formal decision
estimated cost versus market quote
OCR text versus visual drawing content
RAG chunk from old source versus newer source
```

Contradiction handling rule:

```text
Do not blend contradictions into one fluent answer.
Name the tension, identify the competing sources, and mark the result to_verify or to_arbitrate.
```

## Evidence Pack expectation

Any consequential architecture-domain output should carry an Evidence Pack Candidate or state why one is missing.

Minimum Evidence Pack Candidate fields:

```text
claim_or_output_id
source_refs
source_authority_classes
source_dates
source_versions_or_revision_refs
selected_passages_or_locations
assumptions
unknowns
contradictions
freshness_status
scope_limit
recommended_status
approval_need
```

The Evidence Pack Candidate must not claim validation.

It supports review.

## Output status discipline

Source quality affects output status.

| Source condition | Minimum output status |
|---|---|
| No source, only model memory | `draft_assumption` or refuse if consequential. |
| Secondary source only | `orientation_only` or `to_verify`. |
| Official source opened, local applicability unknown | `to_verify`. |
| Project source opened, revision unclear | `to_verify`. |
| Conflicting sources | `to_arbitrate`. |
| Fresh official + local + project evidence aligned | `candidate_for_professional_review`. |
| Human validated within scope | `validated_with_scope`. |

No source condition makes the AI the final professional authority.

## External communication rule

Drafts to clients, contractors, BET, authorities, insurers, experts or legal-facing recipients must carry a source status and approval gate when the content may bind the architect.

Default behavior:

```text
Hermes may draft.
Pantheon governs status, evidence expectation and approval.
The professional decides, signs and sends.
```

External communication should be at least C4 when it contains:

```text
regulatory interpretation
technical validation wording
financial commitment
contractual position
liability-sensitive chronology
instruction to a contractor
response to authority
insurance or dispute material
```

## Forbidden collapses

```text
search result = evidence
RAG chunk = proof
source exists = source applies
old source + new source = combined truth
project document = current document
official source = project-specific conclusion
technical source = execution validation
manufacturer page = compliance guarantee
model confidence = certainty
connector access = source validation
Evidence Pack Candidate = professional approval
```

## Safe fallback

When the source basis is insufficient, the correct behavior is:

```text
state what is known
state what is missing
state the consequence of the missing source
name the source type needed
keep the output as draft / to_verify / to_arbitrate
avoid external-action wording
```

Typical fallback wording:

```text
The available sources do not allow a reliable conclusion at this stage.
The result should remain a draft assumption until the current source is checked.
```

## Relationship to the future architecture domain pack

This document is intended to feed the future `DOMAIN_PACK_SPEC.md` section:

```text
3. Source policy
4. Evidence expectations
5. Risk triggers
7. Output statuses and delivery gates
10. Review angles and decision gates
```

When the full domain pack is created, this document should either:

```text
be folded into that pack, or
remain as a supporting source-policy document referenced by it.
```

That decision remains to arbitrate.

## Boundary

This document does not modify:

```text
schemas/
tests/
operations/
platform/
Docker files
.env files
pyproject.toml
CLAUDE.md
```

It does not implement anything.

It does not create an OpenWebUI Knowledge configuration.

It does not create a Hermes skill.

It does not define an automatic evidence validator.

It defines source-treatment discipline for architecture-domain work.

## Final rule

```text
The database may record.
The workflow may propose.
The evidence may support.
The approval may validate.
The architect decides.
```
