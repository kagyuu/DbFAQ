-- 保存済み Query とひな型の登録記録(docs/P002-frontend-spec.md §4.2、docs/P003-backend-spec.md §5.4)。※CR-005により追加
-- スナップショットのテーブルとは外部キーで結ばない(テーブルが無くなっても残すため。ADR-016)
CREATE TABLE saved_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL CHECK (scope IN ('table', 'pdb')),
    owner TEXT NOT NULL,
    table_name TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    sql TEXT NOT NULL,
    template_key TEXT UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (scope, owner, table_name, name)
);

CREATE TABLE query_template_seeds (
    template_key TEXT PRIMARY KEY,
    seeded_at TEXT NOT NULL
);
