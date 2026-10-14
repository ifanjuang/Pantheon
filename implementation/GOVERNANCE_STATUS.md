# Governance Status

Status: co-located executable candidate — implemented and tested / not adopted.

This directory is the bounded executable candidate zone of the Pantheon Next monorepo. Co-location does not transfer governance authority, production adoption or professional truth.

## Current boundary

```text
Hermes-compatible clients -> runtime interaction
Hermes Agent              -> external execution
Pantheon implementation   -> bounded candidate persistence/projection/admission seams
Pantheon Next              -> governance and consequential status
human                      -> consequential decision
```

```text
retrieved != truth
runtime success != authorization
projection != persistence
memory != Evidence
implementation path != governed identity
```

## Current executable owners

The co-located candidate includes, among other bounded seams:

```text
canonical schema consumption and digest-verified packaged contracts
PostgreSQL/pgvector candidate persistence and retrieval
local/NAS document ingestion with declared-source/path/digest checks
Source intake and source/project-link governance
Docling/structured extraction where selected
Cockpit API, Navigation Registry, Cards and governed projections
Knowledge update preview/apply chokepoint
human OIDC identity binding chokepoint
Architecture Project Understanding reviewed-dossier import chokepoint
Knowledge publish (reviewed claim) and edit-application chokepoints
Agency Information act (supersede-and-promote) chokepoint
policy/PEP client and effect preflight contracts
capability lifecycle projection/management seams
Hermes Runs observation, launch reservation/binding and active-context bridge
Hermes context plugin candidate
issuer-signing/authentication support
runtime_observation generic envelope
```

None of these establishes target deployment, adoption, activation or real-dossier authorization.

## Phase B composition

`compose.phase-b.yaml` now contains only the current candidate service composition:

```text
pgvector
Docling
cockpit-api
Hermes Agent
```

Paperless, its gateway/ingestion binding, the Paperless-specific Hermes skill and the dedicated document-runtime observer have been retired after consumer audit.

```text
Paperless absent != document ingestion unavailable
DMS absent != source identity absent
source captured != Evidence
```

The generic local/NAS source path remains available through existing source/document owners. Obsidian is not promoted into a DMS by this removal.

## Residual compatibility

OpenWebUI is refused as a target dependency, but residual protected compatibility files are audited separately. Their repository presence does not make OpenWebUI an active architecture owner.

```text
compatibility present != selected dependency
client compatibility != governance authority
```

## Selected implementation status

```text
installation_status: not installed by Pantheon Next
activation_status: not activated
production_status: forbidden pending separate adoption
generic_source_intake: implemented_candidate_not_deployed
local_document_ingestion: implemented_candidate_not_deployed
structured_extraction: implemented_candidate_not_deployed
cockpit_projection: implemented_candidate_not_deployed
policy_chokepoint_seam: implemented_not_connected
knowledge_update_chokepoint: wired_not_connected
human_identity_binding_chokepoint: wired_not_connected
apu_reviewed_dossier_chokepoint: wired_not_connected
knowledge_publish_chokepoint: wired_not_connected
knowledge_edit_apply_chokepoint: wired_not_connected
agency_information_act_chokepoint: wired_not_connected
capability_management_slice: implemented_not_connected
hermes_runs_api_observer: implemented_candidate_not_connected
hermes_run_launch_reservation: implemented_candidate_not_connected
hermes_runs_external_binding: implemented_candidate_not_connected
hermes_active_context_bridge: implemented_candidate_not_connected
hermes_context_plugin: implemented_candidate_not_installed
human_issuer_signing: implemented_not_connected
runtime_observation_envelope: implemented_candidate
```

A green test suite proves only that these candidate contracts remain coherent in the repository. It does not prove production admission or activation.

The repository policy path now distinguishes direct human governed-state effects from delegated runtime work. The five reviewed direct-human intents (`bind_oidc_identity`, `store_reviewed_dossier`, `publish_knowledge_reviewed`, `apply_edit_request`, and `act_working_information`) remain K3/C2 and blocked until an exact human decision is verified, but they do not fabricate a Task Contract or Evidence Pack solely because they write local governed state. Unknown, delegated, or external-effect requests remain fail-conservative and keep the applicable Task Contract and Evidence requirements. This correction and its closed intent set are traced in the private Pantheon-Next archive and exercised by the policy/PEP tests.

## Adoption gates still open

```text
real Hermes deployment/adoption
reviewed restricted Hermes tool surface
live Runs/context binding proof
live target issuer registry + signed-decision round trip
production source-path permissions and rollback proof
human approval for activation
real-dossier authorization
```

## Final rule

```text
candidate implementation != adopted runtime
healthy/reachable != safe
test pass != approval
runtime receipt != Evidence
provider selected != authority transfer
```
