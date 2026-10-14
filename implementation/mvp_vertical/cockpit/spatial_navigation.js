(() => {
  "use strict";

  function boundedIndex(index, length) {
    if (!length) return 0;
    return Math.max(0, Math.min(length - 1, index));
  }

  function frame({ collection_id, item_ids, index = 0, parent_entity_id = null }) {
    const ids = Array.isArray(item_ids) ? [...item_ids].filter(Boolean) : [];
    return {
      collection_id: String(collection_id || "collection"),
      item_ids: ids,
      index: boundedIndex(Number(index) || 0, ids.length),
      parent_entity_id: parent_entity_id || null,
    };
  }

  function create(options = {}) {
    const rootIds = Array.isArray(options.root_item_ids) ? options.root_item_ids : [];
    const stack = [frame({ collection_id: options.root_collection_id || "root", item_ids: rootIds })];

    function currentFrame() {
      return stack[stack.length - 1];
    }

    function currentId() {
      const current = currentFrame();
      return current.item_ids[current.index] || null;
    }

    function snapshot() {
      const current = currentFrame();
      return {
        depth: stack.length - 1,
        collection_id: current.collection_id,
        current_id: currentId(),
        current_index: current.index,
        sibling_ids: [...current.item_ids],
        can_move_previous: current.index > 0,
        can_move_next: current.index < current.item_ids.length - 1,
        can_ascend: stack.length > 1,
        path: stack.map(item => ({
          collection_id: item.collection_id,
          parent_entity_id: item.parent_entity_id,
          current_id: item.item_ids[item.index] || null,
        })),
      };
    }

    function moveHorizontal(delta) {
      const current = currentFrame();
      current.index = boundedIndex(current.index + Math.sign(Number(delta) || 0), current.item_ids.length);
      return snapshot();
    }

    function selectSibling(entityId) {
      const current = currentFrame();
      const index = current.item_ids.indexOf(entityId);
      if (index < 0) throw new Error(`Entity is not a sibling in ${current.collection_id}: ${entityId}`);
      current.index = index;
      return snapshot();
    }

    function descend({ parent_entity_id, collection_id, item_ids, initial_entity_id = null }) {
      if (!parent_entity_id || parent_entity_id !== currentId()) {
        throw new Error("Descend requires the current entity as parent_entity_id");
      }
      const next = frame({ collection_id, item_ids, parent_entity_id });
      if (!next.item_ids.length) return snapshot();
      if (initial_entity_id) {
        const index = next.item_ids.indexOf(initial_entity_id);
        if (index >= 0) next.index = index;
      }
      stack.push(next);
      return snapshot();
    }

    function ascend() {
      if (stack.length > 1) stack.pop();
      return snapshot();
    }

    function returnToRoot(entityId = null) {
      stack.splice(1);
      if (entityId) selectSibling(entityId);
      return snapshot();
    }

    return Object.freeze({
      snapshot,
      currentId,
      moveHorizontal,
      selectSibling,
      descend,
      ascend,
      returnToRoot,
    });
  }

  window.PantheonSpatialNavigation = Object.freeze({ create });
})();
