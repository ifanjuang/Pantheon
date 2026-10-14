"""Explicit rejection shim for packaging tools that fall back to setuptools."""

raise SystemExit(
    "Pantheon Next root is non-distributable; build or install mcp-server/ instead."
)
