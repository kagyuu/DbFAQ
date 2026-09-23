"""FastMCP サーバとツール登録(docs/P003-backend-spec.md §3、ADR-001)。"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Awaitable
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from dbfaq_common.config import AppConfig

from . import rows as rows_mod
from . import snapshot as snapshot_mod
from .db import Database
from .errors import INTERNAL_ERROR, ToolFailure

logger = logging.getLogger(__name__)


async def _call(coro: Awaitable[dict[str, Any]]) -> dict[str, Any]:
    try:
        return await coro
    except ToolFailure as f:
        raise ToolError(f.to_json()) from None
    except Exception:
        logger.exception("unexpected error in MCP tool")
        raise ToolError(ToolFailure(INTERNAL_ERROR, "内部エラーが発生しました").to_json()) from None


def create_server(cfg: AppConfig, db: Database | None = None) -> FastMCP:
    mcp = FastMCP("dbfaq-oracle")
    database = db if db is not None else Database(cfg.oracle)

    @mcp.tool
    async def get_schema_snapshot(owner: str | None = None) -> dict[str, Any]:
        """スキーマのテーブル・列・主キー・一意制約・外部キー・インデックス・コメント・統計をまとめて返す。"""
        return await _call(
            snapshot_mod.get_schema_snapshot(
                database, owner, cfg.oracle.target_schema, now=lambda: dt.datetime.now(dt.UTC)
            )
        )

    @mcp.tool
    async def get_table_rows(owner: str, table: str, offset: int = 0, limit: int = 50) -> dict[str, Any]:
        """テーブルのデータを主キー順(主キーが無ければ ROWID 順)に 1 ページ分返す。"""
        return await _call(rows_mod.get_table_rows(database, owner, table, offset, limit))

    @mcp.tool
    async def ping() -> dict[str, Any]:
        """Oracle への疎通を確認し、バージョンと接続ユーザーを返す。"""

        async def work(conn: Any) -> dict[str, Any]:
            cur = conn.cursor()
            try:
                await cur.execute("SELECT USER, SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM DUAL")
                user, schema = (await cur.fetchall())[0]
            finally:
                cur.close()
            return {"version": conn.version, "user": user, "current_schema": schema}

        return await _call(database.run_readonly(work))

    return mcp
