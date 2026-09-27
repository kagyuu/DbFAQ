"""backend の単体テスト用の偽の Oracle アクセス(dbfaq_api.oracle.client.OracleAccess)。"""

from __future__ import annotations

import inspect
from typing import Any


class FakeOracle:
    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses: dict[str, Any] = responses or {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def _respond(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, args))
        resp = self.responses[name]
        if callable(resp):
            resp = resp(args)
            if inspect.isawaitable(resp):
                resp = await resp
        if isinstance(resp, BaseException):
            raise resp
        return resp

    async def get_schema_snapshot(self, owner: str | None) -> dict[str, Any]:
        return await self._respond("get_schema_snapshot", {"owner": owner})

    async def get_table_rows(self, owner: str, table: str, offset: int, limit: int) -> dict[str, Any]:
        return await self._respond("get_table_rows", {"owner": owner, "table": table, "offset": offset, "limit": limit})

    async def ping(self) -> dict[str, Any]:
        return await self._respond("ping", {})

    async def close(self) -> None:
        pass
