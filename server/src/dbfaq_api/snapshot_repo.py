"""スナップショットの保存と読み出し(docs/P003-backend-spec.md §4.3、ADR-003、ADR-008)。"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import Connection, Engine, text


def _summary(row: Any) -> dict[str, Any]:
    return {
        "owner": row.owner,
        "fetched_at": row.fetched_at,
        "oracle_version": row.oracle_version,
        "table_count": row.table_count,
        "relation_count": row.relation_count,
    }


class SnapshotRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    # ---- 保存 ----------------------------------------------------------------

    def replace(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """同じ owner の旧スナップショットを消して新しいものを入れる。失敗したら全体が元に戻る。"""
        tables = snapshot["tables"]
        relation_count = sum(1 for t in tables for c in t["constraints"] if c["type"] == "R")
        summary = {
            "owner": snapshot["owner"],
            "fetched_at": snapshot["fetched_at"],
            "oracle_version": snapshot["oracle_version"],
            "table_count": len(tables),
            "relation_count": relation_count,
        }
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM snapshots WHERE owner = :owner"), {"owner": summary["owner"]})
            snapshot_id = conn.execute(
                text(
                    "INSERT INTO snapshots (owner, fetched_at, oracle_version, table_count, relation_count) "
                    "VALUES (:owner, :fetched_at, :oracle_version, :table_count, :relation_count) RETURNING id"
                ),
                summary,
            ).scalar_one()
            for t in tables:
                self._insert_table(conn, snapshot_id, t)
        return summary

    def _insert_table(self, conn: Connection, snapshot_id: int, t: dict[str, Any]) -> None:
        table_id = conn.execute(
            text(
                "INSERT INTO db_tables (snapshot_id, name, comment, num_rows, last_analyzed, iot) "
                "VALUES (:sid, :name, :comment, :num_rows, :last_analyzed, :iot) RETURNING id"
            ),
            {
                "sid": snapshot_id,
                "name": t["name"],
                "comment": t.get("comment"),
                "num_rows": t.get("num_rows"),
                "last_analyzed": t.get("last_analyzed"),
                "iot": int(bool(t.get("iot"))),
            },
        ).scalar_one()
        if t["columns"]:
            conn.execute(
                text(
                    "INSERT INTO db_columns (table_id, column_id, name, data_type, data_type_display, data_length, "
                    "data_precision, data_scale, char_length, char_used, nullable, data_default, comment) VALUES "
                    "(:tid, :column_id, :name, :data_type, :data_type_display, :data_length, :data_precision, "
                    ":data_scale, :char_length, :char_used, :nullable, :data_default, :comment)"
                ),
                [
                    {
                        "tid": table_id,
                        "column_id": c["column_id"],
                        "name": c["name"],
                        "data_type": c["data_type"],
                        "data_type_display": c["data_type_display"],
                        "data_length": c.get("data_length"),
                        "data_precision": c.get("data_precision"),
                        "data_scale": c.get("data_scale"),
                        "char_length": c.get("char_length"),
                        "char_used": c.get("char_used"),
                        "nullable": int(bool(c["nullable"])),
                        "data_default": c.get("data_default"),
                        "comment": c.get("comment"),
                    }
                    for c in t["columns"]
                ],
            )
        for k in t["constraints"]:
            cid = conn.execute(
                text(
                    "INSERT INTO db_constraints (table_id, name, type, ref_owner, ref_table, delete_rule) "
                    "VALUES (:tid, :name, :type, :ref_owner, :ref_table, :delete_rule) RETURNING id"
                ),
                {
                    "tid": table_id,
                    "name": k["name"],
                    "type": k["type"],
                    "ref_owner": k.get("ref_owner"),
                    "ref_table": k.get("ref_table"),
                    "delete_rule": k.get("delete_rule"),
                },
            ).scalar_one()
            refs = k.get("ref_columns") or []
            conn.execute(
                text(
                    "INSERT INTO db_constraint_columns (constraint_id, position, column_name, ref_column_name) "
                    "VALUES (:cid, :pos, :col, :ref)"
                ),
                [
                    {"cid": cid, "pos": i + 1, "col": col, "ref": refs[i] if i < len(refs) else None}
                    for i, col in enumerate(k["columns"])
                ],
            )
        for ix in t["indexes"]:
            iid = conn.execute(
                text(
                    "INSERT INTO db_indexes (table_id, name, is_unique, index_type) "
                    "VALUES (:tid, :name, :u, :itype) RETURNING id"
                ),
                {"tid": table_id, "name": ix["name"], "u": int(bool(ix["unique"])), "itype": ix["index_type"]},
            ).scalar_one()
            conn.execute(
                text(
                    "INSERT INTO db_index_columns (index_id, position, column_name, descending) "
                    "VALUES (:iid, :pos, :name, :desc)"
                ),
                [
                    {"iid": iid, "pos": i + 1, "name": c["name"], "desc": int(bool(c["descending"]))}
                    for i, c in enumerate(ix["columns"])
                ],
            )

    # ---- 読み出し --------------------------------------------------------------

    def _snapshot_row(self, conn: Connection, owner: str) -> Any:
        return conn.execute(text("SELECT * FROM snapshots WHERE owner = :owner"), {"owner": owner}).first()

    def get_summary(self, owner: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = self._snapshot_row(conn, owner)
        return _summary(row) if row else None

    def table_exists(self, owner: str, table: str) -> bool | None:
        """スナップショットが無ければ None。owner がスナップショットと違えば False。"""
        with self.engine.connect() as conn:
            snap = self._snapshot_row(conn, owner)
            if snap is None:
                if conn.execute(text("SELECT 1 FROM snapshots LIMIT 1")).first() is None:
                    return None
                return False
            found = conn.execute(
                text("SELECT 1 FROM db_tables WHERE snapshot_id = :sid AND name = :name"),
                {"sid": snap.id, "name": table},
            ).first()
        return found is not None

    def has_any_snapshot(self) -> bool:
        with self.engine.connect() as conn:
            return conn.execute(text("SELECT 1 FROM snapshots LIMIT 1")).first() is not None

    def get_er_view(self, owner: str) -> dict[str, Any]:
        with self.engine.connect() as conn:
            snap = self._snapshot_row(conn, owner)
            if snap is None:
                return {"loaded": False, "snapshot": None, "tables": [], "relations": []}
            tables = conn.execute(
                text("SELECT id, name, comment, num_rows FROM db_tables WHERE snapshot_id = :sid ORDER BY name"),
                {"sid": snap.id},
            ).all()
            columns = conn.execute(
                text(
                    "SELECT c.table_id, c.name, c.column_id, c.data_type_display, c.nullable FROM db_columns c "
                    "JOIN db_tables t ON t.id = c.table_id WHERE t.snapshot_id = :sid ORDER BY c.table_id, c.column_id"
                ),
                {"sid": snap.id},
            ).all()
            constraints = conn.execute(
                text(
                    "SELECT k.id, k.table_id, k.name, k.type, k.ref_owner, k.ref_table FROM db_constraints k "
                    "JOIN db_tables t ON t.id = k.table_id WHERE t.snapshot_id = :sid ORDER BY k.name"
                ),
                {"sid": snap.id},
            ).all()
            cons_cols = conn.execute(
                text(
                    "SELECT cc.constraint_id, cc.column_name, cc.ref_column_name FROM db_constraint_columns cc "
                    "JOIN db_constraints k ON k.id = cc.constraint_id JOIN db_tables t ON t.id = k.table_id "
                    "WHERE t.snapshot_id = :sid ORDER BY cc.constraint_id, cc.position"
                ),
                {"sid": snap.id},
            ).all()

        cols_of: dict[int, list[tuple[str, str | None]]] = defaultdict(list)
        for r in cons_cols:
            cols_of[r.constraint_id].append((r.column_name, r.ref_column_name))
        name_of = {t.id: t.name for t in tables}
        pk_cols: dict[int, set[str]] = defaultdict(set)
        fk_cols: dict[int, set[str]] = defaultdict(set)
        relations = []
        for k in constraints:
            names = [c for c, _ in cols_of[k.id]]
            if k.type == "P":
                pk_cols[k.table_id].update(names)
            elif k.type == "R":
                fk_cols[k.table_id].update(names)
                relations.append(
                    {
                        "name": k.name,
                        "from_owner": owner,
                        "from_table": name_of[k.table_id],
                        "from_columns": names,
                        "to_owner": k.ref_owner,
                        "to_table": k.ref_table,
                        "to_columns": [r for _, r in cols_of[k.id]],
                    }
                )
        cols_by_table: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for c in columns:
            cols_by_table[c.table_id].append(
                {
                    "name": c.name,
                    "column_id": c.column_id,
                    "data_type_display": c.data_type_display,
                    "nullable": bool(c.nullable),
                    "is_pk": c.name in pk_cols[c.table_id],
                    "is_fk": c.name in fk_cols[c.table_id],
                }
            )
        return {
            "loaded": True,
            "snapshot": _summary(snap),
            "tables": [
                {
                    "owner": owner,
                    "name": t.name,
                    "comment": t.comment,
                    "num_rows": t.num_rows,
                    "columns": cols_by_table[t.id],
                }
                for t in tables
            ],
            "relations": relations,
        }

    def get_table_detail(self, owner: str, table: str) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            snap = self._snapshot_row(conn, owner)
            if snap is None:
                return None
            t = conn.execute(
                text("SELECT * FROM db_tables WHERE snapshot_id = :sid AND name = :name"),
                {"sid": snap.id, "name": table},
            ).first()
            if t is None:
                return None
            columns = conn.execute(
                text("SELECT * FROM db_columns WHERE table_id = :tid ORDER BY column_id"), {"tid": t.id}
            ).all()
            constraints = conn.execute(
                text("SELECT * FROM db_constraints WHERE table_id = :tid ORDER BY name"), {"tid": t.id}
            ).all()
            cons_cols = conn.execute(
                text(
                    "SELECT cc.* FROM db_constraint_columns cc JOIN db_constraints k ON k.id = cc.constraint_id "
                    "WHERE k.table_id = :tid ORDER BY cc.constraint_id, cc.position"
                ),
                {"tid": t.id},
            ).all()
            indexes = conn.execute(
                text("SELECT * FROM db_indexes WHERE table_id = :tid ORDER BY name"), {"tid": t.id}
            ).all()
            idx_cols = conn.execute(
                text(
                    "SELECT ic.* FROM db_index_columns ic JOIN db_indexes i ON i.id = ic.index_id "
                    "WHERE i.table_id = :tid ORDER BY ic.index_id, ic.position"
                ),
                {"tid": t.id},
            ).all()
            referencing = conn.execute(
                text(
                    "SELECT k.id, k.name, rt.name AS from_table FROM db_constraints k "
                    "JOIN db_tables rt ON rt.id = k.table_id "
                    "WHERE rt.snapshot_id = :sid AND k.type = 'R' AND k.ref_owner = :owner AND k.ref_table = :table "
                    "ORDER BY k.name"
                ),
                {"sid": snap.id, "owner": owner, "table": table},
            ).all()
            ref_cols = conn.execute(
                text(
                    "SELECT cc.* FROM db_constraint_columns cc JOIN db_constraints k ON k.id = cc.constraint_id "
                    "JOIN db_tables rt ON rt.id = k.table_id "
                    "WHERE rt.snapshot_id = :sid AND k.type = 'R' AND k.ref_owner = :owner AND k.ref_table = :table "
                    "ORDER BY cc.constraint_id, cc.position"
                ),
                {"sid": snap.id, "owner": owner, "table": table},
            ).all()
            table_names = {
                r.name
                for r in conn.execute(text("SELECT name FROM db_tables WHERE snapshot_id = :sid"), {"sid": snap.id})
            }

        cc_of: dict[int, list[Any]] = defaultdict(list)
        for r in cons_cols:
            cc_of[r.constraint_id].append(r)
        primary_key = None
        unique_keys: list[dict[str, Any]] = []
        foreign_keys: list[dict[str, Any]] = []
        for k in constraints:
            cols = [r.column_name for r in cc_of[k.id]]
            if k.type == "P":
                primary_key = {"name": k.name, "columns": cols}
            elif k.type == "U":
                unique_keys.append({"name": k.name, "columns": cols})
            else:
                foreign_keys.append(
                    {
                        "name": k.name,
                        "columns": cols,
                        "ref_owner": k.ref_owner,
                        "ref_table": k.ref_table,
                        "ref_columns": [r.ref_column_name for r in cc_of[k.id]],
                        "delete_rule": k.delete_rule,
                        "ref_in_snapshot": k.ref_owner == snap.owner and k.ref_table in table_names,
                    }
                )
        pk_pos = {name: i + 1 for i, name in enumerate(primary_key["columns"])} if primary_key else {}
        fk_names = {c for fk in foreign_keys for c in fk["columns"]}
        rc_of: dict[int, list[Any]] = defaultdict(list)
        for r in ref_cols:
            rc_of[r.constraint_id].append(r)
        ic_of: dict[int, list[Any]] = defaultdict(list)
        for r in idx_cols:
            ic_of[r.index_id].append(r)

        return {
            "snapshot": {"owner": snap.owner, "fetched_at": snap.fetched_at},
            "table": {
                "owner": owner,
                "name": t.name,
                "comment": t.comment,
                "num_rows": t.num_rows,
                "last_analyzed": t.last_analyzed,
                "iot": bool(t.iot),
            },
            "columns": [
                {
                    "column_id": c.column_id,
                    "name": c.name,
                    "data_type": c.data_type,
                    "data_type_display": c.data_type_display,
                    "data_length": c.data_length,
                    "data_precision": c.data_precision,
                    "data_scale": c.data_scale,
                    "nullable": bool(c.nullable),
                    "data_default": c.data_default,
                    "comment": c.comment,
                    "pk_position": pk_pos.get(c.name),
                    "is_fk": c.name in fk_names,
                }
                for c in columns
            ],
            "primary_key": primary_key,
            "unique_keys": unique_keys,
            "foreign_keys": foreign_keys,
            "referenced_by": [
                {
                    "name": r.name,
                    "from_owner": owner,
                    "from_table": r.from_table,
                    "from_columns": [c.column_name for c in rc_of[r.id]],
                    "columns": [c.ref_column_name for c in rc_of[r.id]],
                }
                for r in referencing
            ],
            "indexes": [
                {
                    "name": i.name,
                    "unique": bool(i.is_unique),
                    "index_type": i.index_type,
                    "columns": [{"name": c.column_name, "descending": bool(c.descending)} for c in ic_of[i.id]],
                }
                for i in indexes
            ],
        }
