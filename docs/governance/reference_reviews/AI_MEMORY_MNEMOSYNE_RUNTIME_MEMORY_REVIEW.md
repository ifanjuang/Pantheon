# ai-memory vs Mnemosyne runtime-memory review

Status: external reference review — comparison only; no binding activation, dependency adoption, installation or authority change.

Date: 2026-08-25

Repository baseline reviewed: `Pantheon-Next@0f834822cab34268696112971500c454d213a4fa`.

External identities rechecked:

```text
akitaonrails/ai-memory
main / v1.32.0 = c304ff6ecba54b05c488345e2c4b0bba81cb9574

mnemosyne-oss/mnemosyne
main = 8e6c010bc823b7833061f0ee53c2a73a9dd6dd24

MrLuciano/ai-memory-hermes-plugin
main = 8e61b19b7481c86ece5ee24285e74514daf2398c
compatibility PR #2 head = af8885b35ebb00ff0199fb01f44b4d3f77c31bd3
```

## Question

Could `ai-memory` replace Mnemosyne for the already existing `external_runtime_memory` responsibility if cross-session and cross-agent workstream continuity becomes more important?

This review does not reconsider Hindsight's distinct workspace/document retrieval responsibility.

## Current responsibility split

```text
Mnemosyne
= observed Hermes runtime / conversational memory

Hindsight
= derived retrieval from intentional workspace/document sources

Pantheon
= governance, identity, provenance, authorization and Evidence
```

The Pantheon capability remains unbound. This review does not add a third active memory path.

## Mnemosyne — current fit

Mnemosyne remains the stronger current fit for fluid Hermes memory:

- direct Hermes integration exists;
- the deployed path has already demonstrated cross-session recall;
- local-first SQLite operation is comparatively simple;
- semantic/episodic recall, importance, recency and temporal memory directly match conversational-memory needs;
- the current deployment does not require a separate memory server plus lifecycle bridge.

The earlier qualification snapshot recorded these deployed package identities:

```text
mnemosyne-memory = 3.15.1
mnemosyne-hermes = 0.5.0
```

The current stable plugin release is `mnemosyne-hermes = 0.7.0`; the Linux
candidate now installs it beside the stable core `mnemosyne-memory = 3.15.1`.
This is an operational update, not a Pantheon authority decision or proof of
Hermes 0.21.3 qualification.

## ai-memory — differentiating value

`ai-memory` is architecturally interesting for a different reason: it models continuity of agent work rather than only recall of remembered facts.

Its useful concepts include:

```text
session history
failed approaches
decisions and rationale
open work
handoffs
cross-agent continuation
```

It also keeps a Git-versioned Markdown wiki as a human-inspectable memory artifact, with SQLite used as a derived operational/search index.

This makes it potentially stronger when the required behavior is:

```text
agent A works
→ agent B resumes the same workstream
→ prior decisions, failed attempts and open work remain recoverable
```

That differentiating capability has not yet been qualified on the target topology.

## Hermes compatibility finding

The current `ai-memory` release is `1.32.0`.

Hermes support remains community-maintained. The reviewed plugin's `main` has not advanced since 2026-07-24 and still predates material ai-memory API/lifecycle changes.

Open plugin PR #2 fixes issues including:

- obsolete search endpoint usage;
- lifecycle event payloads;
- configured scope handling;
- handoff consumption;
- session switching;
- cross-agent recall behavior;
- failure visibility.

However, PR #2 remains open/unmerged and reports validation against:

```text
Hermes Agent 0.20.5
ai-memory 1.28.1
Python 3.11
Windows 11
```

Therefore current compatibility with ai-memory `1.32.0` is not established.

```text
bridge exists != current compatibility qualified
community plugin available != production-ready binding
```

## Operational trade-off

Mnemosyne currently has the simpler runtime path:

```text
Hermes
→ Mnemosyne provider
→ local memory store
```

The reviewed ai-memory path adds more moving parts:

```text
Hermes bridge
→ ai-memory service
→ lifecycle capture / replay
→ derived index
→ Git / Markdown memory artifact
```

That additional complexity is justified only if cross-agent/workstream continuity demonstrates a material gain.

## Relationship to Hindsight

ai-memory is not a Hindsight replacement.

```text
Hindsight
= retrieval from intentional workspace/document sources

runtime memory
= conversational or workstream continuity
```

The first ai-memory qualification must keep its wiki outside the LiveSync/Hindsight source tree. Otherwise the same information could be persisted independently as runtime-derived memory and intentional workspace content without a clear responsibility boundary.

## Current classification

```text
ai-memory
capability_slot: external_runtime_memory
status: to_verify
possible_role: Mnemosyne successor for cross-session / cross-agent workstream continuity
comparison_target: Mnemosyne
not_a_target: Hindsight
activation: none
Pantheon authority: none
```

Current recommendation:

```text
KEEP      Mnemosyne as the observed Hermes fluid-memory path
KEEP      Hindsight for workspace/document retrieval
QUALIFY   ai-memory only as a possible Mnemosyne successor
DO NOT    run Mnemosyne and ai-memory as concurrent steady-state fluid memories
DO NOT    change Pantheon authority or Evidence semantics
```

## Qualification gate

A useful future comparison should test the same scenarios on both candidates.

### Q1 — current Hermes compatibility

Use the current Hermes target and current ai-memory release. Do not infer compatibility from README text or the older PR #2 matrix.

### Q2 — cross-session continuity

```text
session A records bounded context
→ session closes
→ fresh Hermes session
→ relevant context is recovered
```

Measure false/stale recall as well as success.

### Q3 — cross-agent workstream handoff

Demonstrate the differentiating capability:

```text
agent A records:
- one decision
- one failed attempt
- one open task

agent B resumes
→ recovers all three without invented state
```

### Q4 — scope isolation

Use two workspaces/projects with deliberately overlapping terminology. Global cross-project recall must not be enabled merely to make handoff work.

### Q5 — capture confidentiality

Prove that an excluded workspace produces no prompt/tool capture before spool or network transmission on the exact Hermes bridge path.

### Q6 — outage / restart

Verify bounded behavior while the memory service is unavailable, replay after restart, duplicate handling and visible failure state.

### Q7 — deletion / export / restore

Verify what deletion means across the runtime index, Markdown/Git artifact, queues and backups. Do not claim strong deletion from unreleased work.

### Q8 — Hindsight non-duplication

Keep ai-memory artifacts outside the workspace/Hindsight ingestion tree for the first qualification.

### Q9 — governance invariants

Every scenario must preserve:

```text
memory recalled != truth
memory artifact != Evidence
handoff delivered != authorization
runtime write success != ingestion authority
folder/path != governed identity
```

## Replacement decision

Replace Mnemosyne only if ai-memory demonstrates a material workflow gain while preserving or improving:

- current Hermes compatibility;
- scope isolation;
- confidentiality boundary;
- outage/recovery behavior;
- deletion/restore semantics;
- memory quality;
- operational maintainability.

Steady-state target remains one fluid runtime-memory provider, not two.

## Non-claims

This review does not establish that ai-memory is installed, approved, production-ready, compatible with Hermes on `1.32.0`, or superior to Mnemosyne. It does not activate any binding and does not change Hindsight, Pantheon authority or Evidence semantics.
