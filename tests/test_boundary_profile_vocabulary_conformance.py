"""The `Boundary profile:` line had an owner, a vocabulary and no enforcement.

`docs/governance/BOUNDARY_PROFILES.md` (active support doctrine) defines the
profiles. `docs/governance/STATUS_HEADER_RULES.md` (active support doctrine)
tells authors to write the line. Neither is checked anywhere, so seventeen
profile names that BOUNDARY_PROFILES.md does not define entered circulation —
including two near-misses of defined names (`validation_only` for
`validation_only_trace`, `candidate_support_doctrine` for
`candidate_support_note`) and six free-form phrases.

That matters now rather than in the abstract: Pantheon-Next#996 migrates 112 documents onto
this vocabulary. Migrating onto an unenforced vocabulary is how the drift got
here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "docs" / "governance" / "BOUNDARY_PROFILES.md"

DECLARATION = "Boundary profile:"

# The documented placeholder in the authoring rule and in the owner's own
# examples. It is a template slot, not a profile name.
PLACEHOLDER = "<profile_name>"

# ai_logs are dated intervention traces. A past entry's declared profile is part
# of what that intervention recorded about itself; rewriting it would edit the
# trace. They are counted (27 non-conforming declarations at the time of
# writing) and deliberately not governed by this test.
EXCLUDED_PREFIXES = ("ai_logs/", ".git/")
EXCLUDED_SUBSTRINGS = ("/build/",)

# Empty since Pantheon-Next#1000 reconciled the vocabulary: every live declaration now names a
# profile BOUNDARY_PROFILES.md defines. The ratchet stays as the floor — a new
# undefined name fails `unexpected` immediately, with no seeded debt to hide in.
KNOWN_UNDEFINED_PROFILE_DECLARATIONS: set[tuple[str, str]] = set()


def _defined_profiles() -> set[str]:
    """Read the vocabulary from the owner rather than restating it here.

    Defining a new profile in BOUNDARY_PROFILES.md therefore admits it with no
    test change, which is the point: the owner stays the owner.
    """
    profiles = set()
    for line in OWNER.read_text(encoding="utf-8").splitlines():
        if line.startswith("### `") and line.endswith("`"):
            profiles.add(line[len("### `") : -1])
    return profiles


def _declarations() -> set[tuple[str, str]]:
    found = set()
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(EXCLUDED_PREFIXES) or any(s in rel for s in EXCLUDED_SUBSTRINGS):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith(DECLARATION):
                continue
            value = line[len(DECLARATION) :].strip().rstrip(".").strip("`").strip()
            if value and value != PLACEHOLDER:
                found.add((rel, value))
    return found


def test_the_owner_still_defines_a_vocabulary():
    """Guards the parser above: a silent parse failure would empty the check."""
    defined = _defined_profiles()
    assert "validation_only_trace" in defined
    assert "candidate_support_note" in defined
    assert len(defined) >= 7


def test_declared_boundary_profiles_are_defined_by_their_owner():
    """A declared profile must be one BOUNDARY_PROFILES.md defines.

    Seeded with what exists so CI stays green and no document is forced to
    change, then ratcheted in both directions: `unexpected` refuses any new
    undefined name, and `no_longer_present` forces an entry out of the list as
    soon as it is reconciled — whether by correcting the document or by
    defining the profile in the owner, which admits it automatically.
    """
    defined = _defined_profiles()
    undefined = {(path, value) for path, value in _declarations() if value not in defined}

    unexpected = undefined - KNOWN_UNDEFINED_PROFILE_DECLARATIONS
    no_longer_present = KNOWN_UNDEFINED_PROFILE_DECLARATIONS - undefined

    assert unexpected == set(), (
        "a document declares a boundary profile BOUNDARY_PROFILES.md does not define; "
        "use a defined profile, or define the new one in the owner first"
    )
    assert no_longer_present == set(), (
        "a listed declaration is reconciled — remove it from "
        "KNOWN_UNDEFINED_PROFILE_DECLARATIONS so the remaining debt stays exact"
    )
