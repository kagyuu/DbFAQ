"""API の内部処理(docs/P003-backend-spec.md §4.3)。"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time
from typing import IO, Any

from starlette.concurrency import run_in_threadpool

from . import __version__
from .config import AppConfig
from .errors import (
    INTERNAL_ERROR,
    ORACLE_ERROR,
    ORACLE_TIMEOUT,
    REFRESH_IN_PROGRESS,
    SCHEMA_NOT_LOADED,
    SQL_REJECTED,
    TABLE_NOT_FOUND,
    VALIDATION_ERROR,
    ApiError,
)
from .oracle import errors as oracle_errors
from .oracle.client import OracleAccess
from .oracle.errors import OracleFailure
from .snapshot_repo import SnapshotRepository

logger = logging.getLogger(__name__)


def _to_api_error(e: OracleFailure, context: str, owner: str = "") -> ApiError:
    """Oracle アクセスのエラーを API エラーに変換する(P003 §4.1 の表)。"""
    if e.code == oracle_errors.ORACLE_ERROR:
        return ApiError(ORACLE_ERROR, e.message, e.ora_code, position=e.position)
    if e.code == oracle_errors.ORACLE_TIMEOUT:
        return ApiError(ORACLE_TIMEOUT, e.message or "Oracle の応答がタイムアウトしました")
    if e.code == oracle_errors.NOT_FOUND:
        if context == "rows":
            return ApiError(ORACLE_ERROR, "テーブルが Oracle 上に見つかりません(削除された可能性があります)", "ORA-00942")
        return ApiError(ORACLE_ERROR, f"スキーマ {owner} が見つかりません")
    if e.code == oracle_errors.INVALID_ARGUMENT:
        return ApiError(VALIDATION_ERROR, e.message)
    if e.code == oracle_errors.SQL_REJECTED:
        return ApiError(SQL_REJECTED, e.message)
    return ApiError(INTERNAL_ERROR, "内部エラーが発生しました")


class SchemaService:
    def __init__(self, repo: SnapshotRepository, oracle: OracleAccess, config: AppConfig, refresh_lock: asyncio.Lock):
        self.repo = repo
        self.oracle = oracle
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
                raw = await self.oracle.get_schema_snapshot(self.owner)
            except OracleFailure as e:
                raise _to_api_error(e, "refresh", owner=self.owner) from e
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
            result = await self.oracle.get_table_rows(owner, table, offset, limit)
        except OracleFailure as e:
            raise _to_api_error(e, "rows", owner=owner) from e
        return {"owner": owner, "table": table, **result}

    async def health(self, now: dt.datetime) -> dict[str, Any]:
        o = self.config.oracle
        oracle: dict[str, Any] = {"status": "ok", "version": None, "user": None, "message": None}
        try:
            pong = await self.oracle.ping()
            oracle.update(version=pong.get("version"), user=pong.get("user"))
        except OracleFailure as e:
            oracle.update(status="error", message=e.message)
        except Exception:  # health は常に 200 で返す(P003 §4.3)
            logger.exception("unexpected error in health check")
            oracle.update(status="error", message="内部エラーが発生しました")
        return {
            "status": "ok" if oracle["status"] == "ok" else "degraded",
            "backend": {"status": "ok", "version": __version__},
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


class QueryService:
    """Query タブの SELECT の実行(P003 §4.3)。SQL の本文と結果はログに出さない。"""

    def __init__(self, oracle: OracleAccess, max_rows: int = 500):
        self.oracle = oracle
        self.max_rows = max_rows

    def _log(self, kind: str, sql: str, started: float, **extra: Any) -> None:
        logger.info(
            kind,
            extra={"sql_chars": len(sql), "elapsed_ms": int((time.perf_counter() - started) * 1000), **extra},
        )

    async def run(self, sql: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = await self.oracle.run_query(sql, self.max_rows)
        except OracleFailure as e:
            self._log("query failed", sql, started, code=e.code, ora_code=e.ora_code)
            raise _to_api_error(e, "query") from e
        self._log("query", sql, started, row_count=result["row_count"], has_more=result["has_more"])
        return result

    async def csv(self, sql: str) -> tuple[IO[bytes], int]:
        started = time.perf_counter()
        try:
            spool, count = await self.oracle.export_csv(sql)
        except OracleFailure as e:
            self._log("query csv failed", sql, started, code=e.code, ora_code=e.ora_code)
            raise _to_api_error(e, "query") from e
        self._log("query csv", sql, started, row_count=count)
        return spool, count
