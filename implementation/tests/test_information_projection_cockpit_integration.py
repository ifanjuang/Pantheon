"""Integration coverage for Information projection routes in the main Cockpit app."""

from __future__ import annotations

import re

from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def test_information_projection_routes_are_installed_in_main_cockpit() -> None:
    app = create_cockpit_app(
        connect_fn=lambda: _Connection(),
        initialize_fn=None,
        api_key="read-key",
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
    )
    paths = {route.path for route in app.routes}
    assert "/agency/information/{information_id}/projection" in paths
    assert "/agency/projects/{project_id}/information-projections" in paths
    assert "/agency/information/{information_id}/projection-metadata" in paths
    assert "/agency/information/{information_id}/documents" in paths
    assert "/agency/information/{information_id}/documents/{document_id}" in paths


def test_projection_migration_is_part_of_cockpit_initializer(monkeypatch) -> None:
    executed: list[str] = []

    class _InitializerConnection:
        def execute(self, sql: str):
            executed.append(sql)
            return self

        def commit(self) -> None:
            pass

        def close(self) -> None:
            pass

    from mvp_vertical import cockpit_shell, information_projection

    monkeypatch.setattr(cockpit_shell.store, "connect", lambda: _InitializerConnection())
    cockpit_shell.initialize_cockpit_schema()
    expected = information_projection.MIGRATION.read_text(encoding="utf-8")
    assert expected in executed


# The general form of this rule lives in tests/test_startup_migrations_lock_light.py,
# which applies the same guarded-block stripping to every migration the composed
# initializer replays rather than to this one alone. The narrow check below is kept
# because it fails against the file a reader of this module is looking at.
def test_projection_startup_migration_remains_lock_light() -> None:
    from mvp_vertical import information_projection

    migration = information_projection.MIGRATION.read_text(encoding="utf-8")
    unguarded = re.sub(
        r"DO\s*\$\$.*?\$\$\s*;",
        "",
        migration,
        flags=re.DOTALL | re.IGNORECASE,
    ).upper()
    assert "ALTER TABLE" not in unguarded
