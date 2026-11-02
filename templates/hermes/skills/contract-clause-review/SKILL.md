---
name: contract-clause-review
description: "Use to review a contract, specification, CCAP, amendment, notice or contractual correspondence for source-located gaps, ambiguities and questions. It prepares a bounded review; it does not provide legal advice or decide contractual validity."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: THEMIS
  governed_by: docs/domain-packs/architecture/METHOD_DECK.md
  related_skills: [architectural-issue-framing, project-context]
---

# Contract clause review

Review the exact document before characterizing a clause. Reuse an already
identified exact source; otherwise use Hindsight once to locate it, then use
Docling only for the identified passages. When a legal, regulatory, insurance
or technical rule is needed to assess the project document, obtain the admitted
DOCUMENTAIRES or authoritative source separately.

Do not infer a document's contents or review scope from its filename. A single
file may combine several documents, sections, appendices or forms. Use the
internal structure returned by Hindsight as a navigation lead, then confirm the
relevant boundaries in the source's own contents, headings or labels. Read and
cite the requested section and only the cross-referenced passages needed for
the question; do not read an entire composite file when the task concerns a
bounded part.

For an assessment against guidance represented in Hindsight Knowledge, follow
`project-context/references/professional-source-routing.md`. A relevant
Knowledge entry may serve as the comparison basis when it identifies the
reference and contains enough criteria; do not open the underlying file merely
to repeat that retrieval. Record its identity, available version/date and the
criteria actually returned. Attribute them to the Knowledge entry, not to an
uninspected original. If the user asks to verify or quote the original, confirm
its edition or completeness, inspect the exact original and cite its locators.
Read the contract or other project document itself for the project-side
comparison.

When the benchmark is a checklist, standard, policy or recommendation, identify
its scope and available edition, and distinguish guidance from the operative
project clause. Do not present a checklist topic as a binding requirement unless
the applicable governing source supports that conclusion.

Do not ask the user to identify a reference before checking whether one focused
Knowledge recall resolves it. Ask only if materially different candidates remain
and the choice changes the conclusion. If the available criteria support a
bounded answer, state the reference and its limits, answer first, and offer any
deeper source check afterward.

## Method

When the user asks what matters to the project or whether the document is
sufficient, use `architectural-issue-framing` briefly before or during the
contract review. Keep the framing to the main issue and priorities; do not add
a second full review or repeat the contract findings.

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
contract version is unresolved. Ask one focused blocking question only when it
prevents a useful bounded answer; otherwise put optional next steps after the
answer.

```text
keyword not found != clause absent
project clause != applicable law
draft clause != validated contractual wording
review finding != instruction or legal advice
```
