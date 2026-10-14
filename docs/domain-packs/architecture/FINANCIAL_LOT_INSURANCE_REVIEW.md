# Architecture Financial, Lot Scope and Insurance Review

Status: candidate — workflow doctrine for architecture-domain review of invoices, quotes, extra works, lot allocation and insurance coverage.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It is not legal advice, accounting validation, payment approval, contract interpretation authority, professional validation, insurer confirmation or execution instruction.

It does not implement a runtime, connector, OCR pipeline, accounting tool, Notion write, email sending, payment workflow, insurance verification service, approval engine or Registre Probatoire entry.

## Purpose

This workflow covers a recurrent architecture-agency situation:

```text
An enterprise sends an invoice, progress payment, quote for extra works, change request or claim.
The architect must understand whether it is formally usable, compatible with progress, justified by the market, assigned to the right lot and covered by the company insurance scope.
```

The workflow must prevent a dangerous collapse between:

```text
document received;
amount extracted;
works described;
works executed;
works included;
works accepted;
works insured;
works payable;
works approved.
```

None of those statuses implies the others automatically.

## Trigger

The workflow may be opened from:

```text
invoice received;
progress payment request;
quote for extra works;
avenant proposal;
enterprise claim;
site observation leading to financial impact;
mail asking whether an item is due;
client question about whether to pay or accept;
contractor request to proceed with a paid extra.
```

## Required posture

The output is always candidate-only unless a specific human approval gate changes status.

Allowed outputs:

```text
Invoice Intake Candidate;
Quote Intake Candidate;
Document Form Check Candidate;
Context Pack Candidate;
Progress Match Candidate;
Justification Matrix Candidate;
Lot Scope Check Candidate;
Cross-Lot Allocation Candidate;
Insurance Coverage Candidate;
Risk Flags Candidate;
Payment / Change Order Review Candidate;
Notion Finance Observation Candidate;
Draft Mail Candidate;
Review Card Candidate;
Capability Gap.
```

Forbidden outputs:

```text
bon a payer;
invoice approval;
payment order;
avenant acceptance;
order to contractor;
recognition of debt;
final legal conclusion;
final accounting conclusion;
final insurance coverage conclusion;
Registre Probatoire entry;
external email send;
Notion write without approval;
canonization of project memory.
```

## Core question

The workflow answers one governed question:

```text
Is this item admissible for human decision, and what blocks or qualifies that decision?
```

It must not answer automatically:

```text
Should we pay?
Should we accept the quote?
Is the company definitely insured?
Is the item legally due?
```

Those are human and professional decisions.

## Source hierarchy

The review should retrieve, if available:

```text
1. received invoice / quote / claim;
2. signed market / AE;
3. CCAP;
4. CCTP for the claimed lot;
5. CCTP for adjacent or possibly competent lots;
6. DPGF / BPU / DQE / initial quote;
7. accepted options;
8. avenants and OS;
9. site meeting reports;
10. photos and observations;
11. previous situations / invoices / payments;
12. reserves and non-conformities;
13. enterprise mails and client mails;
14. BET / economist / control office notes;
15. insurance certificate;
16. insurer confirmation or nominative certificate if required.
```

If a required source is absent, the workflow returns a Capability Gap instead of improvising.

## Step 1 — Document type classification

Classify the received document:

```text
invoice;
progress payment request;
advance invoice;
final invoice;
initial quote;
quote for extra works;
avenant proposal;
claim;
credit note;
unclear document.
```

Extract:

```text
project;
enterprise;
lot;
document date;
document number;
amount HT;
VAT rate;
amount TTC;
payment deadline;
market / quote / avenant reference;
work item labels;
location;
quantities;
unit prices;
conditions;
exclusions;
claimed justification.
```

Output:

```text
Invoice / Quote Intake Candidate
```

## Step 2 — Formal document check

The review checks whether the document is usable for decision.

Invoice form indicators:

```text
invoice number;
date;
enterprise identity;
SIRET / SIREN;
VAT details where applicable;
client identity;
project / site reference;
description of works;
quantity / unit / unit price where relevant;
HT / VAT / TTC;
payment terms;
references to quote, market, situation, OS or avenant;
retention / advance / previous payment handling where relevant.
```

Quote / extra works form indicators:

```text
date;
enterprise identity;
project / site;
lot;
object;
location;
precise designation;
quantity;
unit;
unit price;
labour / material split if useful;
time impact;
validity period;
VAT;
HT / TTC;
conditions;
exclusions;
whether work is already executed or proposed;
link to instruction, request, OS or avenant.
```

Output:

```text
Document Form Check Candidate
status: usable | incomplete | vague | inconsistent | unusable_for_decision
```

## Step 3 — Context retrieval

Before assessing justification, retrieve project context:

```text
current phase;
current contract status;
lot attribution;
market amount;
works progress;
previous invoices / situations;
approved avenants / OS;
open reserves;
open observations;
site reports;
contractual hierarchy;
client decisions;
enterprise explanations;
BET / economist input.
```

Output:

```text
Context Pack Candidate
```

## Step 4 — Progress match

Each claimed or invoiced item is compared to progress evidence.

Statuses:

```text
executed_and_observed;
partially_executed;
not_observed;
not_executed;
executed_but_reserved;
executed_but_nonconforming_candidate;
not_verifiable_from_available_sources;
already_paid_candidate;
duplicate_candidate;
premature_billing_candidate.
```

Output:

```text
Progress Match Candidate
```

## Step 5 — Justification matrix

Each line is classified against the market and project history.

Possible line classifications:

```text
included_in_initial_market;
accepted_option;
approved_avenant;
approved_OS;
client_requested_extra_candidate;
enterprise_requested_extra_candidate;
site_adaptation_candidate;
correction_of_enterprise_error_candidate;
correction_of_design_error_alleged;
reserve_or_rework_candidate;
already_in_CCTP_candidate;
explicitly_excluded_candidate;
wrong_lot_candidate;
ambiguous;
requires_arbitration.
```

The matrix should include:

```text
line ref;
description;
amount;
claimed reason;
market source;
progress source;
approval source;
status;
risk;
recommended handling.
```

Output:

```text
Justification Matrix Candidate
```

## Step 6 — Lot scope check

The review identifies whether the item belongs to the enterprise lot.

Inputs:

```text
CCTP of claimed lot;
CCTP of adjacent lots;
AE / market attribution;
interfaces and exclusions;
technical nature of item;
site observation;
BET / economist note.
```

Statuses:

```text
in_lot;
interface_with_lot;
possibly_other_lot;
explicitly_excluded;
not_found;
ambiguous;
requires_arbitration.
```

Example:

```text
Item: structural lintel reinforcement.
Claimed by: external joinery lot.
Likely lot: masonry / structure / metalwork depending CCTP.
Joinery lot: interface only.
Status: possibly_other_lot / requires_arbitration.
```

Output:

```text
Lot Scope Check Candidate
Cross-Lot Allocation Candidate
```

## Step 7 — Insurance coverage check

The review checks whether the enterprise insurance certificate appears to cover the specific technical item.

This check is candidate-only.

It must never declare final insurance coverage without explicit human and, if needed, insurer confirmation.

Inputs:

```text
enterprise identity;
SIRET / SIREN;
insurance certificate;
contract number;
insurer;
validity period;
opening date of site;
covered activities;
technical processes covered;
geographic scope;
operation / market limits;
exclusions or limits;
item technical nature;
lot scope classification.
```

Coverage statuses:

```text
match_candidate;
partial_match_candidate;
ambiguous;
no_match_candidate;
missing_attestation;
expired_or_wrong_period_candidate;
enterprise_identity_mismatch;
operation_not_declared_candidate;
technique_not_confirmed;
requires_nominative_certificate;
requires_insurer_confirmation;
requires_arbitration.
```

Examples:

```text
Item: reinforcement in load-bearing wall.
Enterprise certificate: external joinery only.
Coverage candidate: no_match_candidate / requires insurer confirmation.
```

```text
Item: under-tile waterproofing system.
Enterprise certificate: floor and wall tiling only.
Coverage candidate: partial_match_candidate / technique_not_confirmed.
```

Output:

```text
Insurance Coverage Candidate
```

## Step 8 — Risk flags

Typical flags:

```text
invoice_form_incomplete;
quote_too_vague;
missing_OS;
missing_avenant;
missing_client_approval;
wrong_lot_candidate;
insurance_scope_gap;
expired_insurance_candidate;
works_already_executed_without_approval;
item_already_included_candidate;
item_already_paid_candidate;
premature_billing_candidate;
reserve_not_lifted;
nonconformity_candidate;
VAT_incoherence_candidate;
retention_or_advance_unchecked;
price_without_quantity;
claim_without_source;
external_action_requested;
```

Each flag should include:

```text
flag_id;
severity;
source refs;
consequence_if_ignored;
recommended handling;
```

Output:

```text
Risk Flags Candidate
```

## Step 9 — Review card and decision gate

The cockpit must answer quickly:

```text
document type;
amount;
enterprise;
lot claimed;
likely lot;
market status;
progress status;
justification status;
insurance status;
OS / avenant status;
risk level;
external action status;
human decision expected.
```

Verdict examples:

```text
Do not validate the quote as extra works in its current form.
The item may belong to another lot and insurance coverage is not demonstrated.
Request detailed breakdown, lot allocation review and updated insurance certificate before decision.
```

```text
Invoice is partially consistent with progress, but payment should remain candidate-only until prior situations, reserves and retention are checked.
```

Output:

```text
Review Card Candidate
User Decision Gate Candidate
```

## Step 10 — Action candidates

Allowed actions after review:

```text
request clarification from enterprise;
request detailed quantity / unit price breakdown;
request updated insurance certificate;
request nominative certificate;
request insurer confirmation;
request economist review;
request BET review;
prepare refusal candidate;
prepare partial validation candidate;
prepare Notion finance observation;
prepare CR observation;
prepare internal arbitrage note;
prepare draft mail candidate.
```

All external messages and state-changing writes require a visible gate.

## Notion write posture

A Notion line may be prepared as candidate:

```text
Notion Finance Observation Candidate
```

It may include:

```text
project;
enterprise;
lot;
document ref;
amount;
status;
risk;
lot allocation;
insurance status;
missing documents;
recommended next action;
validation status.
```

It must not be written as validated state unless the user approves the exact content and destination.

## Review statuses

Recommended high-level statuses:

```text
reviewable;
form_incomplete;
progress_unverified;
justification_insufficient;
wrong_lot_candidate;
insurance_gap_candidate;
requires_arbitration;
blocked;
ready_for_user_decision_gate;
```

## Capability gaps

Safe gaps:

```text
missing_market;
missing_CCTP;
missing_CCAP;
missing_AE;
missing_OS_or_avenant;
missing_previous_situations;
missing_progress_evidence;
missing_insurance_certificate;
insurance_certificate_unreadable;
covered_activity_unclear;
wrong_period;
source_version_unknown;
amount_breakdown_missing;
lot_scope_ambiguous;
approval_missing;
```

## Final rule

```text
A received invoice or quote is not a decision.
A described item is not necessarily in the enterprise lot.
A decade insurance certificate is not necessarily coverage for the specific work.
A runtime analysis is not a bon a payer.
Pantheon surfaces the candidate status, gaps and gates.
The human decides.
```
