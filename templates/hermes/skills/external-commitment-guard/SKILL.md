---
name: external-commitment-guard
description: Use before any candidate content or action could affect an external party or system, to detect implied approval, instruction, filing, publication, contractual commitment or transmission and to open the applicable User Decision Gate. Authorizes nothing by itself.
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_capability_id: external-commitment-guard
  governed_by: docs/examples/vertical_devis_reprise/workflow_manifest.devis-reprise.yaml
  upstream: agentskills.io SKILL.md standard; loadable by Hermes Agent (NousResearch) >= 0.18
---

# External commitment guard (governed candidate)

Non-executable candidate skill in the `agentskills.io` / `SKILL.md` standard. It opens
a gate; it never sends. Pantheon governs; Hermes executes outside the repo.

## When to use
Before any candidate content or action crosses from the current governed
interaction into an external audience, system or real-world effect.

## Governed boundary
- Allowed outputs: open the User Decision Gate; risky-wording/action note;
  safer candidate; recipient/object/scope check; capability gap.
- Forbidden: external send, filing, publication or mutation; sign; enterprise
  instruction; final approval; promoting a Registre Probatoire entry.
- The guard opens the gate; the human decides. The draft is the system's; the signature
  and the send remain the human's.
