"""Pantheon Next — MCP policy server (bounded module).

Read-only / consultation / validation / candidate-preparation surface centered
on governed sources and the capability passport. It serves doctrine, explains
allowlisted placement, qualifies provided status candidates, validates
passports and returns policy decisions as data. It executes nothing, approves
nothing, writes nothing and promotes no memory. See CLAUDE.md,
docs/governance/MCP_PANTHEON_MINIMAL_PROFILE.md and
mcp-server/docs/HTTP_API_CONTRACT.md.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pantheon-mcp-server")
except PackageNotFoundError:
    # Source-tree imports are not installed distributions. Do not pretend that
    # checkout state is package metadata.
    __version__ = "0+uninstalled"
