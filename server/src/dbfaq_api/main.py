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

from . import __version__
from .config import AppConfig, load_config
from .db import create_sqlite_engine
from .errors import INTERNAL_ERROR, VALIDATION_ERROR, ApiError
from .log import setup_logging
from .migrate import apply_all
from .oracle.client import OracleAccess, OracleClient
from .pdb_templates import PDB_TEMPLATES
from .routers import health, pdb, query, saved_queries, schema
from .saved_query_repo import SavedQueryRepository
from .services import PdbService, QueryService, SavedQueryService, SchemaService
from .snapshot_repo import SnapshotRepository

logger = logging.getLogger("dbfaq_api")


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def create_app(
    config: AppConfig | None = None,
    oracle: OracleAccess | None = None,
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

        def stamp() -> str:
            return now().strftime("%Y-%m-%dT%H:%M:%SZ")

        applied = apply_all(engine, now=stamp)
        if applied:
            logger.info("migrations applied", extra={"versions": applied})
        # PDB のひな型は登録記録の無いものだけを 1 回登録する(P003 §4.7。※CR-005により追加)
        saved_repo = SavedQueryRepository(engine, stamp)
        seeded = saved_repo.seed_templates(PDB_TEMPLATES)
        if seeded:
            logger.info("pdb templates seeded", extra={"keys": seeded})
        # 接続プールは最初の Oracle アクセスで作る(Oracle に届かなくても backend は起動する)
        ora = oracle if oracle is not None else OracleClient(config.oracle)
        app.state.now = now
        app.state.service = SchemaService(SnapshotRepository(engine), ora, config, asyncio.Lock())
        app.state.query_service = QueryService(ora)
        app.state.saved_query_service = SavedQueryService(saved_repo)
        app.state.pdb_service = PdbService(ora)
        try:
            yield
        finally:
            await ora.close()
            engine.dispose()

    app = FastAPI(title="DbFAQ", version=__version__, lifespan=lifespan)

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
    app.include_router(query.router)
    app.include_router(saved_queries.router)
    app.include_router(pdb.router)
    return app
