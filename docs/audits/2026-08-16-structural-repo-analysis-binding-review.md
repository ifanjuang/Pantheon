# Structural repository analysis binding review — 2026-08-16

Status: non-normative audit / candidate qualification note. No installation, activation, preferred-binding change or dependency adoption is authorized here.

Repository baseline: `ifanjuang/Pantheon-Next` `main` at `31b0e180f08d869c490a054115ea699af0fbe4da`.

## Objective

Qualify candidates under the existing `structural_repo_analysis` Capability Slot before changing any binding, schema, runtime or governance vocabulary.

Questions:

1. Is the responsibility already modeled?
2. Which candidate most reduces repository-discovery cost without becoming an authority?
3. What is the minimum useful profile for each candidate?
4. Does RepoWise `distill` justify a new Pantheon concept?
5. What evidence is required before a preferred-binding change?

## Authority and convergence boundary

```text
Pantheon Next = governance, doctrine, schemas, status, Evidence, scopes, approvals, Capability Slots
pantheon-mvp = operational implementation candidate, APIs, PostgreSQL, Cockpit projections, adapters
Hermes = tasks, skills, tools, external runtimes
OpenWebUI / Cockpit = user and decision surfaces
human = consequential decisions
```

The responsibility already exists:

```text
Capability Slot: structural_repo_analysis
canonical registry reference: Lum1104/Understand-Anything
current upstream location observed: Egonex-AI/Understand-Anything
```

GitHub currently resolves `Lum1104/Understand-Anything` to `Egonex-AI/Understand-Anything` with the same repository identity. This observed upstream continuity does not itself update Pantheon's canonical binding record.

No parallel `repo_intelligence`, `codebase_memory`, `repository_graph`, `context_distillation` or equivalent Capability Slot is justified.

```text
index_success != truth
graph_edge != proof
risk_score != authorization
health_score != safety
mined_decision != Pantheon Decision
generated_documentation != doctrine
retrieved_context != Evidence
runtime_success != Evidence
binding_selected != dependency_adopted
```

## Candidate framing

```text
Repowise
  persistent repo intelligence + Git behaviour + risk/health + multi-repo + reversible distillation

CodeGraph
  narrow structural/semantic graph with graph-only/profiled runtime

Understand Anything
  human-oriented architecture exploration, explanation and onboarding

Serena
  semantic code navigation/editing; complementary, not a direct slot replacement
```

A winner-takes-all architecture is not justified.

### RepoWise

Upstream: `repowise-dev/repowise`.

Observed 2026-08-16:

```text
commit: 580e17f065fd0cc73192e2bb09405aef57b9b2ae
version: 0.43.0
license: AGPL-3.0-or-later
classifier: Development Status :: 3 - Alpha
Python: >= 3.11
Hermes integration: Good tier
```

Useful surfaces include symbol/file graph, call/dependency relations, Git hotspots and ownership, co-change, bug-fix history, change-risk hints, related tests, multi-repository workspaces, source-linked mined/generated statements and reversible output distillation.

The package also bundles a broad runtime surface including Tree-sitter parsers, graph/Git analysis, SQLite/SQLAlchemy, LanceDB, FastAPI/MCP, scheduling support and model-provider SDKs. Qualification must therefore measure a minimal profile rather than treating package breadth as required capability.

Expected value:

```text
less repeated rediscovery
more targeted source verification
smaller Hermes context
fewer sequential search/read calls
better cross-repository impact discovery
```

GitHub, repository source and tests remain verification authority.

### Understand Anything

Current upstream: `Egonex-AI/Understand-Anything`, inspected commit `32944829e7a63a9fa9c55d811d7f98a9530c6a6a`. GitHub resolves the older canonical path `Lum1104/Understand-Anything` to this same repository identity.

Strongest comparison dimensions: interactive structural graph, guided architecture exploration/onboarding, semantic explanation, diff-impact and knowledge-base views, broad agent-platform installation support, MIT license.

Relative engineering-path concern: a more explanation/visualization-oriented pipeline with potentially higher LLM/token cost and less emphasis on Git behavioural intelligence, co-change and reversible output reduction.

Keep it in the benchmark and preserve the canonical binding until measured evidence justifies change.

### CodeGraph

Upstream: `codegraph-ai/CodeGraph`, inspected commit `489ccf1612555510f8367e3e673181f6a1275fe4`.

Relevant profile:

```text
native Rust engine
Apache-2.0
semantic graph
MCP + LSP / IDE clients
persistent local graph
graph-only mode
profiled tool surface
multi-workspace paths
```

Its value is a potentially lean structural fallback. Test graph-only + the narrowest useful graph/core profile first. Memory/documentation surfaces are not Pantheon owners and should be disabled or ignored for this slot.

### Serena and broader references

Serena is primarily a semantic navigation/editing candidate (`find symbol`, references, implementations, rename/refactor, diagnostics). Keep it outside this binding decision unless a demonstrated responsibility gap later requires extending an existing capability or, only if necessary, a distinct slot.

Aider's repo-map pattern remains useful as a context-budgeting reference; Sourcegraph remains a scale reference. Neither currently justifies another binding or platform dependency.

## Minimum useful profile

Qualify the smallest profile that demonstrates the required value.

```text
available feature != required capability
installed component != adopted dependency
broader tool surface != better binding
```

Initial profiles:

```text
RepoWise: deterministic/local analysis first; no optional prose/provider path unless needed
CodeGraph: graph-only + narrow graph/core profile
Understand Anything: current supported path, with actual token/runtime cost measured
```

Do not install any candidate into the production Hermes image during comparison. Use an isolated environment and controlled/disposable repository clones.

## Distill boundary

RepoWise `distill` is a binding-local context/output optimization, not a governance primitive.

Relevant properties:

```text
bounded output
errors and exit codes preserved
omitted material retained before marker emission
stable references permit recovery
filter/storage failure falls back to raw output
small output passes through unchanged
```

```text
distilled != complete
omitted_but_recoverable != reviewed
token_saving != correctness
```

Do not create a `context_distillation` Capability Slot or a top-level `DistilledContext` model. Benchmark distillation separately from structural-analysis quality so token savings are not mistaken for better graph quality.

## Target topology

```text
Pantheon Next
  governs Capability Slot + binding / activation / compatibility
                 |
                 v
        structural_repo_analysis
                 |
          selected binding
                 |
                 v
Hermes -------- MCP / bounded CLI -------- isolated repo-analysis runtime
                 |
                 +-> controlled/disposable repository clones
                 +-> controlled local index/cache
                 +-> candidate navigation/risk/graph outputs

Git/source/tests remain repository-fact authority.
```

The runtime must not become Pantheon memory, Decision owner, Evidence authority, approval engine, second scheduler/orchestrator or repository mutation authority by default.

## Qualification matrix

Use the same immutable snapshots and representative questions.

```text
A. baseline Hermes + current Git/source workflow, no repo-analysis binding
B. RepoWise 0.43.x, minimum deterministic/local profile
C. CodeGraph current release, graph-only + narrow graph/core profile
D. Understand Anything current release
```

Use exact SHAs for Pantheon-Next, pantheon-mvp and Pantheon-plugins. Multi-repository cases are first-class.

Representative tasks:

1. Find where one governed concept is defined, projected, consumed and tested.
2. Determine the blast radius of changing one canonical schema field.
3. Find historical co-change and recent PR/commit context around one implementation path.
4. Identify relevant tests for a bounded change.
5. Trace a generated/mined statement back to exact repository sources.
6. Detect a deliberately introduced contradiction or stale relation after a new commit.
7. Reach the correct owner/consumer files with minimal context and tool calls.
8. Recover omitted detail without rerunning the original operation where supported.

Measure structural quality separately from operational cost.

Structural quality:

```text
correct-file recall
false-positive relations
source/provenance quality
freshness after commit
incremental-update accuracy
multi-repo coverage
relevant-test recall
contradiction/staleness detection
time/tool calls to correct owner and consumers
```

Operational cost:

```text
tokens delivered to Hermes
cold-index time
incremental-update time
startup latency
CPU peak / steady state
RAM peak / steady state
disk/index footprint
failure/recovery behaviour
installation side effects
rollback/removal completeness
license implications
```

For material candidate assertions consumed by Hermes, prefer provenance resolving to:

```text
repository
commit SHA
path
symbol or line/span when available
```

A relation without exact provenance remains a discovery hint, not a basis for consequential modification.

## Context contract finding

The audit exposed an existing inter-repository convergence issue unrelated to RepoWise selection.

Pantheon Next has a canonical `ContextPack` schema for governed purpose, scope, target surface, included context/doctrine, constraints, Evidence/approval/output expectations and forbidden assumptions.

The current MVP Hermes path stores a narrower context centered on admitted entity identities, exclusions, source references and a digest; running Hermes access then resolves current owner values for admitted identities.

This can be a valid projection boundary, but it should be explicit:

```text
Canonical ContextPack
  -> governed scope / constraints / provenance expectations
  -> Hermes launch-context projection
  -> exact admitted identities / bounded resolution
  -> trace of context actually consumed
```

Do not create a third context model. Treat this as convergence between existing owners.

This finding is out of scope for implementation in Pantheon-Next#674 and does not block the structural-repository benchmark or H5.9.

Reusable lineage:

```text
used ⊆ admitted ⊆ retrieved
```

Future reversible compression must preserve this lineage rather than create a new authority.

## Recommendation

1. Keep `structural_repo_analysis`; create no parallel slot.
2. Do not change the preferred binding before comparative evidence.
3. Benchmark RepoWise using its minimum deterministic/local profile first.
4. Benchmark CodeGraph graph-only/profiled as the efficiency fallback.
5. Keep Understand Anything for human exploration/onboarding comparison.
6. Keep Serena complementary and outside this slot decision.
7. Score `distill` separately from repository-analysis quality.
8. Prefer the candidate that most reduces discovery work while preserving freshness, provenance and exact source verification.
9. Test target-runtime/Synology compatibility only after a candidate proves useful on a development workstation.

```text
Python package != guaranteed NAS compatibility
native Rust binary != guaranteed DSM/glibc compatibility
low idle RAM != safe peak indexing behaviour
successful startup != acceptable sustained footprint
```

## Relationship to Pantheon-Next#666 and retirement rule

This file is an audit artifact, not candidate-support doctrine and not a second binding registry.

Its output must converge back into existing owners:

```text
benchmark observations
-> existing Capability Binding / Compatibility owners
-> canonical binding registry update only if justified
-> audit remains historical/non-normative
```

Do not keep expanding this file as a parallel source of current binding truth. After the bounded benchmark and any resulting owner updates, future consumers should use canonical registry/contracts. This is the audit's retirement path under Pantheon-Next#666.

## Closure

Closed by this audit:

- responsibility mapped to existing `structural_repo_analysis`;
- no new repo-intelligence/distillation concept justified;
- Understand Anything upstream continuity recorded without silently rewriting canonical governance;
- candidates separated by responsibility/profile;
- minimum-useful-profile principle established;
- structural quality separated from context/cost optimization;
- multi-repo, freshness, provenance and resource criteria defined;
- existing ContextPack/Hermes convergence issue recorded without creating a model;
- retirement path relative to Pantheon-Next#666 defined.

Still open:

- comparative benchmark;
- preferred-binding selection and any canonical registry update;
- target-environment compatibility;
- installation/production activation;
- ContextPack/Hermes contract convergence.

H5.9 remains independent and is not blocked by this audit.
