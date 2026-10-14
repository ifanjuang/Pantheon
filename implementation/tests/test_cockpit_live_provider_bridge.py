"""Regression guard for the navigation -> live renderer -> LiveProvider -> CockpitSnapshot bridge."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_live_adapter_keeps_projected_siblings_inside_snapshot_envelope() -> None:
    projection = (COCKPIT / "projection" / "cockpit_projection.js").read_text(encoding="utf-8")
    adapter = (COCKPIT / "live_collection_adapter.js").read_text(encoding="utf-8")

    # SpatialNavigation owns the active collection identity and explicit parent.
    # The projection passes both into the bridge instead of making the adapter
    # infer either relation from a naming convention.
    assert "key: snapshot.collection_id" in projection
    assert "parentEntityId = snapshot.path[snapshot.path.length - 1]?.parent_entity_id || null" in projection
    assert "mount({ key = null, models, activeIndex = 0, parentEntityId = null, onActiveChange })" in adapter
    assert "loadSnapshot(key, models, activeIndex, parentEntityId)" in adapter

    # LiveProvider owns one explicit object contract. Passing the models array as
    # the first positional argument silently defaults `siblings` to [], which is
    # rendered as "Aucune carte dans cette collection.".
    assert "provider.toSnapshot(projectSnapshotInput(models), activeIndex)" not in adapter
    assert "provider.toSnapshot({" in adapter
    assert "key," in adapter
    assert "siblings: projectSnapshotInput(models)" in adapter
    assert "index: activeIndex" in adapter

    # CockpitSnapshot stores collection identity under `collection.id`; the
    # adapter reads that projected envelope and never looks for a parallel field.
    assert "snapshot.collection_id" not in adapter
    assert "snapshot.collection?.id" in adapter
    assert "parentIdForCollection" not in adapter
    assert "CHILD_COLLECTION_PREFIX" not in adapter
