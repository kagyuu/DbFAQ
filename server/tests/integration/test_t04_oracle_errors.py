"""T04: Oracle のエラー変換(docs/P008-test-direction/T04-oracle-errors.md)。"""

import pytest

from dbfaq_api.config import load_config
from dbfaq_api.oracle.client import OracleClient
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import ORACLE_ERROR, ORACLE_TIMEOUT, OracleFailure

from .conftest import write_config


async def test_wrong_password(tmp_path):
    cfg = load_config(str(write_config(tmp_path, password="wrong-password")), env={})
    client = OracleClient(cfg.oracle)
    try:
        with pytest.raises(OracleFailure) as ei:
            await client.ping()
    finally:
        await client.close()
    assert ei.value.code == ORACLE_ERROR
    assert ei.value.ora_code == "ORA-01017"
    assert "wrong-password" not in ei.value.message


async def test_timeout_then_recover(tmp_path):
    cfg = load_config(str(write_config(tmp_path, query_timeout_sec=1)), env={})
    db = Database(cfg.oracle)
    try:
        async def sleepy(conn):
            await conn.execute("BEGIN DBMS_SESSION.SLEEP(3); END;")

        with pytest.raises(OracleFailure) as ei:
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
