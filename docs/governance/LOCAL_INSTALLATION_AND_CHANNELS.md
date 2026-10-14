# Local Installation and Governed Channels

Status: product direction — governance framing — implementation to verify capability by capability.
Boundary profile: candidate_support_note.

This document explains how Pantheon Next should describe local installation, model choice and everyday work channels.

It is not an installation guide.

It is not a Docker guide.

It is not a provider configuration document.

It is not a connector specification.

It is not a runtime implementation plan.

## Purpose

Pantheon Next should be understandable as a controlled professional workspace.

It may be deployed around a cockpit and an external execution runtime, while keeping governance, evidence, memory and approvals explicit.

The reader-facing message is simple:

```text
Installed around your dossiers.
Connected to your tools.
Governed by your rules.
```

French:

```text
Installé autour de vos dossiers.
Connecté à vos outils.
Gouverné par vos règles.
```

## Core posture

Pantheon Next is installed around professional dossiers, not above them.

It may be deployed on:

- a NAS;
- a local server;
- a dedicated workstation;
- another controlled infrastructure chosen by the professional or organization.

This describes target architecture posture, not an implemented installer.

Pantheon Next does not become the runtime that installs, schedules, executes or self-manages external tools.

## Hardware posture

A local or shared deployment may require different resources depending on model and workload.

Relevant variables include:

- CPU;
- RAM;
- GPU;
- VRAM;
- storage;
- network access;
- number of users;
- type of local model;
- document volume;
- OCR, transcription and search workload.

Pantheon Next does not define these requirements as implemented deployment specifications in this repository.

Hardware sizing must be verified during implementation or deployment planning.

## Model posture

A governed deployment may use:

- local LLMs;
- cloud model providers;
- mixed local/cloud strategies;
- local models for sensitive tasks;
- cloud models for less sensitive or high-capability tasks.

Model selection must remain governed by dossier sensitivity, external tools policy, evidence requirements and approval levels.

Do not describe ChatGPT or Claude as direct app integrations unless implemented and documented.

Prefer:

```text
model providers
external LLM providers
local models
cloud models
mixed model strategy
```

Avoid:

```text
Pantheon connects directly to ChatGPT and Claude
Pantheon routes every provider internally
Pantheon includes a provider router
```

## Cockpit posture

OpenWebUI is the target cockpit surface.

It may expose:

- chat;
- source upload or reference;
- Knowledge Base consultation;
- Task Contract display;
- Evidence Pack display;
- approval prompts;
- Register Candidate review;
- candidate output display.

OpenWebUI does not govern, execute, canonize memory or become source of truth.

OpenWebUI exposes the governed interaction.

## Runtime posture

Hermes Agent remains the target external execution runtime.

It may execute work under Task Contract, such as:

- OCR;
- transcription;
- extraction;
- comparison;
- search;
- formatting;
- controlled tool use;
- Evidence Pack production;
- candidate output preparation.

Hermes does not canonize memory.

Hermes does not approve outputs.

Hermes does not bypass approval levels.

Pantheon Next governs the rules and artifacts around execution.

## Channel posture

Everyday tools should be described as governed entry points, not automatic truth sources.

Examples:

- email;
- Gmail;
- Outlook;
- Google Drive;
- Google Docs;
- Google Sheets;
- Office documents;
- Notion;
- Trello;
- Slack;
- WhatsApp;
- Telegram;
- calendars;
- notes;
- local files;
- PDFs;
- web search.

These channels may supply sources, messages, files, reminders or work material.

They do not become a Registre Probatoire entry.

They do not approve evidence.

They do not validate outputs.

They do not decide.

They remain channels.

## Local data posture

In a local configuration, the deployment should be able to keep controlled material on chosen infrastructure, such as:

- working dossiers;
- source files;
- exports;
- local databases;
- traces;
- Task Contracts;
- Evidence Packs;
- Register Candidates;
- a Registre Probatoire entry;
- AI Logs;
- Context Packs.

When a cloud model or external tool is used, the boundary must be explicit:

- what data leaves;
- why it leaves;
- for which task;
- with which approval level;
- with what evidence trace;
- whether memory promotion is excluded.

Local-first is a preference where possible, not a universal guarantee.

## Security posture

External providers, cloud APIs, messengers and collaboration tools introduce external effects.

External capabilities must follow `EXTERNAL_TOOLS_POLICY.md`.

Memory promotion must follow `MEMORY.md`.

Approvals must follow `APPROVALS.md`.

Knowledge, context, evidence and memory must remain separate according to `KNOWLEDGE_TAXONOMY.md`.

## Reader-facing wording

Preferred public wording:

```text
Pantheon Next is installed around professional dossiers.

On a NAS, local server or dedicated workstation, it organizes sources, evidence, assumptions, validations and memory.

It can be used from a dedicated chat cockpit, then progressively through everyday channels such as email, shared documents, messengers, project boards and local files.

AI accelerates selected tasks.

Pantheon keeps the frame.

The human validates.

The validated remains.
```

French version:

```text
Pantheon Next s’installe autour des dossiers professionnels.

Sur un NAS, un serveur local ou un poste dédié, il organise les sources, les preuves, les hypothèses, les validations et la mémoire.

Il peut être utilisé depuis un cockpit de chat dédié, puis progressivement depuis les canaux du quotidien : emails, documents partagés, messageries, tableaux projet et fichiers locaux.

L’IA accélère certaines tâches.

Pantheon garde le cadre.

L’humain valide.

Le validé demeure.
```

## Wording to avoid

Avoid:

```text
Everything stays local.
All connectors are available.
Pantheon connects to ChatGPT and Claude.
Pantheon installs skills automatically.
Pantheon executes tools.
Pantheon routes every model provider.
Pantheon reads WhatsApp and Gmail by default.
Pantheon stores everything as memory.
```

Prefer:

```text
In a local configuration, controlled material can remain on the chosen infrastructure.
Channels remain entry points, not truth.
Model and provider choices are governed by dossier sensitivity.
Implementation status must be verified capability by capability.
```

## Current status

Documented but not implemented as a deployment feature in this repository.

This document is a framing document for product communication, future architecture decisions and README wording.

It must not be read as evidence that Pantheon Next currently provides:

- an installer;
- a Docker stack;
- a provider router;
- built-in Gmail integration;
- built-in WhatsApp or Telegram integration;
- built-in Slack integration;
- automatic local database provisioning;
- automatic Evidence Pack generation;
- automatic Register Candidate review;
- automatic Registre Probatoire promotion.

Implementation must be verified separately, capability by capability.
