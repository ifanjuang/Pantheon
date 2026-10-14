"""Fail-closed guard for the protocol-level read-only declaration.

`server.py` states in prose that every primitive is read-only and
side-effect-free, and the surrounding suite verifies that each tool returns
governed data rather than performing an effect. Until the tools carried
`ToolAnnotations`, that property was invisible to any client: an MCP consumer
had to trust the package's documentation instead of reading the tool list.

These tests keep the declaration and the surface aligned in both directions.
A newly registered tool without annotations fails here, so the read-only claim
cannot quietly stop covering the whole surface.

```text
annotation declared != effect prevented
prose asserted != client verifiable
```
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import server  # noqa: E402


def _registered_tools():
    return asyncio.run(server.mcp.list_tools())


class TestReadOnlyToolAnnotations(unittest.TestCase):
    def test_every_registered_tool_declares_the_read_only_boundary(self):
        missing = [tool.name for tool in _registered_tools() if tool.annotations is None]
        self.assertEqual(
            missing,
            [],
            "every Pantheon policy tool must declare its read-only boundary at the "
            "protocol level; register it with @_read_only_tool() rather than "
            f"@mcp.tool(): {missing}",
        )

    def test_declared_hints_match_the_side_effect_free_surface(self):
        for tool in _registered_tools():
            with self.subTest(tool=tool.name):
                annotations = tool.annotations
                self.assertIsNotNone(annotations)
                self.assertIs(annotations.read_only_hint, True)
                self.assertIs(annotations.destructive_hint, False)
                self.assertIs(annotations.idempotent_hint, True)
                self.assertIs(annotations.open_world_hint, False)

    def test_the_surface_is_not_empty(self):
        # A future refactor that stops registering tools would make the two
        # assertions above vacuously true.
        self.assertGreaterEqual(len(_registered_tools()), 20)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
