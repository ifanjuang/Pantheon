// Cockpit — NavigationState.
//
// The business state of the cockpit. Pure data: no DOM, no Swiper, no rendering.
// Any presentation (mobile deck, scroll-snap, grid, list, desktop master/detail)
// can be driven from this object, and it can be tested without a browser.
//
//   { spaceId, collectionId, activeEntityId, activeIndex, path, face, overlay }
//
// The whole collection lives here as data; how many projections get mounted is a
// presentation concern, not a state concern.

const FRONT = "front";
const BACK = "back";

export function createNavigationState({ spaceId = null } = {}) {
  const listeners = new Set();

  let state = {
    spaceId,
    collectionId: null,
    items: [],
    activeIndex: -1,
    face: FRONT,
    overlay: null,
    loading: false,
    path: [],
  };

  function snapshot() {
    const active = state.items[state.activeIndex] || null;
    return Object.freeze({
      spaceId: state.spaceId,
      collectionId: state.collectionId,
      activeEntityId: active ? active.id ?? null : null,
      activeIndex: state.activeIndex,
      activeItem: active,
      itemCount: state.items.length,
      face: state.face,
      overlay: state.overlay,
      loading: state.loading,
      path: state.path.slice(),
      canPrevious: state.activeIndex > 0,
      canNext: state.activeIndex >= 0 && state.activeIndex < state.items.length - 1,
    });
  }

  function emit() {
    const current = snapshot();
    for (const listener of listeners) listener(current);
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  // Bind a new collection. `items` is the full list as data; nothing is mounted.
  function setCollection({ spaceId: nextSpace, collectionId, items = [], index = 0, loading = false }) {
    state = {
      ...state,
      spaceId: nextSpace === undefined ? state.spaceId : nextSpace,
      collectionId: collectionId ?? null,
      items: items.slice(),
      activeIndex: items.length ? clamp(index, 0, items.length - 1) : -1,
      face: FRONT,
      overlay: null,
      loading,
    };
    emit();
  }

  // Append items discovered progressively (async sources).
  function appendItems(newItems) {
    if (!newItems?.length) return;
    const wasEmpty = state.items.length === 0;
    state = { ...state, items: state.items.concat(newItems) };
    if (wasEmpty) state.activeIndex = 0;
    emit();
  }

  function setLoading(loading) {
    if (state.loading === loading) return;
    state = { ...state, loading };
    emit();
  }

  function setIndex(index) {
    if (!state.items.length) return;
    const next = clamp(index, 0, state.items.length - 1);
    if (next === state.activeIndex) return;
    state = { ...state, activeIndex: next, face: FRONT };
    emit();
  }

  function move(delta) {
    setIndex(state.activeIndex + Math.sign(delta || 0));
  }

  function setFace(face) {
    const next = face === BACK ? BACK : FRONT;
    if (next === state.face) return;
    state = { ...state, face: next };
    emit();
  }

  function flip() {
    setFace(state.face === BACK ? FRONT : BACK);
  }

  function setOverlay(overlay = null) {
    if (state.overlay === overlay) return;
    state = { ...state, overlay };
    emit();
  }

  // Level navigation: the path records the chosen parents.
  function pushLevel(frame) {
    state = { ...state, path: state.path.concat([frame]) };
    emit();
  }

  function popLevel() {
    if (!state.path.length) return null;
    const path = state.path.slice();
    const frame = path.pop();
    state = { ...state, path };
    emit();
    return frame;
  }

  function itemAt(index) {
    return state.items[index] || null;
  }

  return Object.freeze({
    snapshot,
    subscribe,
    setCollection,
    appendItems,
    setLoading,
    setIndex,
    move,
    setFace,
    flip,
    setOverlay,
    pushLevel,
    popLevel,
    itemAt,
    get items() { return state.items.slice(); },
  });
}

function clamp(value, min, max) {
  const numeric = Number.isFinite(value) ? value : min;
  return Math.max(min, Math.min(max, numeric));
}
