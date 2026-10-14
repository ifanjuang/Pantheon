// Cockpit — CollectionProvider.
//
// Feeds a collection into NavigationState. Two shapes, and no pretending:
//
//   - an Array (already resident) is applied synchronously, in one go;
//   - a real AsyncIterable is consumed progressively, as items actually arrive.
//
// There is deliberately no per-frame "streaming" of an array that is already in
// memory: that would be latency for show.

export function isAsyncIterable(source) {
  return Boolean(source) && typeof source[Symbol.asyncIterator] === "function";
}

// Apply `source` to `state` for `collection`. Returns a cancel handle so a
// superseding navigation can abandon an in-flight async load.
export function loadCollection(state, collection, source, index = 0) {
  if (!isAsyncIterable(source)) {
    const items = Array.isArray(source) ? source : [];
    state.setCollection({
      spaceId: collection.spaceId,
      collectionId: collection.id,
      items,
      index,
      loading: false,
    });
    return () => {};
  }

  let cancelled = false;

  state.setCollection({
    spaceId: collection.spaceId,
    collectionId: collection.id,
    items: [],
    index: 0,
    loading: true,
  });

  (async () => {
    try {
      for await (const item of source) {
        if (cancelled) return;
        state.appendItems([item]);
      }
    } finally {
      if (!cancelled) state.setLoading(false);
    }
  })();

  return () => { cancelled = true; };
}
