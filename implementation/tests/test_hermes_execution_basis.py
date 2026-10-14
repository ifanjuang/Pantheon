from __future__ import annotations

from pathlib import Path

import pytest

from mvp_vertical import (
    hermes_execution,
    hermes_handoff_store,
    hermes_launch_context,
    hermes_scoped_context,
)
from mvp_vertical.hermes_execution_basis import (
    HermesExecutionBasis,
    HermesExecutionBasisError,
)


def test_execution_basis_normalizes_and_compares_exact_contract_identity() -> None:
    first = HermesExecutionBasis.from_values(
        requested_effect=" read_only ",
        task_contract_ref=" task:1 ",
        context_pack_ref=" context:1 ",
        preview_digest=" digest-1 ",
    )
    second = HermesExecutionBasis.from_values(
        requested_effect="read_only",
        task_contract_ref="task:1",
        context_pack_ref="context:1",
        preview_digest="digest-1",
    )

    assert first == second
    assert first.is_read_only is True


def test_execution_basis_keeps_each_dimension_independent() -> None:
    baseline = HermesExecutionBasis.from_values(
        requested_effect="read_only",
        task_contract_ref="task:1",
        context_pack_ref="context:1",
        preview_digest="digest-1",
    )
    changed_context = HermesExecutionBasis.from_values(
        requested_effect="read_only",
        task_contract_ref="task:1",
        context_pack_ref="context:2",
        preview_digest="digest-1",
    )

    assert baseline != changed_context


def test_execution_basis_refuses_incomplete_structure() -> None:
    with pytest.raises(HermesExecutionBasisError, match="context_pack_ref"):
        HermesExecutionBasis.from_values(
            requested_effect="read_only",
            task_contract_ref="task:1",
            context_pack_ref="",
            preview_digest="digest-1",
            label="test basis",
        )


def test_hermes_chain_shares_basis_without_granting_authority() -> None:
    execution_source = Path(hermes_execution.__file__).read_text(encoding="utf-8")
    handoff_source = Path(hermes_handoff_store.__file__).read_text(encoding="utf-8")
    launch_source = Path(hermes_launch_context.__file__).read_text(encoding="utf-8")
    runtime_source = Path(hermes_scoped_context.__file__).read_text(encoding="utf-8")

    assert "HermesExecutionBasis.from_values" in handoff_source
    assert "HermesExecutionBasis.from_values" in execution_source
    assert "HermesExecutionBasis.from_values" in launch_source
    assert "HermesExecutionBasis.from_values" in runtime_source
    assert "execution_authorized=false" in handoff_source
    assert 'current["admission_state"] != "admitted"' in launch_source
    assert 'scope["run_status"] != "running"' in runtime_source
    assert 'scope["run_requested_effect"] == "read_only"' in runtime_source
    assert '"launch reservation != runtime dispatch"' in launch_source
    assert '"runtime success != Evidence"' in runtime_source


def test_human_admission_constructs_basis_after_work_issue_gates() -> None:
    source = Path(hermes_execution.__file__).read_text(encoding="utf-8")

    basis_index = source.index("execution_basis = HermesExecutionBasis.from_values")
    assert source.index('issue["assigned_to"] != "hermes"') < basis_index
    assert source.index('issue["status"] != "open"') < basis_index
    assert source.index('issue["task_contract_ref"] != handoff["task_contract_ref"]') < basis_index
    assert source.index('issue["context_pack_ref"] != handoff["context_pack_ref"]') < basis_index
    assert "admission_digest_basis" in source
    assert '"human actor is required for execution admission"' in source
    assert '"immutable handoff basis is incomplete"' in source
    assert "VALUES (%s,%s,%s,'allow',%s" in source


def test_execution_envelope_checks_basis_before_consumability_and_never_dispatches() -> None:
    source = Path(hermes_execution.__file__).read_text(encoding="utf-8")

    assert source.index("admission_basis = HermesExecutionBasis.from_values") < source.index(
        'if not projection["ready_for_external_runtime"]'
    )
    assert '"execution admission no longer matches immutable handoff"' in source
    assert '"runtime_instruction":None' in source
    assert '"dispatch_requested":False' in source
