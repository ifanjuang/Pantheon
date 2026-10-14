# Architecture Proof Register — Vertical Example

Status: example — fictional, documented non-implemented.
Boundary profile: candidate_support_note.

This example tests the interaction between architecture target workflows, document intake, source qualification, proof candidates, answer verification candidates, review triggers and human decision.

It does not implement a schema, database, dashboard, runtime, connector, RAG engine, provenance graph, approval engine, memory engine, OpenWebUI action, Hermes skill, form filler, image analyzer, PDF exporter, scheduler, queue or external action.

## Purpose

This example exists to test the architecture proof-register idea before changing `schemas/`.

It is not a data-platform implementation.

It is not a substitute for `schemas/architecture-proof-register/*`.

It is a vertical professional scenario showing how a small architecture dossier should move through:

```text
request framing
-> candidate preflight note
-> Document Intake Scan
-> source qualification
-> retrieval / ranking candidate
-> version and authority review
-> event-centric provenance view
-> proof candidates
-> Answer Verification Gate candidate
-> review trigger
-> Human Decision Gate
-> trace / memory decision
```

The example is intentionally concrete. It is designed to expose the difference between:

```text
latest file
contractual authority
visual index
enterprise claim
client preference
proof candidate
human decision
```

## Current doctrine position

This example aligns with current candidate and support material, without promoting any candidate to canonical doctrine.

| Source area | How this example treats it |
|---|---|
| `TARGET_WORKFLOWS.md` | Uses Document Intake Scan and workflow atoms as candidate support model. |
| `PROOF_REGISTER.md` and related documents | Uses their proof-register direction as candidate, not implementation. |
| PR #35 schema proposal | Does not depend on or modify schemas. |
| Issue #37 schema reconciliation | Remains unresolved; this example is intentionally schema-free. |
| PR #71 Answer Verification Gate | Referenced only as candidate alignment, not canonical doctrine. |
| PR #66 / #67 / #72 preflight / Pantheon Control | Referenced only as candidate dashboard / preflight alignment, not implementation. |
| PR #73 LLM system patterns review | Uses retrieval / ranking as candidate ordering, not proof. |
| PR #74 BrainAPI review | Uses event-centric provenance as review interface, not graph adoption. |

## Scenario

### Fictional project

```text
Project: Maison Lierre — extension of a single-family house
Location: fictional
Agency role: architect / maître d'œuvre
Phase: construction / site follow-up
Subject: exterior sliding door, performance requirement and enterprise plus-value
```

### User request

```text
The enterprise sent a plus-value quote for a reinforced-performance sliding door.
Can I validate the plus-value, or should I refuse it?
```

This question is consequential.

A wrong answer could create:

- a false contractual conclusion;
- an improper visa or advice position;
- a cost decision without clear mandate;
- a weak record for a later dispute;
- an external action if the response is transmitted.

Allowed output:

```text
recommendation candidate
proof candidates
contradictions
questions to ask
human decision gate
```

Forbidden output:

```text
final approval
final refusal
legal conclusion
automatic transmission
automatic memory promotion
```

## Candidate preflight note

This is not an executable preflight. It is a documentary note showing what an external preflight system should make visible before running a workflow.

| Check | Candidate result | Consequence |
|---|---|---|
| Project selected | Maison Lierre | scope can be dossier-scoped |
| User mandate clear | partial | user asks for validation/refusal; should be reframed as candidate review |
| External action requested | no | no sending, signing, filing or deposit in this task |
| Connector write needed | no | read-only example |
| Schema write needed | no | example stays outside `schemas/` |
| Memory promotion requested | no | trace decision only at the end |
| Required sources available | partial | photo metadata and formal MOA approval are uncertain |
| Consequence level | consequential | evidence and human decision required |

Preflight candidate status:

```text
preflight_candidate: pass_with_warnings
warnings:
  - user question asks for validation/refusal, but the workflow may only prepare a decision candidate
  - photo is weak unless dated and linked to the site event
  - MOA email may express preference without formal approval
```

## Incoming corpus

| Ref | Fictional document | Received as | Claimed relevance |
|---|---|---|---|
| D1 | `CCTP_Lot06_Menuiseries_PRO_A.pdf` | project PDF | baseline technical requirement |
| D2 | `DPGF_Lot06_signed.pdf` | signed PDF | contractual amount and included items |
| D3 | `Devis_PV_Menuiserie_Entreprise_Boisclair.pdf` | enterprise quote | plus-value claim |
| D4 | `Mail_MOA_option_coulissant.txt` | email excerpt | possible client decision |
| D5 | `CR08_Chantier.pdf` | site report | reserve / contradiction candidate |
| D6 | `Photo_coulissant_2026-04-18.jpg` | photo | visual index |
| D7 | `Notice_fabricant_coulissant_performance.pdf` | manufacturer notice | technical support |

## Document Intake Scan

A document must not move directly from transmitted to trusted.

The first pass identifies each source, checks its declared scope and decides whether it may enter detailed analysis.

| Ref | Document type | Date / version | Authority class | Applicability | Risk | Recommended next step |
|---|---|---|---|---|---|---|
| D1 | CCTP lot | PRO indice A | project source; contractual only if included in signed market | applicable | medium | compare with D2 signed DPGF |
| D2 | Signed DPGF | signed, date present | contractual candidate | applicable | high | use as market baseline candidate |
| D3 | Enterprise plus-value quote | recent, unsigned | enterprise claim candidate | partial | high | verify contractual basis before advice |
| D4 | MOA email | dated, informal | decision candidate, not necessarily approval | partial | medium | ask whether this was formal paid-option approval |
| D5 | Site report CR08 | dated report | site evidence candidate | applicable | high | compare reserve wording with D3 claim |
| D6 | Photo | metadata uncertain | visual index candidate | partial | medium | never conclude from photo alone |
| D7 | Manufacturer notice | technical / commercial | technical support, not regulatory or contractual proof | partial | medium | use only to understand product performance |

Admission decision:

```text
D1-D5 may enter detailed comparison.
D6 may enter only as visual index.
D7 may enter only as technical support.
No document is accepted as final proof by intake alone.
```

## Source qualification table

| Ref | Source status | Freshness | Scope | Reuse scope | Notes |
|---|---|---|---|---|---|
| D1 | source_candidate | acceptable but may be superseded | project / lot 06 | dossier only | contract status depends on market documents |
| D2 | strong_candidate | current if latest signed DPGF | project / lot 06 | dossier only | likely strongest cost baseline |
| D3 | claim_candidate | current | project / lot 06 | dossier only | enterprise position, not proof |
| D4 | decision_candidate | date present | project / MOA intent | dossier only | ambiguous legal/contract status |
| D5 | evidence_candidate | current at CR08 date | site event | dossier only | may support contradiction |
| D6 | index_candidate | metadata uncertain | visual | dossier only | requires correlation with CR/date/location |
| D7 | support_candidate | version to verify | product | product context only | commercial/technical support |

## Retrieval / ranking candidate

A retrieval or RAG step may order excerpts for review. It must not decide authority.

Example ranked excerpts:

| Rank | Source | Retrieved excerpt candidate | Why ranked high | Authority warning |
|---:|---|---|---|---|
| 1 | D2 | DPGF line mentioning baseline sliding door price | signed financial baseline | may not describe all performance details |
| 2 | D1 | CCTP performance requirement for exterior sliding door | technical baseline | contractual only if integrated into market |
| 3 | D3 | plus-value quote for reinforced-performance option | direct claim under review | enterprise claim only |
| 4 | D4 | MOA email: “we prefer the higher-performance sliding door if possible” | possible decision signal | preference is not formal approval |
| 5 | D5 | CR08 reserve: “menuiserie à clarifier avant validation” | contradiction / unresolved item | reserve wording must be read in context |
| 6 | D6 | photo showing installed or proposed sliding unit | visual correlation | not proof by itself |
| 7 | D7 | product performance table | technical background | manufacturer source is not contract |

Rule:

```text
retrieval proposes
ranking orders
LLM assesses
Evidence Pack supports
status is qualified under Pantheon rules
human decides
```

## Version and authority matrix

| Question | Stronger source candidate | Weaker source candidate | Status |
|---|---|---|---|
| What was priced in the signed market? | D2 signed DPGF | D3 plus-value quote | D2 likely controls amount baseline |
| What technical performance was expected? | D1 CCTP if contractually attached | D7 manufacturer notice | D1 controls only if part of market |
| Did the MOA approve a paid option? | formal signed approval or explicit written order | D4 informal preference email | missing / to confirm |
| Is the current item compliant? | site inspection + CCTP + CR + product data | D6 photo alone | cannot conclude from photo alone |
| Can the architect validate/refuse the plus-value? | full contract basis + MOA decision + site facts | any single source alone | human decision required |

## Event-centric provenance view

A provenance graph may reveal relationships. It does not prove truth, approval or memory by itself.

| Event | Actor | Target | Source | Effect candidate |
|---|---|---|---|---|
| CCTP issued | MOE | Lot 06 exterior joinery | D1 | technical baseline candidate |
| DPGF signed | MOA + enterprise | market amount | D2 | contractual amount candidate |
| Option discussed | MOA | sliding door preference | D4 | preference / possible decision candidate |
| Plus-value requested | enterprise | reinforced-performance door | D3 | enterprise claim candidate |
| Reserve noted | MOE | joinery clarification | D5 | contradiction / unresolved issue candidate |
| Photo received | enterprise or site actor | installed/proposed unit | D6 | visual index candidate |
| Product performance cited | manufacturer | technical characteristics | D7 | technical support candidate |

Graph boundary:

```text
relationship_candidate != proof
multi-hop relationship != approval
graph visibility != canonical memory
```

## Proof candidates

### Claim A — baseline item appears priced in the signed market

```text
claim_id: claim_A_baseline_priced
status: proof_candidate
confidence: medium
evidence_refs: D2, D1
reasoning: DPGF appears to include a baseline sliding door; CCTP may define expected performance if contractually attached.
risk: DPGF may not capture performance nuance; CCTP attachment to signed market must be verified.
```

### Claim B — plus-value may relate to an option not clearly ordered

```text
claim_id: claim_B_option_unclear
status: proof_candidate
confidence: low_medium
evidence_refs: D3, D4
reasoning: enterprise requests a plus-value and MOA expressed a preference, but the email does not clearly approve a paid extra.
risk: confusing preference with formal approval.
```

### Claim C — CR08 creates a contradiction requiring review

```text
claim_id: claim_C_cr08_contradiction
status: contradiction_candidate
confidence: medium
evidence_refs: D5, D3, D6
reasoning: site report asks to clarify the joinery before validation; enterprise quote asks for acceptance; photo may illustrate but not prove.
risk: validating a plus-value while an unresolved reserve remains open.
```

### Claim D — photo is an index, not a finding

```text
claim_id: claim_D_photo_index_only
status: evidence_limit
confidence: high
evidence_refs: D6
reasoning: the photo may help locate and review the issue, but cannot alone prove compliance, non-compliance or contractual entitlement.
risk: visual overreach.
```

## Answer Verification Gate candidate

This section is candidate alignment only. It does not treat the Answer Verification Gate candidate doctrine as canonical until it is explicitly resolved.

User question:

```text
Can I validate this plus-value or refuse it?
```

Candidate classification:

| Axis | Candidate classification |
|---|---|
| Consequence | consequential |
| Evidence need | required |
| Status need | required |
| Approval need | required before external action |
| Memory need | trace decision after human decision |
| Allowed answer | decision-support candidate |
| Forbidden answer | final validation / refusal / legal conclusion |

Answer status candidate:

```text
answer_status: cannot_answer_as_final
allowed_output:
  - evidence-backed recommendation candidate
  - contradiction list
  - missing information
  - questions to MOA / enterprise
  - human decision options
```

## Review trigger

Trigger conditions:

```text
signed market and plus-value diverge
MOA email may be interpreted as approval but is not explicit enough
photo is insufficient proof
CR08 reserve conflicts with enterprise request
validation/refusal may engage MOE advice or visa risk
```

Review trigger candidate:

```text
review_trigger_id: rt_plus_value_contract_authority
trigger_type: human_decision_required
severity: high
reason: plus-value validation/refusal affects cost, contract interpretation and professional advice
next_gate: Human Decision Gate
```

## Human Decision Gate

The system should ask the architect or responsible human to choose a next action.

Options:

```text
A. Request clarification from the enterprise: contractual basis, product reference, performance delta, amount breakdown.
B. Ask MOA to confirm whether the reinforced-performance option was approved as a paid extra.
C. Refuse validation pending explicit contract basis and reserve resolution.
D. Accept in principle but request corrected quote and supporting documents before any formal position.
E. Escalate to contract / insurance / legal review if dispute risk is high.
```

Recommended candidate:

```text
recommended_next_action: A + B before any validation/refusal
rationale: missing contract basis and ambiguous MOA approval
external_action_status: draft_only_until_human_approval
```

## Draft question set

### To enterprise

```text
Please provide the contractual basis for the requested plus-value:
- DPGF line concerned;
- performance difference compared with the signed market;
- product reference;
- reason why the requested performance was not included in the original offer;
- amount breakdown;
- impact on delay, if any.
```

### To MOA

```text
Please confirm whether your previous email expressed:
A. a general preference;
B. acceptance of a paid option;
C. request for a technical clarification before decision.

No formal position should be taken on the plus-value until this is clarified.
```

These are draft candidates only. They are not sent by this example.

## Trace / memory decision

At the end of the task, the human should decide what remains.

Options:

| Option | Effect |
|---|---|
| No trace | discard the working discussion |
| Short trace | record that plus-value review was prepared |
| Project log entry | record decision and source refs in dossier |
| Register Candidate | scoped to Maison Lierre only |
| Improvement candidate | improve future plus-value / visa-risk workflow |

Recommended trace candidate:

```text
trace_status: project_log_candidate
memory_status: no_canonical_memory
reason: useful dossier event, but no reusable global memory until decision validated
```

## Refused shortcuts

```text
Do not treat the newest file as authority.
Do not treat the enterprise quote as proof.
Do not treat a MOA email as formal approval without qualification.
Do not treat a photo as a finding.
Do not treat RAG ranking as validation.
Do not treat a provenance graph as evidence by itself.
Do not approve, reject, sign, send or record canonical memory automatically.
Do not modify schemas from this example.
```

## Expected value of the example

This example gives a concrete review object for future #35 / #37 discussion.

It can be used to ask:

```text
Can the proposed Architecture Proof Register schema represent this case?
Can it express document intake status?
Can it express authority differences?
Can it express contradiction candidates?
Can it express a review trigger without implementing approval?
Can it keep photo / graph / retrieval outputs as candidates rather than proof?
```

## Boundary restatement

This example is documentation only.

It does not create or modify:

```text
schemas/
tests/
operations/
platform/
Docker files
.env files
pyproject.toml
```

It does not implement Pantheon Control, module preflight, Answer Verification Gate, BrainAPI, RAG, proof registry storage, document extraction, image review, dashboard rendering, approval, external action or memory promotion.

```text
The database records.
The workflow proposes.
The evidence supports.
The approval validates.
The human decides.
```