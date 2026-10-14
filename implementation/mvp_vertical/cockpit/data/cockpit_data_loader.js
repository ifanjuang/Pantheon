(() => {
  "use strict";

  const ROUTES = Object.freeze({
    toolCatalog: () => "tool_catalog.json",
    decisionInbox: () => "../decision-inbox?status=pending&limit=200",
    agencyProjects: () => "../agency/projects?limit=200",
    projectSchema: () => "../agency/schema/project",
    projectInformation(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../agency/projects/${encoded}/information`;
    },
    projectDocuments(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../projects/${encoded}/documents`;
    },
    projectKnowledge(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../projects/${encoded}/knowledge`;
    },
    projectWorkIssues(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../work/scopes/project/${encoded}/issues`;
    },
    projectDecisionRequests(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../agency/projects/${encoded}/decision-requests?status=pending&limit=100`;
    },
    projectPendingCandidates(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../agency/projects/${encoded}/change-candidates?status=pending_review&limit=100`;
    },
    projectRevisionCandidates(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../agency/projects/${encoded}/change-candidates?status=revision_requested&limit=100`;
    },
    projectAnatomy(projectId) {
      const encoded = encodeURIComponent(projectId);
      return `../agency/projects/${encoded}/project-anatomy`;
    },
  });

  function create(options = window.PantheonCockpitDataLoaderOptions || {}) {
    const fetchImpl = options.fetchImpl
      || options.fetchImplFactory?.(ROUTES)
      || window.fetch.bind(window);
    let projectSchemaToken = null;
    let projectSchemaRequest = null;

    async function readJson(path, requestOptions = {}) {
      const response = await fetchImpl(path, requestOptions);
      if (!response.ok) {
        const payload = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(payload.detail || response.statusText);
      }
      return response.json();
    }

    async function loadOptionalCollection(path, collectionKey) {
      try {
        const payload = await readJson(path, { cache: "no-store" });
        return Array.isArray(payload[collectionKey]) ? payload[collectionKey] : [];
      } catch (_) {
        return [];
      }
    }

    function authorizedJson(path, token, requestOptions = {}) {
      return readJson(path, {
        ...requestOptions,
        headers: {
          ...(requestOptions.headers || {}),
          Authorization: `Bearer ${token}`,
        },
      });
    }

    async function authorizedOptionalJson(path, token, optionalStatuses = [404]) {
      const response = await fetchImpl(path, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (response.ok) return response.json();
      if (optionalStatuses.includes(response.status)) return null;
      const payload = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(payload.detail || response.statusText);
    }

    async function loadDecisionInbox(token) {
      const payload = await authorizedJson(ROUTES.decisionInbox(), token);
      return Array.isArray(payload.decision_requests) ? payload.decision_requests : [];
    }

    async function loadAgencyProjects(token) {
      const payload = await authorizedJson(ROUTES.agencyProjects(), token);
      return Array.isArray(payload.projects) ? payload.projects : [];
    }

    async function loadProjectSchema(token, options = {}) {
      const normalizedToken = String(token || "");
      if (options.forceRefresh === true || projectSchemaToken !== normalizedToken) {
        projectSchemaToken = normalizedToken;
        projectSchemaRequest = null;
      }
      if (!projectSchemaRequest) {
        const pending = authorizedJson(ROUTES.projectSchema(), token)
          .then(payload => payload.schema || null)
          .catch(error => {
            if (projectSchemaRequest === pending) projectSchemaRequest = null;
            throw error;
          });
        projectSchemaRequest = pending;
      }
      return projectSchemaRequest;
    }

    async function fetchProjectBundle(projectId, token) {
      const [information, documents, knowledge, workIssues, decisionRequests, pendingCandidates, revisionCandidates, anatomyPayload] = await Promise.all([
        authorizedJson(ROUTES.projectInformation(projectId), token),
        authorizedJson(ROUTES.projectDocuments(projectId), token),
        authorizedJson(ROUTES.projectKnowledge(projectId), token),
        authorizedJson(ROUTES.projectWorkIssues(projectId), token),
        authorizedJson(ROUTES.projectDecisionRequests(projectId), token),
        authorizedJson(ROUTES.projectPendingCandidates(projectId), token),
        authorizedJson(ROUTES.projectRevisionCandidates(projectId), token),
        authorizedOptionalJson(ROUTES.projectAnatomy(projectId), token, [404, 409]),
      ]);
      const projectDecisionRequests = Array.isArray(decisionRequests.decision_requests)
        ? decisionRequests.decision_requests
        : [];
      return {
        information: Array.isArray(information.information) ? information.information : [],
        legacyDocuments: Array.isArray(documents.documents) ? documents.documents : [],
        knowledge: Array.isArray(knowledge.knowledge) ? knowledge.knowledge : [],
        workIssues: Array.isArray(workIssues.work_issues) ? workIssues.work_issues : [],
        decisionRequests: projectDecisionRequests,
        changeCandidates: [
          ...(Array.isArray(pendingCandidates.change_candidates) ? pendingCandidates.change_candidates : []),
          ...(Array.isArray(revisionCandidates.change_candidates) ? revisionCandidates.change_candidates : []),
        ],
        projectAnatomy: anatomyPayload?.project_anatomy || null,
      };
    }

    async function loadProjectBundle(projectId, token) {
      return fetchProjectBundle(projectId, token);
    }

    function collectionReadHref(action) {
      const href = String(action?.href || "").trim();
      if (!href) throw new Error("Collection read action requires href");
      if (!href.startsWith("/")) {
        throw new Error("Collection read href must be an absolute internal path");
      }
      let resolved;
      try {
        resolved = new URL(href, "http://pantheon.invalid/");
      } catch (_) {
        throw new Error("Collection read href is invalid");
      }
      if (resolved.origin !== "http://pantheon.invalid" || !resolved.pathname.startsWith("/cockpit/")) {
        throw new Error("Collection read href must stay on the internal /cockpit/ surface");
      }
      return `${resolved.pathname}${resolved.search}`;
    }

    async function loadProjectedCollection(action, token) {
      const payload = await authorizedJson(collectionReadHref(action), token, { cache: "no-store" });
      if (payload?.cards_are_projections !== true) {
        throw new Error("Collection read response must declare projected Cards");
      }
      if (!payload.collection || typeof payload.collection !== "object" || Array.isArray(payload.collection)) {
        throw new Error("Collection read response is missing collection");
      }
      return payload.collection;
    }

    async function loadChildCollection(action, token) {
      if (!action || typeof action !== "object" || Array.isArray(action)) {
        throw new Error("Child collection load action must be an object");
      }
      if (action.kind === "collection_read") return loadProjectedCollection(action, token);
      if (action.kind === "project_bundle") {
        const contextId = String(action.context_id || "").trim();
        if (!contextId) throw new Error("Project bundle load action requires context_id");
        return loadProjectBundle(contextId, token);
      }
      throw new Error(`Unsupported child collection load action: ${String(action.kind)}`);
    }

    return Object.freeze({
      loadRegistry: (path, collectionKey) => loadOptionalCollection(path, collectionKey),
      loadToolCatalog: () => loadOptionalCollection(ROUTES.toolCatalog(), "items"),
      loadAgencyProjects,
      loadDecisionInbox,
      loadProjectSchema,
      loadProjectBundle,
      loadChildCollection,
    });
  }

  window.PantheonGlobalDecisionRequests = Object.freeze([]);
  window.PantheonProjectDecisionRequests = Object.freeze([]);
  window.PantheonCockpitDataLoader = Object.freeze({ create });
})();