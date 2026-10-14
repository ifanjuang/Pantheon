---
name: quote-variation-review
description: Use when reviewing a complementary quote (devis complémentaire) against the prior signed amendment and the project dossier, to produce a candidate opinion and the points to verify. Never approves the quote, advises payment as final, or sends anything.
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_capability_id: quote-variation-review
  governed_by: docs/examples/vertical_devis_reprise/workflow_manifest.devis-reprise.yaml
  upstream: agentskills.io SKILL.md standard; loadable by Hermes Agent (NousResearch) >= 0.18
  compatibility_target: construction-cost-review
---

# Quote variation review (governed candidate)

Compatibility adapter for the versioned `devis-reprise` example. When
`construction-cost-review` is installed, use that general owner and do not load
both skills. Do not project this adapter into a current profile.

Non-executable candidate skill in the `agentskills.io` / `SKILL.md` standard, so a
Hermes Agent can load it. Pantheon governs; Hermes executes outside the repo.

## When to use
A complementary quote adds a plus-value whose amount or scope is unclear or may not
reconcile with a prior signed amendment. Produce a candidate opinion and a draft, not
a decision.

## Governed boundary
- Allowed outputs: candidate opinion; point to verify; amount/scope discrepancy note;
  capability gap.
- Forbidden: approving the quote; final payment advice; external send; "quote
  validated"; promoting a Registre Probatoire entry.
- A discrepancy is returned as a point to verify, not a decision. `forged != authorized`.
