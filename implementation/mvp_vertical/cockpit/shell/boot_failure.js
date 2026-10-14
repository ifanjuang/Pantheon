export function projectBootFailure(error) {
  console.error(error);
  document.documentElement.dataset.cockpitLoad = "failed";

  const network = document.getElementById("v2-network");
  if (network) network.textContent = "chargement impossible";

  const stage = document.getElementById("v2-stage");
  if (!stage) return;

  stage.replaceChildren();
  const message = document.createElement("p");
  message.className = "v2-empty";
  message.textContent = "Le Cockpit n’a pas pu être chargé. Rechargez la page.";
  stage.append(message);
}
