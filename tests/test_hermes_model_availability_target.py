from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs" / "install" / "HERMES_MODEL_AVAILABILITY_TARGET.md"
RELEASE = ROOT / "deployment" / "ubuntu" / "release.env"


def test_model_availability_target_uses_native_hermes_fallback() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert "qwen3.5:27b" in text
    assert "qwen3.5:9b" in text
    assert "fallback_providers" in text
    assert "PAIR node selection" in text
    assert "Do not add a Pantheon model router" in text


def test_target_preserves_linux_baseline_and_pc00_optional_quality_tier() -> None:
    text = TARGET.read_text(encoding="utf-8")
    assert "Linux — always available" in text
    assert "AFFAIRES producer" in text
    assert "Hindsight" in text
    assert "CLM" in text
    assert "gpu-node — quality tier" in text
    assert "not become a prerequisite" in text


def test_selected_hermes_release_remains_runtime_pin_not_model_policy() -> None:
    release = RELEASE.read_text(encoding="utf-8")
    image = next(
        line.split("=", 1)[1]
        for line in release.splitlines()
        if line.startswith("RELEASE_HERMES_IMAGE=")
    )
    assert image.startswith("nousresearch/hermes-agent:v")
    cockpit_dockerfile = ROOT / "implementation" / "workspace_cockpit" / "Dockerfile"
    assert f"ARG HERMES_IMAGE={image}" in cockpit_dockerfile.read_text(encoding="utf-8")
    assert "qwen3.5:27b" not in release
    assert "qwen3.5:9b" not in release
