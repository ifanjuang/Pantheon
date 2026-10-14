#!/usr/bin/env python3
"""Verify that Pantheon Next does not regain a second executable cockpit.

The check is intentionally narrow. It validates the explicit retained inventory
under ``docs/assets/pantheon-control`` and the orientation-only entry page. The
current candidate Cockpit lives under the bounded ``implementation/`` zone; this
orientation directory must not become a second product surface or point current
ownership back to the historical ``pantheon-mvp`` repository.

It is not a generic policy scanner and it does not inspect or contact any runtime.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL_REL = Path("docs/assets/pantheon-control")

ALLOWED_CONTROL_FILES = {
    Path("README.md"),
    Path("index.html"),
    Path("hermes-modules.html"),
    Path("hermes-modules-demo.json"),
    Path("hermes-preview/demo-sdk.js"),
    Path("hermes-preview/demo-shell.css"),
    Path("hermes-preview/plugin-index.js"),
    Path("hermes-preview/plugin-style.css"),
    Path("installations-data.js"),
    Path("installations-ui.js"),
    Path("backup-verify.js"),
    Path("update-verify.js"),
    Path("exposure-verify.js"),
    Path("observability-verify.js"),
    Path("card_revision_proposal_lifecycle.md"),
}

RETIRED_PRODUCT_PATHS = {
    Path("dashboard"),
    Path("docs/assets/architecture-mvp"),
    Path("examples/architecture/mvp_dossier_fictif"),
}


class OrientationParser(HTMLParser):
    """Collect executable resource references from the orientation page."""

    def __init__(self) -> None:
        super().__init__()
        self.executable_refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "script" and values.get("src"):
            self.executable_refs.append(f"script:{values['src']}")
        if tag == "link" and "stylesheet" in values.get("rel", "").lower() and values.get("href"):
            self.executable_refs.append(f"stylesheet:{values['href']}")
        if tag in {"iframe", "embed"} and values.get("src"):
            self.executable_refs.append(f"{tag}:{values['src']}")
        if tag == "object" and values.get("data"):
            self.executable_refs.append(f"object:{values['data']}")


def check(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    control = root / CONTROL_REL

    for retired in sorted(RETIRED_PRODUCT_PATHS, key=str):
        if (root / retired).exists():
            findings.append(f"retired product path exists: {retired.as_posix()}")

    if not control.is_dir():
        findings.append(f"required orientation directory missing: {CONTROL_REL.as_posix()}")
        return findings

    actual = {
        path.relative_to(control)
        for path in control.rglob("*")
        if path.is_file()
    }
    for missing in sorted(ALLOWED_CONTROL_FILES - actual, key=str):
        findings.append(f"required retained boundary artifact missing: {missing.as_posix()}")
    for unexpected in sorted(actual - ALLOWED_CONTROL_FILES, key=str):
        findings.append(f"unexpected cockpit asset: {unexpected.as_posix()}")

    index = control / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        parser = OrientationParser()
        parser.feed(html)
        for ref in parser.executable_refs:
            findings.append(f"orientation page loads executable resource: {ref}")
        lowered = html.lower()
        if "implementation/" not in lowered:
            findings.append("orientation page does not name the co-located implementation cockpit")
        if "pantheon-mvp" in lowered:
            findings.append("orientation page still names the historical pantheon-mvp repository as current cockpit")
        if "non-runtime" not in lowered:
            findings.append("orientation page does not state its non-runtime boundary")

    return findings


def main() -> int:
    findings = check()
    if findings:
        print("FAIL: Pantheon Next local-cockpit boundary was crossed:")
        for finding in findings:
            print(f"  - {finding}")
        return 1
    print("OK: no second executable cockpit is present in Pantheon Next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
