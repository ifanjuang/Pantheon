"""Bounded, read-only host observations for the Workspace producer panel."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess


UNITS = {
    "affaires": "pantheon-affaires-producer.service",
    "bibliotheque": "pantheon-bibliotheque-producer.service",
}
COORDINATOR_UNIT = "pantheon-workspace-multivault-producer.service"


def _scope_config(argv: list[str], exec_start: str) -> tuple[str, str]:
    """Read the scope passed to run_existing_producer.py, if this unit uses it."""
    config_path = ""
    for arguments in (argv, exec_start.split()):
        for index, argument in enumerate(arguments[:-1]):
            if argument.endswith("run_existing_producer.py"):
                config_path = arguments[index + 1].rstrip(";}")
                break
        if config_path:
            break
    if not config_path:
        return "", ""
    try:
        scope = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "", ""
    root = scope.get("path")
    state_db = scope.get("state_db")
    return (
        root if isinstance(root, str) else "",
        state_db if isinstance(state_db, str) else "",
    )


def _vault_config(argv: list[str], exec_start: str) -> dict[str, dict[str, str]]:
    config_path = ""
    for arguments in (argv, exec_start.split()):
        for index, argument in enumerate(arguments[:-1]):
            if argument == "--vault-config":
                config_path = arguments[index + 1].rstrip(";}")
                break
        if config_path:
            break
    if not config_path:
        return {}
    try:
        payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    raw_vaults = payload.get("vaults") if isinstance(payload, dict) else None
    if not isinstance(raw_vaults, list):
        return {}
    result: dict[str, dict[str, str]] = {}
    for vault in raw_vaults:
        if not isinstance(vault, dict):
            continue
        name, root = vault.get("name"), vault.get("root")
        if isinstance(name, str) and isinstance(root, str):
            result[name.casefold()] = {"name": name, "root": root}
    return result


def _run(arguments: list[str], *, timeout: float = 3) -> str:
    result = subprocess.run(
        arguments, capture_output=True, text=True, timeout=timeout, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"{arguments[0]} exited {result.returncode}")
    return result.stdout.strip()


def _service(unit: str) -> dict[str, object]:
    try:
        values = _run([
            "systemctl", "show", unit, "--property=ActiveState,SubState,MainPID,ExecStart",
        ])
        fields = dict(line.split("=", 1) for line in values.splitlines() if "=" in line)
        pid = int(fields.get("MainPID", "0"))
        command = []
        process_state = ""
        if pid > 0:
            try:
                command = [value.decode(errors="replace") for value in
                           Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if value]
                for line in Path(f"/proc/{pid}/status").read_text().splitlines():
                    if line.startswith("State:"):
                        process_state = line.split(":", 1)[1].strip()
                        break
            except OSError:
                pass
        root = ""
        state_db = ""
        for flag, destination in (("--root", "root"), ("--state-db", "state_db")):
            if flag in command:
                position = command.index(flag) + 1
                if position < len(command):
                    if destination == "root":
                        root = command[position].split("=", 1)[-1]
                    else:
                        state_db = command[position]
        configured = str(fields.get("ExecStart", ""))
        configured_root = re.search(r"--root Affaires=([^ ;]+)", configured)
        configured_db = re.search(r"--state-db ([^ ;]+)", configured)
        scope_root, scope_db = _scope_config(command, configured)
        vaults = _vault_config(command, configured)
        if scope_root:
            configured_root_value = scope_root
            configured_db_value = scope_db
            if not root and pid > 0:
                root = scope_root
            if not state_db and pid > 0:
                state_db = scope_db
        else:
            configured_root_value = configured_root.group(1) if configured_root else ""
            configured_db_value = configured_db.group(1) if configured_db else ""
        return {
            "unit": unit, "active": fields.get("ActiveState", "unknown"),
            "substate": fields.get("SubState", "unknown"), "pid": pid,
            "process_state": process_state, "root": root, "state_db": state_db,
            "configured_root": configured_root_value,
            "configured_state_db": configured_db_value,
            "vaults": vaults,
        }
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        return {"unit": unit, "active": "unavailable", "pid": 0,
                "process_state": "", "root": "", "state_db": ""}


def _mount(root: str) -> dict[str, str]:
    if not root:
        return {"source": "", "target": "", "relative": ""}
    try:
        output = _run(["findmnt", "--target", root, "--noheadings", "--output", "SOURCE,TARGET", "--raw"])
        source, target = output.split(None, 1)
        relative = os.path.relpath(root, target)
        return {"source": source, "target": target, "relative": relative}
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        return {"source": "", "target": "", "relative": ""}


def status(expected_root: str, expected_source: str) -> dict[str, object]:
    coordinator = _service(COORDINATOR_UNIT)
    configured_vaults = coordinator.get("vaults")
    if isinstance(configured_vaults, dict) and configured_vaults:
        services = {}
        for key in UNITS:
            profile = configured_vaults.get(key)
            if profile is None:
                continue
            root_path = str(profile["root"])
            running = coordinator["active"] == "active"
            services[key] = {
                **coordinator,
                "root": root_path if running else "",
                "configured_root": root_path,
                "state_db": coordinator.get("state_db", "") if running else "",
                "configured_state_db": coordinator.get("configured_state_db", ""),
            }
    else:
        services = {name: _service(unit) for name, unit in UNITS.items()}
    for name in UNITS:
        if name not in services:
            services[name] = _service(UNITS[name])
    affaires = services["affaires"]
    root = str(affaires["root"])
    configured_root = str(affaires.get("configured_root", ""))
    mount = _mount(root or configured_root)
    configured_source = mount["source"].rstrip("/")
    if mount["relative"] not in ("", "."):
        configured_source += "/" + mount["relative"]
    actual_source = (
        f"smb:{configured_source}"
        if mount["source"] and configured_source.startswith("//")
        else configured_source if mount["source"] else ""
    )
    expected = expected_source.removeprefix("smb:").rstrip("/")
    config_ok = bool(expected and expected_root and configured_root == expected_root and configured_source == expected)
    warnings = []
    if not root and affaires["active"] == "active":
        warnings.append("Chemin du worker indisponible")
    if expected_root and configured_root != expected_root:
        warnings.append("Le worker ne parcourt pas le dossier local attendu")
    if expected and configured_source != expected:
        warnings.append("Le chemin SMB effectif diffère du chemin attendu")
    if not mount["source"]:
        warnings.append("Montage du worker indisponible")
    if affaires["process_state"].startswith("T"):
        warnings.append("Worker Affaires suspendu")
    if affaires["active"] != "active":
        warnings.append("Worker Affaires arrêté")
    library = services["bibliotheque"]
    library_root = str(library.get("root") or library.get("configured_root") or "")
    library_mount = _mount(library_root) if library_root else {"source": "", "target": "", "relative": ""}
    library_source = library_mount["source"].rstrip("/")
    if library_mount["relative"] not in ("", "."):
        library_source += "/" + library_mount["relative"]
    expected_library_source = os.getenv(
        "WORKSPACE_EXPECTED_BIBLIOTHEQUE_SOURCE", ""
    ).removeprefix("smb:").rstrip("/")
    expected_library_root = os.getenv("WORKSPACE_EXPECTED_BIBLIOTHEQUE_ROOT", "")
    library_scope_ok = bool(
        library["active"] == "active"
        and library_root == expected_library_root
        and library_mount["source"]
        and library_source == expected_library_source
    )
    if library_root and library["active"] != "active":
        warnings.append("Worker Bibliothèque arrêté")
    elif library_root and not library_scope_ok:
        warnings.append("Portée Bibliothèque à vérifier")
    return {
        "services": services, "mount": mount, "actual_source": actual_source,
        "configured_source": configured_source, "config_ok": config_ok,
        "expected_root": expected_root, "expected_source": expected_source,
        "scope_ok": bool(
            affaires["active"] == "active"
            and expected
            and expected_root
            and root == expected_root
            and actual_source.removeprefix("smb:") == expected
        ),
        "library_mount": library_mount,
        "library_actual_source": (
            f"smb:{library_source}"
            if library_mount["source"] and library_source.startswith("//")
            else library_source if library_mount["source"] else ""
        ),
        "library_scope_ok": library_scope_ok,
        "coordinator": coordinator,
        "warnings": warnings,
    }


def logs(name: str, lines: int = 80) -> dict[str, object]:
    if name not in UNITS or not 1 <= lines <= 200:
        raise ValueError("invalid_producer_or_limit")
    try:
        coordinator = _service(COORDINATOR_UNIT)
        unit = COORDINATOR_UNIT if coordinator.get("vaults") else UNITS[name]
        output = _run([
            "journalctl", "--unit", unit, "--lines", str(lines),
            "--no-pager", "--output=short-iso", "--quiet",
        ], timeout=5)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return {"producer": name, "lines": [], "error": "journal_unavailable"}
    return {"producer": name, "lines": output[-65536:].splitlines(), "error": None}
