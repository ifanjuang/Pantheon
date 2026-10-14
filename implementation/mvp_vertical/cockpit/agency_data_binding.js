(() => {
  "use strict";

  const MODES = Object.freeze(["disabled", "read_only"]);
  const DEFAULT_RESOURCES = Object.freeze({
    affaires: "projects",
    people: "people",
    organizations: "organizations",
  });
  const PAYLOAD_KEYS = Object.freeze({
    affaires: "projects",
    people: "people",
    organizations: "organizations",
  });

  function field(record, name) {
    return record?.fields?.[name] ?? record?.[name] ?? null;
  }

  function text(value) {
    if (value == null) return "";
    if (typeof value === "string" || typeof value === "number") return String(value);
    if (typeof value === "object" && typeof value.label === "string") return value.label;
    if (Array.isArray(value)) return value.map(text).filter(Boolean).join(", ");
    return "";
  }

  function recordIdentity(record) {
    return record?.entity_id
      ?? record?.project_id
      ?? record?.person_id
      ?? record?.organization_id
      ?? record?.id
      ?? null;
  }

  function sourceProjection(record, resource) {
    return {
      system: "postgres",
      resource,
      entity_id: recordIdentity(record),
      revision: record?.revision ?? null,
      observed_at: record?.observed_at ?? record?.updated_at ?? null,
      authority: "agency_system_of_record",
    };
  }

  function normalizeProject(record, config) {
    const label = text(field(record, "display_name")) || text(field(record, "code")) || text(record.label) || "Affaire sans nom";
    const status = text(field(record, "status"));
    const phase = text(field(record, "phase"));
    const location = text(field(record, "location"));
    return {
      entity_id: recordIdentity(record),
      entity_type: "project",
      label,
      secondary_label: [status, phase, location].filter(Boolean).join(" · "),
      description: text(field(record, "description")),
      status: status || null,
      tags: Array.isArray(record.tags) ? record.tags : [],
      aliases: [text(field(record, "code")), ...(Array.isArray(record.aliases) ? record.aliases : [])].filter(Boolean),
      search_terms: [
        text(field(record, "code")),
        phase,
        location,
        text(field(record, "parcel_reference")),
        text(field(record, "plu_zone")),
        text(field(record, "permit_number")),
        text(field(record, "erp_type")),
      ].filter(Boolean),
      scope: { system: "postgres", resource: config.resources.affaires },
      source: sourceProjection(record, config.resources.affaires),
    };
  }

  function normalizePerson(record, config) {
    const label = text(field(record, "display_name")) || text(field(record, "name")) || text(record.label) || "Personne sans nom";
    const organization = text(field(record, "organization_name"));
    return {
      entity_id: recordIdentity(record),
      entity_type: "person",
      label,
      secondary_label: organization,
      description: "",
      status: record.status ?? null,
      tags: Array.isArray(record.tags) ? record.tags : [],
      aliases: Array.isArray(record.aliases) ? record.aliases : [],
      search_terms: [
        text(field(record, "email")),
        text(field(record, "phone")),
        text(field(record, "address")),
        organization,
      ].filter(Boolean),
      scope: { system: "postgres", resource: config.resources.people },
      source: sourceProjection(record, config.resources.people),
    };
  }

  function normalizeOrganization(record, config) {
    const label = text(field(record, "display_name")) || text(field(record, "name")) || text(record.label) || "Société sans nom";
    return {
      entity_id: recordIdentity(record),
      entity_type: "organization",
      label,
      secondary_label: text(field(record, "siret")),
      description: "",
      status: record.status ?? null,
      tags: Array.isArray(record.tags) ? record.tags : [],
      aliases: Array.isArray(record.aliases) ? record.aliases : [],
      search_terms: [
        text(field(record, "email")),
        text(field(record, "phone")),
        text(field(record, "address")),
        text(field(record, "siret")),
      ].filter(Boolean),
      scope: { system: "postgres", resource: config.resources.organizations },
      source: sourceProjection(record, config.resources.organizations),
    };
  }

  function normalizePayload(payload, kind) {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.results)) return payload.results;
    const key = PAYLOAD_KEYS[kind];
    if (key && Array.isArray(payload?.[key])) return payload[key];
    return [];
  }

  function buildMutationIntent(input = {}) {
    if (!input.entity_type || !input.entity_id || !input.field) {
      throw new Error("Agency mutation intent requires entity_type, entity_id and field");
    }
    if (input.expected_revision == null) {
      throw new Error("Agency mutation intent requires expected_revision");
    }
    return Object.freeze({
      operation: "agency_record_mutation_candidate",
      owner_system: "postgres",
      entity_type: input.entity_type,
      entity_id: input.entity_id,
      field: input.field,
      value: input.value ?? null,
      expected_revision: input.expected_revision,
      requested_by: input.requested_by ?? "hermes",
      effect: input.effect ?? "internal_state_change",
      execution_authorized: false,
    });
  }

  function create(options = {}) {
    const mode = options.mode ?? "disabled";
    if (!MODES.includes(mode)) throw new Error(`Unsupported Agency Data binding mode: ${mode}`);

    const resolver = options.resolver ?? window.PantheonContextResolver;
    const transport = options.transport;
    const config = {
      mode,
      resources: { ...DEFAULT_RESOURCES, ...(options.resources ?? {}) },
    };

    let attached = false;
    let detachCallbacks = [];

    async function query(kind, request) {
      if (config.mode !== "read_only") return [];
      if (typeof transport !== "function") {
        throw new Error("Read-only Agency Data binding requires an injected bounded transport");
      }
      const payload = await transport({
        operation: "search",
        effect: "read_only",
        owner_system: "postgres",
        resource: config.resources[kind],
        query: request.query,
        limit: request.limit,
        currentScope: request.currentScope,
      });
      return normalizePayload(payload, kind);
    }

    async function affairesProvider(request) {
      return (await query("affaires", request)).map(record => normalizeProject(record, config));
    }

    async function peopleProvider(request) {
      return (await query("people", request)).map(record => normalizePerson(record, config));
    }

    async function globalProvider(request) {
      const organizations = await query("organizations", request);
      return organizations.map(record => normalizeOrganization(record, config));
    }

    function attach() {
      if (attached || config.mode === "disabled") return status();
      if (!resolver?.registerProvider) throw new Error("Pantheon Context Resolver is unavailable");
      detachCallbacks = [
        resolver.registerProvider("affaires", affairesProvider),
        resolver.registerProvider("people", peopleProvider),
        resolver.registerProvider("global", globalProvider),
      ];
      attached = true;
      return status();
    }

    function detach() {
      detachCallbacks.splice(0).forEach(detach => detach());
      attached = false;
      return status();
    }

    function status() {
      return {
        provider: "agency_data",
        system_of_record: "postgres",
        mode: config.mode,
        attached,
        resources: { ...config.resources },
        direct_database_credentials: false,
        browser_write_execution: false,
        health_inferred: false,
      };
    }

    return Object.freeze({ attach, detach, status, config: Object.freeze(config) });
  }

  window.PantheonAgencyDataBinding = Object.freeze({
    modes: MODES,
    defaultResources: DEFAULT_RESOURCES,
    buildMutationIntent,
    create,
  });
})();
