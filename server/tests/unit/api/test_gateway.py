import asyncio
import sys
from pathlib import Path

import pytest

from dbfaq_api.errors import McpToolError, McpUnavailable
from dbfaq_api.mcp_gateway import StdioMcpGateway

ECHO = str(Path(__file__).with_name("echo_mcp.py"))


@pytest.fixture
async def gw(tmp_path):
    g = StdioMcpGateway(str(tmp_path / "unused.yaml"), call_timeout=10, command=[sys.executable, ECHO])
    yield g
    await g.close()


async def test_echo_and_session_reuse(gw):
    assert await gw.call("echo", {"x": "a"}) == {"x": "a"}
    pid1 = (await gw.call("pid", {}))["pid"]
    pid2 = (await gw.call("pid", {}))["pid"]
    assert pid1 == pid2


async def test_parallel_calls(gw):
    results = await asyncio.gather(*[gw.call("echo", {"x": str(i)}) for i in range(5)])
    assert [r["x"] for r in results] == [str(i) for i in range(5)]


async def test_tool_error(gw):
    with pytest.raises(McpToolError) as ei:
        await gw.call("fail", {})
    assert ei.value.code == "NOT_FOUND"


async def test_unparsable_error(gw):
    with pytest.raises(McpToolError) as ei:
        await gw.call("bad_error", {})
    assert ei.value.code == "INTERNAL_ERROR"


async def test_timeout_keeps_session(gw):
    pid1 = (await gw.call("pid", {}))["pid"]
    with pytest.raises(McpToolError) as ei:
        await gw.call("sleep", {"sec": 3}, timeout=1)
    assert ei.value.code == "ORACLE_TIMEOUT"
    assert (await gw.call("pid", {}))["pid"] == pid1


async def test_crash_then_restart(gw):
    pid1 = (await gw.call("pid", {}))["pid"]
    with pytest.raises(McpUnavailable):
        await gw.call("crash", {})
    # 壊れたセッションは捨てられており、次の呼び出しで起動し直す
    pid2 = (await gw.call("pid", {}))["pid"]
    assert pid2 != pid1


async def test_bad_command(tmp_path):
    g = StdioMcpGateway(str(tmp_path / "x.yaml"), call_timeout=5, command=["/nonexistent/cmd"])
    with pytest.raises(McpUnavailable):
        await g.start()
    with pytest.raises(McpUnavailable):
        await g.call("echo", {"x": "a"})
