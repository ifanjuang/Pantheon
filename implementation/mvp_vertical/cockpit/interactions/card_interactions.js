(() => {
  "use strict";

  const stage = document.getElementById("v2-stage");
  if (!stage) return;

  const state = { materials: [], observer: null };
  const DRAG_THRESHOLD = 9;

  function hash(value) {
    let result = 2166136261;
    const text = String(value || "card");
    for (let index = 0; index < text.length; index += 1) {
      result ^= text.charCodeAt(index);
      result = Math.imul(result, 16777619);
    }
    return result >>> 0;
  }

  function cardEntityId(card) {
    return card.dataset.entityId
      || card.querySelector(".card-entity-id")?.textContent?.trim()
      || null;
  }

  function cardKey(card, index) {
    return cardEntityId(card)
      || card.getAttribute("data-card-id")
      || card.querySelector("[data-entity-id]")?.dataset.entityId
      || card.querySelector("h1,h2,h3,.card-title")?.textContent?.trim()
      || `projection-${index}`;
  }

  function setMaterial(card, index) {
    if (!state.materials.length || card.dataset.v3Material) return;
    const material = state.materials[hash(cardKey(card, index)) % state.materials.length];
    card.dataset.v3Material = material.id;
    material.stops.forEach((stop, stopIndex) => card.style.setProperty(`--v3-stop-${stopIndex + 1}`, stop));
  }

  function isInteractive(target) {
    return target instanceof Element && Boolean(target.closest("button,a,input,select,textarea,label,[contenteditable='true'],[role='button']"));
  }

  function bindFlip(card) {
    if (card.dataset.cardFlipBound === "true" || card.closest("[aria-hidden='true']")) return;
    card.dataset.cardFlipBound = "true";
    card.tabIndex = card.tabIndex >= 0 ? card.tabIndex : 0;
    card.setAttribute("aria-roledescription", "carte recto verso");

    let pointerId = null;
    let startX = 0;
    let startY = 0;
    let dragged = false;

    const toggle = () => {
      const next = card.dataset.flipped !== "true";
      card.dataset.flipped = String(next);
      card.setAttribute("aria-label", next ? "Carte, verso visible" : "Carte, recto visible");
      card.dispatchEvent(new CustomEvent("pantheon:card-flip", {
        bubbles: true,
        detail: {
          entity_id: cardEntityId(card),
          flipped: next,
        },
      }));
    };

    card.addEventListener("pointerdown", event => {
      pointerId = event.pointerId;
      startX = event.clientX;
      startY = event.clientY;
      dragged = false;
    }, { passive: true });

    card.addEventListener("pointermove", event => {
      if (event.pointerId !== pointerId) return;
      if (Math.hypot(event.clientX - startX, event.clientY - startY) >= DRAG_THRESHOLD) dragged = true;
    }, { passive: true });

    card.addEventListener("pointercancel", () => {
      pointerId = null;
      dragged = true;
    }, { passive: true });

    card.addEventListener("click", event => {
      pointerId = null;
      if (dragged || stage.dataset.swiperNavigation === "true" || isInteractive(event.target)) {
        dragged = false;
        return;
      }
      toggle();
    });

    card.addEventListener("keydown", event => {
      if ((event.key !== "Enter" && event.key !== " ") || (isInteractive(event.target) && event.target !== card)) return;
      event.preventDefault();
      toggle();
    });
  }

  function decorate() {
    const cards = [...stage.querySelectorAll(".card:not([data-v3-placeholder='true'])")];
    cards.forEach((card, index) => {
      card.dataset.cockpitV3 = "living-card";
      setMaterial(card, index);
      bindFlip(card);
    });
    document.documentElement.dataset.cockpitVisual = cards.length ? "v3" : "v2";
  }

  async function loadMaterials() {
    const response = await fetch("registries/materials.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Material registry unavailable: ${response.status}`);
    const registry = await response.json();
    state.materials = Array.isArray(registry.materials)
      ? registry.materials.filter(item => item?.id && Array.isArray(item.stops) && item.stops.length >= 5)
      : [];
    if (!state.materials.length) throw new Error("Material registry is empty");
  }

  async function start() {
    try { await loadMaterials(); }
    catch (error) { console.warn("Cockpit card materials disabled", error); }

    decorate();
    state.observer = new MutationObserver(decorate);
    state.observer.observe(stage, { childList: true, subtree: true });
    window.addEventListener("pagehide", () => state.observer?.disconnect(), { once: true });
  }

  window.PantheonCardInteractions = Object.freeze({ start, decorate });
  start();
})();