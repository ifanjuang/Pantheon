# Source Need and Registry

Status: active support doctrine — source need, source registry and freshness policy. Documented non-implemented.

This document defines how Pantheon Next handles missing sources, trusted source routes, source additions, freshness requirements and source-family distinctions.

It is a governance method, not an implementation.

It does not create a web search engine, source database, crawler, scraper, connector gateway, source validator, evidence engine, memory engine, approval engine, runtime-client action, Hermes skill, scheduler, queue or external action.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes retrieval or query handoffs, Pantheon Cockpit projects governed source/evidence status, and Pantheon retains governance authority.

## Core thesis

```text
A missing source does not authorize guessing.
A registered source does not automatically become evidence.
A method source guides treatment; it does not prove project facts.
A competence source enables a capability; it does not validate the capability output.
A volatile source must be checked at use time or at the relevant project date.
```

Pantheon governs the route from source need to source candidate to evidence candidate. It does not run the search.

## Why this exists

A professional request may need information that is absent from the current corpus.

The missing information may be:

```text
project-specific fact
local rule
public official information
professional method
agency method
technical competence documentation
stable knowledge
volatile information
memory or recall
```

These are not equivalent.

Pantheon must not treat a web page, a recalled memory, a method note, an API wiki and a project email as the same kind of source.

## Source Need Candidate

When required information is absent, create a Source Need Candidate before searching.

Minimum questions:

```text
What information is missing?
Why is it needed?
Which output status depends on it?
Which source family is required?
Which source routes are legitimate?
How fresh must the source be?
What happens if the source is not found?
```

The Source Need Candidate may lead to:

```text
ask_user
search_registered_sources
use_official_web_route
consult_project_corpus
query_operational_owner
consult_professional_method
consult_technical_competence_documentation
consult_memory_or_register
allow_draft_only
block_external_action
```

`query_operational_owner` is an acquisition route, not a source family. Use it when current structured or operational state is already owned by an admitted system or service. Prefer querying that existing owner over creating an AI-specific indexed copy merely to make the state easier for a model to access. The returned observation remains candidate material; ownership of operational state does not make it professional truth or Evidence.

It must not lead directly to truth, approval, external action or memory promotion.

## Source families

Use these families when classifying a source.

| Family | Meaning | Typical use | Must not become |
|---|---|---|---|
| `project_source` | Material from the specific Case / Project. | Facts of the matter. | General rule by itself. |
| `external_official_source` | Public or institutional authority source. | Regulations, procedures, official data. | Project fact by itself. |
| `professional_method_source` | Professional conduct or method reference. | How to handle a situation. | Proof of a project fact. |
| `agency_method_source` | Internal agency method or preference. | Agency-standard treatment. | External authority. |
| `technical_competence_source` | Documentation that enables a capability, API or adapter. | Correct tool use. | Evidence for the content returned. |
| `stable_knowledge_source` | Slow-changing background knowledge. | Orientation and method. | Case-specific validation. |
| `volatile_source` | Information likely to change. | Current rules, prices, deadlines, forms. | Reused without freshness check. |
| `memory_or_recall_source` | Recalled past material. | Candidate context. | Register or evidence by itself. |
| `registered_source` | Source listed in the source registry. | Approved route candidate. | Evidence by registration alone. |
| `absent_source` | Needed but missing material. | Gap tracking. | Assumption. |

## Project-specific versus generally applicable

Pantheon distinguishes:

```text
project fact
rule externally applicable to the project
method professionally applicable to the treatment
technical competence needed to obtain or transform data
```

Examples:

```text
A client email may prove a project instruction, but not PLU compliance.
A PLU excerpt may support a regulatory claim, but not prove client preference.
A professional recommendation may guide wording and prudence, but not prove a breach.
An API documentation page may enable a geodata query, but not prove the returned zoning by itself.
```

## Source Registry

The source registry is a governed list of legitimate source routes.

It is not evidence.

It is not a database engine by itself.

It is not a web search whitelist that guarantees truth.

A registry entry says:

```text
this source route is recognized for this family, scope, use and freshness policy
```

It does not say:

```text
anything retrieved from this route is automatically true
```

## Workspace source notebook

An optional Markdown workspace may keep one human-maintained source notebook,
for example a `Carnet de sources`, to group useful websites, databases,
institutional routes and working annotations.

The notebook is a discovery surface for Source Leads. It is not the Source
Registry, an Evidence store, a whitelist or an authorization surface.

```text
workspace source notebook != Source Registry
notebook entry != Source Registry Entry
listed route != inspected source
workspace path != governed identity
```

The notebook may remain one file organized by source family. Pantheon does not
require one note, manifest or governed object per website. Its filename, folder
and link from a workspace index are deployment choices, not generic Pantheon
contracts. Hermes and other consumers must not hard-code an Obsidian-specific
path.

A lightweight notebook entry may record:

```text
label and route
intended use
proposed source family
freshness caution
working status
optional Source Registry reference
```

These fields support discovery without forcing every bookmark through registry
admission. When a listed route is used for a task, the exact page, document,
query result or observation must still be inspected, dated, scoped and linked
through the normal Source Reference and Evidence chain.

```text
notebook entry
-> Source Lead
-> task-authorized inspection
-> Source or Observation Candidate
-> Evidence Candidate when selected and bounded
```

When a route is recurrent or consequential enough to deserve governed reuse,
the existing promotion path applies:

```text
notebook entry
-> Source Addition Candidate
-> required review and arbitration
-> Source Registry Entry when accepted
```

No synchronization, retrieval result, runtime success, repeated use or Cockpit
projection promotes a notebook entry automatically. A separately authorized
workspace edit may update the human note; it does not mutate the Source Registry
or admit Evidence by implication.

## Source Addition Candidate

A user may propose a source.

Pantheon may propose a source.

No source is accepted silently.

A Source Addition Candidate must identify:

```text
proposed source
source family
intended use
scope
authority claim
freshness policy
risk if wrong
review required
Zeus status
```

ARGOS reviews provenance, source status, scope and freshness.

THEMIS reviews risk and professional consequence.

ZEUS arbitrates status.

## Freshness policy

Every registry entry or source need should declare a freshness policy.

Use:

```text
invariant
versioned
verify_each_use
verify_on_project_date
verify_on_change
stale_after_duration
obsolete
unknown
```

Examples:

| Source | Suggested freshness policy |
|---|---|
| Professional method note | `versioned` or `verify_on_change` |
| Agency drafting method | `versioned` |
| PLU / local planning rule | `verify_each_use` or `verify_on_project_date` |
| Administrative form | `verify_each_use` |
| Financial aid amount | `verify_each_use` |
| API documentation | `versioned` or `verify_on_change` |
| Project email | `project_date_bound` may be noted under metadata, with reconfirmation if stale or contradicted |
| Runtime memory recall | `to_reconfirm` under memory status, not evidence |

If freshness is unknown and the output is consequential, the safe default is draft-only or block.

## Official web route

When the missing information is general but applicable to a project, Pantheon may route to an official or registered source route.

Examples:

```text
planning portal
public service page
government dataset
local authority website
cadastre or geodata service
official form portal
```

This is a route, not authority by itself.

Returned material remains Source Candidate until read, dated, scoped and reviewed.

## Professional method route

Some sources describe how a professional should handle a situation.

Examples:

```text
recommendations for reception and reserve lifting
professional insurer guidance
internal agency caution method
standard wording discipline
```

Allowed uses:

```text
method_guidance
risk_framing
wording_precaution
review_angle
```

Forbidden uses:

```text
prove_project_fact
prove_regulatory_compliance_by_itself
automatic_client_advice
automatic_external_transmission
```

## Technical competence route

Some sources explain how to use a capability.

Examples:

```text
API documentation
connector documentation
OCR documentation
form-filling technical note
geodata query guide
```

Allowed uses:

```text
technical_execution_support
adapter_configuration_support
capability_understanding
```

Forbidden uses:

```text
truth_about_project_by_itself
regulatory_claim_by_itself
approval
memory_promotion
```

## Acquisition and evidence chain

Pantheon uses this chain:

```text
Source Need Candidate
-> permitted source or acquisition route
-> external direct access / search / retrieval / typed query handoff
-> Source or Observation Candidate
-> Evidence Candidate
-> Evidence Pack Candidate
-> Gate / Approval
```

Do not collapse steps.

A search result is not a source.

An operational observation is not Evidence by itself.

A source is not evidence by itself.

Evidence is not approval.

Approval is not execution.

## Safe defaults

When source status is incomplete:

```text
mark source missing
ask user
request official route
allow orientation only
allow draft only
surface uncertainty
block external action
block memory promotion
send to ZEUS or human gate
```

## Relationship to existing doctrine

This document applies:

```text
REQUEST_LIFECYCLE.md       -> proportional request handling activates source need
CONTEXT_STACK.md           -> HESTIA context sufficiency and source gaps
DOMAIN_PACK_SPEC.md        -> source policy per professional domain
EVIDENCE_PACK.md           -> evidence candidate packaging
MEMORY.md                  -> recall is not register
CAPABILITY_PLACEMENT.md    -> search and connectors execute outside Pantheon
```

## Boundary

```text
The registry proposes routes.
The search retrieves candidates.
ARGOS qualifies sources.
THEMIS qualifies consequence.
HESTIA qualifies context sufficiency.
ZEUS arbitrates status.
The human decides.
```
