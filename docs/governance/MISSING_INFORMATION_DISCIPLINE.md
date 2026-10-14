# Missing Information Discipline

Status: candidate — transverse discipline for required information, missing information, assumptions and deductions.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a runtime, extractor, router, scheduler, queue, UI, schema, memory engine, approval engine, document generator or automatic question-asking system.

It defines a candidate governance rule for all workflows that produce professional outputs from incomplete sources.

## Purpose

Professional drafting must not fill consequential gaps by imagination.

This discipline applies to:

```text
CCTP from plans;
Cerfa filling;
architectural descriptions;
site report finalization;
photo chantier analysis;
invoice / quote review;
lot and insurance review;
DTU / normative source checks;
client response drafting;
Notion / register write candidates.
```

The system must locate, classify and expose missing information before producing a stronger output.

## Core rule

```text
Do not invent.
Search first.
Cross-check sources.
Infer only when low-risk and clearly supported.
Ask when the gap matters.
Block or produce an explicitly incomplete candidate when the gap is consequential.
```

## Required Information Map

Every output type should define the information it normally needs.

Examples:

### CCTP Draft Candidate

```text
project identity;
phase;
plan index and date;
scale / legibility;
lot structure;
works existing / demolished / created;
materials;
locations;
interfaces;
technical constraints;
BET notes when relevant;
normative references when relevant;
output granularity expected.
```

### Cerfa Fill Candidate

```text
authorization type;
current official form version;
project address;
cadastral references;
applicant identity;
land ownership / authorization status;
existing and created surfaces;
emprise au sol;
destination / subdestination;
parking / networks / trees where applicable;
attachments required;
signature / certification fields.
```

### Site Report Candidate

```text
project;
visit date;
phase;
attendees / absentees;
previous report;
open points;
new observations;
photos;
lot and enterprise attribution;
delays;
blockers;
support acceptances;
next meeting;
actions and due dates.
```

### Invoice / Quote Review Candidate

```text
document type;
enterprise;
lot;
amount;
market / AE;
CCTP;
CCAP;
OS / avenant;
progress evidence;
previous situations;
insurance certificate if technical scope requires it;
justification and breakdown.
```

These maps are not exhaustive. They are starting points that domain packs or reflex packs may refine.

## Missing Information Register

When information is missing, record it explicitly.

Minimum fields:

```text
missing_info_id;
requested_output;
information_needed;
why_needed;
expected_source;
criticality: blocking | important | useful | optional;
consequence_if_missing;
question_to_user;
search_status: not_searched | searched_not_found | source_found_unreadable | source_found_conflicting;
current_status: missing | answered | inferred | waived | blocked;
```

Criticality rules:

```text
blocking:
  output cannot be produced safely without it.

important:
  output can be drafted, but must be marked incomplete and not transmissible.

useful:
  output can proceed with a visible assumption or note.

optional:
  output quality improves, but the task is not materially affected.
```

## Contradiction handling

A contradiction is not a gap.

The Core rule's loop — search, cross-check, infer or ask — assumes that more
searching moves a question toward resolution. A contradiction breaks that
assumption: once two admitted sources make incompatible claims about the same
object, further searching does not resolve the tension. It can only add a third
opinion. The `source_found_conflicting` search outcome above is therefore not
one more case of "not yet found" — it is a different terminal state, reached
instead of "found" rather than on the way to it.

```text
gap            -> search reduces uncertainty
contradiction  -> search cannot reduce the tension, only the sources cited
```

The discipline for a contradiction is preservation, not resolution:

```text
record both (or all) conflicting claims explicitly;
preserve provenance, revision and scope for each;
do not silently prefer one source, one date or one format over another;
do not average, merge or split the difference between conflicting values;
expose the tension rather than resolving it into a single output value;
route to a human decision when the contradiction is consequential.
```

This is already implemented, not merely proposed, for scalar ProjectClaims:
`implementation/mvp_vertical/project_claim_conflicts.py` detects unresolved
tension between active Claims and is explicit that detection is not resolution
(`resolves_conflict: False`, `merges_identity: False`). Its own limitations
state that the detector reaches only scalar Claim values; a contradiction
between representations, geometry or relations is not detected there and must
still be caught by this discipline's search and ask policies until a
demonstrated need justifies extending it.

```text
conflict detected  != conflict resolved
contradiction      != gap
more searching     != tension reduced
one source winning != contradiction handled
```

## Assumption Ledger

Any inferred or assumed element must be tracked.

Minimum fields:

```text
assumption_id;
statement;
source_support;
reasoning;
confidence: low | medium | high;
risk_if_wrong: low | medium | high;
allowed_use;
forbidden_use;
needs_confirmation: yes | no;
status: assumption | inferred | confirmed | rejected;
```

## Deduction policy

Deduction is allowed only when all of the following are true:

```text
1. at least one clear source supports it;
2. the consequence is low or reversible;
3. it is displayed as deduction or assumption;
4. it does not create external action;
5. it does not validate a contractual, financial, regulatory, structural, insurance, normative, memory or responsibility status.
```

Examples of acceptable low-risk deductions:

```text
room name from plan label;
probable lot from an already-classified CR point;
project address from a cartouche when the same address appears in the dossier;
phase when explicitly shown in the file name and cartouche.
```

Examples of forbidden deductions:

```text
structural adequacy;
insurance coverage;
DTU compliance;
urbanism compliance;
surface regulatory values;
payment status;
quote acceptance;
formal notice threshold;
responsibility attribution;
validated support acceptance;
external send authorization;
canonical memory promotion.
```

## Ask policy

Ask the user when:

```text
information is blocking;
information is ambiguous and affects consequence;
multiple sources conflict and the contradiction is consequential (see Contradiction handling above — asking here means presenting the tension, not asking which source to discard);
the target object is unclear;
the project / phase / recipient is unclear;
an image does not show enough;
a plan legend or scale is unreadable;
a source version is unknown for consequential work;
an approval or write target is unclear.
```

Questions must be targeted.

Bad:

```text
Please provide more information.
```

Good:

```text
Is the transmitted plan the latest DCE index?
Is there a structural note for the enlarged opening?
Should the CCTP be split by lot or drafted as a general descriptive note?
Is this photo related to the existing point 3.2 or a new observation?
Do you want this as a Notion observation candidate or only as a CR note candidate?
```

## Search before asking

Before asking, the system should search within the admitted context when available and proportional to depth.

Fast depth:

```text
current user input;
visible attachment metadata;
obvious missing information.
```

Normal depth:

```text
latest CR;
open observations;
project context;
lot likely concerned;
recent relevant material.
```

Deep depth:

```text
full Context Pack;
CCTP / CCAP / AE;
OS / avenants;
insurance;
DTU / official sources;
financial history;
relevant correspondence;
Evidence Pack Candidate.
```

If search is not possible or a connector is unavailable, return a Capability Gap.

## Production with gaps

The system may produce a draft with gaps only if the output is clearly marked.

Allowed statuses:

```text
complete_candidate;
incomplete_candidate;
blocked;
to_verify;
needs_user_input;
ready_for_user_decision_gate;
```

Draft with gaps must include:

```text
what was used;
what was not found;
what was assumed;
what must be confirmed before transmission;
which parts should not be relied on.
```

## Compact output format

Default compact block:

```text
Information status:
- Found:
- Missing blocking:
- Missing useful:
- Assumptions:
- Questions:
- Output possible: yes/no, candidate only
```

Detailed register can be opened on demand or when Deep depth is required.

## Interaction with Workflow Depth Policy

Missing-information handling must remain proportionate.

```text
Fast:
  identify obvious gaps and ask 1-3 targeted questions.

Normal:
  search bounded context and maintain a short Missing Information Register.

Deep:
  create full Missing Information Register + Assumption Ledger + Evidence Pack Candidate when consequence requires it.
```

## Interaction with learning

If the same missing-information pattern recurs, the system may propose a Required Information Map improvement.

Example:

```text
Repeated gap: users often request CCTP from plan without specifying phase or lot split.
Candidate improvement: CCTP-from-plan reflex should ask phase + lot structure first unless already present.
```

This is a Learning Candidate. It is not automatically promoted.

## Final rule

```text
A missing source is not a blank to fill.
It is a status to expose.
If it is low-risk, it may be assumed visibly.
If it is consequential, ask or block.
```
