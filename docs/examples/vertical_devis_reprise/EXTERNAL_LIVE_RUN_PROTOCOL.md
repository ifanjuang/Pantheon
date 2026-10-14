# External live run protocol — `architecture_devis_reprise`

Status: validation-only / external-infra protocol.

Issue: Pantheon-Next#273.

This protocol frames a fictional governed Hermes run. It does not install a runtime, create a client bridge, approve a result, send a message or admit anything to the Registre Probatoire.

## Boundary ownership

```text
interaction -> Hermes Web/dashboard or another compatible replaceable Hermes client
execution   -> externally installed Hermes Agent and two bounded skills
governance  -> Pantheon Task Contract, return contract, Evidence Pack and gates
approval    -> human operator before execution and professional before use
forbidden   -> real dossier data, external send, signature, payment approval,
               enterprise instruction, automatic approval or register admission
```

## Repository-side status

Implemented/testable here are the fictional governed dossier, return fixture and read-only validator under `docs/examples/vertical_devis_reprise/`, `docs/examples/external_run_returns/` and `scripts/validate_devis_reprise_return.py`.

External and separately observed are Hermes installation/configuration, interaction client, provider/model selection, credentials, network posture, execution and rollback.

```text
repository fixture valid != external runtime installed
client selected != authority transfer
runtime success != authorization
```

## External runtime qualification

Before calling a test a complete Hermes run, record the exact Hermes version/commit, interaction client/version where material, transport, Pantheon pin, model/provider, operator, network boundary, credential-location class, and rollback procedure.

Pantheon may validate declared returns and govern consequential status. It must not become the external runtime, connector, queue, scheduler or provider router.

## Candidate bindings

```text
templates/hermes/run_manifests/devis_reprise_run_manifest.template.yaml
templates/hermes/skills/quote-variation-review/SKILL.md
templates/hermes/skills/external-commitment-guard/SKILL.md
```

The skills remain candidates until separately installed and approved on the external Hermes host.

## Return contract

Hermes returns or persists an envelope shaped like `docs/examples/external_run_returns/architecture_devis_reprise.example.yaml` with one outcome type:

```text
candidate_return
capability_gap
refusal
```

A candidate return must preserve the Task Contract and Context Pack identifiers, exact Pantheon ref, runtime identity, trace references, candidate status, Evidence Pack Candidate, explicit forbidden-effect flags and an unresolved human decision.

The validator checks structure and declared boundaries only. It does not probe the host, establish professional truth or prove self-reported effect flags.

## Validation

```bash
python3 .github/scripts/check_vertical_slice.py

python3 scripts/validate_devis_reprise_return.py \
  --return-file /path/to/sanitized-external-return.yaml \
  --task-contract docs/examples/vertical_devis_reprise/task_contract.devis-reprise.yaml \
  --expected-pantheon-ref "$PANTHEON_PIN"
```

Passing structural validation remains reviewable and does not authorize consequence.

## Rollback

After the fictional test, remove disposable runtime configuration/credentials, confirm no schedule/task/writable mount remains, and record rollback separately from runtime result.

## Final distinctions

```text
static fixture valid != runtime return valid
runtime success != Evidence
validator pass != professional truth
trace != proof
candidate != Registre Probatoire entry
projection != persistence
human decision remains required
```
