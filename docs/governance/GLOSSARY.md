# Glossary

Status: canonical — phase 1 terminology baseline.
Boundary profile: active_governance_doctrine.

This glossary clarifies Pantheon Next vocabulary. It also records the one governed rename in progress: "memory" is reserved to Hermès, and Pantheon governs the `Registre Probatoire` in place of "Canonical Memory" (see `REGISTRE_PROBATOIRE_DIRECTION.md`). This file is the owner of the certainty and decision axes.

## Core doctrine

## Terms

### Pantheon Role

A canonical governance role defined in `docs/governance/AGENTS.md`.

A Pantheon Role may define authority, scope, escalation rules, approval boundaries and evidence requirements.

A Pantheon Role is not an executable runtime agent.

### Hermes Profile

A runtime-facing execution profile template under `hermes/profiles/<profile>/`.

A Hermes Profile may execute under Task Contract and produce candidates.

A Hermes Profile must not govern, approve, canonize, promote memory or merge code.

A Hermes Profile is admitted for a demonstrated runtime boundary, not merely to mirror a Pantheon Role or cognitive function.

### Pantheon Skill

A governed capability contract defined by Pantheon policy.

A Pantheon Skill describes what may be done, under which constraints, with which evidence and approval requirements.

### Hermes Skill

An executable capability available to Hermes Agent.

A Hermes Skill executes only when allowed by Task Contract and governance policy.

### Task Contract

The execution contract that defines scope, inputs, limits, allowed capabilities, approval ceilings, evidence requirements and expected outputs.

### Evidence Pack

The structured proof bundle attached to a candidate output or operation.

It records sources, assumptions, commands, outputs, risks, rollback notes and validation state.

### Role Signal

A governed signal emitted by a role or execution surface to request review, escalate risk, report a capability gap or produce a candidate.

### Registre Probatoire

The governed evidence register: the rigorous, citeable record of evidence with certainty levels, exhibits (pièces), dates and citations. It replaces the former term "Canonical Memory".

It is the only basis Pantheon allows for a consequential decision. An entry is not binding until approved through the required path. Detailed in `REGISTRE_PROBATOIRE_DIRECTION.md` and `EVIDENCE_MEMORY_CANONICALIZATION.md`.

### Hermès memory

The execution runtime's own memory (mem0 or another system). It is free, self-evolving and ungoverned by Pantheon.

Hermès memory may propose and recall; it carries no authority. It is not a Registre Probatoire entry and may not be cited for a consequential decision.

### Register Candidate (formerly Memory Candidate)

A proposed entry for the Registre Probatoire: a sourced claim awaiting review.

It is not a Registre Probatoire entry until approved under Pantheon policy. "Memory Candidate" is the former name, retained where not yet migrated; the concept now feeds the register, not a Pantheon-owned memory.

### Candidate

A proposed output produced by Hermes or another execution surface.

A candidate is not canonical and not validated by default.

### Canonical

A validated source of truth governed by Pantheon policy.

Canonical status requires the appropriate approval path.

## Certainty and decision axes

These four axes answer four different questions. They are distinct and must not be conflated or merged into one scale. This file owns their names; the detailed levels are owned where noted.

### E0–E4 — probative certainty

"How trustworthy is this piece of evidence?" Owned here; carried by the Registre Probatoire.

```text
E0  no usable source — unsupported or rejected
E1  weak — a single unconfirmed or low-trust source
E2  plausible — sourced but not corroborated, or not fresh
E3  strong — corroborated, dated and attributed
E4  established — corroborated, fresh, attributed, and human-confirmed where consequential
```

A certainty level is not an approval, not an answer-verification level and not a consequence level.

### V0–V4 — answer verification

"Is this answer verified?" The axis name is owned here; the detailed levels are owned by the Answer Verification Gate (candidate, see `ANSWER_VERIFICATION_GATE.md` when promoted) and reconciled against this glossary. The answer-verification axis must use `V`, never `C`, so it does not collide with the approval ceiling.

### K0–K4 — consequence level

"What consequence class would acting on this answer or capability create?" The axis name is owned here; detailed operational use belongs to the Answer Verification Gate / answer status proposal until promoted. `K` is used so it does not collide with `C0–C5` approval ceilings.

```text
K0  no consequential effect — orientation, formatting, local display or harmless draft
K1  low consequence — reversible internal effect with no external commitment
K2  bounded consequence — professional work support, still internal or clearly draft
K3  consequential — client, project, register, scope or external-action impact possible
K4  critical consequence — legal, financial, safety, contractual, irreversible or public effect
```

A consequence level is not proof and not approval. It helps decide whether the chokepoint and approval ceiling must engage.

### C0–C5 — approval ceiling

"What clearance is required to act?" Owned by `APPROVALS.md`; used by the MCP capability passport. Not redefined here.

## Critical distinctions

Hermes done does not mean Pantheon validated.

Candidate does not mean canonical.

OpenWebUI Knowledge Base is not a Registre Probatoire entry.

Hermès memory (free runtime recall) is not a Registre Probatoire entry, and may not be cited for a consequential decision.

Probative certainty (E), answer verification (V), consequence level (K) and approval ceiling (C) are four distinct axes.

A Hermes Profile does not replace a Pantheon Role.

## Canonical spelling

Use `HEPHAISTOS` for the Pantheon Role.

Do not use `HEPHAESTUS` as the canonical Role spelling.

There is no canonical Hermes profile named for HEPHAISTOS. A future profile, if any, must be named for and justified by its actual runtime boundary rather than by the Role name.

## Bilingual terms (EN ↔ FR)

Language direction (arbitration B-6): internal governance is EN-dominant; the
professional-facing surfaces (README, landing, cockpit, architecture domain pack)
are FR. This single table is the shared reference so the two do not drift; do not
duplicate it into a separate glossary. FR is the working term for a surface; EN
stays the canonical spelling for governance and code.

| EN (canonical) | FR (surface) | Note |
|---|---|---|
| Governance | Gouvernance | Pantheon governs; it does not execute. |
| Chokepoint | Point de contrôle (goulot de gouvernance) | Where a consequential effect passes the policy check. |
| Capability passport | Passeport de capacité | Data declaration carried by each capability. |
| Task Contract | Contrat de tâche | The bounded frame of a Hermès execution. |
| Evidence Pack | Dossier de preuves | Human-auditable dossier of evidence. |
| Registre Probatoire | Registre Probatoire | Already FR; the governed proof register. |
| Register Candidate | Candidat au registre | Proposed Registre entry awaiting review. |
| Candidate | Candidat | Not promoted until reviewed. |
| Canonical | Canonique | Binding governance rule. |
| User Decision Gate | Seuil de décision (utilisateur) | The human decides; the seuil authorizes or blocks. |
| Gate | Seuil (seuil de décision) | Visible point where a decision, escalation or approval is required (aligned with TERMINOLOGY_BOUNDARIES). |
| Guardrail | Garde-fou | Method that protects scope / mission boundary. |
| Scope | Périmètre / portée | Boundary of a scoped artifact (project, dossier…). |
| Proof | Preuve | What supports an assertion. |
| Provenance | Provenance | Origin and chain of a source. |
| Method Card | Carte de méthode | Names a method without executing it. |
| Read-only verification | Vérification en lecture seule | `mcp-server/` verifies; it does not execute. |
| Exposure surface | Surface d'exposition | The UI exposes (the `pantheon-control` prototype today). |
| Probative certainty (E0–E4) | Certitude probatoire | Certainty axis (owned by this glossary). |
| Answer verification (V0–V4) | Vérification de réponse | Answer-verification axis. |
| Consequence level (K0–K4) | Niveau de conséquence | Consequence axis. |
| Approval ceiling (C0–C5) | Plafond d'approbation | Approval axis. |
| Candidate → active | Candidat → actif | Requires a referent (schema / test / end-to-end example). |
