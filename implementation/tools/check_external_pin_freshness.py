#!/usr/bin/env python3
"""Observe whether upstream has moved since each external pin was last reviewed.

`external-pins.json` records which external artifact each qualification targets.
Nothing compares it to upstream, so a pin can silently fall behind: at the time
this tool was written, three of ten pins had — `self-hosted-livesync` by three
releases, on a version whose successor fixes behaviour under the exact Obsidian
release pinned beside it.

Dependabot cannot cover this. It watches `pip` and `github-actions`; the pins are
git refs, container images and releases in a repository-specific registry.

This tool observes. It never bumps a pin, opens a pull request, installs,
activates or authorizes anything. It reports two distinct signals as data:

```text
observation_stale  -> upstream released something after we last looked;
                      the observation record must be refreshed by a human look
unacknowledged_lag -> we recorded a newer upstream release and never decided
                      whether to move, stay, or why
```

An acknowledged lag is a legitimate, final state. Recording "we know a newer
release exists and we stay where we are because …", with a date, closes the
signal. That is the operational form of an invariant this repository already
states:

```text
update_available != update_authorized
observed != adopted
pin selected != pin current
```

No current pin version is quoted anywhere in this file. Pin values live in the
registry alone — `test_external_qualification_pins.py` enforces that, and a
freshness tool that hard-coded the versions it audits would be the first thing
to drift.

Usage:

    check_external_pin_freshness.py                  # fetch upstream, compare
    check_external_pin_freshness.py --offline        # compare recorded state only
    check_external_pin_freshness.py --format json
    check_external_pin_freshness.py --observed-json f.json   # inject observations
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

QUALIFICATION = Path(__file__).resolve().parents[1] / "qualification"
REGISTRY = QUALIFICATION / "external-pins.json"
OBSERVATIONS = QUALIFICATION / "external-upstream-observations.json"

REGISTRY_SCHEMA = "pantheon.external_qualification_pins"
OBSERVATIONS_SCHEMA = "pantheon.external_upstream_observations"

# Sources a pin's upstream head can be read from. `derived` and `not_observable`
# are honest terminal answers, not gaps to be filled with a guess.
FETCHABLE_SOURCES = {"github_releases_latest", "pypi_latest", "dockerhub_latest_semver"}
DECLARED_SOURCES = FETCHABLE_SOURCES | {"derived_from_source_pin", "not_observable"}

_TIMEOUT = 20


class FreshnessError(RuntimeError):
    """The registry or the observation record is structurally unusable."""


def load_json(path: Path, expected_schema: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_id") != expected_schema:
        raise FreshnessError(f"{path.name}: expected schema {expected_schema!r}")
    return data


# --------------------------------------------------------------------------
# Fetching. Isolated so that comparison stays pure and testable offline.
# --------------------------------------------------------------------------


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "pantheon-pin-freshness"}
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_upstream_head(source: str, locator: str) -> str:
    """Return the upstream head identifier for one observable pin."""
    if source == "github_releases_latest":
        return str(_get_json(f"https://api.github.com/repos/{locator}/releases/latest")["tag_name"])
    if source == "pypi_latest":
        return str(_get_json(f"https://pypi.org/pypi/{locator}/json")["info"]["version"])
    if source == "dockerhub_latest_semver":
        # An image pin's upstream head is the registry, not a source repository:
        # apache/couchdb publishes no GitHub releases at all, so the tag list is
        # the only authoritative answer for the artifact actually referenced.
        payload = _get_json(
            f"https://hub.docker.com/v2/repositories/{locator}/tags"
            "?page_size=100&ordering=last_updated"
        )
        semver = [
            tag["name"]
            for tag in payload.get("results", [])
            if re.fullmatch(r"\d+\.\d+\.\d+", tag.get("name", ""))
        ]
        if not semver:
            raise FreshnessError(f"no semantic tag found for image {locator!r}")
        return max(set(semver), key=lambda s: [int(part) for part in s.split(".")])
    raise FreshnessError(f"source {source!r} is not fetchable")


def observe_all(observations: dict[str, Any]) -> dict[str, str]:
    """Fetch the current upstream head for every fetchable pin.

    A network failure for one pin is reported for that pin only. One unreachable
    host must not erase the signal for the other nine.
    """
    heads: dict[str, str] = {}
    for pin_id, record in sorted(observations["observations"].items()):
        source = record["source"]
        if source not in FETCHABLE_SOURCES:
            continue
        try:
            heads[pin_id] = fetch_upstream_head(source, record["locator"])
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
            heads[pin_id] = f"__unreachable__:{type(exc).__name__}"
    return heads


# --------------------------------------------------------------------------
# Comparison. Pure: the tests exercise this with injected data, never network.
# --------------------------------------------------------------------------


def compare(
    registry: dict[str, Any],
    observations: dict[str, Any],
    fetched_heads: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return the freshness report for the recorded and observed state."""
    fetched_heads = fetched_heads or {}
    pins = registry["pins"]
    records = observations["observations"]

    missing = sorted(set(pins) - set(records))
    if missing:
        raise FreshnessError(
            "every pin needs an upstream-observation record so its freshness is "
            f"answerable; missing: {missing}"
        )
    orphaned = sorted(set(records) - set(pins))
    if orphaned:
        raise FreshnessError(f"observation records describe pins that no longer exist: {orphaned}")

    rows: list[dict[str, Any]] = []
    for pin_id in sorted(pins):
        record = records[pin_id]
        source = record["source"]
        if source not in DECLARED_SOURCES:
            raise FreshnessError(f"{pin_id}: unknown observation source {source!r}")

        delta = record["delta"]
        acknowledged = isinstance(delta, dict) and delta.get("state") == "acknowledged"
        head = fetched_heads.get(pin_id)

        if head is None:
            observation_state = "not_fetched"
        elif head.startswith("__unreachable__"):
            observation_state = "unreachable"
        elif head == record["latest_seen"]:
            observation_state = "current"
        else:
            observation_state = "observation_stale"

        tracking_policy = pins[pin_id].get("tracking_policy", "reviewed_pin")
        selected_release = pins[pin_id].get("release_tag")
        if tracking_policy == "follow_latest_stable" and not selected_release:
            raise FreshnessError(
                f"{pin_id}: follow_latest_stable requires release_tag in the pin registry"
            )

        if source == "derived_from_source_pin":
            # Its freshness question belongs to the pin it follows; reporting a
            # lag here would double-count that pin's signal.
            signal = "derived"
        elif observation_state == "unreachable":
            # An earlier version fell through to `aligned` here. That was wrong:
            # once the open lags are decided, a total upstream outage would leave
            # `actionable` empty and let the scheduled run report success having
            # observed nothing. Not observing is its own outcome, and it is
            # neither drift nor alignment.
            signal = "unreachable"
        elif observation_state == "observation_stale":
            signal = "observation_stale"
        elif (
            tracking_policy == "follow_latest_stable"
            and record["latest_seen"] != selected_release
        ):
            signal = "required_update_pending"
        elif delta == "none":
            signal = "aligned"
        elif acknowledged and tracking_policy == "follow_latest_stable":
            signal = "required_update_pending"
        elif acknowledged:
            signal = "acknowledged_lag"
        else:
            signal = "unacknowledged_lag"

        rows.append(
            {
                "pin": pin_id,
                "pinned_version": pins[pin_id]["version"],
                "latest_seen": record["latest_seen"],
                "observed_on": record["observed_on"],
                "upstream_head_now": head,
                "source": source,
                "tracking_policy": tracking_policy,
                "selected_release": selected_release,
                "signal": signal,
                "note": delta.get("reason") if isinstance(delta, dict) else None,
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["signal"]] = counts.get(row["signal"], 0) + 1

    return {
        "schema_id": "pantheon.external_pin_freshness_report",
        "rows": rows,
        "counts": counts,
        "actionable": sorted(
            row["pin"]
            for row in rows
            if row["signal"]
            in {"observation_stale", "unacknowledged_lag", "required_update_pending"}
        ),
        # Kept apart from `actionable` on purpose: an unreachable host is not a
        # drift claim about the pin, and must not be reported as one. It is a
        # failure to observe, which the run reports on its own terms.
        "unobserved": sorted(row["pin"] for row in rows if row["signal"] == "unreachable"),
        "authority": {
            "deployment_truth": False,
            "installation_state": False,
            "update_authorization": False,
            "task_authorization": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# External pin freshness observation",
        "",
        "Observation only. No pin was changed, and nothing here authorizes an update.",
        "",
        "| Pin | Pinned | Last seen upstream | Upstream now | Signal | Note |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            "| {pin} | `{pinned}` | `{seen}` ({on}) | `{now}` | {signal} | {note} |".format(
                pin=row["pin"],
                pinned=row["pinned_version"],
                seen=row["latest_seen"],
                on=row["observed_on"],
                now=row["upstream_head_now"] or "not fetched",
                signal=row["signal"],
                note=row["note"] or "",
            )
        )
    lines += ["", "```text", "update_available != update_authorized", "```"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--offline", action="store_true", help="compare recorded state only")
    parser.add_argument("--observed-json", type=Path, help="inject upstream heads instead of fetching")
    parser.add_argument(
        "--structure-only",
        action="store_true",
        help=(
            "answer only whether the registry and the observation record are "
            "consistent and comparable; do not report a pin needing a human look "
            "as a failure"
        ),
    )
    args = parser.parse_args(argv)

    registry = load_json(REGISTRY, REGISTRY_SCHEMA)
    observations = load_json(OBSERVATIONS, OBSERVATIONS_SCHEMA)

    if args.observed_json is not None:
        heads = json.loads(args.observed_json.read_text(encoding="utf-8"))
    elif args.offline:
        heads = {}
    else:
        heads = observe_all(observations)

    report = compare(registry, observations, heads)
    text = json.dumps(report, indent=2) if args.format == "json" else render_markdown(report)

    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)

    if args.structure_only:
        # Two different questions share this tool, and only one of them is a
        # pull-request concern. "Are the records consistent and comparable?" must
        # stay answerable while pins legitimately lag: an undecided lag is a
        # standing state for a human, not a defect in the diff under review.
        return 0

    fetched = args.observed_json is not None or not args.offline
    if fetched and report["unobserved"]:
        print(
            "\nupstream could not be read for: " + ", ".join(report["unobserved"])
            + "\nthis run observed nothing for those pins; it is not a clean freshness result",
            file=sys.stderr,
        )
        return 1

    if report["actionable"]:
        print(
            "\nactionable pins (a human look is required, not an automatic bump): "
            + ", ".join(report["actionable"]),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
