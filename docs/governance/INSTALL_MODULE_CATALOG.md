# Install Module Catalog

Status: candidate support doctrine — installable module record grammar. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

## Purpose

This document defines a governance-readable catalog shape for individual installable modules used by the common installation baseline.

It does not define alternative stack compositions. The required component set is owned by `COMMON_INSTALLATION_BASELINE.md`.

The catalog records only:

```text
module identity
source and version
installation mechanism
technical dependencies
conflicts
configuration status
health
exposure
backup
rollback
update status
governance gates
```

This document does not create a live registry, installer, Portainer stack, Docker file, SSH runner, package manager, plugin marketplace, provider router, scheduler, queue, approval engine or memory engine.

## Boundary

```text
exposed_by:
  OpenWebUI or Pantheon Control may display module cards, dependency maps,
  conflict warnings, version status, health, update status and gates.

executed_by:
  The human operator, Portainer, Docker Compose, SSH, a package manager or
  another bounded external mechanism performs installation outside Pantheon.

governed_by:
  Pantheon governs status vocabulary, source trust, dependency adoption,
  conflict review, activation, evidence expectations and rollback visibility.

approved_by:
  The human approves installation, configuration, activation, public exposure,
  provider binding, secret handling, updates and rollback.

forbidden:
  The catalog must not become an auto-installer, secret store, provider router,
  update runner, shell runner, approval shortcut or memory-promotion path.
```

## Module record

```json
{
  "apiVersion": "pantheon.next/v1alpha1",
  "kind": "InstallModule",
  "metadata": {
    "module_id": "postgres",
    "display_name": "PostgreSQL",
    "description": "Internal relational service for the common baseline.",
    "family": "data",
    "roles": ["primary_relational_database"],
    "owner": "human_admin",
    "maturity": "stable"
  },
  "spec": {
    "source": {},
    "provisioning": {},
    "dependencies": {},
    "conflicts": [],
    "configuration": {},
    "gates": {},
    "health": {},
    "exposure": {},
    "backup": {},
    "rollback": {},
    "updates": {},
    "forbidden": []
  },
  "status": {
    "catalog_status": "candidate",
    "detection_status": "unknown",
    "install_status": "not_installed",
    "configuration_status": "not_configured",
    "connection_status": "not_checked",
    "health_status": "not_checked",
    "activation_status": "disabled",
    "adoption_status": "not_adopted",
    "update_status": "unknown",
    "rollback_status": "unknown"
  }
}
```

The common baseline determines whether a module is required. A module record does not decide that requirement by itself.

```text
catalogued != installed
installed != configured
configured != connected
connected != healthy
healthy != safe
enabled != task-authorized
```

## Source and version

```json
{
  "source": {
    "type": "official_image | official_repo | internal_repo | package_manager | postgres_extension",
    "repo": "docker.io/library/postgres",
    "homepage": "https://www.postgresql.org/",
    "release_channel": "stable",
    "version_policy": "pinned",
    "selected_version": "<PINNED_VERSION>",
    "digest_or_checksum": "sha256:<DIGEST>",
    "allow_latest": false,
    "source_trust": "official",
    "license": "to_verify"
  }
}
```

```text
repo_exists != source_trusted
latest_exists != latest_authorized
official_source != no_review_required
checksum_present != source_approved
```

## Provisioning

```json
{
  "provisioning": {
    "mechanism": "portainer | docker_compose | ssh | package_manager | manual",
    "install_mode": "container | compose_stack | package_install | postgres_extension | manual",
    "requires_bootstrap": true,
    "requires_privilege": "user | sudo | root | unknown",
    "writes_files": true,
    "network_access": true,
    "secret_inputs": ["database_password"],
    "public_exposure_default": false
  }
}
```

```text
mechanism_available != execution_authorized
stack_generated != stack_approved
portainer_running != portainer_governed
ssh_available != free_shell_authorized
```

## Dependencies and roles

```json
{
  "dependencies": {
    "requires": ["container_runtime"],
    "provides_roles": ["primary_relational_database"],
    "requires_roles": ["private_container_network"]
  }
}
```

Dependencies are technical facts. Adoption and use remain separate decisions.

```text
dependency_installed != dependency_adopted
role_available != role_selected
binding_selected != dependency_adopted
```

## Conflicts

```json
{
  "conflicts": [
    {
      "with": "external_postgres",
      "type": "role_conflict",
      "severity": "soft",
      "reason": "Only one primary relational binding should be selected unless multi-store use is explicitly reviewed."
    }
  ]
}
```

Supported conflict classes:

```text
hard_conflict
soft_conflict
role_conflict
port_conflict
resource_conflict
data_conflict
governance_conflict
version_conflict
security_conflict
lifecycle_conflict
```

```text
conflict_detected != conflict_resolved
soft_conflict != safe_combination
hard_conflict != impossible_forever
```

## Configuration and bindings

The record may list candidate endpoints and binding states, but it must not store credentials.

```json
{
  "configuration": {
    "endpoint": "postgres:5432",
    "network": "ai-net",
    "binding_status": "not_selected",
    "credential_reference": "external_secret_reference"
  }
}
```

```text
endpoint_declared != reachable
reachable != selected
selected != activated
credential_reference_present != secret_governed
```

## Gates

```json
{
  "gates": {
    "install": "human_required",
    "configure": "human_required",
    "activate": "human_required",
    "adopt_for_project": "human_required",
    "expose_public": "blocked_by_default",
    "provide_secret": "external_secret_store_or_runtime_prompt",
    "major_update": "human_required",
    "delete_volume": "elevated_approval_required"
  }
}
```

```text
install_approved != activation_approved
secret_present != secret_governed
public_port_open != exposure_authorized
update_available != update_authorized
```

## Health, backup and rollback

```json
{
  "health": {
    "check_kind": "container_health | http | command | postgres_extension | manual",
    "expected_result": "ready",
    "last_result": "not_checked"
  },
  "backup": {
    "required": true,
    "last_result": "unknown"
  },
  "rollback": {
    "required": true,
    "strategy": "snapshot | previous_image | volume_backup | previous_config | manual",
    "last_verified": "never"
  }
}
```

```text
health_green != safe
service_ready != data_policy_safe
backup_present != restore_verified
rollback_defined != rollback_tested
```

## Updates

```json
{
  "updates": {
    "check_latest": true,
    "policy": "manual | security_patch_only | pinned_only",
    "patch": "human_or_policy_review",
    "minor": "human_required",
    "major": "human_required",
    "breaking": "blocked_until_review",
    "rollback_required": true
  }
}
```

```text
update_available != update_authorized
update_downloaded != update_applied
update_applied != update_activated
patch != harmless
```

## Common baseline relationship

The catalog does not compose alternative installations.

```text
COMMON_INSTALLATION_BASELINE.md
  -> states the required shared component set

INSTALL_MODULE_CATALOG.md
  -> describes each component independently

COMMON_BASELINE_RUNBOOK.md
  -> describes the manual operator sequence
```

A component may be required but inactive. That state remains visible through its module record and gates.

## Final rule

```text
The common baseline determines required presence.
Module records describe concrete components.
Bindings connect components under reviewed scope.
External operator mechanisms execute approved changes.
Pantheon governs status and gates.
The human decides.
```
