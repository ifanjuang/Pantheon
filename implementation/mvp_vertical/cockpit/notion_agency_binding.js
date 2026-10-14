(() => {
  "use strict";

  const MODES = Object.freeze(["disabled", "mirror_read_only", "selective_bidirectional"]);
  const SYNC_DIRECTIONS = Object.freeze(["postgres_to_notion", "bidirectional"]);
  const CONFLICT_POLICIES = Object.freeze(["human_review", "merge_append", "postgres_authoritative"]);

  function normalizePolicy(policy = {}) {
    const direction = policy.sync_direction ?? "postgres_to_notion";
    const conflictPolicy = policy.conflict_policy ?? "postgres_authoritative";
    if (!SYNC_DIRECTIONS.includes(direction)) {
      throw new Error(`Unsupported Notion sync direction: ${direction}`);
    }
    if (!CONFLICT_POLICIES.includes(conflictPolicy)) {
      throw new Error(`Unsupported Notion conflict policy: ${conflictPolicy}`);
    }
    return Object.freeze({
      notion_visible: policy.notion_visible !== false,
      notion_editable: Boolean(policy.notion_editable),
      sync_direction: direction,
      conflict_policy: conflictPolicy,
      validation_rule: policy.validation_rule ?? null,
      sensitivity: policy.sensitivity ?? "normal",
    });
  }

  function policyKey(entityType, field) {
    return `${entityType}:${field}`;
  }

  function createFieldPolicyRegistry(entries = []) {
    const registry = new Map();
    for (const entry of entries) {
      if (!entry?.entity_type || !entry?.field) {
        throw new Error("Notion field policy requires entity_type and field");
      }
      const policy = normalizePolicy(entry);
      if (policy.notion_editable && policy.sync_direction !== "bidirectional") {
        throw new Error("Notion-editable field must use bidirectional sync");
      }
      registry.set(policyKey(entry.entity_type, entry.field), Object.freeze({
        entity_type: entry.entity_type,
        field: entry.field,
        ...policy,
      }));
    }
    return Object.freeze({
      get(entityType, field) {
        return registry.get(policyKey(entityType, field)) ?? null;
      },
      list() {
        return Array.from(registry.values());
      },
    });
  }

  function createProjectPoliciesFromSchema(schema, overrides = []) {
    if (!schema || schema.entity_type !== "project") {
      throw new Error("Notion Project projection requires agency.project schema");
    }
    const resolved = schema.resolved_view?.name;
    if (resolved && resolved !== "notion") {
      throw new Error(`Notion Project projection requires the notion view, got ${resolved}`);
    }

    const overrideMap = new Map(
      (overrides || []).map(item => [policyKey("project", item.field), item])
    );
    const entries = (schema.fields || []).map(field => ({
      entity_type: "project",
      field: field.key,
      notion_visible: true,
      // Projection/claim fields are read-only by construction. A view never
      // grants write authority, and source-backed values must not become a
      // generic Notion -> Project attribute mutation path.
      notion_editable: false,
      sync_direction: "postgres_to_notion",
      conflict_policy: "postgres_authoritative",
      ...(overrideMap.get(policyKey("project", field.key)) || {}),
    }));
    return createFieldPolicyRegistry(entries);
  }

  function projectProjection(record = {}, schema) {
    if (!schema || schema.entity_type !== "project") {
      throw new Error("Project projection requires agency.project schema");
    }
    const attributes = record.attributes && typeof record.attributes === "object" ? record.attributes : {};
    const claimValues = record.claim_values && typeof record.claim_values === "object" ? record.claim_values : {};
    const projection = {};
    for (const field of schema.fields || []) {
      if (field.storage === "attributes") {
        projection[field.key] = attributes[field.key] ?? null;
      } else if (field.storage === "projection") {
        projection[field.key] = claimValues[field.claim_type || field.key] ?? null;
      } else {
        projection[field.key] = record[field.key] ?? null;
      }
    }
    return Object.freeze(projection);
  }

  function classifyIncomingMutation(input = {}, registry) {
    const policy = registry?.get?.(input.entity_type, input.field) ?? null;
    if (!policy || !policy.notion_editable || policy.sync_direction !== "bidirectional") {
      return Object.freeze({
        status: "rejected_not_editable",
        execution_authorized: false,
        reason: "field_not_editable_from_notion",
      });
    }

    if (input.base_revision == null || input.postgres_revision == null) {
      return Object.freeze({
        status: "conflict",
        execution_authorized: false,
        reason: "revision_context_missing",
        conflict_policy: policy.conflict_policy,
      });
    }

    if (Number(input.base_revision) !== Number(input.postgres_revision)) {
      return Object.freeze({
        status: "conflict",
        execution_authorized: false,
        reason: "postgres_changed_since_notion_base",
        conflict_policy: policy.conflict_policy,
        base_revision: input.base_revision,
        postgres_revision: input.postgres_revision,
      });
    }

    return Object.freeze({
      status: "mutation_candidate",
      execution_authorized: false,
      reason: "field_policy_allows_candidate",
      conflict_policy: policy.conflict_policy,
      expected_revision: input.postgres_revision,
      candidate: Object.freeze({
        operation: "notion_projection_mutation_candidate",
        owner_system: "postgres",
        origin: "notion",
        entity_type: input.entity_type,
        entity_id: input.entity_id,
        field: input.field,
        value: input.value ?? null,
        expected_revision: input.postgres_revision,
      }),
    });
  }

  function buildSyncState(input = {}) {
    const postgresRevision = input.postgres_revision ?? null;
    const notionRevision = input.notion_revision ?? null;
    let status = input.status ?? null;
    if (!status) {
      if (input.notion_available === false) status = "notion_unavailable";
      else if (postgresRevision == null || notionRevision == null) status = "unknown";
      else if (Number(postgresRevision) === Number(notionRevision)) status = "synced";
      else if (Number(postgresRevision) > Number(notionRevision)) status = "postgres_ahead";
      else status = "notion_ahead";
    }
    return Object.freeze({
      status,
      postgres_revision: postgresRevision,
      notion_revision: notionRevision,
      notion_last_edited_time: input.notion_last_edited_time ?? null,
      last_synced_at: input.last_synced_at ?? null,
      notion_available: input.notion_available !== false,
    });
  }

  function create(options = {}) {
    const mode = options.mode ?? "disabled";
    if (!MODES.includes(mode)) throw new Error(`Unsupported Notion collaboration mode: ${mode}`);
    const fieldPolicies = options.projectSchema
      ? createProjectPoliciesFromSchema(options.projectSchema, options.fieldPolicies ?? [])
      : createFieldPolicyRegistry(options.fieldPolicies ?? []);

    function status() {
      return {
        provider: "notion",
        role: "optional_collaborative_projection",
        system_of_record: "postgres",
        mode,
        declared_field_policies: fieldPolicies.list().length,
        project_view: options.projectSchema?.resolved_view?.name ?? null,
        direct_browser_credentials: false,
        browser_sync_execution: false,
        browser_write_execution: false,
        sync_runtime_inferred: false,
        health_inferred: false,
        adoption_inferred: false,
      };
    }

    return Object.freeze({
      mode,
      fieldPolicies,
      status,
      projectProjection(record) {
        return projectProjection(record, options.projectSchema);
      },
      classifyIncomingMutation(input) {
        return classifyIncomingMutation(input, fieldPolicies);
      },
      buildSyncState,
    });
  }

  window.PantheonNotionAgencyBinding = Object.freeze({
    modes: MODES,
    syncDirections: SYNC_DIRECTIONS,
    conflictPolicies: CONFLICT_POLICIES,
    createFieldPolicyRegistry,
    createProjectPoliciesFromSchema,
    projectProjection,
    classifyIncomingMutation,
    buildSyncState,
    create,
  });
})();
