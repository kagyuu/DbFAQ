"""Oracle アクセスの入口(docs/P003-backend-spec.md §3.9、ADR-014)。"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import IO, Any, Protocol

from ..config import OracleConfig
from . import query as query_mod
from . import rows as rows_mod
from . import snapshot as snapshot_mod
from .db import Database
from .pdb import get_pdb_info as _get_pdb_info

HEALTH_TIMEOUT_SEC = 5

_PING_SQL = "SELECT USER, SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM DUAL"


class OracleAccess(Protocol):
    async def get_schema_snapshot(self, owner: str | None) -> dict[str, Any]: ...

    async def get_table_rows(self, owner: str, table: str, offset: int, limit: int) -> dict[str, Any]: ...

    async def ping(self) -> dict[str, Any]: ...

    async def run_query(self, sql: str, max_rows: int) -> dict[str, Any]: ...

    async def export_csv(self, sql: str) -> tuple[IO[bytes], int]: ...

    async def get_pdb_info(self) -> dict[str, Any]: ...

    async def close(self) -> None: ...


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class OracleClient:
    def __init__(self, cfg: OracleConfig, db: Database | None = None, now: Callable[[], dt.datetime] = _utc_now):
        self._cfg = cfg
        self._db = db if db is not None else Database(cfg)
        self._now = now

    async def get_schema_snapshot(self, owner: str | None) -> dict[str, Any]:
        """スキーマのテーブル・列・主キー・一意制約・外部キー・インデックス・コメント・統計をまとめて返す。"""
        return await snapshot_mod.get_schema_snapshot(self._db, owner, self._cfg.target_schema, now=self._now)

    async def get_table_rows(self, owner: str, table: str, offset: int, limit: int) -> dict[str, Any]:
        """テーブルのデータを主キー順(主キーが無ければ ROWID 順)に 1 ページ分返す。"""
        return await rows_mod.get_table_rows(self._db, owner, table, offset, limit)

    async def run_query(self, sql: str, max_rows: int = query_mod.MAX_ROWS) -> dict[str, Any]:
        """利用者の SELECT を実行し、先頭 max_rows 行を返す(P003 §3.11)。"""
        return await query_mod.run_query(self._db, sql, max_rows)

    async def export_csv(self, sql: str) -> tuple[IO[bytes], int]:
        """利用者の SELECT の全行を CSV の一時ファイルにして返す(P003 §3.11)。"""
        return await query_mod.export_csv(self._db, sql)

    async def get_pdb_info(self) -> dict[str, Any]:
        """PDB の情報をセクションごとに返す(権限不足のセクションは error 付き。P003 §3.12)。※CR-005により追加"""
        return await _get_pdb_info(self._db)

    async def ping(self) -> dict[str, Any]:
        """Oracle への疎通を確認し、バージョンと接続ユーザーを返す。問い合わせの上限は HEALTH_TIMEOUT_SEC。"""

        async def work(conn: Any) -> dict[str, Any]:
            cur = conn.cursor()
            try:
                await cur.execute(_PING_SQL)
                user, schema = (await cur.fetchall())[0]
            finally:
                cur.close()
            return {"version": conn.version, "user": user, "current_schema": schema}

        return await self._db.run_readonly(work, timeout_sec=HEALTH_TIMEOUT_SEC)

    async def close(self) -> None:
        await self._db.close()
