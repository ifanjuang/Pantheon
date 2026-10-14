# Common Installation Baseline — Manual Runbook

Status: candidate operator runbook — current selected-stack handoff — documented non-implemented.
Boundary profile: candidate_support_note.

This is the single current operator runbook for the common Pantheon Next baseline. It documents reviewable installation and acceptance steps; it executes nothing, stores no secret and grants no production authorization.

Read first:

```text
docs/governance/COMMON_INSTALLATION_BASELINE.md
docs/governance/HERMES_INTEGRATION.md
docs/governance/OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md
docs/install/REFERENCE_PLATFORM_COMPONENTS.md
docs/governance/BOOTSTRAP_INSTALLATION_LADDER.md
templates/hermes/connection/pantheon_policy_mcp.template.yaml
```

OpenWebUI and Paperless are not baseline dependencies. Historical product-specific implementation may remain under `implementation/` until the protected cleanup slice removes verified-unused compatibility code.

## 1. Record operator decisions

Keep deployment-specific values outside the repository:

```text
TARGET_HOST
HOST_OS_AND_ARCHITECTURE
CONTAINER_RUNTIME_VERSION
PRIVATE_CONTAINER_NETWORK
CONTAINER_DATA_ROOT
PANTHEON_COMMIT
PANTHEON_VERSION
HERMES_VERSION
HERMES_CONTAINER
HERMES_API_SERVER_KEY reference
MODEL_PROVIDER_AND_MODEL
SELECTED_CONDITIONAL_SERVICES
PINNED_IMAGES_OR_DIGESTS
GOVERNED_SOURCE_ROOTS
OBSIDIAN_WORKSPACE_ROOT when selected
BACKUP_TARGET
ROLLBACK_TARGET
```

Do not commit real credentials, private paths or unredacted environment files. A deployment path is not a governed identity.

## 2. Bootstrap the external runtime environment

Before Hermes is available, the human/operator uses SSH, Docker/Podman, Portainer or equivalent infrastructure tooling.

Required foundation:

```text
administrative maintenance access
container/runtime substrate where used
private network boundary
persistent storage where required
backup / rollback posture
Hermes Agent
Hermes Web/dashboard
```

Pantheon does not install itself through Hermes and does not acquire Docker, SSH or host-administration authority.

## 3. Private network posture

Use an operator-selected private network for internal services. `ai-net` remains an implementation example, not a governed identity or mandatory name.

Command Candidate — not executed by Pantheon:

```bash
docker network inspect ai-net >/dev/null 2>&1 \
  || docker network create --driver bridge ai-net
```

Default exposure rule:

```text
Hermes Web/dashboard -> operator-selected LAN/VPN/private exposure
Hermes internal API  -> private by default
Pantheon policy API  -> private by default
PostgreSQL            -> private when selected
model/search/browser/extraction services -> private when selected
```

Publishing a port or dashboard beyond the selected private boundary is a separate reviewed operator/security decision.

## 4. Configure Hermes

Use a pinned/reviewed Hermes release and provider/model configuration.

Typical API-server settings where the selected Hermes deployment needs the Pantheon integration seams:

```yaml
API_SERVER_ENABLED: "true"
API_SERVER_HOST: "0.0.0.0"
API_SERVER_PORT: "8642"
API_SERVER_KEY: "${HERMES_API_SERVER_KEY}"
HERMES_INFERENCE_PROVIDER: "<PINNED_PROVIDER>"
HERMES_INFERENCE_MODEL: "<PINNED_MODEL>"
```

Provider-specific credentials remain externally managed.

```text
model downloaded != model approved
provider reachable != task-authorized
Hermes running != Pantheon admission enforced
```

Persist Hermes state according to the runtime's own operational contract. Do not give Hermes a write mount to the Pantheon repository, Docker socket or host SSH credentials merely to simplify deployment.

## 5. Prepare a pinned Pantheon checkout

Operator Candidate:

```bash
export PANTHEON_COMMIT="<FULL_COMMIT_SHA>"
export PANTHEON_SHORT="$(printf '%s' "$PANTHEON_COMMIT" | cut -c1-7)"
export PANTHEON_ROOT="<CONTAINER_DATA_ROOT>/pantheon"
export PANTHEON_CHECKOUT="$PANTHEON_ROOT/pantheon-next-$PANTHEON_SHORT"

mkdir -p "$PANTHEON_ROOT"
git clone https://github.com/ifanjuang/Pantheon.git "$PANTHEON_CHECKOUT"
git -C "$PANTHEON_CHECKOUT" checkout --detach "$PANTHEON_COMMIT"
git -C "$PANTHEON_CHECKOUT" status --short
git -C "$PANTHEON_CHECKOUT" rev-parse HEAD
```

Expected:

```text
working tree clean
resolved commit == selected commit
```

A pinned checkout is provenance/configuration input. It does not prove deployment, adoption or activation.

## 6. Connect Pantheon policy/consultation surfaces when selected

The bounded MCP/policy service remains a separate Pantheon implementation surface. Install it into Hermes only when the reviewed deployment requires it.

Operator Candidate:

```bash
docker exec -it <HERMES_CONTAINER> sh -lc '
  set -eu
  VENV=/opt/data/pantheon-mcp/<PANTHEON_VERSION>/venv
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip
  "$VENV/bin/python" -m pip install /opt/pantheon-next-<COMMIT_SHORT>/mcp-server
  "$VENV/bin/pantheon-mcp-server" --help
'
```

Use the reviewed Hermes connection fragment:

```text
templates/hermes/connection/pantheon_policy_mcp.template.yaml
```

Required posture:

```text
bounded tool allowlist
prompts disabled unless separately reviewed
resources disabled unless separately reviewed
sampling disabled
parallel calls disabled where the contract requires serialization
pinned read-only repository path
no hidden external-effect authorization
```

A successful consultation proves only that the bounded interface answered.

## 7. Configure governed professional source paths

Where local/NAS document ingestion is selected:

```text
reviewed source root
-> read-only runtime mount where possible
-> Task Contract declared-source check
-> resolved-path containment check
-> exact source locator + digest
-> selected extraction binding when needed
-> candidate Document / Project Document state
```

```text
file visible != source admitted
folder != governed Project identity
extracted text != source truth
runtime success != Evidence
```

No DMS product is required for this baseline.

## 8. Configure Obsidian separately when selected

Obsidian is the human Markdown workspace direction, not the professional-source or Evidence authority.

Record separately:

```text
workspace root
synchronization mechanism
backup/restore posture
project/context mapping policy
Hindsight indexing scope when selected
```

```text
Obsidian note != professional source file
Obsidian folder != governed identity
Hindsight recall != truth
memory != Evidence
```

## 9. Conditional services

Install only when an existing capability/binding owner demonstrates the need:

```text
PostgreSQL / pgvector for the selected co-located implementation
Ollama or another model runtime
embedding service
SearXNG or another search binding
Chromium / Browserless or another browser binding
Docling or another document-structure binding
OCR / VLM extraction
observability / evaluation backend
Hindsight or another reviewed runtime-memory binding
compatible Hermes mobile/PWA client
other reviewed connectors
```

```text
service present != binding selected
binding selected != activated
activated != task-authorized
reachable != healthy
healthy != safe
```

## 10. Hermes dashboard helpers

Hermes-native dashboard/plugin helpers may be installed only when separately reviewed. Installation and enablement remain Hermes operational states, not Pantheon approval.

If the reviewed `pantheon-modules` dashboard plugin is selected, retain a pinned source reference and review its copied files before enablement.

```text
plugin available != installed
installed != enabled
enabled != task-authorized
```

## 11. Acceptance checks

At minimum record:

```text
Hermes version and selected model/provider
Hermes dashboard reachable through intended exposure boundary
Pantheon consultation surface reachable when selected
bounded source path accepts one declared synthetic source
path escape / undeclared source is refused
selected conditional services report their own bounded observations
backup / rollback target recorded
```

Pantheon consultation should continue to preserve:

```text
contract=pantheon.consultation.v1
authority_effect=none
external_action_authorized=false
```

Do not collapse separate runtime observations into one synthetic `ready` or `safe` flag.

## 12. Update and rollback

Before change, retain:

```text
previous Hermes configuration
previous MCP executable/configuration when selected
previous pinned Pantheon checkout
previous image references
stateful-service backup references
source/workspace mount notes
network/exposure notes
```

Rollback order:

```text
disable the changed binding/plugin/client
restore the previous native runtime configuration
restart only the affected external runtime when required
verify the previous Hermes interaction path
verify Pantheon consultation when selected
verify source and conditional-service bindings
preserve failure logs as technical trace
```

Do not delete governed records or application volumes during routine rollback.

## 13. Refused former baseline paths

Do not add these merely to recreate responsibilities already covered by the selected baseline:

```text
OpenWebUI as required chat/cockpit layer
Paperless as required or preferred DMS/source-management layer
```

Historical compatibility artifacts are not installation instructions for the target architecture.

## Responsibility map

```text
Hermes Web/dashboard -> runtime interaction
Hermes Agent         -> external execution
Pantheon Cockpit     -> governed projections
Pantheon Next        -> governance/admission/status semantics
Obsidian             -> human Markdown workspace
professional files   -> exact source/provenance owners
Human/operator       -> installation, exposure, secrets, update, rollback and consequential approval
```

```text
projection != persistence
retrieved != truth
memory != Evidence
execution success != authorization
```
