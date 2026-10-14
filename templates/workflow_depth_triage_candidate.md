# Workflow Depth Triage Candidate

Status: template candidate — non-executable.

This template classifies how deep a workflow should go before producing a candidate answer.

It is not a router, scheduler, approval engine or runtime instruction.

## Request

```text
request_id:
user_request:
project_ref:
received_material:
```

## Requested depth

```text
user_depth_hint: fast | normal | deep | unspecified
system_selected_depth: fast | normal | deep
selection_reason:
```

## Risk triggers

```text
money_or_invoice: yes / no
quote_or_extra_works: yes / no
insurance: yes / no
DTU_or_normative_source: yes / no
structure: yes / no
waterproofing_or_safety: yes / no
formal_notice: yes / no
client_reproach_or_responsibility: yes / no
external_action: yes / no
notion_validated_write: yes / no
canonical_memory: yes / no
source_contradiction: yes / no
```

## Depth result

```text
Fast:
- use when no risk trigger is active;
- answer short;
- state what was not checked.

Normal:
- use when context matters;
- check bounded project context;
- output candidate only.

Deep:
- use when consequence matters;
- require Task Contract / Context Pack / Evidence Pack Candidate or Capability Gap;
- open User Decision Gate for external/canonical effects.
```

## Checked sources

```text
checked:
not_checked:
missing:
```

## Output posture

```text
governance_result_status: candidate | to_verify | needs_approval | blocked
external_action_status: none | blocked | needs_approval
memory_status: none | candidate | blocked
notion_write_status: none | candidate | needs_approval | blocked
```

## Compact answer shape

```text
Depth:
What I can say now:
What I checked:
What I did not check:
Risk:
Next action:
```

## Stop condition

```text
If a decisive missing source already blocks conclusion, stop and emit a Capability Gap instead of expanding the workflow indefinitely.
```
