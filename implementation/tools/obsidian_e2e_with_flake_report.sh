#!/usr/bin/env bash
# One bounded retry for the real-Obsidian e2e qualification labs, with the flake
# recorded rather than hidden.
#
# Why this exists
# ---------------
# Four labs (S2, S3, S4, S5) start a real Obsidian/Electron session under Xvfb.
# All four go through the upstream harness call
# `startObsidianPluginSession` (@vrtmrz/obsidian-test-session), which waits a
# fixed 60 s for the plugin session to become ready.
#
# That wait is exceeded under runner contention even though the scenario itself
# takes far less. Observed on 2026-08-31, same commit, same pins:
#
#     S4  timeout at 60 s under 35 parallel checks  ->  19 s when re-run alone
#     S3  timeout at 60 s under 35 parallel checks  ->  33 s when re-run alone
#
# And it is not new: of the 28 runs of the S3 workflow preceding that date — on
# branches touching no LiveSync pin — 11 failed. Roughly 39 %.
#
# A check that fails a third of the time for reasons unrelated to the change
# under review does not gate anything. It trains reviewers to re-run until
# green, which is worse than no check: it produces the appearance of a
# qualification while selecting for persistence rather than correctness.
#
# What this does, and what it deliberately does not do
# ----------------------------------------------------
# One bounded retry restores the gate's meaning: a real regression still fails
# twice. It is not a skipped, disabled or quarantined test — the scenario runs
# in full and must pass.
#
# The retry is restricted to the diagnosed condition. The first attempt's output
# is captured and matched against the readiness-timeout signature; anything else
# — an assertion failure, a CouchDB error, a genuine LiveSync regression — fails
# immediately on the first attempt, unretried. Retrying every nonzero result
# would be the "re-run until green" pathology this script exists to remove, and
# it would let a real regression be reported as contention.
#
# The flake is never silent. A first-attempt failure is always written to the
# run summary, so the fragility stays visible and countable instead of being
# absorbed by a green tick.
#
#     bounded retry != skipped test
#     silent retry != honest gate
#     green after retry != green
#
# The real fix is upstream: `startObsidianPluginSession` needs a configurable
# timeout, or these labs need to stop competing for one runner. This script also
# dumps the harness's wait site into the summary on a flake, so that fix can be
# specified from a real observation rather than guessed at.

set -uo pipefail

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <command> [args...]" >&2
    exit 2
fi

SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
HARNESS="node_modules/@vrtmrz/obsidian-test-session"

# The upstream harness call whose fixed readiness wait is the diagnosed flake,
# and the wait's own failure mode. Both must appear for a retry to be justified.
FLAKE_SITE="startObsidianPluginSession"
FLAKE_MODE="waitForFunction|Timeout [0-9]+ms exceeded|Timeout.*exceeded"

capture="$(mktemp)"
trap 'rm -f "$capture"' EXIT

"$@" 2>&1 | tee "$capture"
first_status=${PIPESTATUS[0]}
if [ "$first_status" -eq 0 ]; then
    exit 0
fi

if ! grep -q "$FLAKE_SITE" "$capture" || ! grep -qE "$FLAKE_MODE" "$capture"; then
    echo "::error title=Obsidian e2e failed::Not the known session-start flake; failing without a retry."
    {
        echo "### Obsidian e2e — failed (exit ${first_status}), not retried"
        echo
        echo "Command: \`$*\`"
        echo
        echo "The first attempt's output does not carry the diagnosed signature"
        echo "(\`${FLAKE_SITE}\` together with a readiness timeout), so this is a real"
        echo "failure and the bounded retry does not apply to it."
        echo
        echo '```text'
        echo "unmatched failure != contention"
        echo "bounded retry != retry until green"
        echo '```'
    } >> "$SUMMARY"
    exit "$first_status"
fi

echo "::warning title=Obsidian e2e first attempt failed::Session-start readiness timeout; retrying once. The flake is recorded in the run summary; a real regression fails both attempts."

{
    echo "### Obsidian e2e — first attempt failed (exit ${first_status})"
    echo
    echo "Command: \`$*\`"
    echo
    echo "Matched the diagnosed session-start readiness timeout (\`${FLAKE_SITE}\`)."
    echo "Retrying once. This is recorded so the flake stays countable."
    echo
    echo '```text'
    echo "bounded retry != skipped test"
    echo "green after retry != green"
    echo '```'
} >> "$SUMMARY"

# Investigative half: report how the upstream harness handles its readiness
# wait, so the durable fix can be specified instead of guessed. Best-effort —
# never fails the step.
{
    echo
    echo "#### Upstream harness readiness wait"
    echo
    if [ -d "$HARNESS" ]; then
        version="$(node -e "process.stdout.write(require('./${HARNESS}/package.json').version)" 2>/dev/null || echo unknown)"
        echo "\`@vrtmrz/obsidian-test-session\` version: \`${version}\`"
        echo
        matches="$(grep -rnE 'waitForFunction|timeout' "$HARNESS/src" "$HARNESS/dist" 2>/dev/null | head -25 || true)"
        if [ -n "$matches" ]; then
            echo "Timeout and wait sites, to establish whether the 60 s wait is configurable:"
            echo
            echo '```text'
            printf '%s\n' "$matches"
            echo '```'
        else
            echo "No \`waitForFunction\` or \`timeout\` reference found in the shipped sources."
        fi
    else
        echo "Harness not found at \`${HARNESS}\` — nothing to report."
    fi
} >> "$SUMMARY" 2>/dev/null || true

"$@"
second_status=$?

if [ "$second_status" -eq 0 ]; then
    {
        echo
        echo "**Second attempt passed.** The first failure matched the shared"
        echo "session-start readiness timeout, so it is recorded as contention rather"
        echo "than a qualification failure. That claim rests on the matched signature,"
        echo "not on the retry having succeeded."
    } >> "$SUMMARY"
    exit 0
fi

{
    echo
    echo "**Second attempt failed as well** (exit ${second_status}). Two consecutive"
    echo "failures are treated as real: this is a qualification failure, not contention."
} >> "$SUMMARY"
exit "$second_status"
