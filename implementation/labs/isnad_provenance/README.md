# ISNAD bounded provenance qualification

Status: qualification lab for Pantheon issue Pantheon-Next#922. Not installed, selected, activated, persisted, or adopted by default.

## Purpose

Exercise ISNAD only as a replaceable transmission-chain grading and tamper-evident audit observer behind existing Pantheon governance owners.

```text
Pantheon/Hermes observed transmission facts
        -> this bounded adapter
        -> ISNAD chain grading + audit primitives
        -> advisory provenance observation
        -> existing Pantheon candidate/review owners
```

ISNAD does not become a Claim owner, Evidence owner, review owner, persistence layer, authorization gate, PDP, governed identity registry, or runtime.

## Qualification target

Canonical pin: `implementation/qualification/external-pins.json`.
Upstream freshness observation: `implementation/qualification/external-upstream-observations.json`.

```text
package: isnad
version: 2.20.1
upstream repository: alizahidraja/isnad
upstream commit: 4a9a9a3dd22b459c5e6a15d87af0997febad1703
latest release observed: v2.20.1 on 2026-09-01
```

The package/ref pair is qualification input, not deployment truth. The upstream observation records what was published; it does not move or authorize the pin.

## What this slice proves

- a complete transmission chain can be graded with ISNAD's `RefinedWeakestLink` implementation;
- a gap in the observed chain is surfaced as `munqati` and advisory `daif`;
- a caller-supplied rejected transmitter is surfaced as advisory `mawdu`;
- the result is a Pantheon-owned provider-neutral dataclass, not an ISNAD serving/review action;
- the observation explicitly carries `evidence_admitted=false`, `claim_verified=false`, `authorized_effect=false`, and `persisted=false`;
- raw transformation snapshots are represented in the audit record only by hashes;
- raw claim text is redacted to a SHA-256 reference by default before the audit artifact is sealed;
- the ISNAD audit record self-hash fails after payload mutation;
- an optional detached HMAC signature fails after payload mutation or when verified with the wrong key;
- no ISNAD API, database persistence, review queue, or decision matrix is imported by the lab.

## Grade semantics in this lab

Narrator grades are supplied to the adapter as qualification inputs. The lab does not create or own a production ISNAD `Registry`, learn grades, promote a Claim, or infer a Pantheon certainty/Evidence level from an ISNAD grade.

```text
ISNAD narrator grade = advisory input about a transmitter
ISNAD chain grade = advisory output about the observed transmission
ISNAD audit integrity = proof the audit payload was not changed under the checked seal
none of the above = claim truth or Pantheon Evidence
```

A future integration would need a separately governed source for transmitter observations before any grade could be relied upon operationally.

## Deliberate exclusions

This slice does **not** qualify:

- ISNAD `decide()` or its `SERVE` / `REVIEW` / `QUARANTINE` action vocabulary;
- ISNAD FastAPI service;
- ISNAD database models, migrations, serving index, or `store_claim` persistence;
- ISNAD review queue or human-resolution endpoint;
- automatic narrator-registry learning or Bayesian updates;
- corroboration/independence promotion;
- content critics or content-verdict truth assessment;
- LangChain/LangGraph/CrewAI/LlamaIndex integrations;
- direct Hermes runtime wiring;
- a new Pantheon provenance schema or canonical registry;
- the planned breaking ISNAD 3.0 issuer/revocation model.

The current upstream issue Pantheon-Next#188 proposes a future breaking evidence-envelope/issuer model. That work is not treated as shipped capability by this qualification.

## Authority boundary

```text
transmission observed != truth
ISNAD grade != Evidence
audit hash valid != claim true
detached signature valid != issuer authorized
narrator id != governed identity
ISNAD action vocabulary != Pantheon authorization
runtime success != authorization
observer output != persistence
upstream observation != adopted pin
lab present != component adopted
```

## Removal test

The lab has no product boot path, schema, migration, runtime registration, or governed-owner mutation. Removing:

- `implementation/labs/isnad_provenance/`;
- `implementation/tests/test_isnad_bounded_provenance_lab.py`;
- `.github/workflows/implementation-isnad-provenance-qualification.yml`;
- the `isnad` external qualification pin;
- the `isnad` upstream-observation record;

restores the prior product behavior.

## Next decision

After qualification, keep ISNAD on candidate-watch unless a demonstrated Hermes/Pantheon workflow benefits from transmission-chain provenance beyond the existing Claim/backing/review lineage. If that need appears, prefer a small provider-neutral provenance-observation seam rather than adopting ISNAD's storage or decision authority.
