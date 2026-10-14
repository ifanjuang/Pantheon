(() => {
  "use strict";

  const NAMESPACES = Object.freeze({
    _: { key: "affaires", label: "Affaires" },
    "#": { key: "capabilities", label: "Capacités" },
    "@": { key: "people", label: "Personnes" },
    "*": { key: "global", label: "Recherche globale" },
  });

  // More than one bounded provider may contribute to a namespace. This matters
  // for global search, where Agency Data, Documents, Knowledge and other sources
  // may coexist without one registration silently replacing another.
  const providers = new Map();

  function normalize(value) {
    return String(value ?? "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("fr")
      .trim();
  }

  function parse(input) {
    const raw = String(input ?? "");
    const prefix = raw.charAt(0);
    const namespace = NAMESPACES[prefix] ? prefix : null;
    return {
      raw,
      namespace,
      namespaceKey: namespace ? NAMESPACES[namespace].key : null,
      query: normalize(namespace ? raw.slice(1) : raw),
    };
  }

  function tagNames(item) {
    return Array.isArray(item.tags)
      ? item.tags.map(tag => typeof tag === "string" ? tag : tag?.name).filter(Boolean)
      : [];
  }

  function aliases(item) {
    return Array.isArray(item.aliases) ? item.aliases.filter(Boolean) : [];
  }

  function searchTerms(item) {
    return Array.isArray(item.search_terms) ? item.search_terms.filter(Boolean) : [];
  }

  function searchableText(item) {
    return normalize([
      item.label,
      item.secondary_label,
      item.title,
      item.display_name,
      item.description,
      ...tagNames(item),
      ...aliases(item),
      ...searchTerms(item),
    ].filter(Boolean).join(" "));
  }

  function scoreItem(item, query, namespace) {
    if (!query) return { score: 1, matched_field: "all", match_reason: "empty_query" };

    const label = normalize(item.label || item.title || item.display_name);
    if (namespace === "_") {
      if (label === query) return { score: 110, matched_field: "label", match_reason: "exact" };
      if (label.startsWith(query)) return { score: 100, matched_field: "label", match_reason: "prefix" };
      const projectAliases = aliases(item).map(normalize);
      if (projectAliases.some(value => value === query)) {
        return { score: 105, matched_field: "alias", match_reason: "exact" };
      }
      if (projectAliases.some(value => value.startsWith(query))) {
        return { score: 95, matched_field: "alias", match_reason: "prefix" };
      }
      const projectTerms = searchTerms(item).map(normalize);
      if (projectTerms.some(value => value === query || value.startsWith(query))) {
        return { score: 85, matched_field: "metadata", match_reason: "identity_prefix" };
      }
      if (label.includes(query)) return { score: 70, matched_field: "label", match_reason: "contains" };
      return { score: 0, matched_field: null, match_reason: null };
    }

    if (label.startsWith(query)) return { score: 90, matched_field: "label", match_reason: "prefix" };
    if (label.includes(query)) return { score: 70, matched_field: "label", match_reason: "contains" };

    const normalizedAliases = aliases(item).map(normalize);
    if (normalizedAliases.some(value => value.startsWith(query))) {
      return { score: 68, matched_field: "alias", match_reason: "prefix" };
    }
    if (normalizedAliases.some(value => value.includes(query))) {
      return { score: 62, matched_field: "alias", match_reason: "contains" };
    }

    const normalizedTags = tagNames(item).map(normalize);
    if (normalizedTags.some(value => value === query || value.startsWith(query))) {
      return { score: namespace === "*" ? 64 : 52, matched_field: "tag", match_reason: "tag" };
    }

    if (searchableText(item).includes(query)) {
      return { score: namespace === "*" ? 55 : 45, matched_field: "metadata", match_reason: "contains" };
    }

    return { score: 0, matched_field: null, match_reason: null };
  }

  function normalizeResult(item, namespaceKey) {
    return {
      entity_id: item.entity_id ?? item.id ?? null,
      entity_type: item.entity_type ?? item.type ?? namespaceKey,
      label: item.label ?? item.title ?? item.display_name ?? "Sans titre",
      secondary_label: item.secondary_label ?? item.subtitle ?? "",
      description: item.description ?? "",
      icon_key: item.icon_key ?? null,
      tags: Array.isArray(item.tags) ? item.tags : [],
      scope: item.scope ?? null,
      status: item.status ?? null,
      // Selection belongs to the active Context state, not to a search result.
      selected: false,
      aliases: aliases(item),
      search_terms: searchTerms(item),
      source: item.source ?? null,
    };
  }

  function validateNamespaceKey(namespaceKey) {
    if (!Object.values(NAMESPACES).some(spec => spec.key === namespaceKey)) {
      throw new Error(`Unknown context namespace provider: ${namespaceKey}`);
    }
  }

  function registerProvider(namespaceKey, provider) {
    validateNamespaceKey(namespaceKey);
    if (typeof provider !== "function") {
      throw new TypeError("Context provider must be a function");
    }
    const group = providers.get(namespaceKey) ?? new Set();
    group.add(provider);
    providers.set(namespaceKey, group);
    return () => unregisterProvider(namespaceKey, provider);
  }

  function unregisterProvider(namespaceKey, provider = null) {
    validateNamespaceKey(namespaceKey);
    if (!provider) {
      providers.delete(namespaceKey);
      return;
    }
    const group = providers.get(namespaceKey);
    if (!group) return;
    group.delete(provider);
    if (group.size === 0) providers.delete(namespaceKey);
  }

  async function providerItems(namespaceKey, request) {
    const group = [...(providers.get(namespaceKey) ?? [])];
    if (group.length === 0) return { items: [], errors: [] };

    const settled = await Promise.allSettled(group.map(provider => provider(request)));
    const items = [];
    const errors = [];

    settled.forEach((entry, index) => {
      if (entry.status === "rejected") {
        errors.push({ namespaceKey, provider_index: index, message: String(entry.reason?.message ?? entry.reason) });
        return;
      }
      if (!Array.isArray(entry.value)) return;
      items.push(...entry.value.map(item => normalizeResult(item, namespaceKey)));
    });

    return { items, errors };
  }

  async function resolve(input, options = {}) {
    const parsed = parse(input);
    const limit = Math.max(1, Number(options.limit) || 12);
    const request = {
      query: parsed.query,
      namespace: parsed.namespace,
      namespaceKey: parsed.namespaceKey,
      currentScope: options.currentScope ?? null,
      limit,
    };

    if (!parsed.namespace) {
      return { ...parsed, results: [], provider_errors: [], reason: "namespace_required" };
    }

    let candidates = [];
    let providerErrors = [];

    if (parsed.namespace === "*") {
      const keys = ["affaires", "capabilities", "people", "global"];
      const groups = await Promise.all(keys.map(key => providerItems(key, request)));
      providerErrors = groups.flatMap(group => group.errors);
      const seen = new Set();
      for (const item of groups.flatMap(group => group.items)) {
        // Stable IDs are preferred. Label fallback is display-only compatibility
        // and must not be used as a durable selection identity.
        const key = `${item.entity_type}:${item.entity_id ?? `label:${normalize(item.label)}`}`;
        if (seen.has(key)) continue;
        seen.add(key);
        candidates.push(item);
      }
    } else {
      const group = await providerItems(parsed.namespaceKey, request);
      candidates = group.items;
      providerErrors = group.errors;
    }

    const ranked = candidates
      .map(item => ({ item, ...scoreItem(item, parsed.query, parsed.namespace) }))
      .filter(entry => entry.score > 0)
      .sort((a, b) => b.score - a.score || a.item.label.localeCompare(b.item.label, "fr"))
      .slice(0, limit)
      .map(entry => ({
        ...entry.item,
        matched_field: entry.matched_field,
        match_reason: entry.match_reason,
      }));

    return { ...parsed, results: ranked, provider_errors: providerErrors, reason: null };
  }

  window.PantheonContextResolver = Object.freeze({
    namespaces: NAMESPACES,
    parse,
    resolve,
    registerProvider,
    unregisterProvider,
  });
})();
