"""backend の単体テスト用の偽ゲートウェイ。"""

from __future__ import annotations

import inspect
from typing import Any


class FakeGateway:
    def __init__(self, responses: dict[str, Any] | None = None):
        self.responses: dict[str, Any] = responses or {}
        self.calls: list[tuple[str, dict[str, Any], float | None]] = []

    async def start(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def call(self, tool: str, args: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        self.calls.append((tool, args, timeout))
        resp = self.responses[tool]
        if callable(resp):
            resp = resp(args)
            if inspect.isawaitable(resp):
                resp = await resp
        if isinstance(resp, BaseException):
            raise resp
        return resp
