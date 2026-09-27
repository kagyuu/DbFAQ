import datetime as dt
from types import SimpleNamespace

import oracledb
import pytest

from dbfaq_api.config import OracleConfig
from dbfaq_api.oracle import rows as rows_mod
from dbfaq_api.oracle import snapshot as snapshot_mod
from dbfaq_api.oracle.client import HEALTH_TIMEOUT_SEC, OracleClient
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import ORACLE_ERROR, OracleFailure

from .fakes import FakeConnection, FakePool

CFG = OracleConfig(host="h", service_name="s", user="hr", password="pw", schema="HR")
NOW = dt.datetime(2026, 9, 27, 1, 0, tzinfo=dt.UTC)


def make_client(conn: FakeConnection) -> OracleClient:
    return OracleClient(CFG, db=Database(CFG, pool_factory=lambda **kw: FakePool(conn)), now=lambda: NOW)


async def test_ping():
    conn = FakeConnection(responder=lambda sql, p: (None, [("HR", "HR")]))
    result = await make_client(conn).ping()
    assert result == {"version": "23.26.3.0.0", "user": "HR", "current_schema": "HR"}
    assert conn.calls[0] == ("execute", "SET TRANSACTION READ ONLY")
    assert conn.calls[1][0] == "cursor.execute" and "FROM DUAL" in conn.calls[1][1]
    assert conn.calls[-1] == ("rollback",)
    assert conn.call_timeout == HEALTH_TIMEOUT_SEC * 1000


async def test_ping_oracle_error():
    err = oracledb.DatabaseError(SimpleNamespace(full_code="ORA-12541", message="ORA-12541: no listener"))
    conn = FakeConnection(fail_on={"SET TRANSACTION READ ONLY": err})
    with pytest.raises(OracleFailure) as ei:
        await make_client(conn).ping()
    assert (ei.value.code, ei.value.ora_code) == (ORACLE_ERROR, "ORA-12541")


async def test_get_table_rows_delegates(monkeypatch):
    seen = {}

    async def fake_rows(db, owner, table, offset, limit):
        seen.update(owner=owner, table=table, offset=offset, limit=limit)
        return {"rows": []}

    monkeypatch.setattr(rows_mod, "get_table_rows", fake_rows)
    assert await make_client(FakeConnection()).get_table_rows("HR", "EMPLOYEES", 50, 20) == {"rows": []}
    assert seen == {"owner": "HR", "table": "EMPLOYEES", "offset": 50, "limit": 20}


async def test_get_schema_snapshot_uses_default_owner(monkeypatch):
    seen = {}

    async def fake_snapshot(db, owner, default_owner, now):
        seen.update(owner=owner, default_owner=default_owner, now=now())
        return {"owner": default_owner}

    monkeypatch.setattr(snapshot_mod, "get_schema_snapshot", fake_snapshot)
    assert await make_client(FakeConnection()).get_schema_snapshot(None) == {"owner": "HR"}
    assert seen == {"owner": None, "default_owner": "HR", "now": NOW}
