PRAGMA foreign_keys = ON;

CREATE TABLE publications (
    publication_id TEXT PRIMARY KEY,
    bibcode TEXT UNIQUE,
    doi TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    publication_year INTEGER,
    legacy_source_id TEXT,
    screening_category TEXT NOT NULL,
    provenance_status TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE publication_aliases (
    alias TEXT PRIMARY KEY,
    publication_id TEXT NOT NULL REFERENCES publications(publication_id),
    alias_type TEXT NOT NULL,
    correction_reason TEXT NOT NULL
);

CREATE TABLE datasets (
    dataset_id TEXT PRIMARY KEY,
    publication_id TEXT NOT NULL REFERENCES publications(publication_id),
    dataset_name TEXT NOT NULL,
    catalog_id TEXT,
    table_id TEXT,
    local_path TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    authority_status TEXT NOT NULL,
    retrieval_method TEXT NOT NULL,
    retrieval_date TEXT,
    UNIQUE (publication_id, dataset_name)
);

CREATE TABLE literature_records (
    record_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id),
    source_row_locator TEXT NOT NULL,
    legacy_object_id TEXT,
    original_name TEXT,
    ra REAL,
    dec REAL,
    host_galaxy TEXT,
    distance_mpc REAL,
    reported_confirmation_status TEXT,
    reported_is_ucd INTEGER CHECK (reported_is_ucd IN (0, 1) OR reported_is_ucd IS NULL),
    gaia_dr3_id TEXT,
    raw_payload_json TEXT NOT NULL,
    UNIQUE (dataset_id, source_row_locator)
);

CREATE TABLE selection_pool_records (
    pool_record_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id),
    source_row_locator TEXT NOT NULL,
    original_name TEXT,
    ra REAL,
    dec REAL,
    proposed_class TEXT NOT NULL,
    ucd_score INTEGER,
    star_score INTEGER,
    galaxy_score INTEGER,
    raw_payload_json TEXT NOT NULL,
    UNIQUE (dataset_id, source_row_locator)
);

CREATE TABLE selection_pool_record_links (
    pool_record_id TEXT NOT NULL REFERENCES selection_pool_records(pool_record_id),
    record_id TEXT NOT NULL REFERENCES literature_records(record_id),
    relationship TEXT NOT NULL,
    association_method TEXT NOT NULL,
    PRIMARY KEY (pool_record_id, record_id, relationship)
);

CREATE TABLE dataset_files (
    dataset_file_id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(dataset_id),
    file_name TEXT NOT NULL,
    local_path TEXT NOT NULL,
    file_role TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    byte_count INTEGER NOT NULL CHECK (byte_count >= 0),
    raw_row_count INTEGER,
    source_url TEXT NOT NULL,
    UNIQUE (dataset_id, file_name)
);

CREATE TABLE canonical_objects (
    canonical_object_id TEXT PRIMARY KEY,
    adopted_ra REAL,
    adopted_dec REAL,
    position_record_id TEXT REFERENCES literature_records(record_id),
    position_status TEXT NOT NULL,
    created_from_record_id TEXT NOT NULL REFERENCES literature_records(record_id)
);

CREATE TABLE canonical_object_aliases (
    retired_canonical_object_id TEXT PRIMARY KEY,
    canonical_object_id TEXT NOT NULL REFERENCES canonical_objects(canonical_object_id),
    reason TEXT NOT NULL
);

CREATE TABLE object_record_associations (
    canonical_object_id TEXT NOT NULL REFERENCES canonical_objects(canonical_object_id),
    record_id TEXT NOT NULL UNIQUE REFERENCES literature_records(record_id),
    association_method TEXT NOT NULL,
    association_status TEXT NOT NULL,
    separation_arcsec REAL,
    review_required INTEGER NOT NULL CHECK (review_required IN (0, 1)),
    PRIMARY KEY (canonical_object_id, record_id)
);

CREATE TABLE association_proposals (
    proposal_id TEXT PRIMARY KEY,
    gaia_dr3_id TEXT,
    record_id_1 TEXT NOT NULL REFERENCES literature_records(record_id),
    record_id_2 TEXT NOT NULL REFERENCES literature_records(record_id),
    separation_arcsec REAL NOT NULL,
    proposal_method TEXT NOT NULL,
    review_reason TEXT NOT NULL,
    proposal_status TEXT NOT NULL,
    UNIQUE (record_id_1, record_id_2, proposal_method)
);

CREATE TABLE object_evidence (
    evidence_id TEXT PRIMARY KEY,
    canonical_object_id TEXT NOT NULL REFERENCES canonical_objects(canonical_object_id),
    record_id TEXT NOT NULL REFERENCES literature_records(record_id),
    publication_id TEXT NOT NULL REFERENCES publications(publication_id),
    evidence_type TEXT NOT NULL,
    evidence_value TEXT NOT NULL,
    evidence_status TEXT NOT NULL,
    review_status TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE TABLE object_classifications (
    canonical_object_id TEXT PRIMARY KEY REFERENCES canonical_objects(canonical_object_id),
    classification_state TEXT NOT NULL CHECK (
        classification_state IN ('confirmed', 'candidate', 'rejected', 'uncertain')
    ),
    classification_subtype TEXT CHECK (
        classification_subtype IS NULL
        OR classification_subtype IN ('reported_ucd_role_conflict')
    ),
    ruleset_id TEXT NOT NULL,
    review_required INTEGER NOT NULL CHECK (review_required IN (0, 1)),
    rationale TEXT NOT NULL
);

CREATE TABLE review_queue (
    review_id TEXT PRIMARY KEY,
    review_type TEXT NOT NULL,
    record_id TEXT REFERENCES literature_records(record_id),
    canonical_object_id TEXT REFERENCES canonical_objects(canonical_object_id),
    proposal_id TEXT REFERENCES association_proposals(proposal_id),
    priority TEXT NOT NULL,
    reason TEXT NOT NULL,
    review_status TEXT NOT NULL
);

CREATE TABLE build_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
);

CREATE INDEX idx_records_coordinates ON literature_records(ra, dec);
CREATE INDEX idx_records_gaia ON literature_records(gaia_dr3_id);
CREATE INDEX idx_selection_pool_coordinates ON selection_pool_records(ra, dec);
CREATE INDEX idx_associations_object ON object_record_associations(canonical_object_id);
CREATE INDEX idx_evidence_object ON object_evidence(canonical_object_id);
