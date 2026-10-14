document.documentElement.classList.add("cockpit");

function reportFailure(error) {
  console.error(error);
  document.documentElement.dataset.cockpitLoad = "failed";

  const stage = document.getElementById("v2-stage");
  if (stage) {
    const message = document.createElement("p");
    message.className = "v2-empty";
    message.setAttribute("role", "status");
    message.textContent = String(error?.message || error).includes("Swiper")
      ? "Le moteur de navigation (Swiper) n’a pas pu être chargé depuis le CDN. Vérifiez la connexion ou un bloqueur de contenu, puis rechargez."
      : "Le Cockpit n’a pas pu être chargé. Rechargez la page.";
    stage.replaceChildren(message);
  }

  const network = document.getElementById("v2-network");
  if (network) network.textContent = "chargement impossible";
}

// Both modes share one boot chain. `live_bootstrap.js` reads `?mode=demo`
// itself, publishes the mode, swaps the fixture layer through
// `demo_bootstrap.js` and then runs the same renderer, providers and classic
// scripts. Demo is a data substitution, never a second application.
try {
  await import("./live_bootstrap.js");
} catch (error) {
  reportFailure(error);
}
