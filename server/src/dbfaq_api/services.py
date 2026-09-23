"""API の内部処理(docs/P003-backend-spec.md §4.3)。"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time
from typing import Any

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from dbfaq_common.config import AppConfig

from . import __version__
from .errors import (
    INTERNAL_ERROR,
    MCP_UNAVAILABLE,
    ORACLE_ERROR,
    ORACLE_TIMEOUT,
    REFRESH_IN_PROGRESS,
    SCHEMA_NOT_LOADED,
    TABLE_NOT_FOUND,
    VALIDATION_ERROR,
    ApiError,
    McpToolError,
    McpUnavailable,
)
from .mcp_gateway import Gateway
from .schemas import McpSnapshot
from .snapshot_repo import SnapshotRepository

logger = logging.getLogger(__name__)

HEALTH_TIMEOUT_SEC = 5


def _mcp_to_api(e: McpToolError, context: str, owner: str = "", table: str = "") -> ApiError:
    """MCP のツールエラーを API エラーに変換する(P003 §4.1 の表)。"""
    if e.code == "ORACLE_ERROR":
        return ApiError(ORACLE_ERROR, e.message, e.ora_code)
    if e.code == "ORACLE_TIMEOUT":
        return ApiError(ORACLE_TIMEOUT, e.message or "Oracle の応答がタイムアウトしました")
    if e.code == "NOT_FOUND":
        if context == "rows":
            return ApiError(ORACLE_ERROR, "テーブルが Oracle 上に見つかりません(削除された可能性があります)", "ORA-00942")
        return ApiError(ORACLE_ERROR, f"スキーマ {owner} が見つかりません")
    if e.code == "INVALID_ARGUMENT":
        return ApiError(VALIDATION_ERROR, e.message)
    return ApiError(INTERNAL_ERROR, "内部エラーが発生しました")


def _unavailable(e: McpUnavailable) -> ApiError:
    return ApiError(MCP_UNAVAILABLE, str(e) or "MCP サーバに接続できません")


class SchemaService:
    def __init__(self, repo: SnapshotRepository, gateway: Gateway, config: AppConfig, refresh_lock: asyncio.Lock):
        self.repo = repo
        self.gateway = gateway
        self.config = config
        self.refresh_lock = refresh_lock

    @property
    def owner(self) -> str:
        return self.config.oracle.target_schema

    async def er_view(self) -> dict[str, Any]:
        return await run_in_threadpool(self.repo.get_er_view, self.owner)

    async def refresh(self) -> dict[str, Any]:
        if self.refresh_lock.locked():
            raise ApiError(REFRESH_IN_PROGRESS, "スキーマの再読み込みを実行中です")
        async with self.refresh_lock:
            started = time.perf_counter()
            try:
                raw = await self.gateway.call("get_schema_snapshot", {"owner": self.owner})
            except McpToolError as e:
                raise _mcp_to_api(e, "refresh", owner=self.owner) from e
            except McpUnavailable as e:
                raise _unavailable(e) from e
            try:
                McpSnapshot.model_validate(raw)
            except ValidationError as e:
                logger.error("unexpected snapshot shape from MCP", extra={"error": str(e)})
                raise ApiError(INTERNAL_ERROR, "内部エラーが発生しました") from e
            summary = await run_in_threadpool(self.repo.replace, raw)
            logger.info(
                "schema refreshed",
                extra={
                    "owner": summary["owner"],
                    "tables": summary["table_count"],
                    "relations": summary["relation_count"],
                    "elapsed_ms": int((time.perf_counter() - started) * 1000),
                },
            )
            return {"snapshot": summary}

    async def _check_table(self, owner: str, table: str) -> None:
        exists = await run_in_threadpool(self.repo.table_exists, owner, table)
        if exists is None:
            raise ApiError(SCHEMA_NOT_LOADED, "スキーマ情報がまだ読み込まれていません")
        if not exists:
            raise ApiError(TABLE_NOT_FOUND, f"テーブルが見つかりません: {owner}.{table}")

    async def table_detail(self, owner: str, table: str) -> dict[str, Any]:
        await self._check_table(owner, table)
        detail = await run_in_threadpool(self.repo.get_table_detail, owner, table)
        if detail is None:
            raise ApiError(TABLE_NOT_FOUND, f"テーブルが見つかりません: {owner}.{table}")
        return detail

    async def rows(self, owner: str, table: str, offset: int, limit: int) -> dict[str, Any]:
        await self._check_table(owner, table)
        try:
            result = await self.gateway.call(
                "get_table_rows", {"owner": owner, "table": table, "offset": offset, "limit": limit}
            )
        except McpToolError as e:
            raise _mcp_to_api(e, "rows", owner=owner, table=table) from e
        except McpUnavailable as e:
            raise _unavailable(e) from e
        return {"owner": owner, "table": table, **result}

    async def health(self, now: dt.datetime) -> dict[str, Any]:
        o = self.config.oracle
        mcp: dict[str, Any] = {"status": "ok", "message": None}
        oracle: dict[str, Any] = {"status": "ok", "version": None, "user": None, "message": None}
        try:
            pong = await self.gateway.call("ping", {}, timeout=HEALTH_TIMEOUT_SEC)
            oracle.update(version=pong.get("version"), user=pong.get("user"))
        except McpUnavailable as e:
            mcp = {"status": "error", "message": str(e)}
            oracle.update(status="error", message="MCP サーバに接続できないため確認できません")
        except McpToolError as e:
            oracle.update(status="error", message=e.message)
        return {
            "status": "ok" if mcp["status"] == "ok" and oracle["status"] == "ok" else "degraded",
            "backend": {"status": "ok", "version": __version__},
            "mcp": mcp,
            "oracle": oracle,
            "config": {
                "host": o.host,
                "port": o.port,
                "service_name": o.service_name,
                "user": o.user,
                "schema": o.target_schema,
                "query_timeout_sec": o.query_timeout_sec,
            },
            "checked_at": now.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
