# Ecosystem Map

Status: active support doctrine — ecosystem positioning only — implemented as documentation.
Boundary profile: active_support_doctrine.

This map positions external systems around Pantheon Next without turning product choices into governance authority.

```text
Hermes clients interact.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides.
```

## Anchor

| Layer | Current relation | Boundary |
|---|---|---|
| Hermes Web/dashboard | baseline runtime interaction surface | chat/session/control UI, not Pantheon authority |
| Compatible Hermes mobile/PWA | optional replaceable client | selected only after compatibility/auth/deployment review |
| Hermes Agent | external execution runtime | tools, skills, sessions and runtime memory; no self-approval |
| Pantheon Cockpit | governed projection surface | Cards/navigation/review; not a general-purpose chat runtime |
| Obsidian | human Markdown workspace | notes/projections; not DMS, Evidence or governed Project identity |
| Hindsight / runtime memory | optional derived recall | memory != truth/Evidence |
| Pantheon Next | governance | contracts, status, Evidence/approval/Register boundaries |
| Professional source owners | exact source/provenance | existence/retrieval != truth |

OpenWebUI and Paperless are refused historical integration candidates, not target layers.

## Ecosystem families

| Family | Examples | Pantheon relation | Main question |
|---|---|---|---|
| Hermes clients | official web/dashboard, reviewed mobile/PWA clients | replaceable runtime UI | Does it use supported Hermes contracts and preserve auth/network boundaries? |
| Execution runtimes | Hermes, other reviewed runtimes | external execution or reference | What executes, under which contract/admission boundary? |
| Cockpit/projection UI | Pantheon Cockpit | governed presentation | What state is projected without becoming persistence or authority? |
| Workspace tools | Obsidian | human working surface | What is authored/edited without silently becoming governed state? |
| Memory systems | Hindsight, runtime memories | optional derived recall | What may be recalled, and what must never be treated as truth/Evidence? |
| Retrieval/RAG | indexes, vector/graph retrieval | Knowledge support | What was retrieved and what actually supports a claim? |
| Observability/evaluation | traces/eval tools | candidate operational evidence support | What can be inspected without treating score/trace as approval? |
| Connectors/tools | MCP, APIs, browser, email/calendar adapters | external capability surfaces | What is authorized, least-capability and evidence-bound? |
| Skill ecosystems | Hermes skills, external skill repositories | capability candidate source | Is an existing capability sufficient before adding another? |
| Professional verticals | architecture/legal/etc. assistants | domain inspiration | What human/professional review remains mandatory? |

## Authority order

External systems usually produce lower-authority artifacts until an existing Pantheon owner qualifies them.

```text
Raw Source
-> Source Reference
-> Knowledge / retrieval support
-> candidate output / observation
-> Evidence Item / Evidence Pack when qualified
-> Approval when required
-> Register Candidate when durable
-> Registre Probatoire entry only after governed promotion
```

## Capability placement

| Capability | Current/default owner | Must not become |
|---|---|---|
| chat/session/runtime controls | Hermes clients | governance source of truth |
| tool/workflow execution | Hermes Agent/external runtime | hidden Pantheon runtime |
| governed Card/navigation projection | Pantheon Cockpit | persistence or approval authority |
| Markdown notes/workspace editing | Obsidian | DMS, Evidence or Project identity |
| runtime/associative recall | Hermes/Hindsight when selected | canonical memory or truth |
| exact professional source identity | existing source/document owners | folder/path identity by implication |
| trace/evaluation | external observability/eval tooling | Evidence or approval by itself |
| approval | Pantheon governance + human | UI click/runtime success by implication |
| provider routing | external runtime | Pantheon provider router |
| connectors/MCP | external capability bindings | unrestricted plugin marketplace |

## Import rule

Before importing an external repository or product pattern:

```text
1. identify the real capability gap;
2. check existing Pantheon/Hermes owners;
3. classify the external system as client, binding, runtime, workspace, memory or reference;
4. distil useful invariants/contracts first;
5. select implementation only when a distinct responsibility remains;
6. keep it replaceable;
7. never infer adoption from working code alone.
```

Useful imports are normally vocabulary, typed contracts, evidence expectations, boundary checks or UX patterns. Avoid importing a second runtime, registry, DMS, chat frontend or memory authority when the need is already covered.

## Current client decision

OpenWebUI no longer has a distinct target responsibility: Hermes already supplies the runtime interaction surface, while the Pantheon Cockpit owns governed projections. Its integration path is refused.

The reviewed `willscott-v2/hermes-mobile-pwa` is a plausible optional Hermes mobile client because it stays thin and speaks Hermes dashboard contracts. It remains a replaceable candidate, not Pantheon core.

## Current document/workspace decision

Paperless no longer has a demonstrated required responsibility in the target architecture. Exact professional sources and local/NAS ingestion remain under the existing document/source owners; Obsidian supplies the human Markdown workspace. Paperless is refused as a target dependency.

```text
Obsidian note != source file
folder != governed identity
memory != Evidence
OCR/extraction != truth
```

## Related owners

- `CORE_CONCEPTS_MAP.md` — compact concept/owner navigation;
- `TARGET_ARCHITECTURE.md` — current target composition;
- `HERMES_INTEGRATION.md` — execution boundary;
- `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` — governed product projection composition;
- `OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md` — workspace/derived-memory topology;
- `EXTERNAL_TOOLS_POLICY.md` — external capability policy;
- `EXTERNAL_TOOL_PLACEMENT_REGISTER.md` — concrete placement decisions;
- `CAPABILITY_PLACEMENT.md` / `ADAPTERS_AND_BINDINGS.md` — abstract placement and binding rules;
- `EVIDENCE_PACK.md`, `APPROVALS.md`, `MEMORY.md` — authority transitions.

## Failure modes

Mapping has failed when:

- a product name replaces a Pantheon capability category;
- a client becomes a governance requirement;
- runtime completion becomes authorization;
- a trace/score becomes Evidence or approval;
- a retrieved item becomes truth;
- a folder becomes governed identity;
- memory becomes a Registre Probatoire entry automatically;
- Pantheon duplicates a capability already owned by Hermes or an existing owner;
- a historical integration is maintained only because code still exists.

## Final rule

```text
Map responsibility before product.
Map authority before trust.
Keep clients/adapters replaceable.
Remove parallel paths when one owner is sufficient.
```
