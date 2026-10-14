# Bootstrap Installation Ladder

Status: candidate orientation — cold-start installation sequence and dependency ladder.
Boundary profile: candidate_support_note.

This document is a candidate orientation, not an implementation.

It does not create Docker configuration, compose files, install scripts, packages, system services, firewall rules, reverse proxy rules, VPN setup, DNS records, SSH keys, secrets, GPU drivers, runtime services, Portainer setup, OpenWebUI setup, Hermes setup, queue, scheduler, memory engine, vector database, GraphRAG runtime, LangGraph runtime, Langflow runtime or connector gateway.

## Purpose

Define how Pantheon should reason about installation when starting from a machine or NAS with nothing installed.

At cold start, Hermes is not installed.
OpenWebUI is not installed.
Docker or Portainer may not be installed.
No runtime can yet execute Pantheon requests.

Therefore Pantheon cannot depend on Hermes for the first installation steps.

## Core distinction

```text
Bootstrap prepares the ground.
Installer executes the first technical actions.
Hermes executes only after it exists.
Pantheon governs before, during and after through checklists, plans and status.
```

## Bootstrap problem

The dependency loop:

```text
Pantheon wants Hermes to install modules.
Hermes is itself a module that may need installation.
OpenWebUI may be the cockpit surface, but may also need installation.
Docker / Portainer may be useful, but may also need installation.
```

This means the first layer must be independent from Hermes.

## Installation layers

### Layer 0 — Human / physical baseline

Required before any automation:

```text
machine selected
administrator access available
network reachable
storage available
backup posture known
risk accepted by human
```

Pantheon role:

```text
provide checklist
classify risk
record decision candidate
```

Execution owner:

```text
human operator
```

### Layer 1 — Bootstrap medium

A minimal installer carrier exists before runtime.

Possible carriers:

```text
manual checklist
copy-paste shell commands
read-only install guide
USB / local folder bundle
Git clone / zip download
NAS package manager when available
vendor app store when available
```

Pantheon role:

```text
generate installation plan candidate
generate preflight checklist
generate rollback checklist
generate expected state
```

Execution owner:

```text
human operator or vendor package manager
```

### Layer 2 — Base system capability

The target machine is checked for:

```text
OS / NAS OS
architecture
CPU
RAM
storage
network
container support
VM support
GPU / NPU / iGPU presence
permission model
logs
backup / snapshot
```

Pantheon role:

```text
classify machine profile
recommend role
block unsafe assumptions
```

Execution owner:

```text
human operator
```

### Layer 3 — Container or service substrate

A substrate may be installed if appropriate:

```text
native packages
Docker / container engine
Portainer or equivalent management UI
VM manager
NAS app container system
systemd / service manager
```

Pantheon role:

```text
prepare substrate plan candidate
state risks and ports
state secret requirements
state rollback path
```

Execution owner:

```text
human operator
bootstrap installer
vendor package manager
```

Pantheon must not silently install it.

### Layer 4 — Minimal cockpit / documentation surface

A minimal static surface can exist before OpenWebUI.

Possible forms:

```text
static HTML cockpit
read-only docs
local markdown folder
NAS static web host
GitHub Pages
private LAN documentation page
```

Pantheon role:

```text
expose installation state and next checks
show what is not installed yet
avoid pretending runtime exists
```

Execution owner:

```text
static file host / human setup
```

### Layer 5 — Hermes installation candidate

Hermes can be installed only after the substrate exists.

Pantheon role:

```text
prepare Hermes install plan candidate
list dependencies
list ports
list volumes
list permissions
list secrets
list health checks
list allowed actions after installation
```

Execution owner:

```text
human operator
bootstrap installer
container substrate
vendor package manager
```

After Hermes is installed, it is still not automatically trusted.

```text
Hermes running != Hermes admitted for all tasks.
```

### Layer 6 — OpenWebUI / exposure surface candidate

OpenWebUI or another exposure surface can be installed after substrate exists.

Pantheon role:

```text
prepare exposure surface install plan candidate
state whether it is local-only, VPN-only or public read-only
state what buttons are display-only
state what requires approval
```

Execution owner:

```text
human operator
bootstrap installer
container substrate
```

### Layer 7 — Runtime modules and services

Only after the substrate and basic runtime exist should modules be installed:

```text
Ollama / local model runtime
PaddleOCR / extraction tools
vector database
memory runtime
GraphRAG tooling
LangGraph runtime
Langflow designer
connector gateway
observability
```

Pantheon role:

```text
prepare module installation candidates
preflight capability and scope
classify module status
record result candidates
show health checks
```

Execution owner:

```text
Hermes when authorized
human operator
external installer
```

### Layer 8 — Admission and task authorization

Installed modules still need governance status.

```text
installed != admitted
admitted != preflighted
preflighted != task-authorized
runtime success != lifecycle promotion
```

Pantheon role:

```text
admission checklist
capability passport review
Task Contract review
scope and approval ceiling
```

Execution owner:

```text
Pantheon governs status
human decides
Hermes executes authorized tasks only
```

## Dependency chain

Conservative order:

```text
human access
-> baseline checklist
-> machine/NAS capability classification
-> backup / snapshot decision
-> substrate candidate: native / container / VM
-> minimal static cockpit / docs
-> Hermes candidate installation
-> exposure surface candidate installation
-> module installation candidates
-> health checks
-> admission review
-> per-task authorization
```

## Bootstrap modes

### Mode A — Manual-first

Best when the machine is unknown or sensitive.

```text
Pantheon produces checklists and plans.
Human executes commands or vendor UI steps.
Pantheon records outcomes manually.
```

Pros:

```text
safe
transparent
no hidden automation
works before Hermes
```

Cons:

```text
slower
manual errors possible
```

### Mode B — Bootstrap script candidate

A minimal script may be generated as an artifact candidate.

This requires explicit approval before use.

Pantheon may prepare:

```text
script draft
expected changes
rollback notes
ports
volumes
permissions
hash/version pins when available
```

Pantheon must not execute the script itself.

### Mode C — Vendor package / app store

Some NAS platforms may provide package managers or app stores.

Pantheon may prepare:

```text
which package to install
why
what permissions it asks for
what service it creates
how to remove it
```

The vendor platform executes installation.

### Mode D — External admin workstation

A local workstation performs installation on the NAS or compute node.

Pantheon may prepare:

```text
SSH checklist
copy files checklist
container import checklist
health check checklist
```

The workstation or human operator executes.

## NAS-first recommendation

When starting from a NAS with nothing installed:

```text
1. classify NAS capability
2. decide whether NAS is storage, cockpit host, gateway, light runtime or compute node
3. prefer NAS as storage + static cockpit + secure redirection
4. delegate heavy compute to workstation / mini-PC / GPU server unless NAS capability is proven
5. install substrate only after backup and access are clear
6. install Hermes only after substrate exists
7. install modules only after Hermes or external installer can report results
```

## Redirection before runtime

A NAS may redirect before Hermes exists.

Allowed candidate pattern:

```text
NAS static page
-> shows install state
-> links to docs
-> links to private endpoints when they later exist
```

Later:

```text
NAS gateway / reverse proxy
-> private cockpit
-> Hermes dashboard
-> compute node service
```

The route must not expose runtime controls publicly.

## Health check ladder

Each layer needs a simple check.

```text
L0 human access        -> can log in, can restore, can decide
L1 bootstrap medium    -> guide or bundle reachable
L2 system capability   -> CPU/RAM/storage/network known
L3 substrate           -> container/VM/native service available
L4 static surface      -> page reachable
L5 Hermes              -> service running, version visible, logs available
L6 exposure surface    -> reachable, auth/scope known
L7 modules             -> installed, version visible, health check passes
L8 governance          -> admitted / blocked / task-authorized status visible
```

## Cockpit representation

The installation cockpit should show:

```text
layer
required dependencies
current state
blocking checks
available installer path
human decision required
risk
rollback path
next action
```

Example states:

```text
absent
unknown
detected
planned
ready_for_manual_install
ready_for_handoff
installing_external
installed_unverified
healthy
blocked
rolled_back
retired
```

## Governance boundary

Pantheon may facilitate installation by producing:

```text
installation plan candidate
preflight checklist
rollback checklist
expected state
health check checklist
handoff candidate
status view
risk summary
```

Pantheon must not become:

```text
installer
package manager
Docker orchestrator
Portainer replacement
Hermes bootstrapper with hidden authority
scheduler
queue
runtime
approval engine
memory engine
gateway
```

## Doctrine summary

```text
Before Hermes exists, Pantheon cannot ask Hermes to install Hermes.
Bootstrap must be human-readable and runtime-independent.
The first installer is human, vendor tooling or a separately approved bootstrap artifact.
Hermes executes only after it exists and is authorized.
Pantheon prepares, classifies, checks and records status.
The human decides each escalation.
```
