import asyncio
import socket
import time
from types import SimpleNamespace

import oracledb
import pytest

from dbfaq_api.config import OracleConfig
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import ORACLE_ERROR, OracleFailure

from .fakes import FakeConnection, FakePool

CFG = OracleConfig(host="h", service_name="s", user="hr", password="pw", query_timeout_sec=7)


def make_db(conn: FakeConnection):
    created = []

    def factory(**kwargs):
        created.append(kwargs)
        return FakePool(conn)

    return Database(CFG, pool_factory=factory), created


async def test_order_and_timeout():
    conn = FakeConnection()
    db, created = make_db(conn)

    async def fn(c):
        c.calls.append(("fn",))
        return 42

    assert await db.run_readonly(fn) == 42
    assert conn.calls == [("execute", "SET TRANSACTION READ ONLY"), ("fn",), ("rollback",)]
    assert conn.call_timeout == 7000
    assert created[0]["dsn"] == "h:1521/s"
    assert created[0]["getmode"] == oracledb.POOL_GETMODE_TIMEDWAIT
    assert created[0]["wait_timeout"] == CFG.connect_timeout_sec * 1000


async def test_timeout_override():
    conn = FakeConnection()
    db, _ = make_db(conn)

    async def fn(c):
        return 1

    await db.run_readonly(fn, timeout_sec=5)
    assert conn.call_timeout == 5000
    await db.run_readonly(fn)
    assert conn.call_timeout == 7000


async def test_pool_created_once():
    conn = FakeConnection()
    db, created = make_db(conn)

    async def fn(c):
        return 1

    await db.run_readonly(fn)
    await db.run_readonly(fn)
    assert len(created) == 1


async def test_exception_still_rolls_back():
    conn = FakeConnection()
    db, _ = make_db(conn)

    async def fn(c):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await db.run_readonly(fn)
    assert conn.calls[-1] == ("rollback",)


async def test_rollback_failure_keeps_original_error():
    conn = FakeConnection(rollback_error=RuntimeError("rollback failed"))
    db, _ = make_db(conn)

    async def fn(c):
        raise ValueError("original")

    with pytest.raises(ValueError, match="original"):
        await db.run_readonly(fn)


async def test_set_transaction_failure_skips_fn():
    err = oracledb.DatabaseError(SimpleNamespace(full_code="ORA-01453", message="ORA-01453: SET TRANSACTION must be first"))
    conn = FakeConnection(fail_on={"SET TRANSACTION READ ONLY": err})
    db, _ = make_db(conn)
    called = []

    async def fn(c):
        called.append(1)

    with pytest.raises(OracleFailure):
        await db.run_readonly(fn)
    assert called == []


async def test_oracle_error_is_converted():
    conn = FakeConnection()
    db, _ = make_db(conn)

    async def fn(c):
        raise oracledb.DatabaseError(SimpleNamespace(full_code="ORA-00942", message="ORA-00942: table or view does not exist"))

    with pytest.raises(OracleFailure) as ei:
        await db.run_readonly(fn)
    assert ei.value.code == ORACLE_ERROR
    assert ei.value.ora_code == "ORA-00942"


async def test_os_error_is_converted():
    # python-oracledb はホスト名を解決できないとき socket.gaierror をそのまま送出する(P202 F007)
    class DnsFailPool(FakePool):
        def acquire(self):
            raise socket.gaierror(-2, "Name or service not known")

    db = Database(CFG, pool_factory=lambda **kw: DnsFailPool(FakeConnection()))

    async def fn(c):
        return 1

    with pytest.raises(OracleFailure) as ei:
        await db.run_readonly(fn)
    assert ei.value.code == ORACLE_ERROR


async def test_close_gives_up_after_connect_timeout():
    # Oracle に届かない間、python-oracledb の close は長く戻らない(P202 F008)
    class HangingPool(FakePool):
        async def close(self, force=False):
            await asyncio.sleep(3600)

    cfg = OracleConfig(host="h", service_name="s", user="hr", password="pw", connect_timeout_sec=1)
    db = Database(cfg, pool_factory=lambda **kw: HangingPool(FakeConnection()))

    async def fn(c):
        return 1

    await db.run_readonly(fn)
    started = time.perf_counter()
    await db.close()
    assert time.perf_counter() - started < 2
