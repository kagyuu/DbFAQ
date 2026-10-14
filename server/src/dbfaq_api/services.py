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
    LLM_ERROR,
    LLM_TIMEOUT,
    LLM_UNAVAILABLE,
    ORACLE_ERROR,
    ORACLE_TIMEOUT,
    QUERY_NAME_CONFLICT,
    REFRESH_IN_PROGRESS,
    SAVED_QUERY_NOT_FOUND,
    SCHEMA_NOT_LOADED,
    SQL_REJECTED,
    TABLE_NOT_FOUND,
    VALIDATION_ERROR,
    ApiError,
)
from .llm import client as llm_client
from .llm.client import LlmAccess, LlmFailure
from .llm.context import build_pdb_context, build_table_context
from .llm.prompt import SYSTEM_PROMPT, build_user_prompt, extract_sql
from .oracle import errors as oracle_errors
from .oracle.client import OracleAccess
from .oracle.errors import OracleFailure
from .oracle.sql_guard import check_select
from .saved_query_repo import NameConflict, SavedQueryRepository
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
    def __init__(
        self,
        repo: SnapshotRepository,
        oracle: OracleAccess,
        config: AppConfig,
        refresh_lock: asyncio.Lock,
        llm: LlmAccess | None = None,
    ):
        self.repo = repo
        self.oracle = oracle
        self.config = config
        self.refresh_lock = refresh_lock
        self.llm = llm if llm is not None else llm_client.DisabledLlm()

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

    async def _oracle_health(self) -> dict[str, Any]:
        oracle: dict[str, Any] = {"status": "ok", "version": None, "user": None, "message": None}
        try:
            pong = await self.oracle.ping()
            oracle.update(version=pong.get("version"), user=pong.get("user"))
        except OracleFailure as e:
            oracle.update(status="error", message=e.message)
        except Exception:  # health は常に 200 で返す(P003 §4.3)
            logger.exception("unexpected error in health check")
            oracle.update(status="error", message="内部エラーが発生しました")
        return oracle

    async def _llm_health(self) -> dict[str, Any]:
        try:
            return await self.llm.health()
        except Exception:  # health は常に 200 で返す(P003 §4.8.4。※CR-007により追加)
            logger.exception("unexpected error in llm health check")
            return {"status": "error", "model": self.llm.model, "base_url": None, "message": "内部エラーが発生しました"}

    async def health(self, now: dt.datetime) -> dict[str, Any]:
        o = self.config.oracle
        # Oracle と LLM の疎通確認は並行して行う。最上位の status は Oracle だけで決める(※CR-007)
        oracle, llm = await asyncio.gather(self._oracle_health(), self._llm_health())
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
            "llm": llm,
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


def check_target(scope: str, owner: str | None, table: str | None) -> None:
    """保存先の scope と owner・table の組み合わせを検査する(P002 §3.10)。違反は 422 VALIDATION_ERROR。"""
    if scope == "table":
        missing = [n for n, v in (("owner", owner), ("table", table)) if not v]
        if missing:
            raise ApiError(VALIDATION_ERROR, ", ".join(f"{n}: scope=table のときは必須です" for n in missing))
    else:
        given = [n for n, v in (("owner", owner), ("table", table)) if v is not None]
        if given:
            raise ApiError(VALIDATION_ERROR, ", ".join(f"{n}: scope=pdb のときは指定しません" for n in given))


class SavedQueryService:
    """保存済み Query(P003 §4.3・§4.6)。SQLite だけを使い、Oracle・スナップショットにはアクセスしない。※CR-005により追加

    名前・説明・SQL の本文はログに出さない。
    """

    def __init__(self, repo: SavedQueryRepository):
        self.repo = repo

    async def list(self, scope: str, owner: str | None, table: str | None) -> dict[str, Any]:
        check_target(scope, owner, table)
        return {"items": await run_in_threadpool(self.repo.list, scope, owner, table)}

    async def create(self, scope: str, owner: str | None, table: str | None, name: str, description: str,
                     sql: str) -> dict[str, Any]:
        check_target(scope, owner, table)
        try:
            item = await run_in_threadpool(self.repo.create, scope, owner, table, name, description, sql)
        except NameConflict as e:
            raise ApiError(QUERY_NAME_CONFLICT, f"同じ名前の Query が既にあります: {name}") from e
        logger.info("saved query created", extra={"saved_query_id": item["id"], "scope": scope, "sql_chars": len(sql)})
        return item

    async def update(self, query_id: int, name: str, description: str, sql: str) -> dict[str, Any]:
        try:
            item = await run_in_threadpool(self.repo.update, query_id, name, description, sql)
        except NameConflict as e:
            raise ApiError(QUERY_NAME_CONFLICT, f"同じ名前の Query が既にあります: {name}") from e
        if item is None:
            raise ApiError(SAVED_QUERY_NOT_FOUND, f"保存済みの Query が見つかりません: {query_id}")
        logger.info("saved query updated", extra={"saved_query_id": query_id, "sql_chars": len(sql)})
        return item

    async def delete(self, query_id: int) -> None:
        if not await run_in_threadpool(self.repo.delete, query_id):
            raise ApiError(SAVED_QUERY_NOT_FOUND, f"保存済みの Query が見つかりません: {query_id}")
        logger.info("saved query deleted", extra={"saved_query_id": query_id})


class PdbService:
    """PDB の情報(P003 §4.3・§3.12)。※CR-005により追加"""

    def __init__(self, oracle: OracleAccess):
        self.oracle = oracle

    async def info(self, now: dt.datetime) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            result = await self.oracle.get_pdb_info()
        except OracleFailure as e:
            raise _to_api_error(e, "pdb") from e
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        failed = [{"key": s["key"], "ora_code": s["error"].get("ora_code")} for s in result["sections"] if s["error"]]
        logger.info("pdb info", extra={"sections": len(result["sections"]), "failed": failed, "elapsed_ms": elapsed_ms})
        return {
            **result,
            "fetched_at": now.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "elapsed_ms": elapsed_ms,
        }


_LLM_ERRORS = {
    llm_client.LLM_UNAVAILABLE: LLM_UNAVAILABLE,
    llm_client.LLM_TIMEOUT: LLM_TIMEOUT,
    llm_client.LLM_ERROR: LLM_ERROR,
}


class LlmService:
    """自然言語の要求から LLM で SELECT を作る(P003 §4.8.4、ADR-018)。作った SQL は検査するが実行しない。

    要求の文・SQL・データの例はログに出さない。※CR-007により追加
    """

    def __init__(self, repo: SnapshotRepository, oracle: OracleAccess, llm: LlmAccess, config: AppConfig):
        self.repo = repo
        self.oracle = oracle
        self.llm = llm
        self.config = config

    async def _table_context(self, owner: str, table: str) -> Any:
        exists = await run_in_threadpool(self.repo.table_exists, owner, table)
        if exists is None:
            raise ApiError(SCHEMA_NOT_LOADED, "スキーマ情報がまだ読み込まれていません")
        main = await run_in_threadpool(self.repo.get_table_detail, owner, table) if exists else None
        if main is None:
            raise ApiError(TABLE_NOT_FOUND, f"テーブルが見つかりません: {owner}.{table}")
        keys = [(fk["ref_owner"], fk["ref_table"]) for fk in main["foreign_keys"] if fk.get("ref_in_snapshot")]
        keys += [(r["from_owner"], r["from_table"]) for r in main["referenced_by"]]
        related = []
        for o, t in dict.fromkeys(keys):
            if (o, t) != (owner, table):
                d = await run_in_threadpool(self.repo.get_table_detail, o, t)
                if d is not None:
                    related.append(d)
        summary = await run_in_threadpool(self.repo.get_summary, owner)
        cfg = self.config.llm
        samples = None
        if cfg.sample_rows > 0:
            try:
                samples = await self.oracle.get_table_rows(owner, table, 0, cfg.sample_rows)
            except OracleFailure as e:  # データの例なしで作成を続ける(P002 §3.15)
                logger.info("llm sample rows unavailable", extra={"code": e.code, "ora_code": e.ora_code})
        return build_table_context(
            main, related, summary["oracle_version"] if summary else None, samples, cfg.sample_rows, cfg.max_context_chars
        )

    async def _pdb_context(self) -> Any:
        owner = self.config.oracle.target_schema
        view = await run_in_threadpool(self.repo.get_er_view, owner)
        version = view["snapshot"]["oracle_version"] if view.get("snapshot") else None
        return build_pdb_context(view, version, owner, self.config.llm.max_context_chars)

    async def generate(self, request: str, scope: str, owner: str | None, table: str | None) -> dict[str, Any]:
        check_target(scope, owner, table)
        cfg = self.config.llm
        if cfg is None or not cfg.enabled:
            raise ApiError(LLM_UNAVAILABLE, llm_client.NOT_CONFIGURED)
        context = await (self._table_context(owner, table) if scope == "table" else self._pdb_context())
        user = build_user_prompt(context.text, request)
        # LLM とのやりとり。画面にだけ返し、ログには出さない(※CR-008により追加)
        exchange: dict[str, Any] = {"system": SYSTEM_PROMPT, "user": user, "reply": None}
        started = time.perf_counter()
        try:
            answer = await self.llm.chat(SYSTEM_PROMPT, user)
        except LlmFailure as e:
            logger.info("llm sql failed", extra={"code": e.code, "request_chars": len(request), "scope": scope})
            raise ApiError(_LLM_ERRORS.get(e.code, LLM_ERROR), e.message, extra={"exchange": exchange}) from e
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        exchange["reply"] = answer
        sql = extract_sql(answer)
        if not sql:
            logger.info("llm sql failed", extra={"code": LLM_ERROR, "request_chars": len(request), "scope": scope})
            raise ApiError(LLM_ERROR, "LLM の応答から SQL を取り出せませんでした", extra={"exchange": exchange})
        guard = {"ok": True, "message": None}
        try:
            check_select(sql)
        except OracleFailure as e:
            guard = {"ok": False, "message": e.message}
        logger.info(
            "llm sql",
            extra={
                "scope": scope,
                "request_chars": len(request),
                "sql_chars": len(sql),
                "model": self.llm.model,
                "tables": len(context.tables),
                "sample_rows": context.sample_rows,
                "guard_ok": guard["ok"],
                "elapsed_ms": elapsed_ms,
            },
        )
        return {
            "sql": sql,
            "guard": guard,
            "model": self.llm.model,
            "elapsed_ms": elapsed_ms,
            "context": context.summary(),
            "exchange": exchange,
        }
