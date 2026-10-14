# Architecture Material Choice Reflex

Status: candidate — architecture-domain reflex for material and facade-choice questions.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a runtime, search tool, PLU checker, ABF checker, estimator, CCTP generator, Notion write, approval engine, memory engine or external communication workflow.

It defines a candidate reflex for simple material-choice questions that may become consequential when they touch regulation, prior decisions, cost, technique, contract, insurance or external communication.

## Purpose

Architectural material questions often look simple:

```text
Which facade material should we choose?
Can we use timber cladding?
Was brick already selected?
Is render cheaper?
What did the client / mairie / ABF say?
Is masonry facing sensible on timber frame?
```

The reflex must keep the answer useful and fast while avoiding unsupported design, regulatory or cost conclusions.

## Core rule

```text
Do not choose in isolation.
Reconstruct the last known decision, known options, regulatory context, technical constraints, economic signals and prior communications.
Then produce a candidate recommendation with visible limits.
```

Pantheon does not choose the material by authority.

It helps the architect see the decision frame.

## Trigger

Open this reflex when the user asks about:

```text
facade material;
finish;
cladding;
render;
brick;
stone;
zinc;
metal;
timber;
colour;
texture;
material substitution;
choice between options;
compatibility of material with support;
impact of material on cost, planning, PLU, ABF, CCTP or client decision.
```

## Default depth

Default: `Normal`.

Use `Fast` only for aesthetic or early internal preference questions with no regulatory, financial or external effect.

Escalate to `Deep` when the question touches:

```text
PLU;
ABF / heritage;
permit / DP / PC material already submitted;
CCTP or DCE change;
cost arbitration;
technical system risk;
structure / facade support;
fire / waterproofing;
insurance;
client decision;
external communication;
Notion validated write;
```

## Required sources by depth

### Fast

```text
user question;
current context;
visible known options;
obvious missing information.
```

Output is a quick preference candidate only.

### Normal

```text
project phase;
latest known decision / resolution;
preselected options;
recent client / MOE / mairie / ABF communications if available;
known PLU / instruction status if already in project context;
relevant plans / notices / renders;
known support system;
known economic notes or estimates if available.
```

### Deep

```text
current official PLU / OAP / prescriptions;
ABF or mairie exchanges;
submitted permit / DP notice and materials;
CCTP / DPGF / AE where the material affects contract;
technical details / manufacturer system / ATec or equivalent where needed;
insurance scope if the execution technique matters;
updated estimate or economist note;
client approval path;
User Decision Gate.
```

## Review axes

### 1. Last known decision

Identify:

```text
material selected;
material rejected;
material still candidate;
decision date;
decision source;
who decided;
status: idea | option_candidate | preselected | client_choice | MOE_choice | urbanism_submitted | urbanism_validated | DCE_integrated | market_integrated | abandoned | to_arbitrate.
```

Do not confuse a sketch, render or casual mail with a validated decision.

### 2. Preselected options

List options already present in the dossier:

```text
option;
source;
status;
why considered;
known advantages;
known risks;
missing checks.
```

### 3. Regulatory / instruction context

Check, proportionally:

```text
PLU zone and material prescriptions;
OAP / heritage constraints;
ABF / protected perimeter if known;
mairie / instructeur / ABF communications;
materials already submitted in permit / DP notice;
latest official source status.
```

Output must classify:

```text
regulatory_status: not_checked | known_context_only | official_source_checked | conflicting | cannot_conclude;
ABF_status: not_applicable | unknown | likely_relevant | checked | requires_confirmation;
```

### 4. Technical context

Check:

```text
support system: timber frame | masonry | concrete | existing old wall | ITE | unknown;
weight;
fixing;
ventilation / cavity;
water management;
vapour / hygrothermal logic;
fire if relevant;
durability;
maintenance;
interface with openings, sills, corners, base, roof;
company know-how;
insurance / system documentation if relevant.
```

Example:

```text
Brick facing on timber frame may be architecturally strong but technically and economically non-neutral. It needs system detail, support compatibility, weight, fixing, base detail, ventilation, openings and insurance confirmation before becoming a validated choice.
```

### 5. Economic context

Check:

```text
budget target;
previous estimate;
enterprise quote;
economist note;
cost class: favourable | medium | high | unknown;
planning effect;
maintenance effect;
alternative cost signals.
```

No precise price should be invented without a source.

### 6. Prior communications

Search where proportionate:

```text
client preference;
MOE / architect decision;
mairie / instructeur statement;
ABF remark;
enterprise technical objection;
economist warning;
BET or control office note;
previous rejection or approval.
```

Classify communications:

```text
information;
preference;
objection;
candidate decision;
validated decision;
unclear.
```

## Output shape

Recommended compact answer:

```text
Depth:
Question:
Last known decision:
Known options:
Regulatory / instruction status:
Technical status:
Economic status:
Prior communications:
Recommendation candidate:
Missing information:
Next action:
Forbidden conclusions:
```

## Option matrix

When useful:

| Option | Status | PLU / ABF | Technique | Economy | Risk | Candidate recommendation |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Safe recommendation language

Allowed:

```text
At this stage, I would use X as the working option.
I would keep Y as a fallback option.
This option looks coherent, subject to PLU / ABF / cost / technical confirmation.
This option should not be validated before checking X.
```

Forbidden unless fully supported and approved:

```text
This material is authorized.
This material is validated.
This will be cheaper.
This is compliant.
This must be changed in the CCTP.
Send this to mairie / ABF / client.
Record this as final in Notion.
```

## Typical recommendations

### Timber frame + facade question

```text
Timber cladding may be technically coherent with timber frame and lighter than masonry facing, but urbanism / ABF and maintenance must be checked.
Brick or masonry facing may preserve an architectural intent, but it can be technically heavier and more expensive on timber frame. Require system detail and estimate before arbitrage.
Render may be a cost-control fallback, but depends on support / ITE system and design intent.
```

### Submitted permit material

```text
If the material was already described in the DP / PC notice, any substitution must be treated as a change candidate, not a casual preference.
Check the submitted notice, mairie / ABF exchanges and modification procedure before updating CCTP or client material board.
```

## Actions candidates

Allowed as candidate only:

```text
prepare material options matrix;
prepare client arbitration note;
request PLU / ABF check;
request economist input;
request technical system detail;
request enterprise pricing;
prepare CCTP update candidate;
prepare Notion decision candidate;
prepare email draft candidate;
open User Decision Gate.
```

Forbidden without approval:

```text
send external email;
modify validated CCTP;
change permit material;
record final decision;
accept cost impact;
issue instruction to enterprise;
claim regulatory compliance.
```

## Missing information

Use `MISSING_INFORMATION_DISCIPLINE.md`.

Typical gaps:

```text
latest decision source;
project phase;
submitted material in permit / notice;
PLU / ABF status;
support type;
technical system;
estimate;
client approval;
CCTP status;
enterprise capability;
```

## Final rule

```text
A material option is not a decision.
A render is not an approval.
A client preference is not a regulatory clearance.
A technical possibility is not an economical choice.
Pantheon frames the decision; the architect decides.
```
