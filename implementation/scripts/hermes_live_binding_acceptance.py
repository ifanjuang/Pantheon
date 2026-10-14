#!/usr/bin/env python3
"""Operator-only synthetic live acceptance for the governed Hermes Runs binding.

Default mode observes the public Hermes Runs/toolset contract only. ``--run-live``
requires ``--ack SYNTHETIC_ONLY`` plus a pre-created synthetic Pantheon admission.
The helper does not install/enable plugins, approve runtime prompts, stop runs,
retry ambiguous submissions, schedule work or authorize production activation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from mvp_vertical.hermes_live_acceptance import (
    CONTEXT_TOOLS,
    HermesLiveAcceptanceError,
    HermesLiveBindingAcceptance,
    HermesRunEventInspector,
    PantheonLiveAcceptanceInspector,
)
from mvp_vertical.hermes_run_binding import (
    ExternalHermesRunBinding,
    HermesRunBindingError,
    HermesRunsHttpClient,
    PantheonRunBridgeClient,
)
from mvp_vertical.hermes_runs_observer import (
    HermesRunsApiObserver,
    HermesRunsObservationError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Observe a Hermes target and optionally run one explicitly synthetic "
            "Pantheon-admitted binding acceptance."
        )
    )
    parser.add_argument(
        "--hermes-url",
        default=os.environ.get("HERMES_API_BASE", "http://hermes:8642"),
    )
    parser.add_argument(
        "--hermes-key",
        default=os.environ.get("HERMES_API_SERVER_KEY", ""),
        help="Prefer HERMES_API_SERVER_KEY environment variable.",
    )
    parser.add_argument(
        "--pantheon-url",
        default=os.environ.get("PANTHEON_HERMES_API_BASE", "http://cockpit:8000"),
    )
    parser.add_argument(
        "--pantheon-key",
        default=os.environ.get("PANTHEON_HERMES_API_KEY", ""),
        help="Required only with --run-live; prefer PANTHEON_HERMES_API_KEY env.",
    )
    parser.add_argument(
        "--actor",
        default="operator:hermes-live-acceptance",
    )
    parser.add_argument(
        "--allowed-tool",
        action="append",
        default=[],
        help=(
            "Concrete Hermes tool allowed on the reviewed acceptance runtime envelope. "
            "Repeat for additional separately reviewed tools. Defaults to the two "
            "Pantheon context tools only."
        ),
    )
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--ack", default="")
    parser.add_argument("--admission-id")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--event-timeout", type=float, default=90.0)
    return parser


def _build_observer(args: argparse.Namespace) -> HermesRunsApiObserver:
    if not args.hermes_key:
        raise HermesLiveAcceptanceError(
            "HERMES_API_SERVER_KEY is required for Hermes API observation"
        )
    allowed_tools = args.allowed_tool or list(CONTEXT_TOOLS)
    return HermesRunsApiObserver(
        args.hermes_url,
        args.hermes_key,
        allowed_tools=allowed_tools,
        required_tools=CONTEXT_TOOLS,
    )


def main() -> int:
    args = build_parser().parse_args()
    try:
        observer = _build_observer(args)
        if not args.run_live:
            receipt = {
                "object_type": "hermes_live_binding_acceptance_receipt",
                "synthetic": True,
                "live_run_attempted": False,
                "observation": observer.observe(),
                "target_binding_status": "not_run",
                "technical_receipt_is_evidence": False,
                "activation_changed": False,
                "production_authorization": False,
            }
            print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        missing = [
            flag
            for flag, value in (
                ("--pantheon-key / PANTHEON_HERMES_API_KEY", args.pantheon_key),
                ("--admission-id", args.admission_id),
                ("--idempotency-key", args.idempotency_key),
            )
            if not value
        ]
        if missing:
            raise HermesLiveAcceptanceError(
                "--run-live missing required values: " + ", ".join(missing)
            )

        pantheon_bridge = PantheonRunBridgeClient(
            args.pantheon_url,
            args.pantheon_key,
            args.actor,
        )
        hermes_runs = HermesRunsHttpClient(args.hermes_url, args.hermes_key)
        harness = HermesLiveBindingAcceptance(
            observer=observer,
            binding=ExternalHermesRunBinding(
                observer=observer,
                pantheon=pantheon_bridge,
                hermes=hermes_runs,
            ),
            pantheon=PantheonLiveAcceptanceInspector(
                args.pantheon_url,
                args.pantheon_key,
                args.actor,
            ),
            hermes=HermesRunEventInspector(
                args.hermes_url,
                args.hermes_key,
                timeout=args.event_timeout,
            ),
        )
        receipt = harness.run_live(
            admission_id=args.admission_id,
            idempotency_key=args.idempotency_key,
            ack=args.ack,
        )
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        status = receipt.get("target_binding_status")
        if status == "pass":
            return 0
        if status == "inconclusive":
            return 2
        return 1
    except (
        HermesLiveAcceptanceError,
        HermesRunsObservationError,
        HermesRunBindingError,
    ) as exc:
        print(
            json.dumps(
                {
                    "object_type": "hermes_live_binding_acceptance_error",
                    "error": str(exc),
                    "technical_receipt_is_evidence": False,
                    "activation_changed": False,
                    "production_authorization": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
