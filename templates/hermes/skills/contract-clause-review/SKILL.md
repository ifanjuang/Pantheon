---
name: contract-clause-review
description: "Use to review a contract, specification, CCAP, amendment, notice or contractual correspondence for source-located gaps, ambiguities and questions. It prepares a bounded review; it does not provide legal advice or decide contractual validity."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: THEMIS
  governed_by: docs/domain-packs/architecture/METHOD_DECK.md
---

# Contract clause review

Review the exact document before characterizing a clause. Use Hindsight first
to locate the source and avoid needless extraction; use Docling only for the
identified passages. When a legal, regulatory, insurance or technical rule is
needed to assess the project document, obtain the admitted DOCUMENTAIRES or
authoritative source separately.

## Method

For each point, distinguish: observed wording with locator; absence not
established; ambiguity; external rule to verify; and practical question for the
appropriate reviewer. A keyword search or an omitted search result does not
establish that a clause is absent. Do not infer a legal obligation, jurisdiction,
guarantee, insurance consequence, professional fault or contract validity from
the project document alone.

Do not propose replacement wording before the document review is synthesized
and the user selects that deliverable. A clause candidate is a draft for human
legal/contractual review, never a ready-to-insert clause or legal advice.

## Return contract

Return a compact matrix: exact source and locator; observed clause or verified
gap; uncertainty; required external reference or reviewer; and readiness. Use
`ready_with_limits` when a material passage, applicable rule, party status or
contract version is unresolved. Ask up to five materially distinct follow-up
choices only when they change the review or deliverable.

```text
keyword not found != clause absent
project clause != applicable law
draft clause != validated contractual wording
review finding != instruction or legal advice
```
