# MVP Prevalidator Readiness

Status: candidate support note — local/manual validator present; CI still not ready.

Date: 2026-07-08

This note consolidates the decisions that must be true before a CI validator may be considered.

It adds no CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Ready for local/manual validation

The following are now present:

```text
positive schema-target fixture
expected positive report
deliberate failing fixture
expected blocked report
central governance invariants
report vocabulary
Source Manifest / Retrieval Trace placement decision
local validator design
local/manual validator script
generated positive report
generated blocked report
```

## Still not ready for CI

CI is still premature.

Missing before CI:

```text
review of first generated reports
status enum proposal based on real validator output
alias equality policy implementation decision
one additional failing fixture for broken reference integrity
explicit decision on whether validator dependencies are vendored, documented or locked
```

## Local validator allowed scope

The local validator may:

```text
parse YAML
validate central object schemas
check object references
check named governance invariants
emit a report
```

It must not:

```text
authorize external action
approve a draft
admit memory
write to database
call Hermes
call OpenWebUI
run as scheduler
block merges through CI
```

## Local command shape

```bash
python scripts/validate_mvp_fixture.py \
  --fixture docs/governance/examples/mvp_vertical_fixture/fixture.schema_targets.yaml \
  --schema schemas/mvp_governed_loop_objects.schema.yaml \
  --output docs/governance/examples/mvp_vertical_fixture/generated_reports/fixture.schema_targets.generated_report.yaml \
  --created-at 2026-07-08T00:00:00Z
```

The command is report-only. It does not authorize anything.

## Next recommended PR

The next PR should review the generated reports and decide:

```text
whether the warning model is acceptable
whether alias equality should become blocking
whether to add a broken-reference failing fixture
whether to document or lock PyYAML/jsonschema versions
```

CI remains out of scope until those decisions are made.
