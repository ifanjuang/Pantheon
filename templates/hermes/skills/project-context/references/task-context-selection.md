# Task-scoped agency context selection

Status: optional Hermes Skill reference for multi-source, version-sensitive or long-document work. Simple tasks need not load this file.

The general contracts remain with `docs/governance/CONTEXT_PACKS.md`, `docs/governance/TASK_CONTRACTS.md` and the architecture `docs/domain-packs/architecture/SOURCE_POLICY.md`. Source/tool names for agency live in `implementation/hermes/skills/vault-search/references/organization-profile.yaml` and `references/professional-source-routing.md`. Do not repeat their rule bodies here.

## Choose useful context

1. Resolve the task, authorized organization/project and requested output. Reuse the existing Context Pack where warranted, not for every simple question.
2. Select the most relevant admitted source: **AFFAIRES** for a project fact, **DOCUMENTAIRES** for a general professional reference, **both** for a project tested against a rule. For a named project, use project Hindsight as a discovery lead when no exact admitted source is already identified; a known exact source may be opened directly. General questions need no project recall.
3. Use Knowledge/wiki entries for quick orientation or navigation when a working read binding exists. A wiki synthesis does not replace inspecting an original document when a professional conclusion needs it. No adopted agency wiki reader has been observed in this repository; do not pretend one ran.
4. Start with the smallest useful passages and an applicable existing Skill. Expand to other sources, whole documents, supplementary Skills or delegation when uncertainty, contradictions or complexity justify the cost.
5. For material claims, retain source identity, edition/date, locator and actual inspection limits in the existing task receipt. Missing, stale and contradictory material changes the readiness of the answer, not the authority of the assistant.

## Examples, not mandatory presets

| Work | Start with | Existing Skill to consider |
|---|---|---|
| Email / correspondence | Relevant message/thread and current project decision | `external-commitment-guard` when an external commitment is involved |
| Devis / DPGF comparison | Offers, quantities and relevant lot CCTP | `construction-cost-review` only when scope, exclusions, variants, tax basis or price comparability must be analyzed |
| Simple question about one remembered quote amount | Exact project scope and focused Hindsight recall | `project-context` + `vault-search`; answer as unconfirmed memory when sufficient, without opening the PDF by default |
| CCTP drafting/revision | Current plans, choices, lot scope and interfaces | `technical-standard-review`, `contract-clause-review` if triggered |
| Technical report analysis | Exact report and project assumptions | Applicable domain Skill |
| Site meeting / compte rendu | Meeting notes, prior open items and verified facts | `site-report-review` |
| Regulatory / DTU research | Official/current text or admitted edition and applicability | `source-research` |

The wiki is a navigation over existing Knowledge Items and source links, **not a new database**. Reuse the existing Knowledge review/recompile owner (Pantheon-Next#1121), without treating publication as verification.

## Practical outcome

Return the requested result with useful citations, material uncertainties and clear source limitations. For comparative trials, measure end-to-end tokens, latency and quality, not just prompt length. The Skill can guide work; task authorization and consequential effects are governed by their existing owners.
