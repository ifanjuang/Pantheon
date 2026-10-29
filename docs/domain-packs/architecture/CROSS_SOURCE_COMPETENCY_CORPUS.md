# Cross-source project comprehension — competency corpus (candidate)

Status: candidate test design, not executed acceptance and not project truth.
Scope: architecture practice, multiple sources, change and dependency reasoning.
Baseline: Pantheon main at `6a8945547e2c20f35b13a0f293180042d1c3a26f` (2026-10-28).
Parallel work: PR #62 proposes `architecture@1` relation vocabulary. Do not duplicate it.

## Goal

Test whether a bounded Hermes context slice can answer practical questions that span
documents, project anatomy, dates, discussions, construction sequencing, requirements,
costs and decisions. The examples are *synthetic reconstructions of question patterns*
encountered in architectural practice, not imported client records or verified project
facts. Names, amounts, dates and sources below are invented fixtures unless stated as
general methodology. Never promote these fixtures to agency knowledge.

Use existing `stable_object`, `source_representation`, `attribute_claim`,
`relation_claim` and `requirement`; preserve existing Revision Set, Observation
Bundle, WorkIssue, Decision Request and authorization owners. Do not introduce a
fifth Project Anatomy primitive, second graph, planning engine or approval engine.
Physical and contractual states are distinct.

## Acceptance format for every case

Input: exact source artifacts with digest/revision, locator, issue/receipt dates,
coverage and an explicit question. Fixture facts may conflict.

Expected: (a) identify the project-scoped subject; (b) cite each material assertion
to exact source/version/locator; (c) distinguish observation, proposal, instruction,
decision, requirement and inference; (d) show dependency chain and unresolved
preconditions; (e) answer as of a specified business date and knowledge date when
relevant; (f) return a bounded answer, unknowns and proposed checks, without
automatic write or professional approval.

Negative checks: never infer approval from an email's receipt, actual execution
from a schedule, verification from installation, liability from delay, payment
entitlement from quantity, identity from a matching label, or absence from an
incomplete source.

## Cases and competency questions

### C01 — Trade sequencing under a missing subcontractor

Fixture sources: baseline schedule P1, CCTP facade and joinery clauses, weekly site
minutes M1, email from facade contractor E1. M1 records the facade contractor absent
this week; joinery installation is separately scheduled. Dependency statements in
the CCTP distinguish the *particular* facade/joinery interfaces from unrelated work.

Questions:
- Which joinery operations can advance while the facade contractor is absent?
- What prerequisites are explicitly documented, and which are only assumptions?
- Which dates are forecasts, commitments or observed completions?

Pass: returns a conditional, per-operation replan rather than declaring that all
joinery must wait for all facade work. Does not change the authoritative schedule.

### C02 — Delay and contractual responsibility

Fixture sources: schedule index E, site minutes M2 showing incomplete roofing on a
later inspection date, contract clause K1 about penalties, and letters L1/L2 with
disputed causes of delay.

Questions:
- What is the measured difference between planned and observed milestones?
- Which other tasks may be affected through *documented* prerequisites?
- Can contractual penalties or responsibility already be concluded?

Pass: separates measured slippage from causation, critical path, applicable
contractual provisions and professional/legal determination. No penalty amount is
calculated without the complete contractual basis.

### C03 — Revised opening and supplier order

Fixture sources: drawing Revision Set B (opening width 1800 mm), meeting request R1
(2100 mm proposed), structural note S1 (lintel verification required), drawing
Revision Set C (2100 mm drawn), joinery order O1 (1800 mm ordered), and Decision
Request D1 (pending).

Questions:
- What changed between B and C for the same governed opening?
- Is the 2100 mm dimension approved, merely drawn or still conditional?
- What must be checked before asserting the planned installation date remains valid?

Pass: tracks same-object alignment and supersession with provenance, separates
drawing change from decision, flags structural review and supplier order mismatch.
No invented authorization to amend an order.

### C04 — Buried tank discovered during earthworks

Fixture sources: site observation O2 with dimensions marked approximate, geotechnical
note G1, structural engineer request S2, contractor quote Q1 and schedule P2.

Questions:
- What is known about the buried object and its effect on foundations?
- Which studies or decisions are prerequisites to filling/removal?
- What could change in costs and schedule?

Pass: keeps observed dimensions approximate, identifies structural/geotechnical
unknowns, and distinguishes priced proposal from authorized work.

### C05 — Stormwater design and unlocated equipment

Fixture sources: site plan revision A showing a rainwater tank, hydraulic study H1
with conditional discharge assumption, DCE CCTP V1, and later site-plan revision B
where an EV charging point is labelled but not dimensioned.

Questions:
- Which rainwater routing details are unresolved for the tender documents?
- Can the charging point's location be treated as fixed?
- Which plan/CCTP inconsistencies need resolution before consultation?

Pass: identifies unlocated equipment, missing distances, levels and outlet evidence;
does not infer precise coordinates from a text label or convert a study assumption
into a final design decision.

### C06 — Permit, protected context and scope changes

Fixture sources: initial permit drawings, administrative decision A1, heritage
consultation correspondence H2, revised design sketch and municipal response M3.
The administrative record includes separate statuses for proposed openings, roof
works and a later extension.

Questions:
- Which changes are covered by the current authorization?
- Which elements are still proposals requiring regulatory verification?
- What documents support the answer, and what remains undecidable?

Pass: separates planning permission, heritage consultation and project intent;
does not infer that a protected perimeter automatically implies the same procedure
for every change, or that a consultation equals authorization.

### C07 — Work completion, reservations and payment

Fixture sources: CCTP, site minutes M4, contractor situation S3, partial completion
photographs, reserve list R2, variation quote Q2 and signed order V2.

Questions:
- What work is contractually due, claimed complete, observed, verified and received?
- Which variations are approved, disputed or only quoted?
- Which financial conclusions require additional contract or payment records?

Pass: does not equate a photograph with complete execution, a submitted situation
with payable quantity, or receipt with reservation-free status.

### C08 — Discussion to decision and accountable follow-up

Fixture sources: technical meeting transcript T1, email E4 correcting one
participant's interpretation, minutes draft M5, published minutes M6, Decision
Request D2 and subsequent design note N1.

Questions:
- What was discussed, proposed, objected to and formally decided?
- Which points require owner, due date or confirmation?
- Does a published minute or absence of reply establish acceptance here?

Pass: preserves contradictory statements and exact temporal sequence; applies only
documented contractual approval rules; proposes a Decision Request or WorkIssue
without silently writing one.

### C09 — Technical assembly and downstream interfaces

Fixture sources: wall section A, thermal note TH1, facade CCTP C1, window schedule
W1 and detail revision B increasing insulation thickness.

Questions:
- Which junctions and usable dimensions may be affected?
- What is explicitly verified versus requiring a thermal/structural/detail check?
- Which trades and documents should be reviewed?

Pass: identifies likely interfaces (window reveals, thresholds, fixings, finish)
without claiming geometric clashes or regulatory noncompliance absent measurements.

### C10 — Reception chronology versus physical reality

Fixture sources: programme milestone P3, site report M7, ventilation test V3,
punch-list R3 and reception record A3 with reservations.

Questions:
- What was planned, installed, tested, compliant and received on each date?
- Which reservations remain and what evidence would close them?
- Can a completed planning task prove the corresponding physical issue is resolved?

Pass: keeps planned, executed, verified, compliant, received and reservation-free
states distinct. A closed task does not close a physical defect.

## Cross-case evaluation matrix

Each case should be evaluated for:
1. Identity: correct project and object, no accidental cross-affair match.
2. Provenance: exact source/version/locator for material assertions.
3. Temporal consistency: issue, receipt, observed and effective times distinguished.
4. Relation relevance: bounded traversal, no unrelated neighboring work.
5. Dependency reasoning: prerequisites explicit vs inferred, conditional impact.
6. Decision fidelity: proposal, approval and authorization remain distinct.
7. Unknown handling: missing/contradictory inputs surfaced, not fabricated.
8. Efficiency: compare retrieved sources, tokens and latency against a document-only
   retrieval baseline, without claiming improvements before measurement.

Suggested test protocol: for each case, prepare a minimal fixture manifest with
source digests and locators, a reference answer with source-linked assertions, and
at least two adversarial variants (contradictory later email; incomplete coverage).
Run existing ingestion/Observation Bundle -> review -> governed read -> bounded
Hermes Context Pack, only where the existing implementation supports the path.
Record pass/fail per criterion and exact failing seam. Do not add new runtime owners.

## Integration boundaries and next actions

- Inspect existing longitudinal H5.8 fixtures before creating new fixture formats.
- Review PR #62 before changing relation vocabulary or validators.
- Reuse `PROJECT_ANATOMY_MODEL.md` sections 9–12 for revisions, incompleteness,
  temporal history and purpose-specific lenses.
- Start with C01, C03 and C08: sequencing, drawing changes, decision status.
- Add executable tests only after identifying current fixture harness and schema
  consumers; this document itself is a competency specification, not a test run.
- Qualify live NAS/Hermes/Revit separately under existing issue #8; a repository
  fixture pass does not imply a successful real-environment proof.
