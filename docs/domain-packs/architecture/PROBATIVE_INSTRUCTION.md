# Architecture Probative Instruction

Status: candidate support doctrine — architecture-domain instruction method.  
Repository state: documented non-implemented.  
Domain pack target: architecture agency / architecture_fr.  
Runtime status: non-executable.
Boundary profile: candidate_support_note.

This document defines how Pantheon Next should frame architecture-domain questions that require source retrieval, professional qualification, responsibility review and human decision.

It is not a RAG engine. It is not a graph runtime. It is not an agent, checker, scheduler, queue, approval engine, memory engine, OpenWebUI extension, Hermes skill, database schema or implementation plan.

```text
The architect decides.
The validated remains.
```

## Purpose

Architecture work is not only document search.

A retrieved clause, plan note, email sentence, drawing dimension, quote line or regulatory excerpt may become dangerous if it is treated as usable truth without being situated in the project, phase, source authority, mission scope and chain of responsibility.

This protocol turns a generic retrieval question into an architecture-specific instruction process:

```text
question
-> professional act at stake
-> phase and mission lens
-> source authority lens
-> responsibility lens
-> contradiction lens
-> risk / external-effect lens
-> Result Candidate + Evidence Pack Candidate
-> human decision gate
```

The goal is not to answer faster at any cost. The goal is to make the answer safer, more inspectable and professionally situated.

## Core rule

```text
A point of architecture is not true because it was retrieved.
It becomes usable only when it is situated in:
- a source;
- a version;
- a phase;
- a mission scope;
- a responsibility chain;
- an external-effect risk;
- an evidence status;
- a human decision path.
```

## Why this is not only RAG

A generic RAG flow asks:

```text
question -> documents -> answer
```

Architecture probative instruction asks:

```text
question -> act -> phase -> source authority -> responsibility -> contradiction -> risk -> candidate -> decision
```

Retrieval can help find material. It does not decide what the material is worth.

A vector match, semantic chunk, OCR extract, graph edge, proof tree, model summary or connector preview is never final proof by itself.

## Object of instruction

The protocol should start by identifying the professional object at stake.

Typical objects:

```text
project fact
program fact
regulatory statement
local planning constraint
technical assumption
mission boundary
phase gate
client decision
contractor request
BET / bureau de controle input
CCTP / DPGF / quote match
site observation
reserve
non-conformity
payment or change-order question
reception / DOE / GPA item
external communication draft
memory / register candidate
```

The system should also identify the professional act being prepared.

Typical acts:

```text
inform
summarize
ask
alert
clarify
refuse
reserve
transmit
file
notify
comment
visa
propose
approve
record
archive
```

Rule:

```text
Document type is not professional act.
Professional act is not legal or contractual effect.
```

A plan attached to an email is not automatically a plan for execution. A site report is not automatically an order. A draft mail is not a sent notice. A retrieved source is not an approved evidence item.

## Required lenses

### 1. Phase lens

Every consequential interpretation must name the project phase or state uncertainty.

Architecture phases and containers include:

```text
prospect / opportunity
contract / mission setup
DIAG / existing-condition survey
ESQ
APS
APD
DP / PC / administrative filing
PRO
DCE
ACT
EXE / VISA
DET / OPC if included
AOR / reception
DOE / handover
GPA
archive / retention
```

The same statement changes status by phase.

Example:

```text
Foundation 80 x 80
```

Possible readings:

```text
APS / APD: preliminary design hypothesis.
PRO: pre-dimensioning or project coordination support.
DCE: consultation baseline, still not contractor EXE unless contract says otherwise.
EXE: contractor / BET execution responsibility.
VISA: MOE review of submitted contractor document, not production of the contractor correction.
DET: site question requiring traceable response.
```

If the phase is unknown, the output must remain `to_verify` or `candidate`.

### 2. Source authority lens

Every output must distinguish original, derived and retrieved material.

Source hierarchy should follow the architecture agency pack and source policy:

```text
1. laws, regulations and binding public texts;
2. operation contract and signed amendments;
3. approved phase decisions;
4. contradictory site evidence and signed records;
5. original documents and filed packages;
6. derived documents: OCR, Markdown, summaries, extracted tables;
7. retrieval outputs: chunks, embeddings, semantic matches.
```

Rule:

```text
A chunk is a locator aid, not a source of authority.
```

### 3. Responsibility lens

Every consequential output must name the responsibility chain, or state that it is unknown.

Typical roles:

```text
maitre d'ouvrage
architect / MOE
mandataire
co-traitant
BET structure
BET thermique
bureau de controle
SPS
OPC
contractor
subcontractor
supplier
municipality
urban planning service
concessionnaire
syndic
insurer
legal counsel
```

The protocol must distinguish at least:

```text
who requests;
who produces;
who calculates;
who checks;
who comments;
who approves;
who decides;
who executes;
who receives;
who bears the consequence.
```

A useful architecture answer often depends more on responsibility than on information.

### 4. Contradiction lens

The process must actively search for tension.

Typical contradictions:

```text
plan vs CCTP;
CCTP vs DPGF;
notice vs elevation;
client email vs last approved phase;
BET note vs architectural layout;
quote exclusion vs CCTP article;
old plan index vs new plan index;
project intent vs local planning rule;
site observation vs contractor statement;
phase label vs actual requested effect.
```

Rule:

```text
Contradictions are surfaced, not smoothed over.
```

When a contradiction affects responsibility, cost, compliance, scope, site execution, reception or external communication, the output must stop at a visible gate.

### 5. Risk and external-effect lens

The protocol must flag language or actions that may externally commit the agency, the client or another party.

Risk phrases:

```text
conforme
valide
bon pour execution
sans reserve
a realiser
dimensions definitives
synthese complete
prepercement
visa favorable
reception validee
paiement valide
solution acceptee
```

Safer candidate formulations may include:

```text
hypothese de conception
pre-dimensionnement
a confirmer par l'entreprise
a verifier par le BET competent
ne vaut pas plan d'execution
avis limite au perimetre de mission
sous reserve de coherence avec les pieces marche
a arbitrer par le maitre d'ouvrage
piece recue pour analyse / visa selon mission
observation a lever avant decision
```

The system may propose safer wording. It must not transmit it without approval.

## Instruction sequence

Minimum safe sequence:

```text
1. Intake
   Identify question, dossier, phase, possible act and requested output.

2. Scope admission
   State what is inside scope, outside scope and unknown.

3. Source inventory
   List received, referenced, missing and superseded sources.

4. Retrieval / extraction
   Retrieve only as needed; preserve locators and source status.

5. Claim decomposition
   Split the requested answer into reviewable claims.

6. Lens review
   Apply phase, source authority, responsibility, contradiction and risk lenses.

7. Evidence assembly
   Produce Evidence Pack Candidate with assumptions, locators, missing items and tensions.

8. Result drafting
   Produce Result Candidate, not final truth.

9. Gate classification
   Mark whether the result is read-only, candidate-only, needs approval, blocked, or capability gap.

10. Human decision
   The architect or authorized human decides what remains, what is sent and what is refused.
```

## Output status vocabulary

Allowed statuses:

```text
source_lead
source_candidate
evidence_item_candidate
evidence_pack_candidate
result_candidate
to_verify
needs_human_arbitrage
blocked
approved_for_internal_use
approved_for_external_transmission
rejected
```

Forbidden collapses:

```text
retrieved = true;
proof_tree = approval;
source found = source valid;
OCR extract = document authority;
graph relation = proof;
runtime success = professional validation;
mail draft = external communication;
VISA comment = contractor correction;
received EXE = visa;
site observation = order;
architect assistance = project-owner decision;
```

## Evidence tree format

The output should expose an Architecture Evidence Tree.

Minimum shape:

```text
architecture_evidence_tree:
  question:
  professional_act:
  phase:
  mission_scope:
  output_status:
  claims:
    - claim:
      source_items:
        - source_ref:
          source_type:
          authority_class:
          version_or_index:
          locator:
          excerpt_or_observation:
          limitation:
      responsibility:
        requester:
        producer:
        checker:
        decision_owner:
        executor:
      contradictions:
        - tension:
          affected_output:
          required_arbitrage:
      risk:
        level: low | medium | high | critical
        external_effect_possible: true | false
        reason:
      candidate_conclusion:
      required_gate:
  unresolved_unknowns:
  safe_wording_candidate:
  forbidden_wording:
```

This is a candidate shape, not an executable schema.

## Output template

A useful answer should be structured like this:

```text
Point instructed:

Status:

Phase / mission reading:

Candidate answer:

Sources used:
- source, index/date, author, locator, authority class, limitation

Evidence tree:
1.
2.
3.

Contradictions / tensions:

Responsibility reading:

Risk if misunderstood:

Safer wording:

Action proposed:

Gate:
```

## Architecture examples

### PRO / EXE confusion

Question:

```text
Can we send these foundation dimensions to the company?
```

Correct posture:

```text
Do not answer only with the dimensions.
First qualify phase, document source, issuer, mission scope and whether transmission could be read as execution instruction.
```

Possible candidate conclusion:

```text
The dimensions may be presented only as pre-dimensioning / design hypothesis if the source is PRO and the mission does not include EXE production. Final execution dimensions must come from the contractor or competent BET under the contract chain. Add an explicit sheet note if the drawing risks being read as EXE.
```

### Quote analysis

Question:

```text
Is this quote acceptable?
```

Correct posture:

```text
Do not accept or reject.
Compare against CCTP, DPGF, lot scope, exclusions, quantities, versions, insurance and validity date. Produce anomalies and questions for review.
```

### Site report point closure

Question:

```text
Can we close this point?
```

Correct posture:

```text
Check prior report chain, responsible lot, claimed completion, visual/site evidence, photos, contradictory status and whether closure creates a contractual or reception effect.
```

### Reception

Question:

```text
Is reception validated?
```

Correct posture:

```text
Reception is pronounced by the project owner. The system may prepare OPR items, reserve lists and a reception proposal candidate. It must not model reception as an automated MOE act.
```

## Projection by layer

Pantheon defines:

```text
instruction method;
source and evidence status;
required gates;
forbidden collapses;
responsibility and risk lenses;
output status vocabulary.
```

The exposure surface may:

```text
show the evidence tree;
show contradictions;
collect user decision;
request revision;
expose source locators;
warn about external-effect risk.
```

The execution runtime may:

```text
extract;
search;
compare;
summarize;
prepare Result Candidates;
prepare Evidence Pack Candidates;
report Capability Gaps;
return Outcome Observation Candidates.
```

The execution runtime must not:

```text
validate truth;
approve a visa;
send an email;
file a permit;
pronounce reception;
close reserves;
approve payment;
promote memory;
modify doctrine;
create canonical project state.
```

## Minimum first slice

The first useful implementation projection should be narrow:

```text
mail or document question
+ project phase
+ source inventory
+ retrieval / extraction as needed
+ responsibility-risk review
+ candidate note or mail draft
+ human approval gate
```

Recommended first use case:

```text
This request or wording may engage the agency beyond its mission. Instruct it before response.
```

## Non-goals

This protocol must not:

```text
automate professional judgment;
replace legal review;
replace BET or bureau de controle review;
replace contractor execution design;
replace official urban-planning verification;
certify regulatory compliance;
produce a visa by itself;
pronounce reception;
close reserves;
approve payment;
auto-send external communications;
promote memory automatically;
turn a source retrieval into a validated project fact.
```

## Boundary phrase

```text
Retrieval finds material.
Instruction qualifies material.
Evidence supports a candidate.
Approval gates external effect.
The architect decides.
```
