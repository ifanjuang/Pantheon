from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "implementation" / "workspace_cockpit" / "worker_observability.py"


def _module():
    spec = importlib.util.spec_from_file_location("workspace_worker_observability", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_service_reads_scope_json_from_wrapped_worker_execstart(tmp_path: Path) -> None:
    module = _module()
    root = "/mnt/AGENCY/PROJECTS/AFFAIRES"
    state_db = "/var/lib/pantheon-workspace-cockpit/affaires.sqlite3"
    scope_path = tmp_path / "affaires.json"
    scope_path.write_text(json.dumps({"path": root, "state_db": state_db}), encoding="utf-8")
    exec_start = (
        "{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 "
        f"/opt/pantheon-workspace-cockpit/run_existing_producer.py {scope_path} ; "
        "ignore_errors=no ; }"
    )
    output = "\n".join((
        "ActiveState=active",
        "SubState=running",
        "MainPID=123456",
        f"ExecStart={exec_start}",
    ))

    with patch.object(module, "_run", return_value=output):
        observed = module._service("pantheon-affaires-producer.service")

    assert observed["root"] == root
    assert observed["configured_root"] == root
    assert observed["state_db"] == state_db
    assert observed["configured_state_db"] == state_db


def test_status_matches_wrapped_scope_to_mounted_smb_root() -> None:
    module = _module()
    root = "/mnt/AGENCY/PROJECTS/AFFAIRES"
    source = "smb://nas.example/agency/PROJECTS/AFFAIRES"
    services = {
        "pantheon-affaires-producer.service": {
            "unit": "pantheon-affaires-producer.service",
            "active": "active",
            "substate": "running",
            "pid": 123456,
            "process_state": "S (sleeping)",
            "root": root,
            "state_db": "/var/lib/pantheon-workspace-cockpit/affaires.sqlite3",
            "configured_root": root,
            "configured_state_db": "/var/lib/pantheon-workspace-cockpit/affaires.sqlite3",
        },
        "pantheon-bibliotheque-producer.service": {
            "unit": "pantheon-bibliotheque-producer.service",
            "active": "inactive",
            "substate": "dead",
            "pid": 0,
            "process_state": "",
            "root": "",
            "state_db": "",
            "configured_root": "",
            "configured_state_db": "",
        },
    }

    with (
        patch.object(module, "_service", side_effect=lambda unit: (
            {"active": "inactive", "vaults": {}} if unit == module.COORDINATOR_UNIT else services[unit]
        )),
        patch.object(module, "_mount", return_value={
            "source": "//nas.example/agency/PROJECTS",
            "target": "/mnt/AGENCY/PROJECTS",
            "relative": "AFFAIRES",
        }),
    ):
        observed = module.status(root, source)

    assert observed["actual_source"] == source
    assert observed["config_ok"] is True
    assert observed["scope_ok"] is True
    assert observed["warnings"] == []


def test_stopped_worker_keeps_configured_scope_visible_without_claiming_active_scope() -> None:
    module = _module()
    root = "/mnt/AGENCY/PROJECTS/AFFAIRES"
    source = "smb://nas.example/agency/PROJECTS/AFFAIRES"
    services = {
        "pantheon-affaires-producer.service": {
            "unit": "pantheon-affaires-producer.service",
            "active": "inactive",
            "substate": "dead",
            "pid": 0,
            "process_state": "",
            "root": "",
            "state_db": "",
            "configured_root": root,
            "configured_state_db": "/var/lib/pantheon-workspace-cockpit/affaires.sqlite3",
        },
        "pantheon-bibliotheque-producer.service": {
            "unit": "pantheon-bibliotheque-producer.service",
            "active": "inactive",
            "substate": "dead",
            "pid": 0,
            "process_state": "",
            "root": "",
            "state_db": "",
            "configured_root": "",
            "configured_state_db": "",
        },
    }

    with (
        patch.object(module, "_service", side_effect=lambda unit: (
            {"active": "inactive", "vaults": {}} if unit == module.COORDINATOR_UNIT else services[unit]
        )),
        patch.object(module, "_mount", return_value={
            "source": "//nas.example/agency/PROJECTS",
            "target": "/mnt/AGENCY/PROJECTS",
            "relative": "AFFAIRES",
        }),
    ):
        observed = module.status(root, source)

    assert observed["actual_source"] == source
    assert observed["config_ok"] is True
    assert observed["scope_ok"] is False
    assert observed["warnings"] == ["Worker Affaires arrêté"]


def test_status_projects_both_vaults_from_one_coordinator(tmp_path: Path) -> None:
    module = _module()
    assert module.COORDINATOR_UNIT == "pantheon-workspace-multivault-producer.service"
    affairs_root = "/mnt/AGENCY/PROJECTS/AFFAIRES"
    library_root = "/mnt/AGENCY/LIBRARY"
    profiles = tmp_path / "vaults.json"
    profiles.write_text(json.dumps({"vaults": [
        {"name": "Affaires", "root": affairs_root},
        {"name": "Bibliotheque", "root": library_root},
    ]}), encoding="utf-8")
    service = {
        "unit": module.COORDINATOR_UNIT,
        "active": "active",
        "substate": "running",
        "pid": 777,
        "process_state": "S (sleeping)",
        "root": "",
        "state_db": "/var/lib/pantheon-workspace-cockpit/multivault.sqlite3",
        "configured_root": "",
        "configured_state_db": "/var/lib/pantheon-workspace-cockpit/multivault.sqlite3",
        "vaults": module._vault_config([], f"ExecStart=/usr/bin/python3 /opt/producer_daemon.py --vault-config {profiles} --state-db /var/lib/pantheon-workspace-cockpit/multivault.sqlite3"),
    }
    with (
        # The expected Bibliotheque scope is a node binding, not a code default.
        patch.dict(module.os.environ, {
            "WORKSPACE_EXPECTED_BIBLIOTHEQUE_SOURCE": "smb://nas.example/agency/LIBRARY",
            "WORKSPACE_EXPECTED_BIBLIOTHEQUE_ROOT": library_root,
        }),
        patch.object(module, "_service", side_effect=lambda unit: service if unit == module.COORDINATOR_UNIT else pytest.fail(unit)),
        patch.object(module, "_mount", side_effect=lambda root: (
            {"source": "//nas.example/agency/PROJECTS", "target": "/mnt/AGENCY/PROJECTS", "relative": "AFFAIRES"}
            if root == affairs_root else
            {"source": "//nas.example/agency/LIBRARY", "target": "/mnt/AGENCY/LIBRARY", "relative": "."}
        )),
    ):
        observed = module.status(affairs_root, "smb://nas.example/agency/PROJECTS/AFFAIRES")

    assert observed["scope_ok"] is True
    assert observed["library_scope_ok"] is True
    assert observed["services"]["affaires"]["pid"] == 777
    assert observed["services"]["bibliotheque"]["pid"] == 777
    assert observed["services"]["bibliotheque"]["configured_root"] == library_root
    assert observed["warnings"] == []
