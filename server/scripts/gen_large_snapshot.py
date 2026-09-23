"""A05 用の大規模な偽スナップショット(300 表・5,000 列・外部キー 400 本、owner=HR)を SQLite に作る。"""

import sys

from dbfaq_api.db import create_sqlite_engine
from dbfaq_api.migrate import apply_all
from dbfaq_api.snapshot_repo import SnapshotRepository

TABLES = 300
COLUMNS = 5000
FKS = 400


def build() -> dict:
    per = [COLUMNS // TABLES + (1 if i < COLUMNS % TABLES else 0) for i in range(TABLES)]
    tables = []
    for i in range(TABLES):
        name = f"T{i:03d}_PERF"
        cols = [
            {
                "column_id": j + 1, "name": "ID" if j == 0 else f"COL_{j:02d}", "data_type": "NUMBER",
                "data_type_display": "NUMBER(10)", "data_length": 22, "data_precision": 10, "data_scale": 0,
                "char_length": 0, "char_used": None, "nullable": j != 0, "data_default": None, "comment": None,
            }
            for j in range(per[i])
        ]
        tables.append({
            "name": name, "comment": f"perf table {i}", "num_rows": 1000, "last_analyzed": None, "iot": False,
            "columns": cols,
            "constraints": [{"name": f"{name}_PK", "type": "P", "columns": ["ID"], "ref_owner": None,
                             "ref_table": None, "ref_columns": None, "delete_rule": None}],
            "indexes": [{"name": f"{name}_PK", "unique": True, "index_type": "NORMAL",
                         "columns": [{"name": "ID", "descending": False}]}],
        })
    for k in range(FKS):
        child = tables[(k % (TABLES - 1)) + 1]
        parent = tables[(k * 7) % TABLES]
        col = child["columns"][1 + (k // (TABLES - 1)) % (len(child["columns"]) - 1)]["name"]
        child["constraints"].append({"name": f"FK_{k:03d}", "type": "R", "columns": [col], "ref_owner": "HR",
                                     "ref_table": parent["name"], "ref_columns": ["ID"], "delete_rule": "NO ACTION"})
    return {"owner": "HR", "oracle_version": "perf", "fetched_at": "2026-09-23T00:00:00Z", "tables": tables}


def main() -> int:
    engine = create_sqlite_engine(sys.argv[1])
    apply_all(engine, lambda: "2026-09-23T00:00:00Z")
    summary = SnapshotRepository(engine).replace(build())
    engine.dispose()
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
