"""T04: Oracle のエラー変換(docs/P008-test-direction/T04-mcp-oracle-errors.md)。"""

import json

import pytest
from fastmcp import Client

from dbfaq_common.config import load_config
from dbfaq_mcp.db import Database
from dbfaq_mcp.errors import ORACLE_TIMEOUT, ToolFailure

from .conftest import mcp_transport, write_config


async def test_wrong_password(tmp_path):
    path = write_config(tmp_path, password="wrong-password")
    async with Client(mcp_transport(path)) as client:
        r = await client.call_tool("ping", {}, raise_on_error=False)
    assert r.is_error
    body = json.loads(r.content[0].text)
    assert body["code"] == "ORACLE_ERROR"
    assert body["ora_code"] == "ORA-01017"
    assert "wrong-password" not in r.content[0].text


async def test_timeout_then_recover(tmp_path):
    cfg = load_config(str(write_config(tmp_path, query_timeout_sec=1)), env={})
    db = Database(cfg.oracle)
    try:
        async def sleepy(conn):
            await conn.execute("BEGIN DBMS_SESSION.SLEEP(3); END;")

        with pytest.raises(ToolFailure) as ei:
            await db.run_readonly(sleepy)
        print("timeout error:", ei.value.ora_code, ei.value.message)
        assert ei.value.code == ORACLE_TIMEOUT

        async def one(conn):
            cur = conn.cursor()
            await cur.execute("SELECT 1 FROM DUAL")
            return (await cur.fetchall())[0][0]

        assert await db.run_readonly(one) == 1
    finally:
        await db.close()
