# PRO / EXE Responsibility Slice

Status: template — candidate-only architecture probative instruction slice, documented non-implemented.
Boundary profile: non_executable_template.

This template materializes the first narrow use case of `docs/domain-packs/architecture/PROBATIVE_INSTRUCTION.md`:

```text
Does this request, drawing, note or wording risk making the agency appear to produce or validate execution work outside its mission?
```

It is not a runtime, Hermes skill, OpenWebUI function, checklist engine, contract validator, legal opinion, engineering validation, approval engine, memory engine or external communication tool.

```text
The architect decides.
The validated remains.
```

## Purpose

The slice exists because the PRO / DCE / EXE / VISA boundary is one of the highest-risk areas in architecture practice.

A drawing may be graphically precise while remaining a design or consultation document.

A note may be useful for coordination while not being an execution instruction.

A VISA comment may review a contractor document while not producing the contractor's execution design.

The template forces each answer to classify:

```text
phase
source
mission scope
professional act
responsibility chain
risk of external effect
safe wording
human gate
```

## In scope

Use this slice for:

```text
foundation dimensions on PRO / DCE drawings;
structure, opening or pre-drilling indications;
contractor questions that ask the architect to finalize technical dimensions;
BET notes that could be forwarded as execution instructions;
plan sheets that need a non-EXE footer;
mail drafts to contractors, BET or client about execution responsibility;
VISA comments where responsibility must stay with the contractor / BET;
site questions where a response could become an order.
```

## Out of scope

This slice must not:

```text
calculate structure;
produce execution drawings;
validate contractor EXE;
replace BET review;
replace bureau de controle review;
issue a visa by itself;
send a mail;
approve payment;
close a reserve;
pronounce reception;
promote memory;
create canonical project state.
```

## Required input packet

A safe run needs:

```text
project_ref:
phase_or_phase_uncertainty:
mission_scope_ref:
source_documents:
  - title:
    index_or_date:
    issuer:
    recipient:
    locator:
question_or_requested_action:
intended_output:
external_recipients_if_any:
known_contract_boundary:
known_specialist_boundary:
```

If the phase or mission scope is unknown, output must remain `to_verify` or `needs_human_arbitrage`.

## Minimum instruction path

```text
1. Identify the requested professional act.
2. Identify the source and its status.
3. Identify the phase and mission scope.
4. Classify whether the request touches execution production or execution validation.
5. Identify who should produce, calculate, check, decide and execute.
6. Surface contradictions between drawing precision, phase label, contract scope and recipient expectation.
7. Flag forbidden wording.
8. Propose safe wording candidate.
9. Produce Result Candidate + Evidence Pack Candidate.
10. Stop at human approval before external transmission.
```

## Output statuses

Allowed statuses:

```text
result_candidate
source_candidate
evidence_pack_candidate
to_verify
needs_human_arbitrage
blocked
approved_for_internal_use
approved_for_external_transmission
rejected
```

Default status for any externally meaningful draft:

```text
needs_human_arbitrage
```

## Risk phrases to detect

```text
bon pour execution
plan d'execution
dimensions definitives
valide
conforme
visa favorable
prepercement
a realiser
synthese complete
sans reserve
```

## Safer wording candidates

```text
hypothese de conception
pre-dimensionnement
support de coordination PRO / DCE
ne vaut pas plan d'execution
a confirmer par l'entreprise
a verifier par le BET competent
dimensions finales a produire par le titulaire du lot / son BET
avis limite au perimetre de mission de maitrise d'oeuvre
sous reserve de coherence avec les pieces marche
```

## Sheet footer candidate

```text
Document de conception / consultation — ne vaut pas plan d'execution.
Les dimensions, assemblages, percements, notes de calcul et dispositions finales d'execution sont a etablir et verifier par l'entreprise titulaire et, le cas echeant, par son BET, dans le respect des pieces marche et de ses obligations contractuelles.
```

This footer is a wording candidate only. It must be adapted by the architect to the actual mission, contract and document.

## Mail posture candidate

```text
We can clarify the design / consultation intent and coordinate the information visible in the project documents.
We must not replace the contractor's execution design or the competent BET calculation.
The final execution dimensions and details remain to be produced, checked and assumed by the responsible party under the contract chain.
```

## Acceptance gates

| Gate | Requirement |
|---|---|
| G0 — source identified | Plan, mail, note or document is identified with date/index and issuer when available. |
| G1 — phase stated | Phase is named or uncertainty is explicit. |
| G2 — mission boundary stated | Contract scope or uncertainty is explicit. |
| G3 — act classified | The output distinguishes information, coordination, comment, visa, instruction and approval. |
| G4 — responsibility chain stated | Producer, checker, decision owner and executor are identified or marked unknown. |
| G5 — risk surfaced | External-effect risk is classified. |
| G6 — safe wording proposed | Risky wording is replaced or flagged. |
| G7 — human gate | External transmission remains blocked until authorized. |

## Definition of done

One slice run is complete when it produces:

```text
- one completed task contract;
- one source inventory;
- one architecture evidence tree candidate;
- one responsibility-risk classification;
- one safe wording candidate or mail candidate;
- one human decision: accepted / refused / to_verify / to_arbitrate.
```

The outcome is not implementation. The outcome is a repeatable professional instruction template for PRO / EXE responsibility drift.
