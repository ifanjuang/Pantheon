from __future__ import annotations

import pytest

from mvp_vertical.cockpit_api import create_app


def test_editor_and_hermes_credentials_must_be_distinct() -> None:
    with pytest.raises(
        ValueError,
        match="MVP_EDITOR_API_KEY and MVP_HERMES_API_KEY must be distinct",
    ):
        create_app(
            editor_api_key="shared-runtime-key",
            hermes_api_key="shared-runtime-key",
            policy_enforcement="disabled",
        )


def test_distinct_editor_and_hermes_credentials_are_accepted() -> None:
    app = create_app(
        editor_api_key="editor-key",
        hermes_api_key="hermes-key",
        policy_enforcement="disabled",
    )

    assert app.state.editor_api_key == "editor-key"
    assert app.state.hermes_api_key == "hermes-key"


def test_one_unconfigured_side_does_not_trigger_false_collision() -> None:
    editor_only = create_app(
        editor_api_key="editor-key",
        hermes_api_key="",
        policy_enforcement="disabled",
    )
    hermes_only = create_app(
        editor_api_key="",
        hermes_api_key="hermes-key",
        policy_enforcement="disabled",
    )

    assert editor_only.state.editor_api_key == "editor-key"
    assert not editor_only.state.hermes_api_key
    assert hermes_only.state.hermes_api_key == "hermes-key"
    assert not hermes_only.state.editor_api_key
