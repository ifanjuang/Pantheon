---
name: construction-cost-review
description: "Use for construction estimates, bids, quotes, invoices, change proposals or lot-cost comparisons that require scope coverage, exclusions, variants, tax basis and price comparability to be checked before any overall conclusion."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: HEPHAISTOS
  governed_by: docs/domain-packs/architecture/FINANCIAL_LOT_INSURANCE_REVIEW.md
  compatibility_alias: quote-variation-review
---

# Construction cost review

Own the economic comparison; do not infer acceptance, execution, insurance,
payment entitlement or approval from the presence of a price document.
This is the general owner. The older `quote-variation-review` remains only for
compatibility with its narrow versioned example manifest; do not load both.

## Required method

1. Identify the reference estimate, DPGF, CCTP or user-declared perimeter and
   its date, revision, tax basis and included or excluded work.
   Read long documents through overview, targeted search and bounded anchors;
   never request a full Markdown export or use terminal/file access for a
   spilled result. A slow successful Docling conversion is not an outage; on a
   real Docling error, retry the same bounded call once only when the service
   supplies a recovery delay, otherwise record the source as unreadable and
   continue `ready_with_limits`.
2. Build the lot and line coverage matrix from that reference before opening
   candidate totals. Use the states defined in
   `pantheon-governed-method/references/source-review.md`.
3. Before opening individual offers, enumerate the complete candidate-source
   family in the selected project (including all quote/devis, ACT consultation,
   revised offer and lot folders). State the count and exact paths selected.
   A search hit, one opened quote or a remembered summary never establishes the
   received-offer set. If the expected family cannot be enumerated, do not say
   "all received quotes"; state the verified subset and use
   `ready_with_limits`.
4. For every enumerated offer or quote, verify issuer, date, validity, scope,
   quantities, options, exclusions, allowances, tax and total from the exact
   document. Record every candidate that cannot be opened as
   `unreadable_or_unverified`; do not silently drop it.
5. Normalize only comparable items. Keep base, variant, option, provisional
   sum and combined scope distinct. Never compare a partial aggregate with a
   broader reference total.
6. Report supported deltas, scope differences, missing offers, unreadable
   material, commercial qualifications and decisions still required.

## Comparison gate

Before displaying a delta or a status, verify the reference, candidate scope,
common basis and readable locators. Otherwise return no conclusion. Read
[references/claim-level.md](references/claim-level.md) for incomplete or
garbled material.

## Claim level

Read [references/claim-level.md](references/claim-level.md) when the request
distinguishes an opinion on the available quotes from a complete consultation
analysis, or when source coverage is incomplete.

## Result contract

Return: reference perimeter; coverage matrix; comparable amounts and deltas;
scope or assumption differences; missing or unresolved lots; sources and
locators; readiness. If a material reference lot has no received offer, label
it `missing_candidate`; do not call the whole consultation conforming.

```text
received != accepted
priced != included
comparable != conforming
offer present != lot covered
amount extracted != amount comparable
```
