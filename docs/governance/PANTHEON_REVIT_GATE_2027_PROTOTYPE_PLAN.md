# Pantheon Revit Gate — Revit 2027 Prototype Plan

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

Repository state: documented non-implemented.

This document is a planning note for a future local Revit 2027 add-in. It does not implement a plugin, Revit add-in, MCP server, local API, relay, schema, test, Docker file or operations change.

## 0. External version signal

The prototype target is **Revit 2027**.

Autodesk Revit 2027 Help exposes the 2027 product documentation, including Revit Developer's Guide and Revit API Reference Guides. Revit 2027 also lists **Revit Public MCP Server (Tech Preview)** and **Migrating Revit to .NET 10** among the 2027 changes. The plan therefore treats:

```text
Revit version: 2027
Add-in runtime target: .NET 10
MCP posture: relevant external signal, not first internal dependency
```

This is an adapter/runtime fact. It does not change Pantheon kernel doctrine.

## 1. Purpose

The purpose of the first prototype is not to build a broad AI modeler. It is to prove the first local loop:

```text
see -> understand -> show -> propose -> act lightly -> log
```

The prototype should demonstrate that Hermes can receive a structured Revit context, reason about the selected architectural scope, and ask the Revit add-in to perform a light, local, traceable action.

## 2. Product boundary

The prototype is **architecture only**.

In scope:

```text
project information
active view
selection
visible elements
walls / rooms / doors / windows context
view image capture
visual context pack
text note creation
detail line creation
sandbox / review view creation
action report
local logs
```

Out of scope:

```text
MEP
HVAC
structure
cloud automation as dependency
central/workshared automation
model deletion
save / sync
arbitrary generated code execution
families
wall profile editing
curtain-wall generation
model geometry write beyond light review artifacts
```

## 3. Revit 2027 technical assumptions

Because Revit 2027 uses .NET 10 for add-ins, the prototype should assume:

```text
C# add-in targeting Revit 2027
.NET 10 runtime
no cross-version promise for Revit 2024 / 2025 / 2026 in the first prototype
Revit API calls executed only inside Revit context
ExternalEvent or equivalent Revit-safe execution path for UI-triggered actions
named transactions for any write_light action
```

The first prototype should not attempt multi-version compatibility. Backporting can be treated as a later adapter decision.

## 4. Architecture target

```text
Revit 2027 Add-in
  -> local panel / command surface
  -> context capture service
  -> local action service
  -> local log service
  -> optional local API relay
  -> Hermes skill / caller outside Revit
```

The plugin executes locally. Pantheon remains documentation/governance and does not execute Revit actions.

## 5. MCP position

Revit 2027 exposing a public MCP server as Tech Preview is important, but it should not invert the architecture.

Prototype sequence:

```text
1. build local Revit add-in primitives
2. expose a minimal local API / relay for Hermes
3. keep capability ids aligned with the registry
4. evaluate MCP wrapping only after the local primitives work
```

Reason:

```text
MCP is transport / adapter.
It is not the authority layer.
It does not replace local Revit transaction discipline.
It does not decide approval, proof, scope or professional status.
```

## 6. First prototype functions

The first implementation slice should be smaller than the full V0 registry.

```text
revit.ping
revit.get_project_info
revit.get_active_view
revit.list_selection
revit.get_element_details
revit.visible_elements_context
revit.capture_active_view
revit.visual_context_pack
revit.create_sandbox_view
revit.create_text_note
revit.create_detail_line
revit.action_report_generate
revit.action_log_read
```

A second slice may add:

```text
revit.read_parameters
revit.read_rooms
revit.read_walls_doors_windows
revit.find_nearest_element
revit.find_parallel_elements
revit.propose_modeling_method
revit.record_modeling_method_choice
```

## 7. First proof scenario

```text
1. Open a local Revit 2027 test RVT.
2. Select one wall or one façade zone.
3. Click “Send context to Hermes”.
4. Revit add-in creates a visual context pack:
   - active view image
   - view id / name / type / scale
   - selected ElementIds
   - visible architecture elements
   - core parameters
5. Hermes explains what it sees and proposes a review note.
6. The add-in creates a sandbox / review view if needed.
7. The add-in creates one TextNote or DetailLine.
8. The add-in writes a local action report.
```

Success means the loop is proven. It does not mean model-modifying capabilities are implemented.

## 8. Minimal local log

Each action report should include at least:

```text
action_id
session_id
timestamp
revit_version
document_title
document_path_hash_or_redacted_path
active_view_id
selected_element_ids
tool_id
effect
transaction_name if any
created_element_ids
modified_element_ids
warnings
status
```

The log is a trace candidate, not an Evidence Pack by itself.

## 9. First C# structure — descriptive only

This repository should not receive code in this planning step. The external plugin repository or local prototype may later use a structure similar to:

```text
PantheonRevitGate2027/
  Addin/
    App.cs
    Commands/
    Panels/
  Core/
    ContextPack/
    Actions/
    Logging/
    Serialization/
  Revit/
    RevitContextReader.cs
    RevitViewCapture.cs
    RevitLightWriter.cs
    RevitTransactionRunner.cs
  Relay/
    LocalApiServer.cs
    HermesRequestHandler.cs
```

This is not a repository instruction. It is a candidate implementation shape for the external runtime.

## 10. First non-negotiable safeguards

Even in free exploration mode, the first writable prototype should enforce:

```text
active document name visible before action
named Revit transaction for write_light actions
local action log
affected ElementIds where available
stop / disable Hermes control
no delete
no save
no sync
no arbitrary code execution
```

## 11. Open decisions

```text
1. Where will the actual plugin code live?
   - separate repository
   - local prototype only
   - later protected path in this repo after confirmation

2. Which local relay is preferred first?
   - localhost HTTP
   - WebSocket
   - named pipe
   - stdio bridge

3. Which UI surface is first?
   - ribbon button only
   - dockable panel
   - modeless WPF panel

4. Which first write_light action is best?
   - TextNote
   - DetailLine
   - sandbox view
   - review parameter

5. How strict should free exploration be on test RVTs?
   - log-only
   - light confirmation
   - always preview
```

## 12. Relationship to existing Revit Gate docs

This plan narrows the existing Revit Gate developer dossier to a Revit 2027 first prototype target. It does not replace:

```text
docs/governance/PANTHEON_REVIT_GATE.md
docs/governance/PANTHEON_REVIT_GATE_DEVELOPER_DOSSIER.md
```

The existing developer dossier remains the broader candidate reference. This file is the 2027 implementation planning slice.

## 13. Boundary

```text
Implemented: no.
Documented non-implemented: yes.
Partial: no runtime.
To verify: Revit 2027 API details, .NET 10 add-in scaffold, local relay choice.
Obsolete: no.
```

The human decides when to move from documented plan to external prototype work.
