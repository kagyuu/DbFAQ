"""PDB の情報の読み取り(docs/P003-backend-spec.md §3.12)。※CR-005により追加

決まった SELECT を 1 回の読み取り専用トランザクションの中でセクションの順に実行する。
権限不足などで失敗したセクションはそのセクションの error に入れて次へ進む。タイムアウトは全体の失敗にする。
"""

from __future__ import annotations

from typing import Any

import oracledb

from .db import Database
from .errors import ORACLE_TIMEOUT, from_oracle_error
from .query import _columns
from .values import format_row

MAX_SECTION_ROWS = 500

_OVERVIEW_SQL = """\
SELECT
  SYS_CONTEXT('USERENV', 'CON_NAME'),
  SYS_CONTEXT('USERENV', 'DB_NAME'),
  SYS_CONTEXT('USERENV', 'SERVICE_NAME'),
  USER,
  SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA'),
  (SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_CHARACTERSET'),
  (SELECT value FROM nls_database_parameters WHERE parameter = 'NLS_NCHAR_CHARACTERSET'),
  (SELECT default_tablespace FROM user_users),
  (SELECT temporary_tablespace FROM user_users)
FROM DUAL"""

# overview の 1 行を ITEM・VALUE に組み替えるときの項目名(SQL の列の順。バージョンは conn.version)
_OVERVIEW_ITEMS = (
    "コンテナ名(PDB)",
    "DB 名",
    "サービス名",
    "接続ユーザー",
    "カレントスキーマ",
    "文字セット",
    "各国語文字セット",
    "既定の表領域",
    "一時表領域",
)

_TS_QUOTAS_SQL = """\
SELECT
  tablespace_name,
  ROUND(bytes / 1024 / 1024, 2) AS used_mb,
  CASE WHEN max_bytes = -1 THEN 'UNLIMITED' ELSE TO_CHAR(ROUND(max_bytes / 1024 / 1024, 2)) END AS max_mb
FROM user_ts_quotas
ORDER BY tablespace_name"""

_SEGMENTS_SQL = """\
SELECT segment_type, COUNT(*) AS segments, ROUND(SUM(bytes) / 1024 / 1024, 2) AS size_mb
FROM user_segments
GROUP BY segment_type
ORDER BY SUM(bytes) DESC"""

_TABLESPACES_SQL = """\
SELECT
  df.tablespace_name,
  ROUND(df.bytes / 1024 / 1024, 2) AS total_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / 1024 / 1024, 2) AS used_mb,
  ROUND(NVL(fs.bytes, 0) / 1024 / 1024, 2) AS free_mb,
  ROUND((df.bytes - NVL(fs.bytes, 0)) / df.bytes * 100, 1) AS used_pct,
  ROUND(df.max_bytes / 1024 / 1024, 2) AS max_mb
FROM (
  SELECT
    tablespace_name,
    SUM(bytes) AS bytes,
    SUM(CASE WHEN autoextensible = 'YES' THEN GREATEST(maxbytes, bytes) ELSE bytes END) AS max_bytes
  FROM dba_data_files
  GROUP BY tablespace_name
) df
  LEFT JOIN (
    SELECT tablespace_name, SUM(bytes) AS bytes
    FROM dba_free_space
    GROUP BY tablespace_name
  ) fs ON fs.tablespace_name = df.tablespace_name
ORDER BY used_pct DESC"""

SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("overview", "概要", _OVERVIEW_SQL),
    ("ts_quotas", "表領域の割り当て(接続ユーザー)", _TS_QUOTAS_SQL),
    ("segments", "セグメントの使用量(接続ユーザー)", _SEGMENTS_SQL),
    ("tablespaces", "表領域の使用状況", _TABLESPACES_SQL),
)

_VARCHAR = "VARCHAR"


def _section(key: str, title: str) -> dict[str, Any]:
    return {"key": key, "title": title, "columns": [], "rows": [], "truncated": [], "error": None}


def _overview(section: dict[str, Any], row: Any, version: str | None) -> None:
    values = list(row) if row else [None] * len(_OVERVIEW_ITEMS)
    pairs = list(zip(_OVERVIEW_ITEMS, values, strict=True))
    pairs.insert(3, ("バージョン", version))
    section["columns"] = [{"name": "ITEM", "data_type": _VARCHAR}, {"name": "VALUE", "data_type": _VARCHAR}]
    section["rows"] = [[item, None if v is None else str(v)] for item, v in pairs]
    section["truncated"] = [[] for _ in pairs]


async def get_pdb_info(db: Database) -> dict[str, Any]:
    async def work(conn: Any) -> dict[str, Any]:
        sections = []
        for key, title, sql in SECTIONS:
            section = _section(key, title)
            cur = conn.cursor()
            try:
                await cur.execute(sql)
                fetched = await cur.fetchmany(MAX_SECTION_ROWS)
                if key == "overview":
                    _overview(section, fetched[0] if fetched else None, conn.version)
                else:
                    columns, type_names = _columns(cur.description)
                    section["columns"] = columns
                    for row in fetched:
                        cells, cut = format_row(row, type_names)
                        section["rows"].append(cells)
                        section["truncated"].append(cut)
            except oracledb.Error as e:
                failure = from_oracle_error(e, db.secret)
                if failure.code == ORACLE_TIMEOUT:
                    raise failure from e
                section["error"] = {"code": failure.code, "message": failure.message, "ora_code": failure.ora_code}
            finally:
                cur.close()
            sections.append(section)
        return {"sections": sections}

    return await db.run_readonly(work)
