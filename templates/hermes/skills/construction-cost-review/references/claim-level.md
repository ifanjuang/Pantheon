# Claim level: point versus complete analysis

For a request for an **opinion**, a point on, or a review of **already received
quotes**, provide the useful, source-backed finding on the verified subset.
Label it `partial_review`, state that it is not an exhaustive consultation
analysis, and list:

- every opened quote with its exact project-relative path;
- every enumerated but unreadable or unreviewed candidate with its path and
  reason; and
- the folders or source families still required for a complete analysis.

For a request explicitly seeking a **complete**, **global** or **all-quotes**
analysis, first establish the candidate set and read every material document.
If that condition is not met, do not give an overall conformity conclusion.
Return the verified partial findings as useful context, identify the exact
missing paths or families, and ask whether the user wants to: (a) stop pending
the missing sources, or (b) continue with an explicitly limited analysis. Use
`needs_user_input` when that choice changes the requested conclusion; otherwise
use `ready_with_limits`.

## Comparison gate

Do not calculate or display a delta, traffic-light status, check mark or
conformity verdict until the exact comparison has a reference line or lot, the
candidate's material scope, a common comparison basis and readable locators for
both. A total, filename, folder name, fragment or remembered amount does not
pass this gate.

If extraction is garbled, contradictory, truncated, or cannot identify scope
and amount reliably, classify it `unreadable_or_unverified`. Do not repair or
reinterpret its text; exclude it from calculations and cite its exact path in
the limits.

For a complete request, do not produce a provisional comparison table while
required reading remains. Return the verified inventory and blocking sources as
`ready_with_limits` or `needs_user_input`. A limited point may show only
independently verified observations, never labels implying conformity or
consultation coverage.
