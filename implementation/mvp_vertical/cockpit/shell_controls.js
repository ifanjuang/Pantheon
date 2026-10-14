(() => {
  "use strict";

  const hermesToggle = document.getElementById("v2-hermes-toggle");
  const hermesDock = document.getElementById("v2-hermes-dock");
  const hermesClose = document.getElementById("v2-hermes-close");
  const menuToggle = document.getElementById("v2-menu-toggle");
  const headerMenu = document.getElementById("v2-header-menu");
  const demoButton = document.getElementById("v2-load-demo");

  function populateSpaceMenu() {
    if (!headerMenu) return;
    const items = window.PantheonNavigationRegistry?.root_collection?.items;
    const definitions = window.PantheonCardProjectionDefinitions;
    if (!Array.isArray(items) || !definitions?.get) {
      throw new Error("Cockpit root projection registries unavailable");
    }

    headerMenu.querySelectorAll("[data-space]").forEach(button => button.remove());
    for (const item of items) {
      const spaceId = String(item?.id || "");
      const definition = definitions.get(spaceId);
      if (!spaceId.startsWith("space:") || !definition?.title) {
        throw new Error(`Cockpit root projection missing for ${spaceId || "unknown root"}`);
      }
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.space = spaceId.slice("space:".length);
      button.textContent = definition.title;
      headerMenu.appendChild(button);
    }
  }

  function setHermesOpen(open) {
    if (!hermesToggle || !hermesDock) return;
    hermesDock.hidden = !open;
    hermesToggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("v2-hermes-open", open);
    if (open) {
      setMenuOpen(false);
      document.dispatchEvent(new CustomEvent("pantheon:hermes-dock-open"));
      requestAnimationFrame(() => document.getElementById("v2-handoff-question")?.focus());
    } else {
      document.dispatchEvent(new CustomEvent("pantheon:hermes-dock-close"));
    }
    if (!open && hermesDock.contains(document.activeElement)) {
      hermesToggle.focus();
    }
  }

  function setMenuOpen(open) {
    if (!menuToggle || !headerMenu) return;
    headerMenu.hidden = !open;
    menuToggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("v2-header-menu-open", open);
    if (open) {
      setHermesOpen(false);
      requestAnimationFrame(() => {
        const target = headerMenu.querySelector("[data-space].is-active")
          || headerMenu.querySelector("[data-space]")
          || document.getElementById("v2-project");
        target?.focus();
      });
    } else if (headerMenu.contains(document.activeElement)) {
      menuToggle.focus();
    }
  }

  populateSpaceMenu();

  hermesToggle?.addEventListener("click", () => setHermesOpen(Boolean(hermesDock?.hidden)));
  hermesClose?.addEventListener("click", () => setHermesOpen(false));
  menuToggle?.addEventListener("click", () => setMenuOpen(Boolean(headerMenu?.hidden)));

  headerMenu?.addEventListener("click", event => {
    if (event.target.closest("[data-space]")) setMenuOpen(false);
  });

  demoButton?.addEventListener("click", () => {
    const project = document.getElementById("v2-project");
    const token = document.getElementById("v2-token");
    if (project) project.value = "ORANGERIE";
    if (token) token.value = "demo-read-only";
    document.getElementById("v2-load")?.click();
    setMenuOpen(false);
  });

  document.getElementById("v2-load")?.addEventListener("click", () => setMenuOpen(false));

  document.addEventListener("pointerdown", event => {
    if (!headerMenu || headerMenu.hidden || !menuToggle) return;
    if (headerMenu.contains(event.target) || menuToggle.contains(event.target)) return;
    setMenuOpen(false);
  });

  document.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (hermesDock && !hermesDock.hidden) setHermesOpen(false);
    else if (headerMenu && !headerMenu.hidden) setMenuOpen(false);
  });
})();
