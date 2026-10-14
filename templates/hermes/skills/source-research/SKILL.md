---
name: source-research
description: "Use for bounded source research under an authorized Task Contract: discover sources, inspect source content, map claims to sources, surface contradictions and uncertainty, and return a traceable research candidate. Never treats retrieval as truth, Evidence, approval, or governed memory."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: ARGOS
  governed_by: docs/governance/AGENTS.md
  upstream: "agentskills.io SKILL.md standard; exact Hermes runtime compatibility must be qualified before admission"
---

# Source research (governed candidate)

Non-executable Hermes skill candidate. Pantheon governs; Hermes executes outside the repository under Task Contract.

## Purpose

Perform source-grounded research within an explicitly bounded question.

```text
question
→ research frame
→ source discovery
→ source inspection
→ claim/source mapping
→ contradiction + uncertainty review
→ synthesis candidate
→ validation
```

This replaces the narrower source-audit candidate. Audit remains one mode of the same research responsibility rather than a parallel skill.

## When to use

Use for:

- source discovery for a bounded question;
- deeper investigation beyond supplied context;
- source credibility or contradiction audit;
- multi-source synthesis;
- final validation of claims, citations, dates or completeness.

Do not use merely to restate already sufficient context.

## Required context

Use the available Task Contract and Context Pack to identify, when relevant:

- research question and scope;
- admitted source references;
- jurisdiction, date or freshness requirements;
- allowed retrieval capabilities;
- evidence/citation expectations;
- material limits on breadth, cost, time or data exposure.

An optional workspace source notebook may be consulted only when its reference
and contents are inside the authorized task/context scope. Treat notebook entries
as Source Leads unless an entry resolves to an admitted Source Registry Entry.
The notebook's absence must not block another permitted discovery route.

Missing capability, scope or authorization must be reported, not bypassed.

## Modes

A task may combine these modes without creating separate skills:

- `discover` — find candidate sources; discovery results are not facts;
- `investigate` — inspect source content and extract relevant claim candidates;
- `audit` — assess provenance, credibility, freshness, methodology, bias signals, limitations and contradictions;
- `synthesize` — combine inspected sources while preserving agreement, disagreement and uncertainty;
- `validate` — re-check material claims, citations, dates, conflicts and coverage before return.

## Method

### 1. Frame

- restate the bounded question;
- split material sub-questions when useful;
- identify important assumptions and unknowns;
- do not silently widen scope.

### 2. Discover

Use only capabilities allowed by the Task Contract.

Before an external retrieval query, minimize unnecessary private, local or dossier-specific detail. Prefer an abstracted or sanitized query when it can answer the same research need. Do not transmit names, identifiers, document text or project-specific detail merely because they are present in local context. Secrets must never be sent to an external retrieval surface. Any remaining exact private detail requires explicit authorization for transmission of that data to that external destination; task/context access alone does not authorize disclosure. If such transmission is authorized and materially necessary, expose the resulting data-exposure limitation when relevant.

```text
local context available != external disclosure required
task/context access != external transmission authorization
query usefulness != authorization to disclose private detail
secrets != externally transmissible research context
```

When an authorized workspace source notebook is available, use it as a bounded
discovery aid for relevant routes. Never hard-code its filename or Obsidian path,
infer authorization from its workspace location, or treat a listed domain as a
whitelist. Whether a route came from the notebook or the Source Registry, inspect
the exact page, document or returned observation before using it to support a
material claim.

```text
notebook entry != Source Registry Entry
registered route != inspected source
workspace access != task authorization
```

### Optional user-enabled discovery routes

Optional product mappings for these routes live in `docs/governance/HERMES_CAPABILITY_BINDINGS.md`; this skill keeps only the abstract runtime contract.

```text
curated_source_library
= optional curated professional source-library route

academic_source_discovery
= optional external academic-discovery route
```

The user chooses at environment/profile level whether a concrete binding for either route is enabled. Enabling a binding makes that route eligible for tactical use; it does not require invoking it on every task.

For each admitted research task, Hermes may invoke only an enabled route when it is materially useful and compatible with the Task Contract, source scope and data-exposure constraints. A task-specific instruction may further narrow the enabled set.

```text
installed != user-enabled
configured != user-enabled
user-enabled != task-permitted
task-permitted != invoked
invoked != Evidence
```

When a curated source-library route is enabled and task-permitted, prefer stable library / collection / item identifiers over physical storage paths. Collection membership may narrow discovery but does not establish Case identity, source applicability, Evidence status or professional authority.

When an external academic-discovery route is enabled and task-permitted, treat returned rankings, metadata, snippets and generated takeaways as discovery material only. For material claims, inspect the original source when technically available before relying on it.

Do not hard-code a universal route order. Among enabled and task-permitted routes, prefer the least exposed and least expensive route that can materially answer the bounded question, then widen only when useful. A disabled route must not be invoked.

A useful pattern may be:

```text
user-enabled research bindings
-> admitted task / source / data-exposure scope
-> Hermes selects materially useful route(s)
-> inspect original material sources
-> challenge / reconcile
-> source-grounded Result Candidate
```

Discovery must not silently promote a source into a curated library. A source worth retaining may return a `source_addition_candidate`; any library mutation requires separate write capability and authorization.

```text
enabled != automatically used
curated != true
discovered != inspected
library membership != Evidence
collection name != governed Case identity
academic search result != source support
source_addition_candidate != library mutation
```

Prefer source classes appropriate to the question, generally:

1. primary or official sources;
2. peer-reviewed or methodologically transparent research;
3. authoritative institutional or industry material;
4. credible expert analysis;
5. reputable reporting;
6. community discussion for experience, dissent or leads.

Popularity does not confer authority.

### 3. Inspect

Search snippets, previews, summaries and retrieval excerpts are discovery aids.

For a material claim, inspect the supporting source content when technically available before relying on it. If full inspection is unavailable, disclose the limitation and reduce certainty.

Do not enforce a fixed source count. Use enough independent sources for the consequence and uncertainty of the claim.

### 4. Map claims to sources

For each material claim candidate, retain when available:

- source reference and identity;
- precise locator;
- publication/revision/observation date;
- posture: `supports`, `contradicts`, `qualifies`, or `uncertain`;
- material limitation.

```text
claim candidate
├─ source A: supports
├─ source B: qualifies
├─ source C: contradicts
└─ uncertainty
```

Citation count is not confidence. Dependent sources are not independent corroboration.

### 5. Evaluate proportionally

Assess only factors material to the question, such as:

- identity and provenance;
- primary vs derivative status;
- issuer/author competence;
- date, revision and applicability;
- methodology and underlying evidence;
- conflict-of-interest signals;
- independent corroboration;
- jurisdiction and scope;
- limitations or missing data.

Do not force a generic framework when it does not improve the answer.

### 6. Challenge material claims

For important or consequential claim candidates, do not search only for support. Run targeted challenge searches when useful for contrary evidence, later versions, failure reports, known exceptions, competing explanations or materially different applicable sources.

Challenge effort should be proportional to consequence and uncertainty. It is not a requirement to manufacture artificial disagreement or to keep searching after the decision-relevant picture has stabilized.

```text
support found != challenge completed
second source agrees != contradiction ruled out
```

### 7. Reconcile

- distinguish real contradiction from differences of scope, date, definition or method;
- preserve material minority/conflicting findings;
- prefer stronger applicable evidence over majority vote;
- state when available sources do not support a conclusion candidate.

### 8. Synthesize

Distinguish:

```text
observed source content
interpretation
inference
recommendation candidate
uncertainty
```

Retrieved statements do not become professional, legal, contractual or project truth.

### 9. Stop proportionally

Stop bounded research when targeted gap and challenge searches no longer materially change the decision-relevant synthesis and the remaining uncertainty is explicit.

A fixed source count, model confidence, citation count or elapsed effort alone does not establish sufficiency. A Task Contract limit may end further work earlier; if so, expose the resulting limitation rather than treating the stop as evidentiary completeness.

```text
research stopped != uncertainty resolved
more searching possible != more searching decision-relevant
```

### 10. Validate

Before return, verify that:

- material claims are source-traceable or labeled inference/uncertainty;
- citations point to the intended source/locator when available;
- relevant dates and versions fit the question;
- important contradictions and limitations are visible;
- material claim candidates received proportionate challenge where useful;
- remaining uncertainty is explicit at the stopping point;
- scope has not silently widened;
- no output has been promoted into Evidence, Decision, Knowledge or a Registre Probatoire entry.

## Allowed outputs

As authorized:

- `research_report_candidate`;
- `source_map`;
- `claim_candidate`;
- `source_risk_note`;
- `contradiction_note`;
- `missing_source_note`;
- `uncertainty_note`;
- `research_limitation`;
- `followup_candidate`;
- `source_addition_candidate`;
- `capability_gap`.

## Forbidden effects

This skill must not by itself:

- approve or professionally validate;
- create or admit Evidence or Knowledge;
- promote memory or a Registre Probatoire entry;
- mutate doctrine or registries;
- promote a notebook entry or rewrite the notebook without separate
  workspace-write authorization;
- send externally;
- perform consequential external effects;
- install or activate tools/providers/runtimes;
- widen the task automatically;
- create autonomous recurring research loops.

## Escalation

- source identity/provenance/evidentiary ambiguity → ARGOS review;
- remembered state, chronology or supersession ambiguity → MNEMOSYNE review;
- legal/policy/authorization/consequential risk → THEMIS;
- completeness/evidence sufficiency → APOLLO;
- unresolved competing candidate postures → ZEUS;
- missing capability → return `capability_gap`.

## Return expectations

A substantial return should expose, as applicable:

1. question and scope;
2. concise findings candidate;
3. material claim/source support;
4. contradictions and uncertainty;
5. source-quality/freshness limitations;
6. missing information;
7. source references and locators;
8. follow-up as candidate, never authorization.

## Non-equivalences

```text
searched != inspected
retrieved != truth
cited != verified
many sources != independent corroboration
source supports claim != professional validation
research synthesis != Evidence
runtime success != result validity
candidate conclusion != Decision
useful result != Registre Probatoire
```
