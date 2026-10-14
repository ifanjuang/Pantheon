# NAS Installation Profiles

Status: candidate orientation — NAS installation profiles, acceleration classes and redirection patterns.
Boundary profile: candidate_support_note.

This document is a candidate orientation, not an implementation.

It does not create Docker configuration, compose files, scripts, packages, firewall rules, reverse proxy rules, VPN setup, DNS records, GPU drivers, runtime services, queue, scheduler, memory engine, vector database, GraphRAG runtime, LangGraph runtime, Langflow runtime, Hermes command surface or external connector.

## Purpose

Define a simple installation-thinking model for a NAS with little or no pre-installed AI stack.

The goal is to avoid assuming that every NAS can run the same workload.

A NAS may be:

```text
storage only
CPU-capable
media-accelerated
NPU / AI-light capable
GPU-capable
NAS-adjacent only, with compute delegated to another machine
secure access gateway / redirection point
```

Pantheon must classify the machine capability before suggesting where cockpit, Hermes, vector search, memory, GraphRAG or local models should live.

## Core rule

```text
Storage availability is not compute capability.
GPU presence is not LLM readiness.
Runtime installability is not governance approval.
Network exposure is not functional authorization.
```

## NAS capability classes

### NAS-0 — Storage only

Capabilities:

```text
file storage
backup
read-only document hosting
static cockpit files
```

Avoid:

```text
local LLM inference
GraphRAG indexing
heavy OCR
vector indexing at scale
multi-user workflow execution
```

Best role:

```text
source store
backup store
static documentation host
project file mount
```

### NAS-1 — CPU service host

Capabilities:

```text
light containers
small web cockpit
small database
light document inventory
small vector index
low-throughput jobs
```

Risk:

```text
slow inference
thermal throttling
memory pressure
I/O contention with file services
```

Best role:

```text
cockpit host
small read-only API
metadata index
low-frequency jobs
```

### NAS-2 — Integrated media acceleration

Some NAS devices include an integrated graphics/media block, often through the CPU.

This may help:

```text
video transcoding
image/media pipelines
some vision preprocessing
limited acceleration if drivers expose it
```

This does not automatically mean:

```text
large LLM inference is practical
CUDA is available
TensorRT is available
Ollama can use acceleration
GraphRAG indexing is accelerated
```

Best role:

```text
media acceleration
light vision preprocessing
still mostly CPU-bound for LLM/RAG unless proven otherwise
```

### NAS-3 — NPU / AI-light appliance

Some NAS or NAS-like appliances include an NPU or AI accelerator.

Potential uses:

```text
photo classification
OCR acceleration
face/object detection
small local AI features
```

Caution:

```text
vendor SDK dependency
model compatibility limits
unclear LLM support
limited memory
hard-to-observe utilization
```

Best role:

```text
vendor-supported AI-light tasks
candidate preprocessing node
not primary reasoning runtime unless tested
```

### NAS-4 — GPU-capable NAS

Some NAS platforms may support PCIe GPU expansion, GPU passthrough or GPU-accelerated containers.

Potential uses:

```text
local inference
vision models
embeddings
OCR
transcoding
GPU-backed containers or VMs
```

Required checks:

```text
GPU compatibility list
available PCIe slot
power and cooling
driver availability
container / VM passthrough support
VRAM
RAM
storage throughput
thermal envelope
vendor support
```

Best role:

```text
local AI runtime only after compatibility proof
Hermes-adjacent execution node
not assumed by default
```

### NAS-5 — NAS as storage, external compute elsewhere

Often the cleanest setup.

NAS provides:

```text
files
snapshots
backups
project store
static cockpit host
secure access entry point when appropriate
```

A separate workstation / mini-PC / GPU server provides:

```text
Hermes runtime
Ollama or local models
GraphRAG indexing
OCR
LangGraph durable execution
vector database
memory runtime
```

Best role:

```text
safe default for agency deployment
separates storage durability from compute volatility
```

### NAS-6 — NAS as secure redirection point

The NAS may expose a controlled entry point and redirect requests to another internal service.

This can be useful when the NAS already provides:

```text
stable LAN presence
TLS / certificate management
reverse proxy features
VPN or private access features
DDNS or domain integration
local identity / account control
```

Possible redirection targets:

```text
cockpit static page
Hermes dashboard
OpenWebUI surface
Langfuse / observability view
read-only documentation
GPU workstation service
mini-PC runtime node
```

This role is network routing, not governance approval.

Best role:

```text
secure gateway / reverse proxy / access concentrator
```

Avoid by default:

```text
open public ports without authentication
exposing Hermes runtime directly
exposing admin panels directly
exposing vector DB / memory DB directly
mixing public cockpit and internal runtime endpoints
```

## Redirection patterns

### Private-only redirection

```text
user
-> VPN / private network
-> NAS gateway
-> internal service
```

Best for:

```text
admin cockpit
Hermes state
internal workflows
non-public project data
```

### Public read-only redirection

```text
user
-> HTTPS subdomain
-> NAS reverse proxy
-> static read-only cockpit / docs
```

Best for:

```text
published documentation
read-only demo
client-safe status page
```

Requires:

```text
no secret data
no write actions
no runtime controls
clear public/private split
```

### Split subdomain pattern

```text
public.example.com     -> static public content
private.example.com    -> authenticated cockpit
runtime.example.local  -> LAN/VPN only runtime endpoint
```

Principle:

```text
public route exposes information only.
private route exposes decision surfaces.
runtime route remains internal.
```

### NAS-to-compute delegation

```text
NAS stores files and routes requests.
Compute node runs Hermes / AI workloads.
Pantheon cockpit displays state and boundaries.
```

This is the preferred pattern when the NAS has weak CPU, weak GPU, uncertain drivers or important storage duties.

## Installation decision matrix

Before installation, classify:

```yaml
nas_profile:
  vendor:
  model:
  cpu:
  ram:
  storage:
  docker_or_container_support:
  vm_support:
  integrated_gpu:
  npu_or_ai_accelerator:
  pcie_slots:
  gpu_passthrough:
  container_gpu_access:
  driver_support:
  thermal_budget:
  network:
  exposed_services:
  reverse_proxy_support:
  vpn_or_private_access:
  domain_or_subdomain_support:
  backup_strategy:
  security_boundary:
  recommended_role: storage_only | cockpit_host | light_runtime | gpu_runtime | gateway_redirect | external_compute_storage
```

## Recommended deployment split

Default conservative split:

```text
NAS
-> files, backups, static cockpit, project store, secure redirection when appropriate

External compute node
-> Hermes, OCR, local models, GraphRAG, vector DB, workflow execution

Pantheon
-> governance docs, cockpit surfaces, status and boundary rules
```

Only promote the NAS into compute role after capability proof.

## Capability proof checklist

A NAS can be considered for local runtime only if the following are verified:

```text
containers or VMs are supported
resource limits are known
GPU/NPU driver support is confirmed when relevant
hardware acceleration is visible to the container or VM
persistent volumes are controlled
network exposure is bounded
backup and restore path exists
logs are accessible
shutdown / restart behavior is understood
security updates are manageable
```

For GPU/NPU acceleration:

```text
device visible to runtime
compatible inference stack exists
small model benchmark passes
thermal behavior acceptable
VRAM / memory adequate
fallback to CPU or external compute defined
```

For redirection:

```text
TLS available
authentication available
public/private split documented
runtime endpoints kept internal
logs available
rate limiting or access control considered
rollback path known
```

## Governance boundary

Installation capability does not change Pantheon authority.

```text
Container running != capability approved.
GPU visible != task authorized.
Subdomain reachable != action approved.
Reverse proxy route != scope approval.
Workflow completed != evidence validated.
Memory recalled != truth.
Retrieval succeeded != proof.
```

Pantheon may display machine capabilities in the cockpit.

Pantheon must not become the installer, runtime, scheduler, queue, provider router, memory engine, gateway or approval engine.

## Cockpit representation

Machines & instances should distinguish:

```text
storage role
cockpit host
runtime host
vector store host
memory host
GPU/NPU capable
gateway / redirection point
external compute delegated
```

Service cards should show:

```text
capability class
runtime status
acceleration status
redirection status
proof status
risk
recommended role
next check
```

## Practical recommendation

Start with:

```text
NAS as storage + static cockpit + optional secure redirection
external compute for Hermes and AI workloads
```

Then upgrade only if measured capability supports it:

```text
NAS-0 / NAS-1 -> storage/cockpit
NAS-2 / NAS-3 -> light preprocessing if supported
NAS-4 -> runtime candidate after proof
NAS-5 -> preferred robust split for serious workloads
NAS-6 -> gateway/redirection candidate if security is controlled
```

## Doctrine summary

```text
The NAS stores by default.
The NAS may redirect when security is controlled.
Compute is earned by proof.
Acceleration is classified, not assumed.
Hermes executes outside Pantheon.
Pantheon governs status, proof, scope and approval.
The human decides deployment posture.
```
