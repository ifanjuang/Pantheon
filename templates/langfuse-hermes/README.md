# Langfuse / Hermes support templates

Status: support templates only — runtime integration qualified in synthetic CI, production deployment not authorized.

Pantheon does not maintain a Langfuse server stack or a parallel Hermes tracing adapter here.

The selected integration is the bundled Hermes plugin:

```text
Hermes
→ observability/langfuse
→ Langfuse SDK
→ operator-selected Langfuse instance
```

The self-hosted server deployment source is the current official Langfuse Docker Compose, pinned and reviewed at deployment time. Do not copy a Pantheon-owned compose or server `.env` as a competing runtime recipe.

## Qualification evidence

Synthetic qualification currently records:

- Hermes `0.20.5`, commit `4c1f53be10d0fce1d25aee1975e5149b6c54f25a`;
- bundled `observability/langfuse` plugin exercised directly;
- Langfuse Python SDK `4.14.5`;
- Langfuse self-hosted server release commit `c2257f7d86b4407a2b27e8d3a95f719736ef4b01` (`v4.18.0`);
- official upstream `docker-compose.yml` used for the real-ingestion CI slice;
- `metadata` capture verified with no synthetic prompt, tool-argument, tool-result or final-response marker visible through the v4 Observations API;
- direct SDK transport and real Hermes plugin ingestion both observed.

These pins describe the qualified test matrix, not a permanent deployment lock. A later deployment must re-check current upstream state and either use the same qualified matrix or requalify the selected versions.

## Files retained here

```text
dashboard-card.langfuse.example.html
dashboard-module.langfuse.example.yaml
hermes-trace-metadata.example.yaml
```

They are presentation/governance support examples only. They do not install Langfuse, configure Hermes, emit traces or create an authority surface.

`hermes-trace-metadata.example.yaml` is a candidate Pantheon correlation vocabulary. The bundled Hermes plugin does not automatically implement every candidate field in that example.

## Hermes runtime configuration

Enable the bundled plugin through Hermes rather than adding a Pantheon tracing adapter:

```bash
pip install langfuse
hermes plugins enable observability/langfuse
```

Configure secrets outside Git using the Hermes-supported environment variables:

```text
HERMES_LANGFUSE_PUBLIC_KEY
HERMES_LANGFUSE_SECRET_KEY
HERMES_LANGFUSE_BASE_URL
```

Initial Pantheon posture:

```text
HERMES_LANGFUSE_CAPTURE=metadata
```

`sanitized` is suitable only for controlled debugging after payload review. `full` is not the default Pantheon posture.

## Deployment source rule

For self-hosting:

1. select an exact Langfuse release/commit;
2. obtain its official upstream Docker Compose and required environment contract;
3. review exposure, credentials, persistence, backup and retention;
4. keep secrets outside Pantheon/Git;
5. start with synthetic traces;
6. verify current v4 Observations API readback;
7. enable real dossier content only after an explicit data/retention review.

Do not resurrect the removed Pantheon-owned v3 compose or server environment template. They were retired after Q2 demonstrated the upstream v4 composition directly.

## Boundary

```text
Langfuse observes.
Hermes executes.
Dashboard exposes.
Pantheon governs.
```

A Langfuse trace is not an Evidence Pack, approval, memory, proof, authorization or professional validation.

Successful trace delivery also does not prove that all expected spans were emitted, that redaction was sufficient, or that a production deployment is hardened.
