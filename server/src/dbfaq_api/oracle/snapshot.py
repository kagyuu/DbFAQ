"""スキーマのスナップショットの組み立て(docs/P003-backend-spec.md §3.5)。"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Any

from . import dictionary as q
from .db import Database
from .errors import NOT_FOUND, OracleFailure
from .identifiers import validate_identifier
from .type_format import format_data_type


def iso_utc(value: dt.datetime | None) -> str | None:
    """naive な日時は UTC とみなす(LAST_ANALYZED は DB のタイムゾーン。★ACCEPTED★(2026-09-24 人間承認) P003 §3.5)。"""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(dt.UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _clean_default(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_snapshot(
    owner: str,
    oracle_version: str,
    fetched_at: dt.datetime,
    tables: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
    indexes: list[dict[str, Any]],
    expressions: list[dict[str, Any]],
) -> dict[str, Any]:
    """辞書の行リストからスナップショットを組み立てる純粋関数。時刻は引数で受け取る。"""
    by_name: dict[str, dict[str, Any]] = {}
    for t in sorted(tables, key=lambda r: r["table_name"]):
        by_name[t["table_name"]] = {
            "name": t["table_name"],
            "comment": t.get("comments"),
            "num_rows": _as_int(t.get("num_rows")),
            "last_analyzed": iso_utc(t.get("last_analyzed")),
            "iot": t.get("iot_type") == "IOT",
            "columns": [],
            "constraints": [],
            "indexes": [],
        }

    for c in sorted(columns, key=lambda r: (r["table_name"], r["column_id"] or 0)):
        table = by_name.get(c["table_name"])
        if table is None:  # ビューなど Q-01 に無いもの
            continue
        table["columns"].append(
            {
                "column_id": _as_int(c["column_id"]),
                "name": c["column_name"],
                "data_type": c["data_type"],
                "data_type_display": format_data_type(
                    c["data_type"],
                    _as_int(c.get("data_length")),
                    _as_int(c.get("data_precision")),
                    _as_int(c.get("data_scale")),
                    _as_int(c.get("char_length")),
                    c.get("char_used"),
                ),
                "data_length": _as_int(c.get("data_length")),
                "data_precision": _as_int(c.get("data_precision")),
                "data_scale": _as_int(c.get("data_scale")),
                "char_length": _as_int(c.get("char_length")),
                "char_used": c.get("char_used"),
                "nullable": c.get("nullable") == "Y",
                "data_default": _clean_default(c.get("data_default")),
                "comment": c.get("comments"),
            }
        )

    cons: dict[tuple[str, str], dict[str, Any]] = {}
    for r in constraints:
        table = by_name.get(r["table_name"])
        if table is None:
            continue
        key = (r["table_name"], r["constraint_name"])
        entry = cons.get(key)
        if entry is None:
            is_fk = r["constraint_type"] == "R"
            entry = {
                "name": r["constraint_name"],
                "type": r["constraint_type"],
                "_cols": [],
                "ref_owner": r.get("r_owner") if is_fk else None,
                "ref_table": r.get("r_table_name") if is_fk else None,
                "delete_rule": r.get("delete_rule") if is_fk else None,
            }
            cons[key] = entry
            table["constraints"].append(entry)
        pos = _as_int(r.get("position"))
        entry["_cols"].append((pos if pos is not None else len(entry["_cols"]) + 1, r["column_name"], r.get("r_column_name")))
    for entry in cons.values():
        cols = sorted(entry.pop("_cols"), key=lambda x: x[0])
        entry["columns"] = [c[1] for c in cols]
        entry["ref_columns"] = [c[2] for c in cols] if entry["type"] == "R" else None

    expr = {(e["index_name"], _as_int(e["column_position"])): str(e["column_expression"]).strip() for e in expressions}
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    for r in indexes:
        table = by_name.get(r["table_name"])
        if table is None:
            continue
        key = (r["table_name"], r["index_name"])
        entry = idx.get(key)
        if entry is None:
            entry = {"name": r["index_name"], "unique": r["uniqueness"] == "UNIQUE", "index_type": r["index_type"], "_cols": []}
            idx[key] = entry
            table["indexes"].append(entry)
        pos = _as_int(r["column_position"])
        name = expr.get((r["index_name"], pos), r["column_name"])
        entry["_cols"].append((pos, {"name": name, "descending": r.get("descend") == "DESC"}))
    for entry in idx.values():
        entry["columns"] = [c for _, c in sorted(entry.pop("_cols"), key=lambda x: x[0])]

    for table in by_name.values():
        table["constraints"].sort(key=lambda c: c["name"])
        table["indexes"].sort(key=lambda i: i["name"])

    return {
        "owner": owner,
        "oracle_version": oracle_version,
        "fetched_at": iso_utc(fetched_at),
        "tables": list(by_name.values()),
    }


async def get_schema_snapshot(
    db: Database, owner: str | None, default_owner: str, now: Callable[[], dt.datetime]
) -> dict[str, Any]:
    target = validate_identifier(owner if owner is not None else default_owner, "owner")

    async def work(conn: Any) -> dict[str, Any]:
        if not await q.owner_exists(conn, target):
            raise OracleFailure(NOT_FOUND, f"スキーマ {target} が見つかりません")
        tables = await q.fetch_tables(conn, target)
        columns = await q.fetch_columns(conn, target)
        constraints = await q.fetch_constraints(conn, target)
        indexes = await q.fetch_indexes(conn, target)
        expressions = await q.fetch_expressions(conn, target)
        return build_snapshot(target, conn.version, now(), tables, columns, constraints, indexes, expressions)

    return await db.run_readonly(work)
