# Revit 2027 implementation foundation

Status: documented implementation decision — non-implemented.

This note specializes the future production repository structure for the Pantheon Revit local adapter. It does not turn `Pantheon-Next` into the implementation repository and does not create runtime authority here.

Canonical owners remain:

- `docs/governance/REVIT_LOCAL_ADAPTER.md` for the execution boundary;
- `docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md` for Project Anatomy V0.2;
- `revit-plugin/docs/PROJECT_ANATOMY_OBSERVATION_CONTRACT.md` for the Revit observation seam.

## 1. Decision summary

The first implementation should use:

```text
Revit 2027
.NET 10 / Windows
Nice3point.Revit.Sdk for Revit project/build mechanics
Nice3point Revit API packages as build-time references, subject to legal/offline packaging review
C#/.NET for all in-process Revit logic
Named Pipes for same-machine Host Agent ↔ add-in IPC
one closed Pantheon Revit Operation Registry
one deterministic operation layer shared by local UI and Hermes
live Revit conformance tests
```

The first implementation should **not** depend directly on RevitMCPSDK as its execution kernel.

RevitMCPSDK remains a useful MIT-licensed reference for:

```text
command abstraction
JSON-RPC-style request identity
ExternalEvent marshalling
normalized technical errors
multi-version Revit compilation examples
```

Pantheon requires a stricter request lifecycle and richer operation metadata than that SDK currently exposes.

## 2. Why Nice3point is the preferred scaffold

The reviewed Nice3point Revit SDK already provides the non-differentiating Revit project mechanics we need:

```text
Revit-version-aware target frameworks
Revit 2027 -> .NET 10 mapping
conditional Revit symbols
addin manifest patching
local deployment
publishing
launch/debug integration
multi-version support if later required
dependency-isolation/repacking support
NuGet-based Revit API references for CI
```

For V0, Pantheon should still target **R27 only** unless a real product need requires an older release. Supporting one Revit version first reduces:

- compatibility branches;
- test matrix size;
- packaging complexity;
- unit/API compatibility ambiguity;
- operational support surface.

The use of a multi-version-capable SDK does not imply a multi-version product commitment.

## 3. Why RevitMCPSDK is not the Operation Registry

The reviewed SDK registry interface is essentially:

```text
RegisterCommand(command)
TryGetCommand(commandName)
```

Its command interface exposes:

```text
CommandName
Execute(JObject parameters, requestId)
```

This is useful dispatch infrastructure, but it does not encode the Pantheon contract dimensions required for an operation:

```text
capability_id
effect_class
warning_level
supported Revit versions
required live context
freshness policy
scope constraints
preflight policy
authorization policy
transaction policy
rollback policy
result contract
coverage semantics
allowed source observations
conformance requirements
local exposure policy
```

Therefore:

```text
RevitMCPSDK command registry != Pantheon Revit Operation Registry
```

The current `ExternalEventCommandBase` also raises an event and then waits synchronously for handler completion with a timeout. Its public waitable-handler interface does not itself specify:

```text
request-bound reset semantics
cancellation
stale-result protection
multi-request correlation
busy/concurrency policy
lifecycle/disposal guarantees
```

Pantheon must make those guarantees explicit rather than assume an implementation supplies them.

## 4. Dependency posture

### Adopt / use directly as build infrastructure

Candidate:

```text
Nice3point.Revit.Sdk
```

Reason:

- removes Revit project boilerplate;
- handles Revit 2027/.NET target mapping;
- supports packaging/debugging;
- does not impose an agent/runtime architecture.

### Use as build-time API reference candidate

```text
Nice3point.Revit.Api.RevitAPI
Nice3point.Revit.Api.RevitAPIUI
```

Conditions before production adoption:

- pin an exact package version;
- archive the required packages for offline builds;
- generate SBOM/license inventory;
- verify Autodesk redistribution/licensing implications separately from the MIT license of the wrapper repository;
- do not download packages at runtime.

### Distill, do not depend initially

```text
DTDucas/RevitMCPSDK
```

Reason:

- useful low-level patterns;
- insufficient governance metadata;
- request/event lifecycle needs stricter Pantheon semantics;
- avoiding it initially keeps the in-process dependency surface smaller.

A direct dependency may be reconsidered only if a later code-level benchmark proves it removes meaningful complexity without weakening request lifecycle guarantees.

## 5. Proposed production repository shape

The production implementation should live in a dedicated repository. Suggested responsibility-based layout:

```text
Pantheon.Revit/
├── README.md
├── Pantheon.Revit.sln
├── Directory.Build.props
├── Directory.Packages.props
├── global.json
│
├── src/
│   ├── Pantheon.Revit.Addin/
│   │   ├── Application/
│   │   ├── Ribbon/
│   │   ├── LocalExposure/
│   │   ├── Ipc/
│   │   └── Pantheon.Revit.Addin.addin
│   │
│   ├── Pantheon.Revit.Operations/
│   │   ├── Registry/
│   │   ├── Context/
│   │   ├── Observation/
│   │   ├── Architecture/
│   │   ├── Documentation/
│   │   ├── Quantities/
│   │   ├── Navigation/
│   │   └── Execution/
│   │
│   ├── Pantheon.Revit.Contracts/
│   │   ├── Capability/
│   │   ├── Requests/
│   │   ├── Results/
│   │   ├── Context/
│   │   └── Observations/
│   │
│   └── Pantheon.Revit.HostProtocol/
│       ├── Messages/
│       ├── Serialization/
│       └── Versioning/
│
├── host/
│   └── Pantheon.Revit.Host/
│       ├── Ipc/
│       ├── Binding/
│       ├── Session/
│       └── Transport/
│
├── tests/
│   ├── Pantheon.Revit.Contracts.Tests/
│   ├── Pantheon.Revit.Operations.Tests/
│   └── Pantheon.Revit.Live.Tests/
│
├── fixtures/
│   ├── models/
│   ├── families/
│   └── expected/
│
├── build/
└── packaging/
```

The exact repository name remains a user/project decision. This document does not create it.

## 6. Assembly boundaries

### `Pantheon.Revit.Contracts`

Pure DTOs and enums shared by add-in tests and Host Protocol mapping.

Must not reference:

```text
Autodesk.Revit.*
MCP SDKs
LLM SDKs
Pantheon database code
Hermes runtime code
```

Contains only technical contracts such as:

```text
OperationRequest
OperationResult
OperationStatus
CapabilityManifest
RevitContextSnapshot
ObservationBundle DTO
CoverageReport
WithheldItem
WarningRecord
ActionReport DTO
```

### `Pantheon.Revit.Operations`

Owns deterministic Revit-domain operations and the closed registry.

References Revit API.

Must not own:

```text
network listener
MCP server
provider client
workflow orchestration
persistent task queue
project memory
human approval state
```

### `Pantheon.Revit.Addin`

Owns Revit application integration:

```text
IExternalApplication
ribbon / local settings UI
local exposure profile
Named Pipe client connection
ExternalEvent dispatcher
Revit application/document lifecycle observation
```

It wires operations; it should not contain most operation business logic.

### `Pantheon.Revit.HostProtocol`

Pure versioned IPC contract between Host Agent and add-in.

It should remain independent of MCP so that MCP is replaceable.

### `Pantheon.Revit.Host`

Out-of-process local adapter host.

Owns:

```text
Named Pipe server endpoint
connection/reconnection
binding session
request correlation across transport
translation to Hermes-facing tool protocol
technical authentication/session checks
```

Does not own:

```text
Pantheon governance
professional decision
project truth
workflow planning
Revit transactions
```

## 7. Named Pipe direction

Recommended same-machine direction:

```text
Pantheon.Revit.Host
= Named Pipe server

Pantheon.Revit.Addin
= Named Pipe client
```

Reasons:

- no TCP/HTTP listener inside Revit;
- Host Agent owns transport lifecycle;
- add-in initiates only a local outbound IPC connection;
- Host Agent restart does not require exposing a network port;
- local Windows access controls can constrain the endpoint.

The add-in may reconnect when the Host Agent is absent/restarted, but Revit operation execution remains disabled while no admitted host session exists.

## 8. No durable queue in the add-in

The add-in needs a minimal technical handoff from an IPC/background thread to Revit's UI/API context, but it must not become a job system.

V0 policy:

```text
maximum Revit API operation in flight: 1
persistent queue: none
scheduler: none
automatic retry: none
```

When another Revit operation is already in flight, the binding should return a typed state such as:

```text
refused_busy
```

Hermes may decide later whether the task should retry, wait, continue independent actions or ask the user.

This keeps task orchestration outside Revit.

## 9. ExternalEvent dispatcher

The dispatcher should be implemented as a small Pantheon-owned component rather than inheriting the SDK wait pattern directly.

Conceptual state:

```text
Idle
→ RequestBound
→ Raised
→ ExecutingOnRevitThread
→ Completed | Refused | Failed
→ Cleared
→ Idle
```

Each request must carry:

```text
request_id
operation_id
binding_id
expected document identity
expected freshness tokens for the operation-declared scopes
scope digest
arguments digest
received_at
```

The dispatcher must guarantee:

- a result can only complete the request that created it;
- previous completion state is cleared before a new request is accepted;
- stale result reuse is impossible by construction;
- timeout does not silently permit a later result to be attached to another request;
- wrong-document and stale-context checks occur again on the Revit thread immediately before execution when required;
- exception paths always clear the in-flight slot;
- disposal/shutdown refuses new operations cleanly.

Implementation can use `TaskCompletionSource<OperationResult>` or an equivalent request-bound completion primitive outside the Revit UI thread.

The Revit UI thread itself must never block waiting for the Host Agent.

## 10. Operation Registry

The registry is a Pantheon-owned typed catalogue, not a string dictionary.

Conceptual descriptor:

```csharp
public sealed record RevitOperationDescriptor(
    string OperationId,
    string CapabilityId,
    RevitEffectClass EffectClass,
    WarningLevel WarningLevel,
    ImmutableArray<int> RevitVersions,
    ContextRequirements Requires,
    LocalExposurePolicy LocalExposure,
    PreflightPolicy Preflight,
    AuthorizationPolicy Authorization,
    TransactionPolicy Transaction,
    ResultPolicy Results,
    ConformancePolicy Tests);
```

An implementation is registered with its descriptor:

```text
OperationDescriptor
+ IRevitOperation<TRequest,TResult>
```

No runtime reflection over the Revit API is allowed to create operations.

The same registry should generate/check:

```text
Capability Manifest
advanced local settings UI
Host Agent tool descriptors
Hermes binding schemas
documentation inventory
contract-test inventory
live-test inventory
```

## 11. Operation interface

The agent-facing payload should not be `JObject` inside the Revit domain layer.

Prefer strongly typed requests:

```csharp
public interface IRevitOperation<TRequest, TResult>
{
    RevitOperationDescriptor Descriptor { get; }
    TResult Execute(RevitOperationContext context, TRequest request);
}
```

Serialization occurs at the Host Protocol boundary.

This provides:

- compile-time input contracts;
- deterministic validation;
- smaller test surface;
- easier schema generation;
- no arbitrary dynamic dispatch.

## 12. Read operation transaction posture

Pure observation operations do not open Revit transactions.

They may use temporary/non-persistent UI state only when the operation contract explicitly declares it and can restore it.

For V0, the first proof operation should avoid even temporary view mutation.

## 13. Write operation posture

Writes remain absent from the first executable proof.

Later, every write descriptor must declare:

```text
preflight required
human/Pantheon authorization required
named transaction required
exact target set required
before/after effect report required
failure handling policy
rollback/manual-reversal posture
```

A generic `Execute(Action<UIApplication>)` or generated-code operation is forbidden.

## 14. Serialization choice

The in-process domain layer should prefer .NET typed DTOs.

For Host Protocol, prefer a small explicit serializer surface (for example `System.Text.Json` on .NET 10) unless a concrete interoperability requirement justifies another serializer.

The add-in does not need to inherit Newtonsoft/JObject solely because an external SDK does.

MCP-specific JSON schema translation belongs in the Host Agent, not in Revit Operations.

## 15. Versioning

Version separately:

```text
addin build version
Host Protocol version
Operation version (`revit....v1`)
Capability identity
Observation Bundle contract revision from
`schemas/architecture-project-understanding/observation_bundle.schema.yaml`
```

Do not tie a capability's semantic identity to:

```text
MCP version
transport implementation
assembly version
Revit ElementId
```

## 16. Offline build and runtime

A production release must be reproducible with Internet unavailable once approved dependencies are mirrored locally.

Required posture:

```text
exact package versions
locked dependency graph
local NuGet package cache/mirror
SBOM
licenses/NOTICE inventory
no runtime package download
no npx -y
no cloud provider bootstrap
no Autodesk hosted runtime requirement
```

Development CI may use remote package feeds, but an approved release bundle must have an offline restore/build path or a documented local mirror process.

## 17. Revit API reference licensing checkpoint

`Nice3point/RevitApi` packages original Autodesk Revit installation libraries for build convenience.

Therefore:

```text
wrapper repository license
!= automatic redistribution permission for Autodesk binaries
```

Before packaging any Autodesk binary into a Pantheon distribution:

- verify Autodesk licensing/EULA;
- prefer reference-only build usage when possible;
- avoid bundling Revit-owned binaries with the add-in unless clearly permitted.

This is a release/legal gate, not a runtime authorization gate.

## 18. Dependency isolation

For Revit 2027, prefer modern dependency isolation supported by current Revit/.NET rather than assembly repacking unless a proven compatibility problem requires repacking.

Keep the add-in dependency set intentionally small.

The Host Agent can carry heavier transport/protocol dependencies because it runs outside Revit.

## 19. Tests

Three layers are required.

### Contract tests

No Revit process required:

```text
registry uniqueness
operation schema generation
request validation
status/refusal mapping
Host Protocol round-trip
manifest derivation
unit conversion helpers with known constants
```

### Operation/domain tests

Pure calculations and mapping logic extracted from Revit calls where possible.

### Live Revit 2027 tests

Execute against actual Revit 2027 fixtures.

At minimum:

```text
load add-in
active document observation
active view observation
selection observation
rooms/doors bounded read
units mm/m²/m³
phases
linked-model identity where applicable
repeat call without stale result
wrong-document refusal
stale-context refusal
zero mutation for read operations
UI/Host parity
Internet disconnected
```

The live suite should eventually use a dedicated Revit test runner such as the Nice3point/TUnit pattern or an equivalent controlled harness.

## 20. Fixture corpus

Start with very small deterministic fixtures rather than real agency projects.

Recommended initial models:

```text
empty_project.rvt
one_room_one_door.rvt
two_rooms_shared_door.rvt
phases_simple.rvt
design_option_simple.rvt
linked_model_host.rvt
workshared_small.rvt (when the harness can support it safely)
```

Expected outputs are committed separately from runtime results.

Later anonymized real-project regression fixtures may be added under explicit data-governance rules.

## 21. Initial Operation Registry slice

The first executable registry should be intentionally small:

```text
revit.system.observe_runtime.v1
revit.document.observe_context.v1
revit.view.observe_active.v1
revit.selection.observe.v1
revit.architecture.observe_rooms.v1
revit.architecture.observe_doors.v1
```

Only after these are live-tested should the registry expand to walls, floors, roofs, windows, materials, schedules, quantities and QA.

No write operation is required in the first registry slice.

## 22. First implementation proof

A production repository can claim the first proof only when all are true:

```text
Revit 2027 loads the add-in
Host Agent and add-in establish local Named Pipe session
capability manifest is generated from the Operation Registry
active document/view/selection observations succeed
one bounded architecture observation emits a V0.2-compatible Observation Bundle
request/result correlation is proven across repeated calls
stale context is refused
wrong document is refused
same operation called by UI and Host gives equivalent domain result
no model mutation occurs
tests run with Internet unavailable
```

## 23. Status classification

### Implemented externally / verified as reference

```text
Nice3point Revit SDK supports a Revit 2027/.NET 10 target mapping
Nice3point templates provide Revit 2027 solution/build patterns
RevitMCPSDK exposes basic command and ExternalEvent abstractions
```

These statements describe external repositories, not Pantheon implementation.

### Documented non-implemented in Pantheon

```text
production repository layout
Pantheon Operation Registry
request-bound ExternalEvent dispatcher
Named Pipe Host Agent/add-in link
Revit 2027 live test corpus
first observation operations
```

Pantheon Next now implements the Observation Bundle validation schema. This
does not make the external Revit add-in, Host, operations or live Revit proof
implemented in Pantheon.

### To verify before implementation freeze

```text
exact Nice3point package versions
Autodesk API package redistribution posture
selected live Revit test harness
Windows Named Pipe ACL/auth details
Revit 2027 API edge cases discovered during first live fixtures
```

## 24. Architectural decision

Current recommendation:

```text
Nice3point.Revit.Sdk
= adopt as scaffold/build mechanism

Nice3point.Revit.Api
= candidate build reference, pin + legal/offline review

RevitMCPSDK
= distill patterns, no direct V0 dependency

Pantheon execution lifecycle
= implement as small owned layer
```

This is intentionally simpler than adopting a third-party MCP runtime inside Revit and preserves the doctrine:

```text
Pantheon governs.
Hermes acts.
Revit executes locally.
The human decides consequential effects.
```
