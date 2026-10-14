"""Pantheon context bridge — bounded model-context transport for Hermes.

The plugin exposes only exact admitted Pantheon context reads and one gateway hook
that demotes adapter-inlined document attachments to data before model dispatch.
It does not mediate terminal/filesystem provenance, install itself, authorize a
task, persist memory or admit Evidence.
"""

from . import context_admission, external_content, schemas, tools


def _protected_handler(tool_name, handler):
    def protected(args, **kwargs):
        result = handler(args, **kwargs)
        protected_result = context_admission.protect_model_bound_result(
            tool_name=tool_name,
            result=result,
        )
        if protected_result is None:  # pragma: no cover - fixed reviewed tool names only
            raise RuntimeError("Pantheon context handler lost Context Admission coverage")
        return protected_result

    return protected


def register(ctx):
    ctx.register_tool(
        name="pantheon_context_manifest",
        toolset="pantheon_context",
        schema=schemas.PANTHEON_CONTEXT_MANIFEST,
        handler=_protected_handler(
            "pantheon_context_manifest",
            tools.pantheon_context_manifest,
        ),
        description="Read the exact admitted Pantheon context manifest for this Hermes session.",
    )
    ctx.register_tool(
        name="pantheon_context_entity",
        toolset="pantheon_context",
        schema=schemas.PANTHEON_CONTEXT_ENTITY,
        handler=_protected_handler(
            "pantheon_context_entity",
            tools.pantheon_context_entity,
        ),
        description="Read one exact entity already admitted for this Hermes session.",
    )
    ctx.register_hook("pre_gateway_dispatch", external_content.pre_gateway_dispatch)
