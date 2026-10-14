-- Versioned structured compilation downstream of immutable converter output,
-- plus explicit document classification used by card projections. This
-- migration does not alter source bytes, approve Evidence, infer professional
-- meaning from extracted text, or authorize parser/runtime use.

CREATE TABLE IF NOT EXISTS document_classifications (
    document_id TEXT PRIMARY KEY REFERENCES source_documents(document_id) ON DELETE CASCADE,
    subject_tags JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(subject_tags) = 'array'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS structured_compilations (
    compilation_id TEXT PRIMARY KEY,
    extraction_id TEXT NOT NULL REFERENCES extraction_runs(extraction_id) ON DELETE CASCADE,
    compiler TEXT NOT NULL,
    compiler_version TEXT NOT NULL,
    config_digest TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ready', 'needs_review', 'failed')),
    quality_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    diagnostics JSONB NOT NULL DEFAULT '[]'::jsonb,
    unit_count INT NOT NULL CHECK (unit_count >= 0),
    chunk_count INT NOT NULL CHECK (chunk_count >= 0),
    page_count INT NOT NULL CHECK (page_count >= 0),
    table_count INT NOT NULL CHECK (table_count >= 0),
    anomaly_count INT NOT NULL CHECK (anomaly_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (extraction_id, compiler, compiler_version, config_digest),
    UNIQUE (compilation_id, extraction_id)
);

CREATE TABLE IF NOT EXISTS extraction_units (
    unit_id TEXT PRIMARY KEY,
    compilation_id TEXT NOT NULL,
    extraction_id TEXT NOT NULL,
    ordinal INT NOT NULL CHECK (ordinal >= 0),
    content_type TEXT NOT NULL CHECK (
        content_type IN ('heading', 'paragraph', 'list', 'table', 'figure_caption', 'page_fragment')
    ),
    body TEXT NOT NULL CHECK (length(body) > 0),
    text_digest TEXT NOT NULL,
    page_start INT CHECK (page_start > 0),
    page_end INT CHECK (page_end >= page_start),
    structural_locator TEXT NOT NULL CHECK (length(structural_locator) > 0),
    parent_heading TEXT,
    heading_level INT CHECK (heading_level BETWEEN 1 AND 6),
    section_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    quality_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    table_data JSONB,
    UNIQUE (compilation_id, ordinal),
    FOREIGN KEY (compilation_id, extraction_id)
        REFERENCES structured_compilations(compilation_id, extraction_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_compilation_bindings (
    document_id TEXT PRIMARY KEY REFERENCES source_documents(document_id) ON DELETE CASCADE,
    compilation_id TEXT NOT NULL REFERENCES structured_compilations(compilation_id) ON DELETE CASCADE,
    bound_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS retrieval_chunk_projections (
    dossier TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    chunk_no INT NOT NULL CHECK (chunk_no >= 0),
    compilation_id TEXT NOT NULL REFERENCES structured_compilations(compilation_id) ON DELETE CASCADE,
    content_type TEXT NOT NULL CHECK (
        content_type IN ('heading', 'paragraph', 'list', 'table', 'figure_caption', 'page_fragment')
    ),
    text_digest TEXT NOT NULL,
    page_start INT CHECK (page_start > 0),
    page_end INT CHECK (page_end >= page_start),
    structural_locator TEXT NOT NULL CHECK (length(structural_locator) > 0),
    parent_heading TEXT,
    section_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    quality_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (dossier, source_ref, source_digest, chunk_no),
    FOREIGN KEY (dossier, source_ref, source_digest, chunk_no)
        REFERENCES chunks(dossier, source_ref, source_digest, chunk_no) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS retrieval_chunk_units (
    dossier TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    chunk_no INT NOT NULL CHECK (chunk_no >= 0),
    unit_id TEXT NOT NULL REFERENCES extraction_units(unit_id) ON DELETE CASCADE,
    unit_order INT NOT NULL CHECK (unit_order >= 0),
    PRIMARY KEY (dossier, source_ref, source_digest, chunk_no, unit_id),
    FOREIGN KEY (dossier, source_ref, source_digest, chunk_no)
        REFERENCES retrieval_chunk_projections(
            dossier, source_ref, source_digest, chunk_no
        ) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS structured_compilation_lookup
    ON structured_compilations (extraction_id, compiler, compiler_version, config_digest);
CREATE INDEX IF NOT EXISTS extraction_units_locator_lookup
    ON extraction_units (compilation_id, page_start, content_type, ordinal);
