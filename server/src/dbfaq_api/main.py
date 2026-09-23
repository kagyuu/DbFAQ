"""FastAPI アプリ(docs/P003-backend-spec.md §4)。uvicorn は --factory dbfaq_api.main:create_app で起動する。"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from dbfaq_common.config import AppConfig, config_file_path, load_config
from dbfaq_common.logging import setup_logging

from .db import create_sqlite_engine
from .errors import INTERNAL_ERROR, VALIDATION_ERROR, ApiError, McpUnavailable
from .mcp_gateway import Gateway, StdioMcpGateway
from .migrate import apply_all
from .routers import health, schema
from .services import SchemaService
from .snapshot_repo import SnapshotRepository

logger = logging.getLogger("dbfaq_api")


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def create_app(
    config: AppConfig | None = None,
    gateway: Gateway | None = None,
    now: Callable[[], dt.datetime] | None = None,
) -> FastAPI:
    config = config if config is not None else load_config()
    now = now or _utc_now
    setup_logging(config.app.log_level)
    # uvicorn 自身のログも JSON に揃える。アクセスログは下のミドルウェアが JSON で出すので止める。
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_sqlite_engine(config.app.sqlite_path)
        applied = apply_all(engine, now=lambda: now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        if applied:
            logger.info("migrations applied", extra={"versions": applied})
        gw = gateway if gateway is not None else StdioMcpGateway(config_file_path(), config.app.mcp_call_timeout_sec)
        try:
            await gw.start()
        except McpUnavailable as e:  # MCP が起動できなくても backend は起動を続ける(次の呼び出しで再試行)
            logger.warning("MCP server is not available at startup", extra={"error": str(e)})
        app.state.now = now
        app.state.service = SchemaService(SnapshotRepository(engine), gw, config, asyncio.Lock())
        try:
            yield
        finally:
            await gw.close()
            engine.dispose()

    app = FastAPI(title="DbFAQ", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.http_status, content=exc.body())

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        parts = [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()]
        err = ApiError(VALIDATION_ERROR, ", ".join(parts))
        return JSONResponse(status_code=err.http_status, content=err.body())

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        logger.exception("unexpected error")
        err = ApiError(INTERNAL_ERROR, "内部エラーが発生しました")
        return JSONResponse(status_code=err.http_status, content=err.body())

    @app.middleware("http")
    async def _access_log(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        return response

    app.include_router(schema.router)
    app.include_router(health.router)
    return app
