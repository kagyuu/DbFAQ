-- DbFAQ 初期スキーマ(docs/P002-frontend-spec.md §4.2)
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL UNIQUE,
    fetched_at TEXT NOT NULL,
    oracle_version TEXT NOT NULL,
    table_count INTEGER NOT NULL,
    relation_count INTEGER NOT NULL
);

CREATE TABLE db_tables (
    id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    comment TEXT,
    num_rows INTEGER,
    last_analyzed TEXT,
    iot INTEGER NOT NULL,
    UNIQUE (snapshot_id, name)
);

CREATE TABLE db_columns (
    id INTEGER PRIMARY KEY,
    table_id INTEGER NOT NULL REFERENCES db_tables(id) ON DELETE CASCADE,
    column_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data_type_display TEXT NOT NULL,
    data_length INTEGER,
    data_precision INTEGER,
    data_scale INTEGER,
    char_length INTEGER,
    char_used TEXT,
    nullable INTEGER NOT NULL,
    data_default TEXT,
    comment TEXT,
    UNIQUE (table_id, name)
);

CREATE TABLE db_constraints (
    id INTEGER PRIMARY KEY,
    table_id INTEGER NOT NULL REFERENCES db_tables(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('P', 'U', 'R')),
    ref_owner TEXT,
    ref_table TEXT,
    delete_rule TEXT,
    UNIQUE (table_id, name)
);

CREATE TABLE db_constraint_columns (
    constraint_id INTEGER NOT NULL REFERENCES db_constraints(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    ref_column_name TEXT,
    PRIMARY KEY (constraint_id, position)
);

CREATE TABLE db_indexes (
    id INTEGER PRIMARY KEY,
    table_id INTEGER NOT NULL REFERENCES db_tables(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    is_unique INTEGER NOT NULL,
    index_type TEXT NOT NULL,
    UNIQUE (table_id, name)
);

CREATE TABLE db_index_columns (
    index_id INTEGER NOT NULL REFERENCES db_indexes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    descending INTEGER NOT NULL,
    PRIMARY KEY (index_id, position)
);

CREATE INDEX ix_db_constraints_ref ON db_constraints(ref_owner, ref_table);
