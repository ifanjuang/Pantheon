"use strict";

const path = require("path");

const loaderPath = process.argv[2]
  || path.resolve(__dirname, "../mvp_vertical/cockpit/data/cockpit_data_loader.js");

const requests = [];

function payloadFor(url) {
  if (url.includes("/agency/projects?limit=200")) return { projects: [] };
  if (url.includes("/agency/schema/project")) {
    return { schema: { schema_id: "agency.project", revision: 1 } };
  }
  if (url.includes("/decision-inbox")) return { decision_requests: [] };
  if (url.includes("/decision-requests")) return { decision_requests: [] };
  if (url.includes("/information")) return { information: [] };
  if (url.includes("/documents")) return { documents: [] };
  if (url.includes("/knowledge")) return { knowledge: [] };
  if (url.includes("/project-anatomy")) {
    return {
      project_id: "project-measurement",
      objects: [],
      relations: [],
      phases: [],
      source_representations: [],
      unmapped_sources: [],
      uncertainties: [],
      coverage: { status: "not_persisted" },
    };
  }
  if (url.includes("/work/scopes/project/")) return { work_issues: [] };
  if (url.includes("/change-candidates")) return { change_candidates: [] };
  throw new Error(`Unexpected Cockpit request: ${url}`);
}

global.window = {
  fetch: async (url) => {
    const normalized = String(url);
    requests.push(normalized);
    return {
      ok: true,
      statusText: "OK",
      json: async () => payloadFor(normalized),
    };
  },
};

require(path.resolve(loaderPath));

(async () => {
  const loader = window.PantheonCockpitDataLoader.create();
  const token = "measurement-token";

  await loader.loadAgencyProjects(token);
  await loader.loadDecisionInbox(token);
  await loader.loadProjectSchema(token);
  await loader.loadProjectSchema(token);
  await loader.loadProjectSchema(token);
  await loader.loadProjectBundle("project-measurement", token);

  const requestsByPath = {};
  for (const request of requests) {
    requestsByPath[request] = (requestsByPath[request] || 0) + 1;
  }

  const schemaPath = "../agency/schema/project";
  const result = {
    measurement: "cockpit_loader_request_count",
    scenario: "project_list_plus_unclassified_decision_inbox_plus_three_schema_reads_plus_one_project_bundle",
    total_requests: requests.length,
    unique_paths: Object.keys(requestsByPath).length,
    schema_requests: requestsByPath[schemaPath] || 0,
    decision_inbox_requests: requests.filter((item) => (
      item.includes("/decision-inbox")
      || item.includes("/agency/projects/project-measurement/decision-requests")
    )).length,
    project_bundle_requests: requests.filter((item) => (
      item.includes("/information")
      || item.includes("/documents")
      || item.includes("/knowledge")
      || item.includes("/project-anatomy")
      || item.includes("/work/scopes/project/")
      || item.includes("/agency/projects/project-measurement/decision-requests")
      || item.includes("/change-candidates")
    )).length,
    requests_by_path: requestsByPath,
  };

  process.stdout.write(`${JSON.stringify(result)}\n`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
