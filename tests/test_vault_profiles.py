from __future__ import annotations

import json
from pathlib import Path

import pytest

from implementation.workspace_cockpit.vault_profiles import load_vault_configuration


def _config(tmp_path: Path) -> dict:
    return {
        "schema_version": 1,
        "settle_observations": 2,
        "vaults": [
            {
                "name": "Affaires",
                "root": str(tmp_path / "affaires"),
                "mount_root": str(tmp_path),
                "bank_id": "PROJECTS",
                "source_kind": "kroqui-sync",
                "metadata_profile": "affaires",
                "max_depth": 8,
            },
            {
                "name": "Bibliotheque",
                "root": str(tmp_path / "library"),
                "mount_root": str(tmp_path),
                "bank_id": "KNOWLEDGE",
                "source_kind": "library-sync",
                "metadata_profile": "bibliotheque",
                "max_depth": 1,
            },
        ],
    }


def test_profile_loader_keeps_each_vault_configuration_separate(tmp_path: Path) -> None:
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(_config(tmp_path), ensure_ascii=False), encoding="utf-8")
    config = load_vault_configuration(path)
    assert [profile.name for profile in config.vaults] == ["Affaires", "Bibliotheque"]
    assert [profile.bank_id for profile in config.vaults] == ["PROJECTS", "KNOWLEDGE"]
    assert [profile.metadata_profile for profile in config.vaults] == ["affaires", "bibliotheque"]
    assert [profile.max_depth for profile in config.vaults] == [8, 1]
    assert config.missing_source_grace_seconds == 86400


def test_profile_loader_validates_missing_source_grace_period(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    payload["missing_source_grace_seconds"] = 3600
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert load_vault_configuration(path).missing_source_grace_seconds == 3600

    payload["missing_source_grace_seconds"] = -1
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="missing_source_grace_seconds"):
        load_vault_configuration(path)


def test_profile_loader_validates_required_mount_contains_vault_root(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    payload["vaults"][0]["mount_root"] = str(tmp_path)
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    config = load_vault_configuration(path)

    assert config.vaults[0].mount_root == tmp_path.resolve()
    assert config.vaults[1].mount_root == tmp_path.resolve()

    payload["vaults"][0]["mount_root"] = str(tmp_path / "outside")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="inside mount_root"):
        load_vault_configuration(path)

    payload = _config(tmp_path)
    payload["vaults"][0].pop("mount_root")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="mount_root"):
        load_vault_configuration(path)


def test_project_overview_prompt_is_opt_in_and_keeps_project_placeholder(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    payload["vaults"][0]["project_overview_prompt"] = "Aperçu de {project}: faits et sources."
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    config = load_vault_configuration(path)
    assert config.vaults[0].project_overview_prompt == "Aperçu de {project}: faits et sources."
    assert config.vaults[1].project_overview_prompt is None


def test_profile_loader_rejects_project_prompt_without_project_placeholder(tmp_path: Path) -> None:
    payload = _config(tmp_path)
    payload["vaults"][0]["project_overview_prompt"] = "Résumé général du projet."
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="project_overview_prompt"):
        load_vault_configuration(path)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda value: value["vaults"][1].update(bank_id=value["vaults"][0]["bank_id"]), "unique"),
        (lambda value: value["vaults"][1].update(root=value["vaults"][0]["root"] + "/nested"), "duplicate vault root"),
        (lambda value: value["vaults"][1].update(metadata_profile="unknown"), "metadata_profile"),
        (lambda value: value["vaults"][1].update(max_depth=0), "max_depth"),
    ],
)
def test_profile_loader_rejects_ambiguous_or_unsupported_settings(tmp_path: Path, mutate, message: str) -> None:
    payload = _config(tmp_path)
    mutate(payload)
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_vault_configuration(path)
