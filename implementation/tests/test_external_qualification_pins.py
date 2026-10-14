from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

IMPLEMENTATION = Path(__file__).resolve().parents[1]
ROOT = IMPLEMENTATION.parent
if str(IMPLEMENTATION) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION))

from tools.export_external_qualification_pins import REGISTRY, selected_exports

CANDIDATE_HERMES_LOCK = ROOT / "implementation" / "hermes" / "distribution" / "pantheon-standard.lock.yaml"
HISTORICAL_ACTIVE_PATHS = {
    ROOT / ".github" / "workflows" / "implementation-hindsight-obsidian-hermes-o3-lab.yml",
    ROOT / "implementation" / "tools" / "run_hindsight_obsidian_hermes_o3.sh",
    ROOT / "implementation" / "tests" / "test_hindsight_obsidian_hermes_o3_contract.py",
}


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_external_pin_registry_is_bounded_and_non_authoritative() -> None:
    data = _registry()
    assert data["schema_id"] == "pantheon.external_qualification_pins"
    assert data["revision"] == 1
    assert data["authority"] == {
        "deployment_truth": False,
        "installation_state": False,
        "runtime_activation": False,
        "task_authorization": False,
        "evidence_admission": False,
    }

    pins = data["pins"]
    assert set(pins) >= {
        "hermes-agent",
        "hindsight",
        "hindsight-obsidian-sync",
        "obsidian-desktop",
        "mnemosyne-memory",
        "mnemosyne-hermes",
    }

    prefixes = [pin["env_prefix"] for pin in pins.values()]
    assert len(prefixes) == len(set(prefixes))
    assert all(re.fullmatch(r"[A-Z][A-Z0-9_]*", prefix) for prefix in prefixes)

    assert pins["hermes-agent"].get("tracking_policy") == "follow_latest_stable"
    assert pins["hermes-agent"].get("release_tag") == "v2026.9.14"

    allowed_tracking_policies = {"reviewed_pin", "follow_latest_stable"}
    for pin_id, pin in pins.items():
        assert pin.get("tracking_policy", "reviewed_pin") in allowed_tracking_policies, pin_id

        if pin.get("tracking_policy") == "follow_latest_stable":
            assert isinstance(pin.get("release_tag"), str) and pin["release_tag"], pin_id

    for pin_id, pin in pins.items():
        assert isinstance(pin["version"], str) and pin["version"]
        if pin["kind"] == "git":
            assert re.fullmatch(r"[0-9a-f]{40}", pin["ref"]), pin_id
            assert re.fullmatch(r"[^/\s]+/[^/\s]+", pin["repository"]), pin_id
        if pin["kind"] == "container":
            assert isinstance(pin["image"], str) and pin["image"], pin_id
            digest = pin.get("digest")
            assert digest is None or re.fullmatch(r"sha256:[0-9a-f]{64}", digest), pin_id
        source_pin = pin.get("source_pin")
        if source_pin is not None:
            assert source_pin in pins, (pin_id, source_pin)


def test_exporter_emits_registry_values_without_second_pin_authority() -> None:
    data = _registry()
    selected = [
        "hermes-agent",
        "hindsight",
        "hindsight-obsidian-sync",
        "obsidian-desktop",
        "harnessrouter",
    ]
    values = selected_exports(selected)

    for pin_id in selected:
        pin = data["pins"][pin_id]
        prefix = pin["env_prefix"]
        assert values[f"{prefix}_PIN_ID"] == pin_id
        for field, suffix in {
            "version": "VERSION",
            "ref": "REF",
            "repository": "REPOSITORY",
            "image": "IMAGE",
            "package": "PACKAGE",
            "source_pin": "SOURCE_PIN",
            "release_tag": "RELEASE_TAG",
            "protocol_version": "PROTOCOL_VERSION",
        }.items():
            if pin.get(field) is not None:
                assert values[f"{prefix}_{suffix}"] == str(pin[field])


def test_candidate_hermes_distribution_snapshot_tracks_current_runtime_pin() -> None:
    data = _registry()
    lock = yaml.safe_load(CANDIDATE_HERMES_LOCK.read_text(encoding="utf-8"))
    assert lock["status"] == "candidate"
    assert (
        lock["source_pins"]["hermes_runtime"]["version"]
        == data["pins"]["hermes-agent"]["version"]
    )


def _pin_literals(pin: dict) -> list[str]:
    literals = [pin["version"]]
    if pin.get("ref"):
        literals.append(pin["ref"])
    return literals


def _provider_markers(pin_id: str, pin: dict) -> set[str]:
    markers = {pin_id, pin["env_prefix"]}
    for field in ("repository", "package", "image"):
        value = pin.get(field)
        if value:
            markers.add(str(value))
    return markers


def _duplicated_pin_literals(data: dict, text: str) -> list[tuple[str, str]]:
    duplicates: list[tuple[str, str]] = []
    for pin_id, pin in data["pins"].items():
        if not any(marker in text for marker in _provider_markers(pin_id, pin)):
            continue
        for literal in _pin_literals(pin):
            if literal in text:
                duplicates.append((pin_id, literal))
    return duplicates


# The repository-relative roots this guard reads. Exposed as a module constant
# rather than hidden inside the function below because the reach is the point:
# `test_pin_guard_ci_coverage.py` reads it to prove the workflow that runs this
# suite is actually triggered by changes to every one of them.
QUALIFICATION_SOURCE_ROOTS = (
    ".github/workflows",
    "implementation/tools",
    "implementation/tests",
    "tests",
)


def _active_qualification_sources() -> list[Path]:
    roots = [ROOT / Path(root) for root in QUALIFICATION_SOURCE_ROOTS]
    suffixes = {".yml", ".yaml", ".py", ".sh", ".ts"}
    paths: list[Path] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in suffixes and path not in HISTORICAL_ACTIVE_PATHS:
                paths.append(path)
    return paths


def test_unrelated_semver_data_does_not_become_a_pin_dependency() -> None:
    data = {
        "pins": {
            "example-provider": {
                "env_prefix": "EXAMPLE_PROVIDER",
                "version": "9.8.7",
                "ref": "a" * 40,
                "repository": "example/provider",
            }
        }
    }
    text = 'payload = {"version": "9.8.7", "kind": "runtime_observation"}'
    assert _duplicated_pin_literals(data, text) == []


def test_provider_consumer_cannot_restate_its_current_pin() -> None:
    ref = "b" * 40
    data = {
        "pins": {
            "example-provider": {
                "env_prefix": "EXAMPLE_PROVIDER",
                "version": "7.6.5",
                "ref": ref,
                "repository": "example/provider",
            }
        }
    }
    text = f'pin_id = "example-provider"\nversion = "7.6.5"\nref = "{ref}"\n'
    assert _duplicated_pin_literals(data, text) == [
        ("example-provider", "7.6.5"),
        ("example-provider", ref),
    ]


def test_active_qualification_code_does_not_duplicate_current_pin_literals() -> None:
    """A provider consumer must import its current pin instead of restating it.

    Version strings are not globally unique identifiers: ordinary tests may
    legitimately contain the same short semantic version as an unrelated
    provider. The guard therefore applies a provider's literals only to files
    that actually name that provider by pin id, env prefix, repository, package
    or image. This keeps the registry canonical without turning coincidental
    application/test data into a qualification dependency.
    """

    data = _registry()
    for path in _active_qualification_sources():
        if path == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        duplicates = _duplicated_pin_literals(data, text)
        assert not duplicates, (
            f"{path} duplicates canonical current pins: "
            + ", ".join(f"{pin_id}={literal}" for pin_id, literal in duplicates)
        )
