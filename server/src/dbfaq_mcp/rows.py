"""テーブルデータのページ取得(docs/P003-backend-spec.md §3.6、ADR-006)。"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .db import Database
from .errors import INVALID_ARGUMENT, NOT_FOUND, ToolFailure
from .identifiers import quote, validate_identifier
from .values import format_row

MAX_OFFSET = 100_000
MAX_LIMIT = 500

_TABLE_EXISTS = "SELECT IOT_TYPE FROM ALL_TABLES WHERE OWNER = :o AND TABLE_NAME = :t"
_PK_COLUMNS = """
SELECT cc.COLUMN_NAME
  FROM ALL_CONSTRAINTS c
  JOIN ALL_CONS_COLUMNS cc ON cc.OWNER = c.OWNER AND cc.CONSTRAINT_NAME = c.CONSTRAINT_NAME
 WHERE c.OWNER = :o AND c.TABLE_NAME = :t AND c.CONSTRAINT_TYPE = 'P'
 ORDER BY cc.POSITION
"""


def build_rows_sql(owner: str, table: str, pk_columns: list[str]) -> tuple[str, str]:
    """(SQL, order_basis) を返す。識別子はクォートし、offset・件数はバインド変数で渡す。"""
    if pk_columns:
        order = ", ".join(quote(c) for c in pk_columns)
        basis = "PRIMARY_KEY"
    else:
        order = "ROWID"
        basis = "ROWID"
    sql = f"SELECT * FROM {quote(owner)}.{quote(table)} ORDER BY {order} OFFSET :off ROWS FETCH NEXT :n ROWS ONLY"
    return sql, basis


async def get_table_rows(
    db: Database,
    owner: str,
    table: str,
    offset: int,
    limit: int,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    validate_identifier(owner, "owner")
    validate_identifier(table, "table")
    if not isinstance(offset, int) or not 0 <= offset <= MAX_OFFSET:
        raise ToolFailure(INVALID_ARGUMENT, f"offset は 0 以上 {MAX_OFFSET} 以下で指定してください")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ToolFailure(INVALID_ARGUMENT, f"limit は 1 以上 {MAX_LIMIT} 以下で指定してください")

    async def work(conn: Any) -> dict[str, Any]:
        cur = conn.cursor()
        try:
            await cur.execute(_TABLE_EXISTS, {"o": owner, "t": table})
            if not await cur.fetchall():
                raise ToolFailure(NOT_FOUND, f"テーブル {owner}.{table} が見つかりません")
            await cur.execute(_PK_COLUMNS, {"o": owner, "t": table})
            pk_columns = [r[0] for r in await cur.fetchall()]
            sql, basis = build_rows_sql(owner, table, pk_columns)
            t0 = clock()
            await cur.execute(sql, {"off": offset, "n": limit + 1})
            fetched = await cur.fetchall()
            elapsed_ms = int((clock() - t0) * 1000)
            type_names = [d.type_code.name for d in cur.description]
            columns = [
                {"name": d.name, "data_type": name.removeprefix("DB_TYPE_")}
                for d, name in zip(cur.description, type_names, strict=True)
            ]
        finally:
            cur.close()
        has_next = len(fetched) > limit
        rows: list[list[str | None]] = []
        truncated: list[list[int]] = []
        for row in fetched[:limit]:
            cells, cut = format_row(row, type_names)
            rows.append(cells)
            truncated.append(cut)
        return {
            "columns": columns,
            "rows": rows,
            "truncated": truncated,
            "offset": offset,
            "limit": limit,
            "has_next": has_next,
            "order_basis": basis,
            "order_by": pk_columns if pk_columns else ["ROWID"],
            "elapsed_ms": elapsed_ms,
        }

    return await db.run_readonly(work)
