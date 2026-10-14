"""Every reviewed pin a deployment script demands must exist in `release.env`.

The Ubuntu node scripts read their pins as `${RELEASE_X:?release.env missing
RELEASE_X}`. Under `set -Eeuo pipefail` an undefined name is not a warning: the
script dies on its first line, before any action. Three such names remain
undefined in the optional Docling configurator:

    configure-docling-local          RELEASE_DOCLING_VERSION
                                     RELEASE_DOCLING_MCP_VERSION
                                     RELEASE_DOCLING_PYTHON

Nothing checked the two halves against each other, so the gap was invisible
until a script was actually run on a machine.

`release.env` carries *reviewed* deployment targets. A value invented to make
this test pass would assert a review that never happened -- and a wrong CUDA
pin breaks a real node. So the three names below are recorded as debt rather than
filled in: the ratchet is the floor, and it only shrinks. Adding a reviewed
value to `release.env` and deleting its line here is the whole retirement path.
A *new* undefined name fails immediately, with no seeded debt to hide in.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT = ROOT / "deployment" / "ubuntu"
RELEASE_LOCK = DEPLOYMENT / "release.env"

REQUIRED = re.compile(r"\$\{(RELEASE_[A-Z0-9_]+):\?")
DEFINED = re.compile(r"^(RELEASE_[A-Z0-9_]+)=", re.MULTILINE)

# Shrink-only. Each entry is a pin a script demands and `release.env` does not
# carry. Removing an entry requires adding the reviewed value, not deleting the
# requirement. Never add to this set.
KNOWN_UNDEFINED_RELEASE_PINS = {
    "RELEASE_DOCLING_MCP_VERSION",
    "RELEASE_DOCLING_PYTHON",
    "RELEASE_DOCLING_VERSION",
}


def _required_pins() -> set[str]:
    found: set[str] = set()
    for path in sorted(DEPLOYMENT.iterdir()):
        if path.is_file():
            found.update(REQUIRED.findall(path.read_text(encoding="utf-8")))
    return found


def _defined_pins() -> set[str]:
    return set(DEFINED.findall(RELEASE_LOCK.read_text(encoding="utf-8")))


def test_no_new_release_pin_is_demanded_without_being_defined() -> None:
    missing = _required_pins() - _defined_pins()
    unexpected = sorted(missing - KNOWN_UNDEFINED_RELEASE_PINS)
    assert not unexpected, (
        "deployment scripts demand reviewed pins that release.env does not "
        f"define: {unexpected}. Add the reviewed value to "
        "deployment/ubuntu/release.env -- these scripts abort on their first "
        "line without it."
    )


def test_the_known_gap_only_shrinks() -> None:
    missing = _required_pins() - _defined_pins()
    resolved = sorted(KNOWN_UNDEFINED_RELEASE_PINS - missing)
    assert not resolved, (
        f"release.env now defines {resolved}; remove them from "
        "KNOWN_UNDEFINED_RELEASE_PINS so the floor keeps falling."
    )


def test_every_defined_pin_is_actually_consumed() -> None:
    """A pin nobody reads is a stale reviewed target, not a safety margin."""
    # RELEASE_SCHEMA identifies the file format itself rather than a target.
    unread = sorted(_defined_pins() - _required_pins() - {"RELEASE_SCHEMA"})
    assert not unread, f"release.env defines pins no script reads: {unread}"
