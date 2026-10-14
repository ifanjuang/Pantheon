# Contributing

Status: active support — repository contribution guardrail.

This file does not create doctrine by itself. It explains the minimum review discipline for changing Pantheon Next.

The canonical architecture boundary is stated in `README.md`, `STATUS.md` and `AUTHORITY_INDEX.md`. Contribution material should not repeat the slogan mechanically; use explicit boundary fields when reviewing a concrete change.

## Before significant work

Read these files first:

```text
docs/governance/STATUS.md
docs/governance/WHAT_RUNS.md
docs/governance/AUTHORITY_INDEX.md
docs/governance/MODULES.md
docs/governance/README.md
docs/governance/STATUS_HEADER_RULES.md
docs/governance/BOUNDARY_PROFILES.md
docs/governance/NON_EQUIVALENCE_RULES.md
```

The repository overrides prompts, comments, historical plans and previous assistant summaries.

## Classify the change

Every significant change should say what it is:

```text
canonical doctrine
active support doctrine
candidate / to verify
validation-only
external reference
implementation artifact
voluntarily absent
obsolete / refused
not applicable
```

Use `docs/governance/STATUS_HEADER_RULES.md` for Markdown `Status:` headers.

Do not let examples, comments, diagrams, static prototypes, watchlists or candidate notes imply live behavior.

## New current-authority documents are a last resort

Before adding a new Markdown document under `docs/governance/` with a `canonical*` or `active*` status, record the owner test in the PR:

1. Which existing owner(s) were searched and read?
2. Why can the responsibility not be an edit, section or local delta of an existing owner?
3. What distinct responsibility will the new document own?
4. Which authority class does that responsibility require?
5. Why is an independent owner necessary rather than merely convenient?
6. Which Authority Index row will make the owner discoverable?

Default preference:

```text
edit existing owner
-> add section / local delta
-> reference existing owner
-> issue / PR / ai_log / reference review
-> new current-authority document only when responsibility is genuinely distinct
```

A new current-authority document without an Authority Index row is invalid repository topology. Indexing makes the owner visible; it does not prove that the owner is necessary or promote its content by itself.

Do not satisfy this rule by creating a second owner and then cross-linking it to the first. The responsibility test comes before the new file.

## Keep the boundary

Pantheon Next may govern consequential decisions:

```text
truth status
memory status
evidence requirement
approval path
scope boundary
external action
activation
installation proposal
update authorization
runtime health visibility
rollback visibility
```

Pantheon Next must not silently become:

```text
execution runtime
agent loop
scheduler
queue
provider router
MCP host
plugin manager
memory engine
automatic approval system
installer
updater
external sender
```

For concrete capabilities, repos, skills, connectors, workflows or runtime changes, express the boundary as fields:

```text
exposed_by
executed_by
governed_by
approved_by
forbidden
```

For repeated non-runtime disclaimers, use `docs/governance/BOUNDARY_PROFILES.md` instead of copying a long boilerplate paragraph.

For repeated “X does not mean Y” lists, use `docs/governance/NON_EQUIVALENCE_RULES.md` and repeat only the local distinctions that matter.

Boundary profiles, status header rules and non-equivalence rules reduce repetition. They do not hide consequential effects.

## Protected paths

Changes under these paths require explicit review:

```text
schemas/
tests/
pyproject.toml
operations/
platform/
Docker files
.env files
CLAUDE.md
mcp-server/
GitHub Actions / CI scripts
```

A green check, a useful prototype or a successful local run does not authorize a protected-path change.

## Capability review

Before adopting, documenting, activating or recommending an external capability, classify it as a Capability Slot:

```text
abstract capability
→ candidate Hermes binding
→ installation status
→ health status
→ update status
→ activation status
→ Pantheon gates
→ human approval
```

Answer these questions:

1. What consequence can it produce?
2. What executes it?
3. What does Pantheon govern?
4. What evidence is required?
5. What human approval is needed?
6. What must remain forbidden?

Use local distinctions from `docs/governance/NON_EQUIVALENCE_RULES.md`, especially:

```text
installed        ≠ approved
healthy          ≠ safe
update_available ≠ update_authorized
runtime_success  ≠ evidence
binding_selected ≠ dependency_adopted
watchlist_item   ≠ install_instruction
```

## Promotion rule

A candidate does not become active doctrine because it is repeated, useful or old.

Promotion requires a referent:

```text
schema
test
end-to-end example
read-only verification surface
explicit dated human decision with a durable referent
```

For the human-decision form, use a bounded repository referent such as `PR #<n>` or `issue #<n>`. A PR, issue, merge, green CI result or automation output does not become a human decision merely by existing; the cited referent must contain the explicit human decision.

Without a referent, keep the material candidate, support, validation-only or reference.

## Commit and PR discipline

A good change states:

- what changed;
- which authority class it affects;
- whether it changes runtime status;
- whether protected paths are touched;
- what remains non-implemented or to verify.

Prefer small, reviewable changes. Do not bundle doctrine, runtime artifacts and public wording unless the relation is explicit.

## Supported Python commands

Do not install the repository root as a package. Install its explicit validation
dependencies, then run the tests in place:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

For the bounded MCP distribution and its tests:

```bash
python3 -m pip install "mcp-server/.[test]"
python3 -m unittest discover -s mcp-server/tests -v
```

Packaging changes must keep `VERSION`, the changelog head, MCP metadata and
installed runtime metadata coherent. They must not re-enable root package
auto-discovery.

## Final rule

```text
Documentation may describe.
Static pages may expose.
Read-only checks may verify structure or status.
External runtimes may execute under contract.
Pantheon governs consequential status.
The human decides.
```
