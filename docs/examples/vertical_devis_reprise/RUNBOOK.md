# Runbook — `architecture_devis_reprise` vertical slice

Status: validation-only runbook.

This runbook identifies governed repository artifacts and the external Hermes execution seam. It is not an operations procedure, runtime installation or client-specific bridge.

## Ownership

```text
interaction -> Hermes Web/dashboard or another compatible replaceable Hermes client
execution   -> externally installed Hermes Agent
governance  -> Pantheon Task Contract, gates, Evidence Pack and return validator
approval    -> human operator and professional reviewer
forbidden   -> external effect, automatic approval or register admission
```

## End-to-end sequence

```text
1. A Hermes client captures the bounded user request.                 [external]
2. Pantheon artifacts frame Task Contract, scope and gates.           [this repo]
3. The authorized request reaches Hermes Agent through its runtime.   [external]
4. Hermes executes only the two candidate skills.                     [external]
5. Hermes persists or returns the exact external return YAML.         [external]
6. Pantheon validates the caller-provided return read-only.           [this repo]
7. A client or Cockpit projection displays candidate status/gaps.     [projection]
8. The human accepts, refuses or requests revision.                   [human]
```

Client operation does not create Pantheon state, and Pantheon Cockpit does not become a second generic chat frontend.

## Governed inputs

```text
task_contract.devis-reprise.yaml
workflow_manifest.devis-reprise.yaml
policy_decision.gate1.yaml
```

Hermes may load only:

```text
templates/hermes/skills/quote-variation-review/SKILL.md
templates/hermes/skills/external-commitment-guard/SKILL.md
```

The expected external run shape is described by `templates/hermes/run_manifests/devis_reprise_run_manifest.template.yaml` and the return fixture `docs/examples/external_run_returns/architecture_devis_reprise.example.yaml`.

## Checks

Static dossier validation:

```bash
python3 .github/scripts/check_vertical_slice.py
```

Caller-provided external return validation:

```bash
python3 scripts/validate_devis_reprise_return.py \
  --return-file /path/to/sanitized-external-return.yaml \
  --expected-pantheon-ref "$PANTHEON_PIN"
```

Both are read-only. Neither proves professional truth, authorization, absence of external effect or Registre Probatoire admission.

## Data boundary

The first run uses fictional data only. Real client documents remain excluded until licence, storage, access and professional-use gates are separately qualified.

## Stop condition

The run stops at the human decision surface. Nothing is sent, signed, approved, paid, instructed or admitted automatically.

```text
static fixture valid != runtime return valid
runtime success != Evidence
validator pass != professional approval
client selected != authority transfer
```
