(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const NAV_IDS = ["v2-previous", "v2-next", "v2-ascend", "v2-descend"];
  const SPATIAL_KEYS = new Set(["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Enter"]);

  function currentCard() {
    return $("v2-stage")?.querySelector(":is(.card, .v2-card)") || null;
  }

  function isBackOpen() {
    return currentCard()?.dataset.flipped === "true";
  }

  function syncControls() {
    const locked = isBackOpen();
    for (const id of NAV_IDS) {
      const button = $(id);
      if (!button) continue;
      if (locked) {
        button.dataset.backLocked = "true";
        button.disabled = true;
        button.title = "Navigation spatiale désactivée au verso";
      } else if (button.dataset.backLocked === "true") {
        delete button.dataset.backLocked;
        button.title = "";
      }
    }
    const stage = $("v2-stage");
    if (stage) stage.dataset.spatialNavigation = locked ? "locked-on-back" : "active-on-front";
  }

  function stopSpatialPointer(event) {
    if (!isBackOpen()) return;
    event.stopImmediatePropagation();
  }

  function stopSpatialKeys(event) {
    if (!isBackOpen() || !SPATIAL_KEYS.has(event.key)) return;
    const tag = document.activeElement?.tagName;
    if (["INPUT", "TEXTAREA", "SELECT", "BUTTON", "A"].includes(tag)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    stage.addEventListener("pointerdown", stopSpatialPointer, true);
    stage.addEventListener("pointerup", stopSpatialPointer, true);
    document.addEventListener("keydown", stopSpatialKeys, true);
    new MutationObserver(syncControls).observe(stage, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["data-flipped"],
    });
    $("v2-flip")?.addEventListener("click", () => queueMicrotask(syncControls));
    syncControls();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();