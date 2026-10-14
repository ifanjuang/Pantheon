"""Bounded, read-only host observations for the Workspace producer panel."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess


UNITS = {
    "affaires": "pantheon-affaires-producer.service",
    "bibliotheque": "pantheon-bibliotheque-producer.service",
}


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
        return {
            "unit": unit, "active": fields.get("ActiveState", "unknown"),
            "substate": fields.get("SubState", "unknown"), "pid": pid,
            "process_state": process_state, "root": root, "state_db": state_db,
            "configured_root": configured_root.group(1) if configured_root else "",
            "configured_state_db": configured_db.group(1) if configured_db else "",
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
    services = {name: _service(unit) for name, unit in UNITS.items()}
    affaires = services["affaires"]
    root = str(affaires["root"])
    configured_root = str(affaires.get("configured_root", ""))
    mount = _mount(root or configured_root)
    configured_source = mount["source"].rstrip("/")
    if mount["relative"] not in ("", "."):
        configured_source += "/" + mount["relative"]
    actual_source = configured_source if root else ""
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
    return {
        "services": services, "mount": mount, "actual_source": actual_source,
        "configured_source": configured_source, "config_ok": config_ok,
        "expected_root": expected_root, "expected_source": expected_source,
        "scope_ok": bool(expected and expected_root and root == expected_root and actual_source == expected),
        "warnings": warnings,
    }


def logs(name: str, lines: int = 80) -> dict[str, object]:
    if name not in UNITS or not 1 <= lines <= 200:
        raise ValueError("invalid_producer_or_limit")
    try:
        output = _run([
            "journalctl", "--unit", UNITS[name], "--lines", str(lines),
            "--no-pager", "--output=short-iso", "--quiet",
        ], timeout=5)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return {"producer": name, "lines": [], "error": "journal_unavailable"}
    return {"producer": name, "lines": output[-65536:].splitlines(), "error": None}
