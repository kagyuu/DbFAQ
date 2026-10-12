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

    async def run_query(self, sql: str, max_rows: int) -> dict[str, Any]:
        return await self._respond("run_query", {"sql": sql, "max_rows": max_rows})

    async def export_csv(self, sql: str):
        return await self._respond("export_csv", {"sql": sql})

    async def get_pdb_info(self) -> dict[str, Any]:
        return await self._respond("get_pdb_info", {})

    async def close(self) -> None:
        pass


class FakeLlm:
    """単体テスト用の偽の LLM(dbfaq_api.llm.client.LlmAccess)。※CR-007により追加"""

    model = "fake-model"

    def __init__(self, answer="```sql\nSELECT 1 FROM DUAL\n```", health=None):
        self.answer = answer
        self.health_result = health or {"status": "ok", "model": "fake-model", "base_url": "http://llm", "message": None}
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    async def health(self):
        if isinstance(self.health_result, BaseException):
            raise self.health_result
        return self.health_result

    async def chat(self, system, user):
        self.calls.append((system, user))
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer

    async def close(self):
        self.closed = True
