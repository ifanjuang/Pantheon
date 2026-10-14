// Cockpit live collection adapter.
//
// Owns the boundary between the active schema projection and the shared
// collection core. Card DOM is produced by the canonical renderer; this module
// only coordinates presentation state around that renderer.

import { createCollectionController } from "./collection/collection_controller.js";
import { canExpandCollection, createDeckMotion } from "./collection/motion_adapter.js";
import { createLiveProvider } from "./providers/live_provider.js";
import { renderCanonicalCard } from "./rendering/card_renderer.js";

const stage = document.getElementById("v2-stage");

if (stage && typeof window.Swiper === "function") {
  const provider = createLiveProvider();
  const flippedByEntity = new Map();
  const childCollectionCache = new Map();
  const collectionParentCache = new Map();
  const movingSources = new Set();

  let controller = null;
  let currentKey = null;
  let currentParentEntityId = null;
  let activeModel = null;
  let notifyActive = null;
  let primaryHost = null;
  let childHost = null;
  let levelHost = null;
  let levelDeck = null;
  let presentation = "compact";
  let expandedEntityId = null;
  let childCacheGraph = null;
  let childPreviewParentId = null;
  let levelCommandInFlight = false;
  let pendingAutoDescendParentId = null;

  function graph() {
    return window.PantheonCockpitGraph || null;
  }

  function syncChildCache() {
    const nextGraph = graph();
    if (nextGraph !== childCacheGraph) {
      childCacheGraph = nextGraph;
      childCollectionCache.clear();
      collectionParentCache.clear();
      childPreviewParentId = null;
    }
    return nextGraph;
  }

  function parentModelForCollection(collectionId) {
    const id = String(collectionId || "");
    if (!id) return null;
    const currentGraph = syncChildCache();
    if (id === currentKey && currentParentEntityId) {
      return currentGraph?.cards?.get?.(currentParentEntityId) || null;
    }
    if (collectionParentCache.has(id)) return collectionParentCache.get(id);
    if (!currentGraph?.cards?.values) return null;
    let parent = null;
    for (const model of currentGraph.cards.values()) {
      if (model?.child_collection?.collection_id === id) {
        parent = model;
        break;
      }
    }
    collectionParentCache.set(id, parent);
    return parent;
  }

  function childModelsFor(entityId) {
    if (!entityId) return null;
    const currentGraph = syncChildCache();
    if (!currentGraph?.children?.has?.(entityId) || !currentGraph?.cards?.get) return null;
    if (childCollectionCache.has(entityId)) return childCollectionCache.get(entityId);
    const models = (currentGraph.children.get(entityId) || [])
      .map(id => currentGraph.cards.get(id))
      .filter(Boolean)
      .map(projectModelViewState);
    childCollectionCache.set(entityId, models);
    return models;
  }

  function childRelationFor(model) {
    const entityId = model?.entity_id || model?.id;
    if (!entityId) return { state: "none", models: [] };
    const loaded = childModelsFor(entityId);
    if (loaded !== null) {
      return loaded.length
        ? { state: "loaded", models: loaded }
        : { state: "empty", models: [] };
    }
    if (model?.child_collection?.state === "available") {
      return { state: "available", models: [], collection: model.child_collection };
    }
    return { state: "none", models: [] };
  }

  function canCreateForParent(parent) {
    return parent?.child_collection?.can_add === true && Boolean(parent.child_collection.create_action);
  }

  function canCreateForCollection(collectionId) {
    return canCreateForParent(parentModelForCollection(collectionId));
  }

  function projectModelViewState(model) {
    if (!model || typeof model !== "object") return model;
    const entityId = model.entity_id || model.id;
    const remembered = entityId ? flippedByEntity.get(entityId) : undefined;
    const flipped = remembered ?? model.view_state?.flipped === true;
    return {
      ...model,
      view_state: {
        ...(model.view_state || {}),
        flipped: Boolean(flipped),
      },
    };
  }

  function projectSnapshotInput(input) {
    if (Array.isArray(input)) return input.map(projectModelViewState);
    if (!input || typeof input !== "object") return input;
    if (Array.isArray(input.siblings)) {
      return { ...input, siblings: input.siblings.map(projectModelViewState) };
    }
    if (Array.isArray(input.models)) {
      return { ...input, models: input.models.map(projectModelViewState) };
    }
    return input;
  }

  function projectChildState(node, model) {
    const relation = childRelationFor(model);
    node.dataset.childState = relation.state;
    node.classList.toggle("has-children", relation.state === "loaded" || relation.state === "available");
    return node;
  }

  function toPreview(node) {
    node.classList.remove("card");
    node.classList.add("card-preview");
    node.removeAttribute("id");
    node.removeAttribute("tabindex");
    node.dataset.flipped = "false";
    node.setAttribute("aria-hidden", "true");
    node.inert = true;
    node.querySelectorAll("[id]").forEach(item => item.removeAttribute("id"));
    node.querySelectorAll("button,input,select,textarea,a,[tabindex]").forEach(item => {
      item.setAttribute("tabindex", "-1");
      if ("disabled" in item) item.disabled = true;
    });
    return node;
  }

  function renderProjectedCard(model) {
    const node = renderCanonicalCard(model, { flipped: model?.view_state?.flipped === true });
    return projectChildState(node, model);
  }

  function renderPlaceholder() {
    const placeholder = document.createElement("div");
    placeholder.className = "card-shell collection-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    const dot = document.createElement("div");
    dot.className = "stack-placeholder";
    placeholder.append(dot);
    return placeholder;
  }

  function renderEmpty() {
    const empty = document.createElement("p");
    empty.className = "v2-empty";
    empty.setAttribute("role", "status");
    empty.textContent = "Aucune carte dans cette collection.";
    return empty;
  }

  function renderNew(collection) {
    const parent = parentModelForCollection(collection?.id);
    const action = parent?.child_collection?.create_action || null;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "v2-information-create-card v3-create-card";
    button.dataset.synthetic = "create";
    button.dataset.collectionId = String(collection?.id || "");
    if (action?.kind) button.dataset.actionKind = action.kind;

    const mark = document.createElement("span");
    mark.className = "v2-information-create-mark";
    mark.textContent = "+";
    const copy = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = action?.title || "Ajouter";
    const detail = document.createElement("small");
    detail.textContent = action?.detail || "Ajouter une carte à cette collection";
    copy.append(title, detail);
    button.append(mark, copy);

    button.addEventListener("click", () => {
      if (action?.kind !== "information_create" || !action.context_id || !window.PantheonInformationCreate?.open) return;
      try {
        window.PantheonInformationCreate.open(action.context_id);
      } catch (error) {
        window.alert(error?.message || String(error));
      }
    });
    return button;
  }

  function stageWidth() {
    return Number(stage.getBoundingClientRect?.().width || stage.clientWidth || window.innerWidth || 0);
  }

  function contextualChildrenFor(entityId) {
    const children = childModelsFor(entityId) || [];
    if (children.length === 1) return children;
    return canExpandCollection({ width: stageWidth(), count: children.length }) ? children : [];
  }

  function setMoving(source, moving) {
    if (moving) movingSources.add(source);
    else movingSources.delete(source);
    if (movingSources.size) {
      stage.dataset.swiperMoving = "true";
      stage.dataset.swiperNavigation = "true";
    } else {
      delete stage.dataset.swiperMoving;
      delete stage.dataset.swiperNavigation;
    }
  }

  function syncPresentationAttributes() {
    stage.dataset.collectionPresentation = presentation;
    if (presentation === "expanded" && expandedEntityId) {
      stage.dataset.collectionExpanded = "true";
    } else {
      delete stage.dataset.collectionExpanded;
    }
  }

  function createLevelPreview(model) {
    const preview = document.createElement("div");
    preview.className = "v3-level-preview level-preview";
    preview.setAttribute("aria-hidden", "true");
    preview.inert = true;
    if (model) preview.append(toPreview(renderProjectedCard(model)));
    return preview;
  }

  function renderParentPreview() {
    const host = levelDeck?.hostAt(0);
    if (!host) return;
    host.replaceChildren();
    const parent = parentModelForCollection(currentKey);
    if (parent) host.append(createLevelPreview(projectModelViewState(parent)));
  }

  function renderChildPreview(model) {
    const host = levelDeck?.hostAt(2);
    if (!host) return { state: "none", models: [] };
    const entityId = model?.entity_id || model?.id || null;
    const relation = childRelationFor(model);

    if (entityId !== childPreviewParentId) {
      host.replaceChildren();
      childPreviewParentId = entityId;
    }

    if (!entityId || relation.state === "none" || relation.state === "empty") {
      host.replaceChildren();
      return relation;
    }

    if (!host.childElementCount) {
      if (relation.state === "loaded" && relation.models[0]) {
        host.append(createLevelPreview(relation.models[0]));
      } else {
        const preview = document.createElement("div");
        preview.className = "v3-level-preview level-preview";
        preview.setAttribute("aria-hidden", "true");
        preview.inert = true;
        preview.append(renderPlaceholder());
        host.append(preview);
      }
    }
    return relation;
  }

  function refreshCompactDeck() {
    if (!levelDeck || presentation !== "compact") return;
    renderParentPreview();
    const relation = renderChildPreview(activeModel);
    levelDeck.setBounds({
      previous: Boolean(parentModelForCollection(currentKey)),
      next: relation.state === "loaded" || relation.state === "available",
    });
  }

  function dispatchLevelControl(controlId) {
    const control = document.getElementById(controlId);
    if (!control || control.disabled) return false;
    control.click();
    return true;
  }

  function handleLevelSettled(index) {
    if (index === 1 || levelCommandInFlight) return;
    const relation = childRelationFor(activeModel);
    const activeEntityId = activeModel?.entity_id || activeModel?.id || null;
    const canAscend = Boolean(parentModelForCollection(currentKey));
    const canDescend = relation.state === "loaded" || relation.state === "available";

    if ((index < 1 && !canAscend) || (index > 1 && !canDescend)) {
      levelDeck?.goTo(1);
      return;
    }

    levelCommandInFlight = true;
    if (index > 1 && relation.state === "available") {
      pendingAutoDescendParentId = activeEntityId;
    }
    const dispatched = dispatchLevelControl(index < 1 ? "v2-ascend" : "v2-descend");
    if (!dispatched && pendingAutoDescendParentId === activeEntityId) pendingAutoDescendParentId = null;
    levelCommandInFlight = false;
    if (levelDeck?.index !== 1) levelDeck?.goTo(1, { animate: false });
    refreshCompactDeck();
  }

  function scheduleLoadedAutoDescend() {
    const entityId = activeModel?.entity_id || activeModel?.id || null;
    if (!pendingAutoDescendParentId || entityId !== pendingAutoDescendParentId) return;
    const relation = childRelationFor(activeModel);
    if (relation.state === "empty" || relation.state === "none") {
      pendingAutoDescendParentId = null;
      return;
    }
    if (relation.state !== "loaded") return;

    pendingAutoDescendParentId = null;
    Promise.resolve().then(() => {
      if (presentation !== "compact") return;
      dispatchLevelControl("v2-descend");
    });
  }

  function ensureLevelDeck() {
    if (levelDeck) {
      const currentSlot = levelDeck.hostAt(1);
      if (primaryHost && primaryHost.parentNode !== currentSlot) currentSlot?.append(primaryHost);
      refreshCompactDeck();
      return;
    }

    stage.replaceChildren();
    levelHost = document.createElement("div");
    levelHost.className = "v3-level-host";
    stage.append(levelHost);
    levelDeck = createDeckMotion({
      mount: levelHost,
      label: "Navigation verticale entre niveaux",
      onSettled: handleLevelSettled,
      onMoveState: moving => setMoving("vertical", moving),
    });
    levelDeck.hostAt(1)?.append(primaryHost);
    refreshCompactDeck();
  }

  function disposeLevelDeck() {
    if (!levelDeck) return;
    if (primaryHost) stage.append(primaryHost);
    levelDeck.dispose();
    levelDeck = null;
    levelHost = null;
    childPreviewParentId = null;
    setMoving("vertical", false);
  }

  function renderExpandedChildren() {
    if (!childHost) return;
    childHost.replaceChildren();
    const children = presentation === "expanded" ? contextualChildrenFor(expandedEntityId) : [];
    if (!children.length) {
      childHost.hidden = true;
      syncPresentationAttributes();
      return;
    }

    const section = document.createElement("section");
    section.className = "v3-expanded-children";
    const parent = graph()?.cards?.get?.(expandedEntityId);
    section.setAttribute("aria-label", parent?.title ? `Sous-cartes de ${parent.title}` : "Sous-cartes");

    const grid = document.createElement("div");
    grid.className = "v3-expanded-child-grid";
    const childCollectionId = parent?.child_collection?.collection_id || null;
    if (childCollectionId && canCreateForParent(parent)) {
      const cell = document.createElement("div");
      cell.className = "v3-expanded-child-cell";
      cell.append(renderNew({ id: childCollectionId }));
      grid.append(cell);
    }
    for (const model of children) {
      const cell = document.createElement("div");
      cell.className = "v3-expanded-child-cell";
      cell.append(renderProjectedCard(model));
      grid.append(cell);
    }
    section.append(grid);
    childHost.append(section);
    childHost.hidden = false;
    syncPresentationAttributes();
  }

  function applyPresentationLayout(nextPresentation) {
    presentation = nextPresentation;
    if (presentation === "compact") {
      expandedEntityId = null;
      childHost.hidden = true;
      ensureLevelDeck();
    } else {
      disposeLevelDeck();
      stage.replaceChildren(primaryHost, childHost);
      renderExpandedChildren();
    }
    syncPresentationAttributes();
  }

  function loadSnapshot(key, models, activeIndex, parentEntityId = null) {
    const previousKey = currentKey;
    const parent = parentEntityId ? syncChildCache()?.cards?.get?.(parentEntityId) || null : parentModelForCollection(key);
    const snapshot = provider.toSnapshot({
      key,
      siblings: projectSnapshotInput(models),
      index: activeIndex,
      canCreate: canCreateForParent(parent),
    });
    currentKey = snapshot.collection?.id ?? null;
    currentParentEntityId = parentEntityId || null;
    if (previousKey && previousKey !== currentKey) expandedEntityId = null;
    controller.load(snapshot);
    if (previousKey !== currentKey && levelDeck?.index !== 1) {
      levelDeck.goTo(1, { animate: false });
    }
    if (presentation === "compact") {
      refreshCompactDeck();
      scheduleLoadedAutoDescend();
    } else {
      renderExpandedChildren();
    }
  }

  function ensureHosts() {
    if (primaryHost && childHost) return;
    stage.replaceChildren();
    primaryHost = document.createElement("div");
    primaryHost.className = "v3-primary-collection-host";
    childHost = document.createElement("div");
    childHost.className = "v3-expanded-children-host";
    childHost.hidden = true;
    stage.append(primaryHost, childHost);
  }

  function ensureController() {
    if (controller) return;
    ensureHosts();
    controller = createCollectionController({
      mount: primaryHost,
      label: "Cartes sœurs",
      renderNew,
      renderItem: (model, { active, presentation: itemPresentation }) => {
        const node = renderProjectedCard(model);
        if (itemPresentation === "expanded") {
          node.dataset.collectionActive = active ? "true" : "false";
          return node;
        }
        return active ? node : toPreview(node);
      },
      renderPlaceholder,
      renderEmpty,
      onActiveChange(model, index, meta = {}) {
        activeModel = model || null;
        if (pendingAutoDescendParentId && model?.entity_id !== pendingAutoDescendParentId) {
          pendingAutoDescendParentId = null;
        }
        if (meta.presentation === "compact") expandedEntityId = null;
        if (index >= 0 && model) notifyActive?.(model, index);
        if (expandedEntityId && model?.entity_id !== expandedEntityId) expandedEntityId = null;
        if (presentation === "compact") refreshCompactDeck();
        else renderExpandedChildren();
      },
      onItemActivate(model, _index, meta = {}) {
        if (meta.presentation !== "expanded" || !model?.entity_id) return;
        const children = contextualChildrenFor(model.entity_id);
        if (!children.length) {
          expandedEntityId = null;
        } else if (meta.reselected && expandedEntityId === model.entity_id) {
          expandedEntityId = null;
        } else {
          expandedEntityId = model.entity_id;
        }
        renderExpandedChildren();
      },
      onPresentationChange(nextPresentation) {
        applyPresentationLayout(nextPresentation);
      },
      onMoveState(moving) {
        setMoving("horizontal", moving);
      },
    });
  }

  stage.addEventListener("pantheon:card-flip", event => {
    const entityId = event.detail?.entity_id;
    if (!entityId) return;
    flippedByEntity.set(entityId, event.detail?.flipped === true);
  });

  window.PANTHEON_COCKPIT_SWIPER = {
    mount({ key = null, models, activeIndex = 0, parentEntityId = null, onActiveChange }) {
      notifyActive = onActiveChange;
      ensureController();
      loadSnapshot(key, models, activeIndex, parentEntityId);
    },
    update({ key = currentKey, models, activeIndex = 0, parentEntityId = currentParentEntityId }) {
      if (!controller) return;
      loadSnapshot(key, models, activeIndex, parentEntityId);
    },
    previous() {
      controller?.move(-1);
    },
    next() {
      controller?.move(1);
    },
    activeElement() {
      return controller?.activeElement?.() || null;
    },
    destroy() {
      disposeLevelDeck();
      controller?.dispose();
      controller = null;
      currentKey = null;
      currentParentEntityId = null;
      activeModel = null;
      notifyActive = null;
      primaryHost = null;
      childHost = null;
      levelHost = null;
      presentation = "compact";
      expandedEntityId = null;
      childCacheGraph = null;
      childCollectionCache.clear();
      collectionParentCache.clear();
      childPreviewParentId = null;
      levelCommandInFlight = false;
      pendingAutoDescendParentId = null;
      movingSources.clear();
      delete stage.dataset.collectionPresentation;
      delete stage.dataset.collectionExpanded;
      delete stage.dataset.swiperMoving;
      delete stage.dataset.swiperNavigation;
      flippedByEntity.clear();
    },
  };
}
