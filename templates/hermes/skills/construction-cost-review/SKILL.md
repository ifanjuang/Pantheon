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
2. If a specific offer is named and its exact source is known, inspect it
   directly; do not inventory the whole dossier or other offers. Build the lot
   and line coverage matrix from the reference using the states defined in
   `pantheon-governed-method/references/source-review.md`.
3. Enumerate the candidate-source family only when the user asks for all offers,
   a complete consultation comparison, or completeness across candidates. In
   that case, record the verified count and exact paths; if the family cannot be
   established, report the verified subset and use `ready_with_limits`.
   A request for the least expensive company by lot is a comparison across the
   offers available for those lots: use the lot structure to organize the
   comparison, then locate the corresponding offers and establish whether the
   candidate set is complete. Do not treat the highest lot number or a partial
   set of recalled offers as a complete list.
4. For each offer within the requested comparison, verify issuer, date,
   validity, scope, quantities, options, exclusions, allowances, tax and total
   from its exact document. Record candidates that cannot be opened as
   `unreadable_or_unverified`; do not silently drop them or imply completeness.
5. Normalize only comparable items. Keep base, variant, option, provisional
   sum and combined scope distinct. Never compare a partial aggregate with a
   broader reference total.
6. Report supported deltas, scope differences, unreadable material, commercial
   qualifications and decisions still required. Mention missing offers only
   when completeness was part of the requested scope and the family was checked.

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
