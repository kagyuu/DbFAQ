from decimal import Decimal

import pytest

from dbfaq_common.config import OracleConfig
from dbfaq_mcp.db import Database
from dbfaq_mcp.errors import INVALID_ARGUMENT, NOT_FOUND, ToolFailure
from dbfaq_mcp.rows import build_rows_sql, get_table_rows

from .fakes import FakeConnection, FakePool, col

CFG = OracleConfig(host="h", service_name="s", user="hr", password="pw")


def test_sql_single_pk():
    sql, basis = build_rows_sql("HR", "EMPLOYEES", ["EMPLOYEE_ID"])
    assert sql == 'SELECT * FROM "HR"."EMPLOYEES" ORDER BY "EMPLOYEE_ID" OFFSET :off ROWS FETCH NEXT :n ROWS ONLY'
    assert basis == "PRIMARY_KEY"


def test_sql_composite_pk():
    sql, _ = build_rows_sql("HR", "JOB_HISTORY", ["EMPLOYEE_ID", "START_DATE"])
    assert 'ORDER BY "EMPLOYEE_ID", "START_DATE"' in sql


def test_sql_no_pk_and_quoted_names():
    sql, basis = build_rows_sql("hr", "my table", [])
    assert sql.startswith('SELECT * FROM "hr"."my table" ORDER BY ROWID')
    assert basis == "ROWID"


def make_db(n_rows: int, pk=("EMPLOYEE_ID",), exists=True):
    desc = [col("EMPLOYEE_ID", "DB_TYPE_NUMBER"), col("NAME", "DB_TYPE_VARCHAR")]

    def responder(sql, params):
        if "FROM ALL_TABLES" in sql:
            return None, [(None,)] if exists else []
        if "ALL_CONSTRAINTS" in sql:
            return None, [(p,) for p in pk]
        requested = params["n"]
        return desc, [(Decimal(100 + i), f"n{i}") for i in range(min(n_rows, requested))]

    conn = FakeConnection(responder=responder)
    return Database(CFG, pool_factory=lambda **kw: FakePool(conn)), conn


class Clock:
    def __init__(self, *values):
        self.values = list(values)

    def __call__(self):
        return self.values.pop(0)


async def test_has_next_true():
    db, conn = make_db(60)
    r = await get_table_rows(db, "HR", "EMPLOYEES", 0, 50, clock=Clock(0.0, 0.0385))
    assert len(r["rows"]) == 50 and r["has_next"] is True
    assert r["rows"][0] == ["100", "n0"]
    assert r["columns"] == [{"name": "EMPLOYEE_ID", "data_type": "NUMBER"}, {"name": "NAME", "data_type": "VARCHAR"}]
    assert r["elapsed_ms"] == 38
    assert r["order_by"] == ["EMPLOYEE_ID"] and r["order_basis"] == "PRIMARY_KEY"
    assert r["truncated"] == [[]] * 50
    last = [c for c in conn.calls if c[0] == "cursor.execute"][-1]
    assert last[2] == {"off": 0, "n": 51}


async def test_has_next_false():
    db, _ = make_db(7)
    r = await get_table_rows(db, "HR", "EMPLOYEES", 100, 50, clock=Clock(0.0, 0.001))
    assert len(r["rows"]) == 7 and r["has_next"] is False


async def test_rowid_order():
    db, _ = make_db(1, pk=())
    r = await get_table_rows(db, "HR", "NOPK", 0, 50, clock=Clock(0.0, 0.0))
    assert r["order_basis"] == "ROWID" and r["order_by"] == ["ROWID"]


@pytest.mark.parametrize("offset, limit", [(-1, 50), (100_001, 50), (0, 0), (0, 501)])
async def test_invalid_ranges(offset, limit):
    class NoDb:
        async def run_readonly(self, fn):
            raise AssertionError("must not be called")

    with pytest.raises(ToolFailure) as ei:
        await get_table_rows(NoDb(), "HR", "EMPLOYEES", offset, limit)
    assert ei.value.code == INVALID_ARGUMENT


async def test_not_found():
    db, _ = make_db(0, exists=False)
    with pytest.raises(ToolFailure) as ei:
        await get_table_rows(db, "HR", "NOPE", 0, 50)
    assert ei.value.code == NOT_FOUND
