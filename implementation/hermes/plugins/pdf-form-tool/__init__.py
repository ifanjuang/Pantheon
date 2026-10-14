"""Native Hermes adapter for the AGPL-3.0 pdf-tool form helpers."""

from . import tools


def register(ctx):
    for name, description, properties, required, handler in (
        (
            "pdf_form_fields",
            "Inspect fillable fields in one permitted local PDF.",
            {"source_path": {"type": "string"}},
            ["source_path"],
            tools.pdf_form_fields,
        ),
        (
            "pdf_form_fill",
            "Fill a copy of a permitted PDF; returns verification details and a private output path.",
            {
                "source_path": {"type": "string"},
                "values": {"type": "object"},
                "flatten": {"type": "boolean"},
            },
            ["source_path", "values"],
            tools.pdf_form_fill,
        ),
        (
            "pdf_form_render_page",
            "Render one page to a private image file for visual review.",
            {"source_path": {"type": "string"}, "page": {"type": "integer", "minimum": 1}},
            ["source_path", "page"],
            tools.pdf_form_render_page,
        ),
        (
            "pdf_form_flatten",
            "Flatten a filled PDF copy after its values have been checked.",
            {"source_path": {"type": "string"}},
            ["source_path"],
            tools.pdf_form_flatten,
        ),
    ):
        ctx.register_tool(
            name=name,
            toolset="pdf_form",
            schema={
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
            },
            handler=handler,
            description=description,
        )
