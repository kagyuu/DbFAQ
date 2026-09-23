"""ゲートウェイの単体テスト用の小さな MCP サーバ(Oracle に接続しない)。"""

import asyncio
import os

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("echo")


@mcp.tool
def echo(x: str) -> dict:
    return {"x": x}


@mcp.tool
def pid() -> dict:
    return {"pid": os.getpid()}


@mcp.tool
def fail() -> dict:
    raise ToolError('{"code": "NOT_FOUND", "message": "m", "ora_code": null}')


@mcp.tool
def bad_error() -> dict:
    raise ToolError("not json")


@mcp.tool
async def sleep(sec: float) -> dict:
    await asyncio.sleep(sec)
    return {"slept": sec}


@mcp.tool
def crash() -> dict:
    os._exit(1)


if __name__ == "__main__":
    mcp.run(show_banner=False)
