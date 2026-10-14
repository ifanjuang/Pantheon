# Ubuntu node bootstrap candidate

Status: operator convenience artifact — candidate, non-authoritative.

Selection update (2026-09-30): the selected professional Workspace target is `NAS / AFFAIRES → one AFFAIRES producer → Cockpit + Hindsight` as owned by Pantheon-Next#660/#659. Self-hosted LiveSync and CouchDB have been retired from the active installer and qualification baseline; Git history preserves the former topology.

This directory provides a bounded convenience path for one Ubuntu compute node. The selected node runtime is native systemd Hermes, Hindsight, Docling and related services; Pantheon remains an installer helper, not a runtime owner, approval engine or deployment authority.

The generic owners remain:

- `docs/governance/COMMON_INSTALLATION_BASELINE.md`;
- `docs/install/COMMON_BASELINE_RUNBOOK.md`;
- `docs/governance/BOOTSTRAP_INSTALLATION_LADDER.md`.

## Current installer profile

The current installer prepares host dependencies and the Pantheon policy package. Native Hermes is an explicit prerequisite and is left untouched:

```text
Ubuntu node
├── native Hermes Agent + dashboard (preinstalled prerequisite)
├── Ollama
├── native Hindsight (optional active service)
└── pinned Pantheon checkout + bounded policy/MCP package
```

`install-node --apply` refuses to proceed unless the native Hermes gateway and dashboard are already active. `--with-hindsight` additionally requires the native Hindsight API service to be active. This installer never installs, enables or starts Docker, Hermes or Hindsight.

The `--bind` option configures the host Ollama API address (`127.0.0.1` by
default). Native Hermes and dashboard bind settings are managed by their own
systemd configuration and are not changed here. The Ollama model remains an
explicit operator choice; the deployment lock does not make a model a Pantheon
architectural dependency.

The local Ollama service uses a 65,536-token effective context window. Hermes
0.21 requires at least 64K; the model's larger advertised native window is not
the effective runtime window unless Ollama is configured accordingly.

The current availability **qualification target**, distinct from this installer lock,
is documented in `docs/install/HERMES_MODEL_AVAILABILITY_TARGET.md`: gpu-node serves
the 27B quality tier when available and Hermes' native fallback chain requests the
always-available Linux 9B tier on a qualifying primary-model failure. PAIR routes
the model Hermes requests; Pantheon does not become a model router. Model names
remain runtime/operator configuration rather than release-lock dependencies.

The same Linux node is also the target for the quantized CLM encoder experiment
under Pantheon-Next#1047. That co-residency is not assumed: the lab must observe whether CLM,
the 9B fallback and Hindsight can share/reload within the real 16 GiB GPU/runtime
envelope before any productive activation.

Hermes execution itself does not make a NAS an authority dependency. The selected professional Workspace path uses the reviewed NAS `/AFFAIRES` tree as its source filesystem for the Cockpit/Hindsight producer. No local LiveSync mirror is part of that path. A filesystem path still does not become governed identity merely because it is mounted.

## Install

From an exact Pantheon checkout on Ubuntu Server 26.04:

```bash
sudo deployment/ubuntu/install-node
```

Read-only preflight:

```bash
deployment/ubuntu/install-node --doctor
```

The default Ollama API bind is `127.0.0.1`. Expose deliberately to a specific LAN or private-network address only when required:

```bash
sudo deployment/ubuntu/install-node --bind <private-address>
```

The installer is intentionally interactive unless `--yes` is supplied. If the Ubuntu-recommended NVIDIA driver must be installed, the script stops after driver installation and requires a reboot before it is rerun.

## What starts automatically

`install-node` configures the Ollama and Pantheon policy components. It leaves
the already-installed native Hermes/Hindsight services in their current
activation state. It does not perform Hermes first-time setup.

The policy package lives in `/srv/pantheon/policy-venv` and reads the pinned
release through `/opt/pantheon/current`. `install-node` and `update-node` keep
both readable (never writable) by service users, so the native Hermes binding
should use them rather than a separate hand-installed copy that no updater
refreshes:

```yaml
mcp_servers:
  pantheon-policy:
    command: /srv/pantheon/policy-venv/bin/pantheon-mcp-server
    env:
      PANTHEON_REPO_PATH: /opt/pantheon/current
```

Keep the reviewed tool allowlist and posture from
`templates/hermes/connection/pantheon_policy_mcp.template.yaml`. After a release
switch, Hermes picks up the new policy package on its next restart.

The optional Hindsight container alone is not a qualified AFFAIRES ingestion route. Pantheon-Next#660 owns the single AFFAIRES producer and Pantheon-Next#659 owns Hindsight retain/retrieval qualification. Historical Obsidian integrations remain separate reference material and are not installed by this baseline.

## Private WireGuard DynHost update

When the router cannot reliably update DynHost, the WireGuard host can maintain
the endpoint DNS name itself. It prompts for the OVH DynHost credentials in the
local terminal, stores them root-only outside Git, and updates the record at
boot and every five minutes:

```bash
deployment/ubuntu/configure-ovh-dynhost-local --check
sudo deployment/ubuntu/configure-ovh-dynhost-local --apply --hostname vpn.example.fr
```

Do not keep a second router DynHost updater enabled for the same hostname after
the local updater succeeds. The router still forwards only WireGuard UDP 51820;
do not publish application dashboards.

## Hermes native capability check (read-only)

On the Ubuntu node with the existing Pantheon checkout and running Hermes
container, use the **existing** runtime observer:

```bash
deployment/ubuntu/observe-hermes-runtime --capabilities | jq '{
  runtime_version,
  running_image: .container.configured_image,
  native_capabilities
}'
```

This opt-in probe reads the selected `pantheon-governed` profile using Hermes
native CLI commands. It reports the configured Tool Search mode, how a few
common toolsets are **configured** for the CLI, and whether native Skill
Bundles can be listed. An unknown result means the CLI response could not be
confirmed, not that the feature is disabled. A configured toolset is **not**
proof its runtime dependencies exist or the tool is usable. The output omits
tool/bundle names beyond a fixed toolset allowlist and does not expose MCP
config or credentials. It does not enable tools, install bundles, restart
the runtime or run an agent.

Compare the **observed** container version with the reviewed deployment image:
a locally updated Hermes installation can legitimately differ from the
older repository candidate pin. Do not overwrite one with the other to hide that difference.
Native capability trials (Tool Search, bundles, `execute_code`, delegation)
continue under Pantheon-Next#1168; comparisons of delegation/Kanban remain under Pantheon-Next#1093.

## Governed visible Role milestones

After the `pantheon-governed` Hermes profile exists, install the versioned
activity-projection skill and its managed profile supplement with:

```bash
deployment/ubuntu/configure-hermes-activity-projection --check
sudo deployment/ubuntu/configure-hermes-activity-projection --apply --restart
```

The command keeps a timestamped backup under `/srv/pantheon/backups`. It affects
presentation for new governed sessions only. It does not expose hidden
chain-of-thought, create agents, persist Role Signals or implement the Cockpit
dialogue view.

To route one WhatsApp conversation to the governed profile and enable safe
progressive Role milestones, use its observed Hermes `chat_id`:

```bash
deployment/ubuntu/configure-hermes-activity-projection --check \
  --route-whatsapp --whatsapp-chat-id '<chat-id>'
sudo deployment/ubuntu/configure-hermes-activity-projection --apply --restart \
  --route-whatsapp --whatsapp-chat-id '<chat-id>' \
  --with-curated-default-skills

# Optional agency organization adapter and its already configured local bindings:
sudo deployment/ubuntu/configure-hermes-activity-projection --apply --restart \
  --with-vault-adapter --bind-local-mcp
```

Use `--all-authorized-whatsapp` instead of `--whatsapp-chat-id` only when every
conversation already admitted by the WhatsApp adapter should use
`pantheon-governed`. The configurator does not widen that adapter allowlist. It
merges existing profile routes and profile allowlist entries, disables raw
reasoning display on WhatsApp, enables safe interim assistant messages, and
keeps a backup of the Hermes configuration. These are supported Hermes settings;
the provider source and image are not patched.

The governed profile remains generalist: its stable repository-owned core is
`pantheon-governed-method`, `pantheon-activity-projection`,
`pantheon-request-intake`, `external-commitment-guard` and `source-research`.
Five progressively loaded domain owners cover construction cost and offer
review, site reports, administrative forms, technical standards and works
schedules. They are selected by the reasoning required and do not redefine the
profile identity. Drafting and correspondence remain production forms rather
than catch-all specialist identities.
Capabilities and organization adapters are available modules selected from the
request, manifest and admitted runtime bindings; they do not redefine the
profile identity.

`--with-vault-adapter` adds `project-context` and `vault-search` as
contextual modules. With that explicit adapter, `--bind-local-mcp` copies no
arbitrary server. It merges only the
already configured local `Doclin`, `hindsight-affaires`,
`hindsight-documentaires` and `pantheon-policy` entries from the default profile
into the governed profile and adds the separately installed, loopback-only
`vault-read` binding with its dedicated bearer credential. The copied
Pantheon Policy entry is narrowed to the
reviewed read-only consultation, request classification/preflight, candidate
skeleton and Context Pack tools. It uses the project-scoped `hindsight-project` binding
from the already configured local Hindsight endpoint and refuses a partial result
when either required professional Hindsight binding is absent.

### Agency exact-source fallback

Pantheon knows two vaults: `projects` (project documents, read one project at
a time) and `knowledge` (reference documents shared across projects). Each
installation maps them to its own roots and Hindsight banks; the names used
on a node stay in its local bindings, not in this repository.

The optional agency reader resolves a project directory before topic keywords,
lists bounded `.md`/PDF candidates within that project, and provides
line-located, capped reads of exact Markdown files. It can also read an exact
`knowledge` Markdown path. It cannot write files or open arbitrary host paths;
`projects` reads require a matching project reference. PDF content still goes
through Docling. Inventory matches and search previews are not source
inspection or Evidence.

The reader runs as the existing `pantheon-docling` service user, which already
has the vault ACL. Do not broaden the Hermes runtime user's filesystem ACL.
This local systemd service does not require Docker. Select both NAS mount paths
on the machine where it runs; they are not fixed by the repository.
Installation and profile binding are separate explicit steps:

```bash
deployment/ubuntu/configure-vault-read-local --check
sudo deployment/ubuntu/configure-vault-read-local \
  --apply --projects-root /path/to/mounted/projects \
  --knowledge-root /path/to/mounted/knowledge --enable
deployment/ubuntu/configure-hermes-activity-projection --check \
  --with-vault-adapter --bind-local-mcp
sudo deployment/ubuntu/configure-hermes-activity-projection --apply --restart \
  --with-vault-adapter --bind-local-mcp
```

The service binds only `127.0.0.1:8021` and requires a retained token under
`/srv/pantheon/docling`; the token is not printed. The configurator puts only
this credential and the four reviewed read-only tool names in the governed
profile's MCP binding. A configuration checkpoint precedes profile changes.

`--with-curated-default-skills` retains the profile's `.no-bundled-skills`
boundary and copies only Obsidian, PDF, DOCX, XLSX, PowerPoint, Google
Workspace and grounded citations from skills installed
under the native Hermes `HERMES_HOME/skills` tree. It also sets dynamic tool
search to `auto`; Web, browser, vision and generation toolsets remain governed
runtime capabilities and are discovered only when relevant.

For material professional questions, that skill set imposes a generic source preflight:
AFFAIRES for dossier facts, DOCUMENTAIRES for transversal professional facts,
and both for mixed questions. The task-local receipt records the actual binding,
exact source opened, inspected locator and limitations; it is a trace, not
Evidence or source validation. When continuity or dossier resolution is needed,
the recall-only memory binding may produce one fast, explicitly unconfirmed
`Mnemosyne` milestone while the exact professional source lookup continues.

Hermes routing is based on trusted platform/chat/thread metadata, not on a
semantic guess about each question. Once a chat reaches `pantheon-governed`, the
activity-projection skill applies the content-sensitive part: simple requests
remain quiet, while non-trivial governed work gets compact Role milestones. A
Hindsight retrieval is observable tool use; it does not by itself activate the
Mnemosyne responsibility.

Pantheon's live-acceptance collector also contains a transient, read-only
`role.stage` projector for public Hermes Runs events. It can show canonical Role
headers as they arrive and real Hermes tool lifecycle stages. It deliberately
ignores `reasoning.available`; it is not installed as a service and does not
persist or authorize anything.

The candidate composed Cockpit also has a bounded authenticated SSE relay for
already-admitted runs. It can attach automatically after governed runtime-start
recording and render a compact browser dialogue when its dedicated Hermes trace
URL and key are configured. The Workspace Cockpit on port 8189 can expose the
same projection through an optional transient sidecar. The browser receives no
Hermes credential, and neither component gains run-control or approval methods.

## Dedicated Hermes reconciliation profile

The transient Workspace/Hindsight reconciliation path uses a separate Hermes
profile with no model tools. Provisioning that profile is explicit and remains
separate from runtime activation:

```bash
export HERMES_RECONCILIATION_API_KEY="$(openssl rand -hex 32)"
sudo -E bash deployment/ubuntu/configure-hermes-reconciliation-profile --apply
```

The configurator creates `reconciliation` with `--no-skills`, disables external
memory and dynamic tool search, sets `platform_toolsets.api_server` to
`[no_mcp]`, clears MCP/plugin bindings, and requires a profile-specific API key.
It does not start a gateway, enable `gateway.multiplex_profiles`, change routing,
or modify Cockpit settings.

When an operator has separately activated either a multiplexed
`/p/reconciliation` route or a separately supervised profile API, verify the
actual runtime surface:

```bash
HERMES_RECONCILIATION_API_KEY=<same-profile-key> \
  bash deployment/ubuntu/configure-hermes-reconciliation-profile --check \
  --runtime-url http://127.0.0.1:8642/p/reconciliation
```

That live check fails if any Hermes toolset is enabled and also confirms the
Responses API and session-deletion endpoint required by Cockpit.

```text
configured != activated
runtime observed != task-authorized
reconciliation candidate != Evidence
```

## Docling for Hermes

Install the pinned Docling SDK and Docling MCP server:

```bash
sudo ./configure-docling-local --enable
```

Docling `2.126.0` and Docling MCP `3.2.0` run as the restricted
`pantheon-docling` user. The MCP endpoint is loopback-only at
`http://127.0.0.1:8020/mcp`; no CouchDB credentials are involved. The installer
writes a reviewable Hermes fragment to `/srv/pantheon/hermes/docling-mcp.yaml`;
it does not silently modify Hermes' active configuration or authorize a new
tool. Merge that fragment into Hermes after reviewing the active MCP policy.
The host Docling service and the bounded source reader must receive the same
operator-selected `PROJECTS_ROOT`. Hermes passes an admitted source path as tool
input; Hermes does not need a separate NAS mount. Hindsight indexes remain outside Hermes' file surface.

## Read-only Workspace Cockpit

The executable Workspace Cockpit now follows the selected direct-NAS topology. It does not require PostgreSQL or pgvector for its bounded workspace projection, does not own a filesystem mirror, and does not read CouchDB.

```text
Project-platform
└── AFFAIRES              -> PROJECTS_ROOT
             |
             v
      one standalone Workspace producer
      |      -> reconstructible SQLite technical state
      |      -> bounded Hindsight producer operations
      |
      +--> optional Cockpit persisted projection
```

The selected node profile runs the producer and optional Cockpit as native
systemd services. The Compose project below is retained for separate,
container-based qualification and is not part of the active node deployment.
On a host where that workflow is deliberately used, keep the selected NAS root
and host group in an ignored local env file:

```bash
umask 077
cat > .env.workspace-cockpit <<'EOF'
PROJECTS_ROOT=/mnt/pantheon-affaires/AFFAIRES
AFFAIRES_GID=replace-with-affaires-mount-group-id
EOF
# Use the group recorded on the qualified mount, for example:
# sed -i "s/replace-with-affaires-mount-group-id/$(stat -c %g "$PROJECTS_ROOT")/" .env.workspace-cockpit
docker compose --env-file release.env --env-file .env.workspace-cockpit \
  -f compose.workspace-cockpit-local.yaml up -d --build
```

To bind to one reviewed LAN/private address, keep host-specific values and secrets in an ignored local env file and load it after the release lock. For authenticated access outside the LAN, the separate Tailscale candidate remains available.

### Additional source producers

A node can feed more mounted source roots into Hindsight than the AFFAIRES producer, such as a professional library. Each root runs as one instance of the templated `pantheon-workspace-producer@NAME.service`. Its non-secret settings live in `/etc/pantheon-workspace-producers/NAME.env`; shared secrets stay in `/etc/pantheon-workspace-cockpit.env`.

```bash
deployment/ubuntu/configure-workspace-producer --list
deployment/ubuntu/configure-workspace-producer --set library --root /mnt/share/LIBRARY --bank LIBRARY_BANK --label Library --max-depth 1
sudo deployment/ubuntu/configure-workspace-producer --set library ... --apply --enable
sudo deployment/ubuntu/configure-workspace-producer --remove library --apply
```

Without `--apply`, the script prints the instance file and the systemd drop-in it would write (`RequiresMountsFor`, service user, writable index directory). `--state-db` reuses an existing index so a migrated root is not resubmitted. The script prints the matching Cockpit `--workspace-db LABEL=PATH` projection argument. The producer runtime itself is installed by `configure-workspace-cockpit-local`.

The AFFAIRES producer keeps its dedicated `pantheon-affaires-producer.service` for now. Converging it onto the template is a follow-up, so that one producer mechanism remains. A producer feeds derived recall only; indexing is not Evidence and a folder is not governed identity.

### Hindsight retain-completed hook

The optional enrichment receiver remains loopback-only. It receives a signed
`retain.completed` event, validates the bank and queues the document identity;
it does not access the NAS, change source files, infer dates, or re-retain a
document. The HMAC secret is generated outside Git. Prepare it, start the
service, then register the webhook in Hindsight:

```bash
sudo ./configure-hindsight-enrichment-hook --prepare
docker compose --env-file release.env --env-file .env.workspace-cockpit \
  -f compose.workspace-cockpit-local.yaml --profile enrichment \
  up -d --build hindsight-enrichment-hook
sudo ./configure-hindsight-enrichment-hook --apply
```

After the final command, **Settings → Webhooks** in the `PROJECTS` bank shows
one enabled `retain.completed` endpoint. The Hindsight bank configuration also
defines a small controlled vocabulary of entity labels (person, organisation,
project, document, place, contract, lot, standard and asset). Unknown entities
remain allowed so that retrieval does not silently discard a source fact.

The enrichment endpoint is private/LAN publication, not authenticated Internet publication.

The native systemd services are the selected deployment. Configure both
units, then activate the Hindsight producer alone; the read-only Cockpit
remains an explicit optional addition:

```bash
sudo ./configure-workspace-cockpit-local \
  --user <linux-user> --projects-root /mnt/pantheon-affaires/AFFAIRES \
  --enable-producer
# Only if the local Cockpit interface is wanted:
sudo ./configure-workspace-cockpit-local \
  --user <linux-user> --projects-root /mnt/pantheon-affaires/AFFAIRES \
  --enable-cockpit
```

The service binds to `127.0.0.1:8189` by default and admits only the reviewed `PROJECTS_ROOT`. `ARCHIVES/PROJET` is not a Workspace source and is not scanned, indexed or sent to Hindsight. Nested directories named Archive/Archives remain excluded recursively inside AFFAIRES. Cockpit is a projection and never becomes another scanner or Hindsight writer.

## Governed Hermes skills

`release.env` carries a small reviewed list of Pantheon-authored Hermes skills.
The install/update path copies only those named packages from the exact target
Pantheon checkout into `/srv/pantheon/hermes-governed-skills`, keeps the copy
read-only, and adds that host path to the existing `pantheon-governed` profile
through the native Hermes CLI when that profile is already present.

The deployment does not expose the whole template tree, create the governed
profile or replace pre-existing external skill directories. Availability of a
skill remains distinct from use, authorization, persistence and approval.

## Update

The native updater does not stop legacy services, remove containers, edit Compose files or delete historical state. Those retained artifacts require a separate, explicitly reviewed retirement procedure.

The distinction between Pantheon Next content, organization overlays and
installation state is documented in
[`docs/install/UPDATE_PRESERVATION_BOUNDARY.md`](../../docs/install/UPDATE_PRESERVATION_BOUNDARY.md).
Review that boundary before applying a Pantheon update, especially when local
Hermes profiles or skills have been added.

```text
runtime disabled != historical data deleted
checkpoint != complete database backup
```

Check only:

```bash
deployment/ubuntu/update-node --check
```

Apply the reviewed target set:

```bash
sudo deployment/ubuntu/update-node --apply
```

Or one component family:

```bash
sudo deployment/ubuntu/update-node --apply --component ollama
```

Pantheon never follows `main` implicitly. A Pantheon change requires a reviewed full commit SHA:

```bash
sudo PANTHEON_COMMIT_OVERRIDE=<40-char-sha> deployment/ubuntu/update-node --apply --component pantheon
```

Root cannot authenticate to a private GitHub repository. Point the update at a local operator checkout that already contains the reviewed commit, for example the clean `main` worktree:

```bash
sudo PANTHEON_REPOSITORY_OVERRIDE=/path/to/clean/main/checkout PANTHEON_COMMIT_OVERRIDE=<40-char-sha> deployment/ubuntu/update-node --apply --component pantheon
```

The new checkout then records that local path as its origin, so later updates read from it as well.

Hermes and Hindsight package upgrades are managed separately from `update-node`; this updater does not pull or replace their runtimes.

## Version posture

The current Hindsight qualification/deployment candidate is 0.10.2. The active node uses a native service. Historical image pins remain available to optional Compose-based qualification workflows; they are not used by the node installer or updater.

`release.env` is a deployment-candidate lock, not the external qualification registry. It may intentionally differ from `implementation/qualification/external-pins.json` where a newer upstream stable release has been reviewed for installation but has not been promoted as a qualified Pantheon binding.

```text
upstream release available != deployment target selected
selected deployment target != qualified provider binding
installed != activated
activated != task-authorized
runtime success != Evidence
filesystem mirror != governed identity
```

## Persistence

Operational data stays outside Git checkouts:

```text
/opt/pantheon/          pinned code checkouts
/opt/pantheon-node/     installer-managed application material
/etc/pantheon-node/     root-owned configuration and generated secrets
/srv/pantheon/          runtime state and workspace mirror
/srv/ai/                models and caches
```

Native Hindsight state remains outside Git checkouts. Use the configured state
path from its systemd environment when planning backups; the updater does not
move, rewrite or remove it. Any former Docker volume remains untouched.

Generated secrets are root-only and must not be committed. The updater creates a configuration checkpoint before changes; it does not pretend that checkpoint is a complete stateful database backup.

## Not in the first executable slice

The following remain intentionally optional rather than becoming hidden baseline dependencies:

- Syncthing Ubuntu `send-only` -> NAS `receive-only` replication;
- Tailscale/private remote access;
- external authenticated web publication;
- Hindsight durable ingestion/producer activation;
- authenticated Workspace Cockpit publication beyond a reviewed private bind.

Those can be added only when their actual configuration and qualification needs are demonstrated.


## Qualify the mounted AFFAIRES path

The productive Workspace/Hindsight topology is evaluated from this Linux host against the NAS path as mounted here. Hindsight remains local to Linux; the AFFAIRES daemon is the filesystem watcher and Hindsight producer.

Set `PROJECTS_ROOT` locally to the reviewed project root whose direct children
are project directories. The project catalogue derives only from these
first-level directories. A filesystem folder is a routing/project-scope
observation, not governed Project identity. The repository never assumes a NAS
hostname, share, project name, or intermediary folder.

Create the SMB credentials file locally as root with mode `0600`; never put its
contents in Git, shell arguments or chat. Install `cifs-utils`, then configure a
persistent mount without embedding site-specific names in the repository:

```bash
sudo deployment/ubuntu/configure-affaires-nas-mount \
  --apply --source //HOST/SHARE --prefix-path RELATIVE/PATH \
  --target /path/to/mounted/AFFAIRES --enable
```

The host, share, relative path and credentials are operator inputs. Consumers
still bind the resulting mount read-only even though the host mount permits the
explicit cartouche write workflow.

Before enabling the producer, run:

```bash
python3 deployment/ubuntu/qualify-affaires-linux-mount.py \
  --root /path/to/mounted/AFFAIRES --require-network-mount
```

The probe is self-cleaning by default. It requires write access because future cartouche generation also requires the Linux service to create `.SOURCE.ext.md` files. Use `--keep` only for manual inspection.

If the probe reports `inotify: not-observed-reconcile-required`, the mount can still qualify for correctness: keep periodic reconcile enabled and treat watcher delivery only as an optimization.

Hindsight banks follow two usages, each with a repository preset in
`hindsight-bank-presets/` (extraction, observation and reflection missions,
entity labels, retrieval modes, no automatic consolidation):

- `projects`: project documents, recalled one project at a time;
- `knowledge`: reference documents shared across projects (regulations,
  standards, templates, methods). They are sources to cite, not governed
  Knowledge, and never project obligations by themselves.

Converge each bank after Hindsight is healthy:

```bash
deployment/ubuntu/configure-hindsight-bank --usage projects --check
deployment/ubuntu/configure-hindsight-bank --usage knowledge --bank KNOWLEDGE --apply
```

An organization adds its own context with `--overlay FILE`, kept outside the
repository with the other installation bindings. The overlay may only append
text to the three missions (`mission_additions`) and add entity labels or
label values (`entity_labels`); the script refuses any other key, so the
preset's safety settings cannot be weakened locally:

```json
{
  "mission_additions": {"retain_mission": "The library also holds ..."},
  "entity_labels": [{"key": "document_family", "values": [{"value": "internal", "description": "..."}]}]
}
```

A failure observed in use is fixed in the preset when it concerns every
organization, and in the overlay when it is specific to one.

Its project material is not exposed through the direct multi-bank Hindsight MCP.
Hermes uses the authenticated project router installed by
`configure-hindsight-project-router-local`, which always applies the exact
`source:project-sync` and `scope:project:*` tags with `all_strict` matching.

A reference library bank (standards, guides, insurer recommendations,
glossaries) uses a second, independent instance of the same router:

```bash
deployment/ubuntu/configure-hindsight-project-router-local --library --check
sudo HINDSIGHT_KNOWLEDGE_BANK_ID=<library-bank> HINDSIGHT_KNOWLEDGE_SOURCE_KIND=<library-source> \
  deployment/ubuntu/configure-hindsight-project-router-local --library --apply --enable
```

It listens on `127.0.0.1:8023` with its own bearer token, exposes only
`recall_knowledge_memory` and `hindsight_knowledge_folders`, and always applies the
library source tag (plus an optional `folder:*` tag) with `all_strict` matching.
Library content is transversal reference, never a project fact. Bank and source
names are installation values kept outside the repository.
