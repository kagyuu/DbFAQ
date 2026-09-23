"""データディクショナリの問い合わせ Q-00〜Q-05(docs/P003-backend-spec.md §3.5)。

結合の書き方は ../OracleSearchMCP/app/src/repositories/schema-metadata.ts を踏襲している。
"""

from __future__ import annotations

from typing import Any

Q00_USER = "SELECT USERNAME FROM ALL_USERS WHERE USERNAME = :owner"

Q01_TABLES = """
SELECT t.TABLE_NAME, t.NUM_ROWS, t.LAST_ANALYZED, t.IOT_TYPE, c.COMMENTS
  FROM ALL_TABLES t
  LEFT JOIN ALL_TAB_COMMENTS c ON c.OWNER = t.OWNER AND c.TABLE_NAME = t.TABLE_NAME
 WHERE t.OWNER = :owner
   AND t.NESTED = 'NO' AND t.SECONDARY = 'N' AND t.DROPPED = 'NO'
   AND (t.IOT_TYPE IS NULL OR t.IOT_TYPE = 'IOT')
 ORDER BY t.TABLE_NAME
"""

Q02_COLUMNS = """
SELECT col.TABLE_NAME, col.COLUMN_ID, col.COLUMN_NAME, col.DATA_TYPE, col.DATA_LENGTH,
       col.DATA_PRECISION, col.DATA_SCALE, col.CHAR_LENGTH, col.CHAR_USED, col.NULLABLE,
       col.DATA_DEFAULT, cc.COMMENTS
  FROM ALL_TAB_COLUMNS col
  LEFT JOIN ALL_COL_COMMENTS cc
    ON cc.OWNER = col.OWNER AND cc.TABLE_NAME = col.TABLE_NAME AND cc.COLUMN_NAME = col.COLUMN_NAME
 WHERE col.OWNER = :owner
 ORDER BY col.TABLE_NAME, col.COLUMN_ID
"""

Q03_CONSTRAINTS = """
SELECT c.CONSTRAINT_NAME, c.TABLE_NAME, c.CONSTRAINT_TYPE, c.DELETE_RULE, c.R_OWNER,
       rc.TABLE_NAME AS R_TABLE_NAME, cc.COLUMN_NAME, cc.POSITION, rcc.COLUMN_NAME AS R_COLUMN_NAME
  FROM ALL_CONSTRAINTS c
  JOIN ALL_CONS_COLUMNS cc
    ON cc.OWNER = c.OWNER AND cc.CONSTRAINT_NAME = c.CONSTRAINT_NAME
  LEFT JOIN ALL_CONSTRAINTS rc
    ON rc.OWNER = c.R_OWNER AND rc.CONSTRAINT_NAME = c.R_CONSTRAINT_NAME
  LEFT JOIN ALL_CONS_COLUMNS rcc
    ON rcc.OWNER = rc.OWNER AND rcc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME AND rcc.POSITION = cc.POSITION
 WHERE c.OWNER = :owner AND c.CONSTRAINT_TYPE IN ('P', 'U', 'R')
 ORDER BY c.TABLE_NAME, c.CONSTRAINT_NAME, cc.POSITION
"""

Q04_INDEXES = """
SELECT i.TABLE_NAME, i.INDEX_NAME, i.UNIQUENESS, i.INDEX_TYPE, ic.COLUMN_NAME, ic.COLUMN_POSITION, ic.DESCEND
  FROM ALL_INDEXES i
  JOIN ALL_IND_COLUMNS ic ON ic.INDEX_OWNER = i.OWNER AND ic.INDEX_NAME = i.INDEX_NAME
 WHERE i.TABLE_OWNER = :owner AND i.INDEX_TYPE <> 'LOB'
 ORDER BY i.TABLE_NAME, i.INDEX_NAME, ic.COLUMN_POSITION
"""

Q05_EXPRESSIONS = """
SELECT INDEX_NAME, COLUMN_POSITION, COLUMN_EXPRESSION
  FROM ALL_IND_EXPRESSIONS
 WHERE TABLE_OWNER = :owner
"""


async def _fetch(conn: Any, sql: str, **binds: Any) -> list[dict[str, Any]]:
    cursor = conn.cursor()
    try:
        await cursor.execute(sql, binds)
        names = [d.name.lower() for d in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in await cursor.fetchall()]
    finally:
        cursor.close()


async def owner_exists(conn: Any, owner: str) -> bool:
    return len(await _fetch(conn, Q00_USER, owner=owner)) > 0


async def fetch_tables(conn: Any, owner: str) -> list[dict[str, Any]]:
    return await _fetch(conn, Q01_TABLES, owner=owner)


async def fetch_columns(conn: Any, owner: str) -> list[dict[str, Any]]:
    return await _fetch(conn, Q02_COLUMNS, owner=owner)


async def fetch_constraints(conn: Any, owner: str) -> list[dict[str, Any]]:
    return await _fetch(conn, Q03_CONSTRAINTS, owner=owner)


async def fetch_indexes(conn: Any, owner: str) -> list[dict[str, Any]]:
    return await _fetch(conn, Q04_INDEXES, owner=owner)


async def fetch_expressions(conn: Any, owner: str) -> list[dict[str, Any]]:
    return await _fetch(conn, Q05_EXPRESSIONS, owner=owner)
