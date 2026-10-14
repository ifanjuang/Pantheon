---
name: administrative-form-review
description: "Use to prepare or review a CERFA or another administrative filing form when every populated field must be traced to a source, uncertainty preserved and filing or signature kept behind a human gate."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: THEMIS
  governed_by: docs/domain-packs/architecture/METHOD_RUN_TESTS.md
---

# Administrative form review

Treat every populated field, box and attachment declaration as a claim.

## Required method

1. Identify the exact form, edition, destination, procedure and declared filing
   purpose. Do not substitute a remembered or similarly named form.
2. Inventory mandatory fields and attachments before filling. Map each value to
   an exact source and locator, a user-confirmed value, a derived calculation or
   an explicit unknown.
3. Check cross-field consistency, units, dates, identities, areas, references,
   signatures and attachment declarations. Show derivations.
4. Never guess a missing value. Leave it unresolved and ask only when it blocks
   the intended candidate.
5. Render or inspect the completed candidate when layout affects meaning.

## Result contract

Return: form identity and edition; field/source ledger; derived values;
uncertain or missing fields; attachment checklist; consistency findings; draft
readiness. Filing, signing and representing the document as final require the
applicable human decision gate.

```text
field populated != field proven
blank avoided != uncertainty resolved
form candidate != signed filing
```
