# MVP Generated Validation Reports

Status: candidate support note — local/manual generated reports.

These reports are committed examples of local validator output.

They do not approve, prove truth, admit memory, authorize external action, validate runtime health, call Hermes, call OpenWebUI, write to a database or act as CI.

## Command shape

```bash
python scripts/validate_mvp_fixture.py \
  --fixture docs/governance/examples/mvp_vertical_fixture/fixture.schema_targets.yaml \
  --schema schemas/mvp_governed_loop_objects.schema.yaml \
  --output docs/governance/examples/mvp_vertical_fixture/generated_reports/fixture.schema_targets.generated_report.yaml \
  --created-at 2026-07-13T00:00:00Z

python scripts/validate_mvp_fixture.py \
  --fixture docs/governance/examples/mvp_vertical_fixture/failing_external_action.fixture.yaml \
  --schema schemas/mvp_governed_loop_objects.schema.yaml \
  --output docs/governance/examples/mvp_vertical_fixture/generated_reports/failing_external_action.generated_report.yaml \
  --created-at 2026-07-13T00:00:00Z
```

## Expected statuses

```text
fixture.schema_targets.generated_report.yaml -> reviewable
failing_external_action.generated_report.yaml -> blocked
```
