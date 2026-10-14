"""Keep the pin-freshness observation honest and keep it wired to the registry.

`external-pins.json` records which external artifact each qualification targets,
and until now nothing compared it to upstream. Dependabot cannot: it watches
`pip` and `github-actions`, while the pins are git refs, container images and
releases in a repository-specific registry. Three of ten pins had drifted
unnoticed when this check was written.

These tests exercise the comparison only. They never reach the network: upstream
heads are injected, so the suite stays deterministic and offline. Fetching lives
behind `observe_all` and is exercised by the scheduled workflow, not here.

```text
observation refreshed != pin moved
update_available != task_authorized

A pin with `tracking_policy=follow_latest_stable` is different: a newer stable
release keeps the freshness signal actionable until the qualification pin moves.
```
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

IMPLEMENTATION = Path(__file__).resolve().parents[1]
if str(IMPLEMENTATION) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION))

from tools.check_external_pin_freshness import (  # noqa: E402
    DECLARED_SOURCES,
    FETCHABLE_SOURCES,
    OBSERVATIONS,
    OBSERVATIONS_SCHEMA,
    REGISTRY,
    REGISTRY_SCHEMA,
    FreshnessError,
    compare,
    load_json,
    main,
)


@pytest.fixture()
def registry() -> dict:
    return load_json(REGISTRY, REGISTRY_SCHEMA)


@pytest.fixture()
def observations() -> dict:
    return load_json(OBSERVATIONS, OBSERVATIONS_SCHEMA)


# --------------------------------------------------------------------------
# The observation record must stay wired to the registry it describes.
# --------------------------------------------------------------------------


def test_every_pin_has_an_upstream_observation_record(registry, observations) -> None:
    missing = sorted(set(registry["pins"]) - set(observations["observations"]))
    assert not missing, (
        "a pin with no observation record has an unanswerable freshness question; "
        f"add one to external-upstream-observations.json: {missing}"
    )


def test_no_observation_describes_a_pin_that_was_removed(registry, observations) -> None:
    orphaned = sorted(set(observations["observations"]) - set(registry["pins"]))
    assert not orphaned, f"observation records outlived their pins: {orphaned}"


def test_observation_records_are_structurally_complete(observations) -> None:
    for pin_id, record in observations["observations"].items():
        assert record["source"] in DECLARED_SOURCES, (pin_id, record["source"])
        assert record["locator"], pin_id
        assert record["latest_seen"], pin_id
        assert record["observed_on"], pin_id

        delta = record["delta"]
        if delta == "none":
            continue
        assert isinstance(delta, dict), pin_id
        assert delta["state"] in {"open", "acknowledged"}, (pin_id, delta["state"])
        assert delta["reason"].strip(), (
            f"{pin_id}: a recorded lag must say why it exists; an unexplained lag "
            "is the state this file was created to remove"
        )
        if delta["state"] == "acknowledged":
            assert delta["decided_on"], (
                f"{pin_id}: an acknowledged lag is a dated human decision, not a "
                "standing exemption"
            )


def test_follow_latest_stable_pins_cannot_record_acknowledged_lag(
    registry, observations
) -> None:
    for pin_id, pin in registry["pins"].items():
        if pin.get("tracking_policy") != "follow_latest_stable":
            continue
        delta = observations["observations"][pin_id]["delta"]
        assert not (
            isinstance(delta, dict) and delta.get("state") == "acknowledged"
        ), f"{pin_id}: follow_latest_stable cannot be closed as an acknowledged lag"


def test_the_observation_record_claims_no_authority(observations) -> None:
    assert observations["authority"] == {
        "deployment_truth": False,
        "installation_state": False,
        "runtime_activation": False,
        "update_authorization": False,
        "task_authorization": False,
        "evidence_admission": False,
    }


# --------------------------------------------------------------------------
# Comparison behaviour, on injected upstream heads.
# --------------------------------------------------------------------------


def _minimal() -> tuple[dict, dict]:
    registry = {
        "schema_id": REGISTRY_SCHEMA,
        "pins": {"thing": {"kind": "git", "version": "1.0.0"}},
    }
    observations = {
        "schema_id": OBSERVATIONS_SCHEMA,
        "observations": {
            "thing": {
                "source": "github_releases_latest",
                "locator": "org/thing",
                "latest_seen": "v1.0.0",
                "observed_on": "2026-08-31",
                "delta": "none",
            }
        },
    }
    return registry, observations


def test_an_aligned_pin_is_not_actionable() -> None:
    registry, observations = _minimal()
    report = compare(registry, observations, {"thing": "v1.0.0"})
    assert report["rows"][0]["signal"] == "aligned"
    assert report["actionable"] == []


def test_a_new_upstream_release_makes_the_observation_stale() -> None:
    registry, observations = _minimal()
    report = compare(registry, observations, {"thing": "v1.1.0"})
    assert report["rows"][0]["signal"] == "observation_stale"
    assert report["actionable"] == ["thing"]


def test_an_undecided_recorded_lag_is_actionable() -> None:
    registry, observations = _minimal()
    observations["observations"]["thing"]["delta"] = {"state": "open", "reason": "not reviewed"}
    report = compare(registry, observations, {"thing": "v1.0.0"})
    assert report["rows"][0]["signal"] == "unacknowledged_lag"
    assert report["actionable"] == ["thing"]


def test_a_dated_decision_closes_the_signal_without_moving_the_pin() -> None:
    registry, observations = _minimal()
    observations["observations"]["thing"]["delta"] = {
        "state": "acknowledged",
        "reason": "staying deliberately",
        "decided_on": "2026-08-31",
    }
    report = compare(registry, observations, {"thing": "v1.0.0"})
    assert report["rows"][0]["signal"] == "acknowledged_lag"
    assert report["actionable"] == []
    assert registry["pins"]["thing"]["version"] == "1.0.0"


def test_follow_latest_stable_cannot_close_lag_by_acknowledgement() -> None:
    registry, observations = _minimal()
    registry["pins"]["thing"]["tracking_policy"] = "follow_latest_stable"
    registry["pins"]["thing"]["release_tag"] = "v1.0.0"
    observations["observations"]["thing"]["latest_seen"] = "v1.1.0"
    observations["observations"]["thing"]["delta"] = {
        "state": "acknowledged",
        "reason": "temporary compatibility concern",
        "decided_on": "2026-08-31",
    }

    report = compare(registry, observations, {"thing": "v1.1.0"})

    assert report["rows"][0]["tracking_policy"] == "follow_latest_stable"
    assert report["rows"][0]["selected_release"] == "v1.0.0"
    assert report["rows"][0]["signal"] == "required_update_pending"
    assert report["actionable"] == ["thing"]


def test_follow_latest_stable_detects_pin_lag_even_if_delta_says_none() -> None:
    registry, observations = _minimal()
    registry["pins"]["thing"]["tracking_policy"] = "follow_latest_stable"
    registry["pins"]["thing"]["release_tag"] = "v1.0.0"
    observations["observations"]["thing"]["latest_seen"] = "v1.1.0"
    observations["observations"]["thing"]["delta"] = "none"

    report = compare(registry, observations, {"thing": "v1.1.0"})

    assert report["rows"][0]["signal"] == "required_update_pending"
    assert report["actionable"] == ["thing"]


def test_follow_latest_stable_requires_a_selected_release_tag() -> None:
    registry, observations = _minimal()
    registry["pins"]["thing"]["tracking_policy"] = "follow_latest_stable"

    with pytest.raises(FreshnessError, match="requires release_tag"):
        compare(registry, observations, {"thing": "v1.0.0"})


def test_an_unreachable_host_does_not_read_as_aligned() -> None:
    """This test previously asserted the opposite of its own name.

    It claimed an unreachable host would not silently read as aligned, and then
    asserted `signal == "aligned"`. A review caught it. The consequence was real:
    once the open lags are decided, a total upstream outage would leave
    `actionable` empty and let the scheduled run report success having observed
    nothing at all.
    """
    registry, observations = _minimal()
    report = compare(registry, observations, {"thing": "__unreachable__:URLError"})

    assert report["rows"][0]["upstream_head_now"].startswith("__unreachable__")
    assert report["rows"][0]["signal"] == "unreachable"
    # Not a drift claim about the pin — kept out of `actionable` — but reported.
    assert report["actionable"] == []
    assert report["unobserved"] == ["thing"]


def test_a_fetching_run_that_observed_nothing_is_not_green(tmp_path, capsys) -> None:
    """The failure mode the review named: green while nothing was observed."""
    heads = tmp_path / "heads.json"
    registry = load_json(REGISTRY, REGISTRY_SCHEMA)
    observations = load_json(OBSERVATIONS, OBSERVATIONS_SCHEMA)
    fetchable = [
        pin for pin, record in observations["observations"].items()
        if record["source"] in FETCHABLE_SOURCES
    ]
    heads.write_text(
        json.dumps({pin: "__unreachable__:URLError" for pin in fetchable}), encoding="utf-8"
    )

    assert registry  # the real registry is what the workflow compares
    assert main(["--observed-json", str(heads), "--format", "json"]) == 1
    capsys.readouterr()


def test_offline_is_not_reported_as_unobserved() -> None:
    """Not fetching on purpose is a different state from failing to fetch."""
    registry, observations = _minimal()
    report = compare(registry, observations, {})
    assert report["rows"][0]["signal"] == "aligned"
    assert report["unobserved"] == []


def test_a_pin_without_an_observation_record_fails_closed() -> None:
    registry, observations = _minimal()
    registry["pins"]["other"] = {"kind": "git", "version": "2.0.0"}
    with pytest.raises(FreshnessError, match="missing"):
        compare(registry, observations, {})


def test_a_derived_pin_does_not_double_count_its_source_signal() -> None:
    registry, observations = _minimal()
    observations["observations"]["thing"]["source"] = "derived_from_source_pin"
    observations["observations"]["thing"]["delta"] = {"state": "open", "reason": "follows source"}
    report = compare(registry, observations, {})
    assert report["rows"][0]["signal"] == "derived"
    assert report["actionable"] == []


def test_the_report_claims_no_update_authority() -> None:
    registry, observations = _minimal()
    report = compare(registry, observations, {"thing": "v1.0.0"})
    assert report["authority"]["update_authorization"] is False
    assert report["authority"]["task_authorization"] is False


def test_fetchable_sources_are_a_subset_of_declared_sources() -> None:
    assert FETCHABLE_SOURCES <= DECLARED_SOURCES


def test_the_committed_records_parse_and_compare(registry, observations) -> None:
    """The real files must survive the comparison the workflow will run."""
    report = compare(registry, observations, {})
    assert len(report["rows"]) == len(registry["pins"])
    assert json.dumps(report)  # serialisable for the workflow artifact


# --------------------------------------------------------------------------
# The two questions the CLI answers must not collapse into one exit code.
# --------------------------------------------------------------------------


def test_structure_only_does_not_fail_on_an_undecided_lag(capsys) -> None:
    """A pull request must not be reddened by a pin someone else moved.

    The first run of this workflow failed exactly here: the pull-request job
    asked "are these records consistent?" and received the answer to "is
    anything waiting on a human?". An undecided lag is a standing state, not a
    defect in the diff under review.
    """
    assert main(["--offline", "--structure-only", "--format", "json"]) == 0
    capsys.readouterr()


def test_the_default_run_still_reports_a_pin_needing_a_human_look(capsys) -> None:
    report = compare(
        load_json(REGISTRY, REGISTRY_SCHEMA), load_json(OBSERVATIONS, OBSERVATIONS_SCHEMA), {}
    )
    expected = 1 if report["actionable"] else 0
    assert main(["--offline", "--format", "json"]) == expected
    capsys.readouterr()


def test_structure_only_still_fails_on_a_structurally_broken_record(tmp_path) -> None:
    """Silencing the lag verdict must not silence a real inconsistency."""
    registry, observations = _minimal()
    registry["pins"]["undeclared"] = {"kind": "git", "version": "9.9.9"}
    with pytest.raises(FreshnessError, match="missing"):
        compare(registry, observations, {})
