import json

from fastmcp import Client

from dbfaq_common.config import AppConfig, OracleConfig
from dbfaq_mcp import rows as rows_mod
from dbfaq_mcp.errors import NOT_FOUND, ToolFailure
from dbfaq_mcp.server import create_server

from .fakes import FakeConnection

CFG = AppConfig(oracle=OracleConfig(host="h", service_name="s", user="hr", password="pw"))


class FakeDb:
    def __init__(self, conn=None, error=None):
        self.conn = conn
        self.error = error

    async def run_readonly(self, fn):
        if self.error:
            raise self.error
        return await fn(self.conn)


def error_body(result) -> dict:
    return json.loads(result.content[0].text)


async def test_tools_listed():
    async with Client(create_server(CFG, db=FakeDb())) as client:
        names = sorted(t.name for t in await client.list_tools())
    assert names == ["get_schema_snapshot", "get_table_rows", "ping"]


async def test_ping():
    conn = FakeConnection(responder=lambda sql, p: (None, [("HR", "HR")]))
    async with Client(create_server(CFG, db=FakeDb(conn=conn))) as client:
        r = await client.call_tool("ping", {})
    assert r.data == {"version": "23.26.3.0.0", "user": "HR", "current_schema": "HR"}


async def test_get_table_rows_delegates(monkeypatch):
    async def fake_rows(db, owner, table, offset, limit):
        return {"owner_seen": owner, "table_seen": table, "offset": offset, "limit": limit}

    monkeypatch.setattr(rows_mod, "get_table_rows", fake_rows)
    async with Client(create_server(CFG, db=FakeDb())) as client:
        r = await client.call_tool("get_table_rows", {"owner": "HR", "table": "EMPLOYEES", "offset": 50})
    assert r.data == {"owner_seen": "HR", "table_seen": "EMPLOYEES", "offset": 50, "limit": 50}


async def test_tool_failure_is_json_error():
    db = FakeDb(error=ToolFailure(NOT_FOUND, "スキーマ X が見つかりません"))
    async with Client(create_server(CFG, db=db)) as client:
        r = await client.call_tool("ping", {}, raise_on_error=False)
    assert r.is_error is True
    assert error_body(r)["code"] == NOT_FOUND


async def test_unexpected_error_is_masked():
    db = FakeDb(error=RuntimeError("secret internals"))
    async with Client(create_server(CFG, db=db)) as client:
        r = await client.call_tool("ping", {}, raise_on_error=False)
    body = error_body(r)
    assert body["code"] == "INTERNAL_ERROR"
    assert "secret internals" not in r.content[0].text
