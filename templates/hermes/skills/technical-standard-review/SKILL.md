---
name: technical-standard-review
description: "Use to analyze a DTU or another construction standard when the exact text, edition, effective date, scope, project applicability and distinction between normative requirements and recommendations matter."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: THEMIS
  governed_by: docs/domain-packs/architecture/DOCUMENT_REVIEW.md
---

# Technical standard review

Own applicability and text-grounded interpretation. Model knowledge, a title,
snippet or secondary summary cannot substitute for the exact admitted edition.

## Required method

1. Identify the question, work type, materials, exposure, date, jurisdiction,
   contract references and exact standard part, edition and amendments.
2. Confirm scope, exclusions, definitions and effective or contractually cited
   edition before extracting a rule.
3. Quote sparingly and locate precisely. Distinguish normative requirement,
   permitted solution, recommendation, informative note and professional
   interpretation.
4. Test the project facts against every condition of applicability. Surface
   missing facts, exceptions, interacting standards and contractual hierarchy.
5. State the conclusion at issue level; do not claim global project conformity
   from a bounded standard review.

When a project source and a standard appear to disagree, keep the project
statement and the standard's requirement as separate claims. Check whether they
address the same object, phase, date, scope, units and conditions; then classify
the relation as an apparent difference, a missing applicability fact, a stale
source or a direct conflict. Do not make either source erase the other. Identify
the applicable legal and contractual hierarchy for the specific issue; if the
inspected sources do not establish it, leave the result `to_verify` or
`to_arbitrate` and name the needed review.

## Result contract

Return: exact standard identity; applicability frame; relevant provisions and
locators; project facts used; condition-by-condition analysis; relationship
between each project and reference claim; contradictions, missing data and
limits; readiness. If the exact applicable text is unavailable,
return `blocked` or `needs_user_input`, not a reconstructed rule. Common
practice may still be stated as `assumption_only`, without number, edition or
locator, together with the source that would confirm it.

Search the knowledge vault first, then the web, and say which was used. Write
a standard reference, section or value only when it appears in a passage read
in this conversation; a related standard recalled from memory is not cited. A
section from the tool's `citation` is the section; a printed page is not the
PDF page.

```text
standard recalled != standard inspected
rule exists != rule applicable
bounded check != global conformity
```
