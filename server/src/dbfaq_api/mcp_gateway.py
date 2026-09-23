"""MCP サーバ(子プロセス、stdio)とのゲートウェイ(docs/P003-backend-spec.md §4.1、ADR-001)。

FastMCP 4.x の実際の挙動(2026-09-23 確認):
* 呼び出しのタイムアウト → mcp.shared.exceptions.MCPError(code=-32001)。セッションは使い続けられる。
* 子プロセスの終了 → MCPError(code=-32000, "Connection closed")。以後そのセッションは使えない。
* 起動失敗(コマンドが無い等)→ RuntimeError("Client failed to connect: ...")。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Protocol

import anyio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.shared.exceptions import MCPError

from .errors import McpToolError, McpUnavailable

logger = logging.getLogger(__name__)

START_TIMEOUT_SEC = 10
MCP_REQUEST_TIMEOUT = -32001

_DISCONNECT_ERRORS = (
    anyio.ClosedResourceError,
    anyio.BrokenResourceError,
    anyio.EndOfStream,
    BrokenPipeError,
    ConnectionError,
    RuntimeError,
)


class Gateway(Protocol):
    async def start(self) -> None: ...

    async def call(self, tool: str, args: dict[str, Any], timeout: float | None = None) -> dict[str, Any]: ...

    async def close(self) -> None: ...


def _parse_tool_error(result: Any) -> McpToolError:
    try:
        body = json.loads(result.content[0].text)
        return McpToolError(body["code"], body["message"], body.get("ora_code"))
    except Exception:
        return McpToolError("INTERNAL_ERROR", "内部エラーが発生しました")


class StdioMcpGateway:
    def __init__(
        self,
        config_path: str,
        call_timeout: float,
        env: dict[str, str] | None = None,
        command: list[str] | None = None,
    ):
        self._config_path = os.path.abspath(config_path)
        self._call_timeout = call_timeout
        self._env = env or {}
        self._command = command or [sys.executable, "-m", "dbfaq_mcp"]
        self._client: Client | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        env = {**os.environ, **self._env, "DBFAQ_CONFIG": self._config_path}
        client = Client(StdioTransport(command=self._command[0], args=self._command[1:], env=env))
        try:
            await asyncio.wait_for(client.__aenter__(), START_TIMEOUT_SEC)
        except Exception as e:
            logger.warning("MCP server could not be started", extra={"error": str(e)})
            raise McpUnavailable(f"MCP サーバを起動できません: {e}") from e
        self._client = client
        logger.info("MCP server started")

    async def _ensure_started(self) -> Client:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    await self.start()
        assert self._client is not None
        return self._client

    async def _discard(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:  # 既に壊れているので閉じるときの失敗は無視する
                logger.debug("error while closing broken MCP session", extra={"error": str(e)})

    async def call(self, tool: str, args: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        client = await self._ensure_started()
        try:
            result = await client.call_tool(tool, args, timeout=timeout or self._call_timeout, raise_on_error=False)
        except MCPError as e:
            if e.error.code == MCP_REQUEST_TIMEOUT:
                raise McpToolError("ORACLE_TIMEOUT", "Oracle の応答がタイムアウトしました") from e
            logger.warning("MCP session lost; will restart on next call", extra={"error": str(e)})
            await self._discard()
            raise McpUnavailable(f"MCP サーバと通信できません: {e}") from e
        except TimeoutError as e:
            raise McpToolError("ORACLE_TIMEOUT", "Oracle の応答がタイムアウトしました") from e
        except _DISCONNECT_ERRORS as e:
            logger.warning("MCP session lost; will restart on next call", extra={"error": str(e)})
            await self._discard()
            raise McpUnavailable(f"MCP サーバと通信できません: {e}") from e
        if result.is_error:
            raise _parse_tool_error(result)
        data = result.structured_content if result.structured_content is not None else result.data
        if not isinstance(data, dict):
            raise McpToolError("INTERNAL_ERROR", "内部エラーが発生しました")
        return data

    async def close(self) -> None:
        await self._discard()
