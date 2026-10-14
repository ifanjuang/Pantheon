# Pantheon Modules for the Hermes dashboard

Status: installable external Hermes dashboard-plugin template — inactive until
an operator installs and enables it in Hermes.

This plugin gives Hermes a live module inventory while preserving the status
distinctions required by Pantheon governance.

```text
listed != detected != installed != configured != enabled != reachable != healthy
Hermes enabled != Pantheon governance activation != task authorization
```

It is not a `dashboard/` runtime inside Pantheon Next. Its Python marker is
inert: it registers no hooks, tools, providers or routes. The plugin does not
receive a Pantheon write mount and does not hold a Hermes session token. The
host-provided plugin SDK performs same-origin authenticated calls to native
Hermes APIs.

## Visual contract

The plugin implements the Pantheon Control `control-v1` visual contract. Its
tokens, hero, toolbar, cards, badges, state grid and responsive rules are shared
with the read-only `docs/assets/pantheon-control/hermes-modules.html` preview.
Automated tests compare the shared CSS block and the required renderer markers
to prevent visual drift. The static preview remains a demonstration surface;
only the installed Hermes plugin exposes confirmed operational actions.

## What it reads

The inventory uses these native Hermes endpoints through the dashboard SDK:

```text
GET /api/memory
GET /api/mcp/catalog
GET /api/mcp/servers
GET /api/dashboard/plugins/hub
GET /api/cron/jobs?profile=all
```

The plugin was checked against Hermes Agent commit
`8b209e0dd7b8e308d5b923fa80f7a72f71042636` on 2026-07-15. Earlier Hermes
versions may not expose every method used by the plugin; unavailable reads are
reported as a partial inventory instead of being treated as a negative result.

## Governed night operations

The `Night ops` view adds an ordered catalog and observes matching native
Hermes Cron jobs by their stable names. The proposed window is:

| Host-local time | Operation | Initial bound |
|---|---|---|
| 00:30 daily | backup and restore preflight | 7 runs |
| 01:00 daily | PDF ingestion and scoped vectorization | 7 runs |
| 02:45 daily | retrieval and index quality review | 7 runs |
| 03:45 Sunday | memory consolidation review | 4 runs |
| 05:00 daily | contradiction and governance-drift review | 7 runs |
| 06:15 daily | local morning decision digest | 7 runs |

These times are proposals in the Hermes host's local timezone. Before any
activation, the operator must confirm the host clock/timezone, Hermes profile,
absolute workdir, input/output scope, adapter, delivery, resource envelope and
finite expiry or run limit. The complete contract is in
`night-operations.template.yaml`.

The plugin never creates or deletes Cron jobs. In the audited Hermes version,
the native dashboard create payload does not expose the core finite `repeat`
limit even though other native Hermes paths support it. Creating an infinite
recurring job from this convenience surface would violate the required
bounded-trial posture.

For one existing, unambiguous job whose finite repeat is observed, the card can:

- disable or re-enable the schedule after confirmation;
- select a host-local start time and save it while the schedule is disabled;
- launch one immediate run after a separate confirmation while the bounded
  schedule is enabled.

An observed unbounded job may be disabled, but it cannot be re-enabled,
retimed, or launched from this view. Missing and ambiguous jobs stay blocked
and route the operator to `Open native Cron`. An exhausted finite trial also
stays blocked until an operator reviews it and creates a new bounded trial.

The operation catalog preserves these distinctions:

```text
catalog entry != configured job != finite trial != enabled job
scheduled != task-authorized != approved result
indexed != evidence
memory review != memory deletion, merge, canonicalization or promotion
contradiction detected != contradiction resolved
```

## Explicit actions

Actions are sent only after a button click and a separate confirmation:

- select or stop using a ready Hermes memory provider;
- install a reviewed entry from the native Hermes MCP catalog;
- enable or disable an installed MCP server;
- probe an MCP connection;
- enable or disable a discovered Hermes plugin.
- pause or resume one existing finite Hermes Cron trial;
- retime that trial while paused;
- trigger one immediate run of an enabled finite trial.

Credentials entered for an MCP catalog install remain only in React component
state until submission. The plugin does not use `localStorage`, log credential
values or implement its own secret store. Hermes persists submitted values
through its native API.

Installation and enablement are operational Hermes states only. They do not
create a Pantheon activation record or authorize the capability for a Task
Contract.

## Known governed placements

| Capability | Placement | Dashboard behavior |
|---|---|---|
| Pantheon policy MCP | Read-only governance wiki | Observe, enable/disable and test when configured |
| Mem0 | Exclusive Hermes memory-provider candidate | Select only when Hermes reports `ready` |
| n8n | Optional high-risk automation MCP | Install from the pinned official catalog entry; show its read-mostly default tools and withheld mutating tools |
| LangGraph | External Hermes runtime candidate | Observe if surfaced by Hermes; no automatic install action |
| Memvid | External memory candidate | Show the adapter gap; no activation action |

n8n is useful when a concrete integration needs deterministic, repeatable
steps. It is not required for the Pantheon MVP and must not duplicate Hermes
reasoning, approvals or Task Contract checks.

## Install after review

The common baseline uses the already audited, read-only Pantheon checkout
mounted inside the Hermes container. Install the plugin from that pinned local
Git repository without enabling its browser code:

```bash
hermes plugins install \
  "file:///opt/pantheon-next-<COMMIT_SHORT>#templates/hermes/dashboard-plugins/pantheon-modules" \
  --no-enable
```

This binds the installed plugin content to the same reviewed commit as the MCP.
The command must run inside the Hermes container, directly or through
`docker exec` from the host.

For an exploratory installation where no pinned local checkout exists, Hermes
also supports the remote subdirectory shorthand below. It follows the remote
repository default branch and is therefore not the reproducible common-baseline
path:

```bash
hermes plugins install \
  ifanjuang/Pantheon/templates/hermes/dashboard-plugins/pantheon-modules \
  --no-enable
```

Review the installed files under
`~/.hermes/plugins/pantheon-modules/`, then enable the dashboard plugin:

```bash
hermes plugins enable pantheon-modules
```

Refresh the Hermes dashboard. The `Pantheon Modules` tab is inserted after the
native Plugins tab.

For a non-interactive installation only after equivalent review, replace
`--no-enable` with `--enable`.

## Disable or remove

```bash
hermes plugins disable pantheon-modules
hermes plugins remove pantheon-modules
```

Disabling or removing this dashboard plugin does not disable the modules it
previously observed. Manage those states in the native Hermes surfaces if the
Pantheon tab is unavailable.

## n8n boundary

The audited Hermes catalog entry pins
`CyberSamuraiX/hermes-n8n-mcp` at commit
`7a9ae00795593aa1fdb4e61ecd640e8bfd0c3841`. Its default tool selection is:

```text
health
list_workflows
get_workflow
find_workflows
list_executions
get_execution
recent_failures
export_workflow
```

The following tools exist in that bridge but are withheld from the default
selection:

```text
activate_workflow
deactivate_workflow
container_logs
```

The dashboard surfaces the upstream source, pinned ref and bootstrap commands
before asking for install confirmation. A successful connectivity probe is a
liveness observation only.
