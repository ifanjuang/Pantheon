# Update and installation-specific content boundary

Status: deployment design and operator guidance. This document describes the
current Ubuntu node updater; it does not authorize installation, activation or
runtime changes.

## The three content layers

Keep three kinds of content distinct. “Local” can otherwise mean either shared
organization policy or state owned by one machine.

| Layer | Owner | Examples | Update behavior |
|---|---|---|---|
| Pantheon Next | This Git repository | Policy package, common Hermes skills, deployment scripts | Updated only to an explicitly reviewed full commit SHA |
| Organization overlay | The organization | Organization methods, adapters, prompt additions and integration definitions shared by its installations | Must have its own explicit source/version and merge point; it must not be treated as machine state or silently replaced by the common release |
| Installation state | One installed node | Hermes configuration, local skills, credentials, service settings, runtime data and operator choices | Kept in persistent host paths and preserved by Pantheon Next updates |

Organization-specific content may currently be versioned in Pantheon Next (for
example, the optional agency adapter). That means it is repository-owned today,
not private installation state. Moving it to an organization overlay is a
separate migration; do not move or delete it as part of a routine node update.

## Current Ubuntu node paths

- `/opt/pantheon/Pantheon-Next-<sha>` is an immutable versioned checkout;
  `/opt/pantheon/current` selects the active checkout.
- `/srv/pantheon/policy-venv` is persistent runtime state whose installed
  Pantheon package is updated from the selected checkout.
- `/srv/pantheon/hermes/` is the native Hermes home. Its configuration,
  profiles and installation-owned skills are not the repository's authoring
  tree.
- `/srv/pantheon/hermes-governed-skills/` is a **deployment-managed projection**
  of the named common skills in a reviewed checkout. It is replaced as a unit
  during synchronization and must not contain hand-maintained or
  installation-specific content.
- `/etc/pantheon-node/` contains node configuration and version records.
- `/srv/pantheon/backups/update-*` contains update checkpoints. A checkpoint
  is a recovery aid, not a complete backup of Hermes, application data or
  secrets.

The updater currently checkpoints `/etc/pantheon-node`, the governed profile
configuration file and the managed common-skills projection before applying
changes. The skill synchronizer adds its managed path to the existing
`pantheon-governed` `skills.external_dirs` list. It must preserve every existing
entry and stop before changing the projection if it cannot read or validate
that list. During replacement it retains the previous projection until profile
binding and service restart succeed; on failure it restores the prior profile
value and projection, then attempts to restart Hermes on the restored state.
The projection itself is deliberately replaceable; local skills belong in a
separate persistent path referenced by the profile.

## Safe update contract

`update-node --apply --component pantheon` does not run `git pull`. It requires
`PANTHEON_COMMIT_OVERRIDE` to contain a reviewed full commit SHA, checks out
that exact revision into a versioned directory, updates the policy package,
switches the `current` symlink and synchronizes only the named managed skill
projection. It does not author or migrate installation configuration and does
not run optional organization configurators.

Before a node update, confirm that installation-specific configuration and
skills are outside the versioned checkout and outside the managed projection.
Keep organization content in a separately versioned overlay when it must be
shared across nodes. A future overlay integration should merge explicitly,
preserve unknown/local values, checkpoint its outputs and fail closed on
unreadable or malformed configuration.

If a Pantheon update fails after package installation begins, `update-node`
attempts to restore the prior checkout link, reinstall the policy package from
the previous checkout, restore the governed profile and skill projection from
the checkpoint, restart Hermes when skill synchronization was attempted, and
restore the prior recorded Pantheon commit. This is a best-effort package
reinstall from source, not an exact snapshot of the policy virtual environment
or its transitive dependency versions. It retains the checkpoint whether the
update succeeds or fails. If any rollback step fails, the updater reports that
the checkpoint needs operator inspection; it cannot guarantee recovery from
disk, package-manager or service failures.

`--component all` applies Ollama first and Pantheon second. If Ollama's
installation, restart or version recording fails, the updater does not roll
back Ollama and does not proceed to Pantheon. If Ollama succeeds but the
Pantheon update later fails, Ollama remains updated while the Pantheon rollback
is attempted. Inspect the checkpoint and both component states after a partial
failure.
