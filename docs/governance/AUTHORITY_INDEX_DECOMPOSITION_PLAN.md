# Authority Index Decomposition Plan

Status: validation-only / decomposition plan — not authority replacement.
Boundary profile: validation_only_trace.

Repository state: documented non-implemented.

This document proposes how to reduce the length of `docs/governance/AUTHORITY_INDEX.md` without weakening its role. It does not split the file, modify the coverage script, create a schema, implement a registry runtime or change authority classes.

## 1. Problem

`AUTHORITY_INDEX.md` now carries three functions at once:

```text
1. It defines the repository authority vocabulary.
2. It records the authority class and repo state of many files.
3. It acts as a coverage map for candidate/support/canonical material.
```

This is useful, but the file has become long enough that review quality is degraded. New rows remain easy to add, but global comprehension is harder:

```text
readability decreases;
merge conflicts become more likely;
review comments focus on index hygiene rather than doctrine;
future decomposition becomes harder as the table grows.
```

The risk is not only file length. The risk is that future contributors stop reading the authority definitions and only append rows.

## 2. Non-goals

This plan does not propose to remove `AUTHORITY_INDEX.md`.

It does not propose a YAML/JSON registry in this step.

It does not propose changing protected paths, tests, schemas, operations, platform files, Docker files or the coverage checker.

It does not promote any candidate document.

It does not make any sub-index canonical by itself.

## 3. Principle

The master file should remain the authority interpreter.

The detailed rows may later move to indexed sub-maps.

```text
AUTHORITY_INDEX.md defines how to read authority.
Sub-indexes list where each document sits.
No sub-index may override the master vocabulary.
```

The decomposition must preserve one invariant:

```text
There is still one authority model.
There may be several authority maps.
```

## 4. Proposed target shape

```text
docs/governance/AUTHORITY_INDEX.md
  -> authority classes
  -> promotion rule
  -> placement test
  -> tool naming rule
  -> terminology boundary rule
  -> protected path summary
  -> sub-index map

optional later, in a new authority/ directory next to AUTHORITY_INDEX.md:

authority/
  GOVERNANCE_AUTHORITY_INDEX.md
  ARCHITECTURE_AUTHORITY_INDEX.md
  RUNTIME_ADAPTERS_AUTHORITY_INDEX.md
  IMPLEMENTATION_ARTIFACTS_AUTHORITY_INDEX.md
  EXTERNAL_REFERENCES_AUTHORITY_INDEX.md
  OBSOLETE_AND_ABSENT_INDEX.md
```

The directory name `authority/` (under `docs/governance`) is only a candidate. It should be confirmed before any file move. Sub-index paths below are written relative to `docs/governance` because the directory does not exist yet; none of them is a live reference.

## 5. Candidate sub-indexes

### 5.1 Governance Authority Index

Candidate path:

```text
authority/GOVERNANCE_AUTHORITY_INDEX.md
```

Intended scope:

```text
canonical doctrine
active support doctrine
core governance candidates
status maps
request/workflow/memory/evidence doctrine
capability placement documents
```

### 5.2 Architecture Authority Index

Candidate path:

```text
authority/ARCHITECTURE_AUTHORITY_INDEX.md
```

Intended scope:

```text
docs/domain-packs/architecture/*
architecture project understanding
architecture method deck
architecture proof register
architecture role/reflex material
Revit Gate planning docs
```

This sub-index is useful because the architecture domain pack is becoming deep enough to require its own readable authority map.

### 5.3 Runtime Adapters Authority Index

Candidate path:

```text
authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md
```

Intended scope:

```text
Hermes-side adapters
OpenWebUI-facing surfaces
MCP candidate notes
browser/page-agent notes
PaddleOCR / Nango / external tool placement notes
```

This keeps tool-specific material away from the tool-agnostic kernel table while preserving the placement rule.

### 5.4 Implementation Artifacts Authority Index

Candidate path:

```text
authority/IMPLEMENTATION_ARTIFACTS_AUTHORITY_INDEX.md
```

Intended scope:

```text
mcp-server/
docs/assets/
schemas/
tests/
platform/
operations/
Docker*
pyproject.toml
.env*
```

This sub-index should remain very conservative. It must continue to distinguish implemented, implemented read-only, partial, protected path and documented non-implemented.

### 5.5 External References Authority Index

Candidate path:

```text
authority/EXTERNAL_REFERENCES_AUTHORITY_INDEX.md
```

Intended scope:

```text
reference reviews
external ecosystem notes
tool distillations
third-party capability reviews
```

External reference remains non-authoritative unless distilled into doctrine elsewhere.

### 5.6 Obsolete and Absent Index

Candidate path:

```text
authority/OBSOLETE_AND_ABSENT_INDEX.md
```

Intended scope:

```text
voluntarily absent items
obsolete/refused notes
historical bootstrap stubs
superseded filenames
known non-goals
```

This improves review discipline because absent/refused items are active decisions, not forgotten gaps.

## 6. Master index after decomposition

After decomposition, `AUTHORITY_INDEX.md` should keep a short table only:

```text
| Area | Sub-index | Authority class | Rule |
|---|---|---|---|
| Governance kernel | authority/GOVERNANCE_AUTHORITY_INDEX.md | active support map | Must not override authority vocabulary |
| Architecture domain | authority/ARCHITECTURE_AUTHORITY_INDEX.md | active support map | Domain-specific map only |
| Runtime adapters | authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md | active support map | Adapter placement only |
| Implementation artifacts | authority/IMPLEMENTATION_ARTIFACTS_AUTHORITY_INDEX.md | active support map | Protected-path status visibility |
| External references | authority/EXTERNAL_REFERENCES_AUTHORITY_INDEX.md | external/support map | Non-authoritative unless distilled |
| Obsolete / absent | authority/OBSOLETE_AND_ABSENT_INDEX.md | refusal/absence map | Does not reinstate refused material |
```

The detailed rows would move to the relevant sub-indexes only after a separate PR.

## 7. Coverage checker implications

This is the main technical risk.

`AUTHORITY_INDEX.md` already describes grouped-row behavior. Before moving rows out, the coverage checker must either already support sub-indexes or be updated in a separate protected-path-aware PR.

Do not silently move rows until this is verified.

Recommended sequence:

```text
1. Document the decomposition plan.
2. Inspect `.github/scripts/check_index_coverage.py` in a separate review.
3. Decide whether grouped rows can cover sub-index files without script changes.
4. If script changes are required, ask for explicit approval because `.github/scripts` may affect CI behavior.
5. Only then split the table.
```

Resolution, 2026-07-05 (explicitly approved): the coverage checker now treats a sub-index registered in the master file (path cited in `AUTHORITY_INDEX.md`) as part of the coverage corpus, so candidate rows may migrate into registered sub-indexes. Unregistered files under `authority/` extend nothing. Grouped rows were already supported. Candidate-row migration is therefore unblocked.

## 8. Proposed rollout

### PR A — Plan only

```text
Add this decomposition plan.
No row migration.
No script change.
No authority behavior change.
```

### PR B — Sub-index skeletons

```text
Create empty/small sub-index files.
Register them in AUTHORITY_INDEX.md.
Do not move existing rows yet.
```

### PR C — Coverage validation

```text
Verify whether the current coverage check accepts the proposed map.
If not, propose a minimal script adjustment separately.
```

### PR D — Row migration by group

```text
Move one group at a time.
Start with external references or obsolete/absent items.
Then architecture.
Then runtime adapters.
Keep canonical/support core rows in the master longest.
```

### PR E — Master index reduction

```text
Reduce AUTHORITY_INDEX.md to authority vocabulary + sub-index map.
Keep promotion rule, placement test, tool naming rule and protected-path summary.
```

## 9. Recommended first migration group

Do not start with core governance rows.

Start with a lower-risk section:

```text
external references
obsolete / refused / voluntarily absent
```

Reason:

```text
lower authority risk;
easier review;
less chance of changing canonical interpretation;
validates the split mechanics before touching core doctrine.
```

## 10. Decision classification

```text
Accepted:
- AUTHORITY_INDEX.md is too long for long-term maintainability.
- The master index should remain the authority interpreter.
- Decomposition should happen by planned PRs, not one large mechanical move.

Refused:
- Removing AUTHORITY_INDEX.md.
- Creating competing authority sources.
- Moving rows before coverage behavior is verified.
- Converting immediately to a machine registry.

To verify:
- How `.github/scripts/check_index_coverage.py` handles grouped rows and sub-indexes.
- Whether a new `authority/` directory under `docs/governance` is the right location.
- Whether architecture gets its own sub-index immediately or later.

To arbitrate:
- Exact number of sub-indexes.
- Whether the first real split starts with external references or obsolete/absent material.
- Whether a later machine-readable index is useful after the Markdown split stabilizes.
```

## 11. Boundary

```text
Implemented: no.
Documented non-implemented: yes.
Partial: planning only.
To verify: coverage checker behavior.
Obsolete: no.
```

This plan changes no authority behavior by itself.
