# Enforcement and exercised authority — 2026-09-06

Status: non-normative audit / repository-truth assessment. No doctrine, binding, activation, schema or authority changes here.
Boundary profile: validation_only_trace.

Repository baseline: `ifanjuang/Pantheon-Next` `main` at `2754625d`, after Pantheon-Next#1003 and Pantheon-Next#1006.

## Objective

Answer one question with measurement rather than impression: is the governance
architecture working, and if not, what is the smallest true statement of why.

Two questions follow from it:

1. Where do the repository's rules stop being enforced?
2. How much of the declared authority has ever been exercised?

## Measured shape

```text
docs/governance/      218 files    70,081 lines
ai_logs/              915 files    70,238 lines
docs/domain-packs/     31 files    15,286 lines
implementation/       471 files   103,826 lines
mcp-server/            73 files    10,992 lines
tests/                124 files    13,404 lines
```

Authority distribution across `docs/governance/`:

```text
101   46%   candidate
 77   35%   active
 25   11%   validation / reference
  4    2%   canonical
 11    5%   other / unclassified status wording
```

Chokepoint state, from `implementation/GOVERNANCE_STATUS.md`:

```text
policy_chokepoint_seam                   implemented_not_connected
knowledge_update_chokepoint              wired_not_connected
human_identity_binding_chokepoint        wired_not_connected
apu_reviewed_dossier_chokepoint          wired_not_connected
knowledge_publish_chokepoint             wired_not_connected
knowledge_edit_apply_chokepoint          wired_not_connected
agency_information_act_chokepoint        wired_not_connected
```

Six wired. None connected.

## What holds

**The one-way authority direction is real.** Reverse authority transfer was
looked for and not found: `implementation/` consumes governed contracts and does
not redefine them. The usual failure of a repository this size — executable code
quietly becoming the specification — has not happened.

**The chokepoint refuses.** Measured against the real `PantheonPolicyService`
during the 2026-09-02/06 gate work: five of six wired chokepoints are refused
with `blocked_pending_task_contract`, not admitted. A governance layer that
declines when it was not meant to is the only kind that is doing anything.

**The non-equivalence vocabulary is the strongest artifact in the repository.**
`installed != approved`, `healthy != safe`, `projection != persistence`,
`schema conformance != professional approval`. These are working tools, not
decoration: this audit's own findings were reached by applying them, and the
retirement-guard finding below is precisely `guard green != subject clean`.

**`WHAT_RUNS.md` states its own limits accurately**, including "Green CI is not
adoption, approval or professional validation." Self-description at that
standard is rare and worth protecting.

## Finding 1 — rules outpace the checks that make them true

Six instances found in a single working session, each independently:

```text
OpenWebUI retirement guard   green because it excluded all 67 offenders   Pantheon-Next#995
boundary profile vocabulary  owner defines 7 names, 19 in use, no check   Pantheon-Next#1000
governance-ci body check     its only sanctioned fix was unreachable       Pantheon-Next#997
knowledge_family vocabulary  canonical enum vs blueprint, unreconciled     Pantheon-Next#989
ai_logs/INDEX.md             retired with ai_logs/ in the public repository  closed
check_index_coverage.py      reads as ai_logs coverage; excludes ai_logs   open
```

This is not six defects. It is one property: **a rule is written, an owner is
named, and nothing is built that can fail when the rule is broken.** Every case
above was green. Every one was invisible until read by hand.

The mechanism that works is already in use — a seeded two-way ratchet, applied
three times now (Pantheon-Next#785, Pantheon-Next#995, Pantheon-Next#1001). Its shape is worth stating as a repeated
pattern rather than rediscovered per incident:

```text
seed the allowlist with what exists   -> CI stays green, nothing is forced
refuse anything new                   -> the debt cannot grow
force delisting on repair             -> the debt stays exact
parse the rule from its owner         -> the check never becomes a second owner
```

The last line matters most and was learned late: `test_boundary_profile_vocabulary_conformance`
reads the defined set from `BOUNDARY_PROFILES.md` rather than restating it, so
editing doctrine admits a name with no test change. A check that holds its own
copy of a rule becomes a competing authority.

## Finding 2 — declared authority is almost entirely unexercised

46% candidate against 2% canonical says the doctrine is overwhelmingly proposed
rather than ratified. Six chokepoints wired and none connected says the same
thing from the executable side.

Nothing in this repository has yet refused anything on real professional work.

That is not an argument against the design. It is the sequencing risk Pantheon-Next#827
already recorded in the repository's own words — *"the risk is that Pantheon
architecture and doctrine advance faster than demonstrated professional value"* —
and the two numbers above are its measurement. Doctrine written before contact
with real refusals is doctrine about imagined cases; 46% is how much is awaiting
that contact.

## Finding 3 — the blocker is a doctrine question, not engineering

The connection gap has one identified cause, and it is not missing code.

`classify_request` assigns `K3` to any request with `writes_state: True`, and
`K3` requires `task_contract_ref` and `evidence_pack_candidate_ref`. Five of the
six chokepoints guard **human-originated writes** with no delegated task behind
them, so they supply neither and are refused.

```text
a Task Contract governs delegated work
these paths are a human writing directly
-> the gate is correct, or the doctrine is incomplete; not both
```

Until that is decided, the governance core cannot be connected to anything, and
therefore cannot be falsified. Recorded in `GOVERNANCE_STATUS.md` adoption gates
and in Pantheon-Next#942; still open.

## Assessment

The engineering underneath is sound and the central idea is correct. The two
risks are ordered:

1. the enforcement gap is cheap to close and is being closed incrementally;
2. the unexercised-authority gap is the one that decides whether any of this was
   right, and it is blocked behind a single unanswered doctrine question.

The highest-value next move is therefore not another doctrine slice and not
another migration. It is to answer the Task Contract question, connect **one**
chokepoint to **one** real path, and let it refuse something a human then accepts
or overrides. One real refusal converts a large share of the 46% from proposal
into evidence — including evidence about which parts were wrong.

## Boundary

Boundary profile applies: `validation_only_trace`.

Protected paths touched: no.
Runtime impact: none. This audit is repository content and changes no runtime,
schema, binding, activation or professional state.
Authority impact: none. It is non-normative. It ratifies no candidate document,
promotes nothing, resolves no open doctrine question — in particular it does not
answer the Task Contract question it names, which remains the maintainer's.
Schema/test/CI impact: none.
External action: none.
Memory behavior: none.

## Local distinctions

```text
rule owned          != rule enforced
guard green         != subject clean
authority declared  != authority exercised
wired               != connected
candidate volume    != demonstrated value
audit               != decision
```
