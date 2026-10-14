"""Inert marker for the dashboard-only Pantheon Modules plugin.

Hermes requires an enabled user plugin before it serves that plugin's browser
assets. This module deliberately registers no hooks, tools, providers, routes,
or runtime behavior.
"""


def register(_ctx) -> None:
    """Satisfy the Hermes plugin lifecycle without registering capabilities."""

    return None
