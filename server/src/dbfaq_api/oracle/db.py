"""Oracle 接続プールと読み取り専用トランザクション(docs/P003-backend-spec.md §3.1、ADR-011)。"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import oracledb

from ..config import OracleConfig
from .errors import OracleFailure, from_oracle_error, from_os_error

oracledb.defaults.fetch_decimals = True  # NUMBER を Decimal で受け取り精度を落とさない
oracledb.defaults.fetch_lobs = False  # CLOB は str、BLOB は bytes(ADR-005)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Database:
    def __init__(self, cfg: OracleConfig, pool_factory: Callable[..., Any] = oracledb.create_pool_async):
        self._cfg = cfg
        self._pool_factory = pool_factory
        self._pool: Any = None
        self._lock = asyncio.Lock()

    @property
    def secret(self) -> str:
        return self._cfg.password.get_secret_value()

    async def _get_pool(self) -> Any:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = self._pool_factory(
                        user=self._cfg.user,
                        password=self.secret,
                        dsn=self._cfg.dsn,
                        min=self._cfg.pool_min,
                        max=self._cfg.pool_max,
                        tcp_connect_timeout=self._cfg.connect_timeout_sec,
                        # 既定(WAIT)だと Oracle に接続できない間 acquire が戻らないため、時間を区切る(F006)
                        getmode=oracledb.POOL_GETMODE_TIMEDWAIT,
                        wait_timeout=self._cfg.connect_timeout_sec * 1000,
                    )
        return self._pool

    async def run_readonly(self, fn: Callable[[Any], Awaitable[T]], timeout_sec: int | None = None) -> T:
        """接続を借り、SET TRANSACTION READ ONLY の中で fn を実行し、必ず ROLLBACK する。

        timeout_sec を省略すると問い合わせの上限は query_timeout_sec になる。
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                conn.call_timeout = (timeout_sec or self._cfg.query_timeout_sec) * 1000
                await conn.execute("SET TRANSACTION READ ONLY")  # 失敗したら fn を実行しない
                try:
                    return await fn(conn)
                finally:
                    try:
                        await conn.rollback()
                    except Exception as rollback_err:  # 元の例外を上書きしない
                        logger.warning("rollback failed after a read-only transaction", extra={"error": str(rollback_err)})
        except OracleFailure:
            raise
        except oracledb.Error as e:
            raise from_oracle_error(e, self.secret) from e
        except OSError as e:
            raise from_os_error(e, self.secret) from e

    async def close(self) -> None:
        """プールを閉じる。Oracle に届かない間は python-oracledb の close が長く戻らないため、
        connect_timeout_sec で打ち切ってプールを捨てる(P202 F008、P003 §3.1)。"""
        if self._pool is not None:
            try:
                await asyncio.wait_for(self._pool.close(force=True), self._cfg.connect_timeout_sec)
            except TimeoutError:
                logger.warning("connection pool did not close in time; abandoning it")
            finally:
                self._pool = None
