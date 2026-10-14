const nativeFetch = window.fetch.bind(window);
const fixtureResponse = (payload, status = 200) => new Response(JSON.stringify(payload), {
  status,
  headers: { "Content-Type": "application/json; charset=utf-8" },
});

function loadStaticJson(path, label) {
  return nativeFetch(path, { cache: "no-store" }).then(response => {
    if (!response.ok) throw new Error(`${label} indisponible (${response.status})`);
    return response.json();
  });
}

const [fixture, workActivityFixture, toolCatalog] = await Promise.all([
  loadStaticJson("demo-data.json", "Fixture"),
  loadStaticJson("demo-work-activity.json", "Fixture Work"),
  loadStaticJson("tool_catalog.json", "Catalogue d’outils"),
]);

if (workActivityFixture.schema_id !== "cockpit.demo_work_activity" || workActivityFixture.revision !== 1) {
  throw new Error("Fixture Work incompatible");
}

function strictWorkIssues(payload) {
  return (payload.work_issues || []).map(item => {
    const issueId = item?.work_issue?.issue_id;
    const strict = workActivityFixture.items?.[issueId];
    if (!strict) throw new Error(`Fixture Work manquante : ${String(issueId)}`);
    return strict;
  });
}

function projectPayload(projectId) {
  const payload = fixture.project_payloads[projectId] || {
    information: [],
    documents: [],
    knowledge: [],
    work_issues: [],
    decision_requests: [],
    change_candidates: [],
    project_anatomy: null,
  };
  return { ...payload, work_issues: strictWorkIssues(payload) };
}

function requestKey(input) {
  const raw = typeof input === "string" ? input : input.url;
  const url = new URL(raw, window.location.href);
  return `${url.pathname}${url.search}`;
}

function createFetchImpl(routes) {
  if (!routes) throw new Error("Routes du CockpitDataLoader indisponibles");

  const responses = new Map();
  const register = (path, payload, status = 200) => {
    responses.set(requestKey(path), { payload, status });
  };

  register(routes.toolCatalog(), toolCatalog);
  register(routes.decisionInbox(), {
    decision_requests: Array.isArray(fixture.decision_requests) ? fixture.decision_requests : [],
  });
  register(routes.agencyProjects(), { projects: fixture.projects });
  register(routes.projectSchema(), { schema: fixture.project_schema });

  for (const project of fixture.projects || []) {
    const projectId = project.project_id;
    const payload = projectPayload(projectId);
    const decisionRequests = Array.isArray(payload.decision_requests)
      ? payload.decision_requests.filter(item => !item?.status || item.status === "pending")
      : [];
    const changeCandidates = Array.isArray(payload.change_candidates) ? payload.change_candidates : [];

    register(routes.projectInformation(projectId), { information: payload.information || [] });
    register(routes.projectDocuments(projectId), { documents: payload.documents || [] });
    register(routes.projectKnowledge(projectId), { knowledge: payload.knowledge || [] });
    register(routes.projectWorkIssues(projectId), { work_issues: payload.work_issues || [] });
    register(routes.projectDecisionRequests(projectId), { decision_requests: decisionRequests });
    register(routes.projectPendingCandidates(projectId), {
      change_candidates: changeCandidates.filter(item => item?.status === "pending_review"),
    });
    register(routes.projectRevisionCandidates(projectId), {
      change_candidates: changeCandidates.filter(item => item?.status === "revision_requested"),
    });

    if (payload.project_anatomy) {
      register(routes.projectAnatomy(projectId), { project_anatomy: payload.project_anatomy });
    } else {
      register(routes.projectAnatomy(projectId), { detail: "Project Anatomy absent de la fixture" }, 404);
    }
  }

  return async (input, init = {}) => {
    const method = String(init.method || "GET").toUpperCase();
    if (method !== "GET") {
      return fixtureResponse({ detail: "Démonstration statique : écriture désactivée" }, 405);
    }

    const key = requestKey(input);
    const matched = responses.get(key);
    if (!matched) {
      return fixtureResponse({
        detail: `Démonstration statique : ressource non simulée (${key})`,
      }, 404);
    }
    return fixtureResponse(matched.payload, matched.status);
  };
}

function waitForInitialProjection() {
  if (window.PantheonCockpitGraph) return Promise.resolve();
  return new Promise(resolve => {
    window.addEventListener("pantheon:graph-updated", resolve, { once: true });
  });
}

window.PantheonCockpitDataLoaderOptions = Object.freeze({ fetchImplFactory: createFetchImpl });
window.PantheonDemoBootstrap = {
  createFetchImpl,
  async start() {
    const projectInput = document.getElementById("v2-project");
    const tokenInput = document.getElementById("v2-token");
    const network = document.getElementById("v2-network");

    if (projectInput) projectInput.value = "VALLONS";
    if (tokenInput) tokenInput.value = "demo-read-only";
    if (network) network.textContent = "univers fictif · lecture seule";

    await waitForInitialProjection();
    const loadButton = document.getElementById("v2-load");
    if (!loadButton) throw new Error("Commande de chargement du Cockpit indisponible");
    loadButton.click();
  },
};
