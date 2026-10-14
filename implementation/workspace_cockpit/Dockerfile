ARG HERMES_IMAGE=nousresearch/hermes-agent:v0.21.6
FROM ${HERMES_IMAGE}

WORKDIR /app
COPY workspace_cockpit/server.py /app/server.py
COPY workspace_cockpit/producer_daemon.py /app/producer_daemon.py
COPY workspace_cockpit/hindsight_producer.py /app/hindsight_producer.py
COPY workspace_cockpit/hindsight_enrichment_hook.py /app/hindsight_enrichment_hook.py
COPY workspace_cockpit/memory_reconciliation.py /app/memory_reconciliation.py
COPY workspace_cockpit/role_server.py /app/role_server.py
COPY workspace_cockpit/static /app/static
COPY mvp_vertical/__init__.py /app/mvp_vertical/__init__.py
COPY mvp_vertical/hermes_role_stage_projection.py /app/mvp_vertical/hermes_role_stage_projection.py
COPY mvp_vertical/hermes_runtime_topology_projection.py /app/mvp_vertical/hermes_runtime_topology_projection.py
COPY mvp_vertical/hermes_role_trace_relay.py /app/mvp_vertical/hermes_role_trace_relay.py

ENTRYPOINT ["/opt/hermes/.venv/bin/python", "/app/server.py"]
CMD ["--host", "0.0.0.0", "--port", "8189", "--max-depth", "2", "--root", "Affaires=/workspace/affaires"]
