(() => {
  "use strict";

  const registry = window.PantheonNavigationRegistry;
  if (!registry) throw new Error("Navigation registry unavailable");

  const root = registry.root_collection;
  window.PantheonNavigationProjection = Object.freeze({
    rootCollectionId: root.id,
    rootItemIds: Object.freeze(root.items.map(item => item.id)),
    sourcesFor(spaceId) {
      const item = root.items.find(entry => entry.id === spaceId);
      return item ? item.sources.slice() : [];
    },
  });
})();
