# Pantheon architecture audit

The architecture audit evaluates one Pantheon monorepo through explicit physical zones. A zone is an audit partition, not a governed identity and not an authorization boundary.

## Current zones

- `governance-core`: repository-root doctrine, schemas, registries, guards and bounded governance modules outside `implementation/`.
- `implementation`: the executable candidate under `implementation/`.
- Hermes remains an external runtime responsibility.
- Cockpit/OpenWebUI remains an interaction/projection responsibility even when its code is physically inside the implementation zone.

The support ownership registry carries logical responsibility identities (`Pantheon governance`, `Pantheon implementation`, `Hermes/external runtime`, `Cockpit/OpenWebUI`). The audit maps each physical zone to one explicit owner identity. This is deliberate: folder/zone != governed identity, and repository name != owner identity.

## Independent merge gate

A pull request must not be able to rewrite both the candidate implementation and the rule that judges that same run. The active workflow therefore uses:

1. one checkout of the current candidate monorepo;
2. one sparse immutable snapshot containing only the bounded audit authority inputs.

Candidate changes to those authority files are reported as drift but do not alter the pinned rule used by the run. Updating the pin is a separate reviewed change.

The current audit authority pin points to the already-merged registry revision that established the logical owner identities. The workflow cannot modify that pinned commit from the pull request being evaluated.

## Review dimensions

Every active artifact is reviewed for generation-named paths, internal versioned routes, duplicate active identities, excessive implementation fragmentation, forbidden runtime responsibilities, compatibility residue, parse failures and unreferenced implementation candidates.

Historical and migration material remains auditable without becoming active debt. A finding is not deletion proof. Successful CI is not semantic authority, authorization, Evidence admission or permission to remove a component.

## Usage

```bash
python implementation/tools/audit_pantheon_architecture.py \
  --zone "governance-core=governance=Pantheon governance=/path/to/Pantheon-Next" \
  --zone "implementation=implementation=Pantheon implementation=/path/to/Pantheon-Next/implementation" \
  --authority-registry /path/to/pinned/PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json \
  --output /tmp/PANTHEON_ARCHITECTURE_INVENTORY.md
```

The nested roots are intentional. Each file is assigned once to the most-specific declared zone, so `implementation/**` is never simultaneously counted as governance.

The audit performs no rewrite, move, deletion, approval or runtime action.
