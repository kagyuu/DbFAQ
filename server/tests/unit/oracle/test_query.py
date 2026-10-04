import csv
import io
from decimal import Decimal
from types import SimpleNamespace

import oracledb
import pytest

from dbfaq_api.config import OracleConfig
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import ORACLE_ERROR, SQL_REJECTED, OracleFailure, error_position
from dbfaq_api.oracle.query import export_csv, run_query

from .fakes import FakeConnection, FakePool, col

CFG = OracleConfig(host="h", service_name="s", user="hr", password="pw")
DESC = [col("ID", "DB_TYPE_NUMBER"), col("NAME", "DB_TYPE_VARCHAR")]


def make_db(rows, desc=DESC, error=None):
    def responder(sql, params):
        if error is not None:
            return error
        return desc, rows

    conn = FakeConnection(responder=responder)
    return Database(CFG, pool_factory=lambda **kw: FakePool(conn)), conn


class Clock:
    def __init__(self, *values):
        self.values = list(values)

    def __call__(self):
        return self.values.pop(0)


def ora(full_code, message, offset):
    return oracledb.DatabaseError(SimpleNamespace(full_code=full_code, message=message, offset=offset))


@pytest.mark.parametrize(
    "sql, byte_offset, expected",
    [
        ("SELECT FOO FROM T", 7, {"offset": 7, "line": 1, "column": 8}),
        ("SELECT 1\nFROM T\nWHERE BAR = 1", 22, {"offset": 22, "line": 3, "column": 7}),
        ("SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1", 33, {"offset": 33, "line": 3, "column": 7}),
        ("-- 日本語コメント\nSELECT ほげ FROM EMPLOYEES", 32, {"offset": 18, "line": 2, "column": 8}),
        ("SELECT\t\tX FROM T", 8, {"offset": 8, "line": 1, "column": 9}),
        ("SELECT 1 FROM DUAL WHERE", 24, {"offset": 24, "line": 1, "column": 25}),  # 末尾(長さちょうど)
        ("SELECT 1 FROM DUAL", 0, None),
        ("SELECT 1 FROM DUAL", 19, None),
        ("SELECT 'あ' FROM DUAL", 9, None),  # 「あ」(3 バイト)の途中
        ("SELECT 1 FROM DUAL", None, None),
    ],
)
def test_error_position(sql, byte_offset, expected):
    assert error_position(sql, byte_offset) == expected


async def test_run_query_truncates_at_max_rows():
    db, conn = make_db([(Decimal(i), f"n{i}") for i in range(600)])
    r = await run_query(db, "SELECT ID, NAME FROM T;", clock=Clock(0.0, 0.0125))
    assert r["row_count"] == 500 and len(r["rows"]) == 500
    assert r["has_more"] is True and r["max_rows"] == 500
    assert r["rows"][0] == ["0", "n0"]
    assert r["columns"] == [{"name": "ID", "data_type": "NUMBER"}, {"name": "NAME", "data_type": "VARCHAR"}]
    assert r["elapsed_ms"] == 12
    executed = [c for c in conn.calls if c[0] == "cursor.execute"]
    assert executed == [("cursor.execute", "SELECT ID, NAME FROM T", {})]  # 包まない・末尾の ; を除く
    assert ("cursor.fetchmany", 501) in conn.calls
    assert conn.calls[0] == ("execute", "SET TRANSACTION READ ONLY") and conn.calls[-1] == ("rollback",)


async def test_run_query_exactly_max_rows_and_zero():
    db, _ = make_db([(Decimal(i), None) for i in range(500)])
    r = await run_query(db, "SELECT ID, NAME FROM T", clock=Clock(0.0, 0.0))
    assert r["row_count"] == 500 and r["has_more"] is False
    assert r["rows"][0] == ["0", None]
    db, _ = make_db([])
    r = await run_query(db, "SELECT ID, NAME FROM T", clock=Clock(0.0, 0.0))
    assert r["rows"] == [] and r["row_count"] == 0 and r["has_more"] is False and len(r["columns"]) == 2


async def test_run_query_formats_and_truncates_cells():
    db, _ = make_db([(Decimal("1.50"), "x" * 1200)])
    r = await run_query(db, "SELECT ID, NAME FROM T", clock=Clock(0.0, 0.0))
    assert r["rows"][0][0] == "1.50"
    assert r["rows"][0][1].endswith("…") and len(r["rows"][0][1]) == 1001
    assert r["truncated"] == [[1]]


async def test_run_query_rejected_does_not_touch_oracle():
    db, conn = make_db([])
    with pytest.raises(OracleFailure) as ei:
        await run_query(db, "DELETE FROM T")
    assert ei.value.code == SQL_REJECTED
    assert conn.calls == []


async def test_run_query_oracle_error_has_position():
    sql = "SELECT 1\nFROM T\nWHERE BAR = 1"
    db, _ = make_db([], error=ora("ORA-00904", 'ORA-00904: "BAR": invalid identifier\nHelp: x', 22))
    with pytest.raises(OracleFailure) as ei:
        await run_query(db, sql)
    f = ei.value
    assert f.code == ORACLE_ERROR and f.ora_code == "ORA-00904"
    assert f.message == 'ORA-00904: "BAR": invalid identifier'
    assert f.position == {"offset": 22, "line": 3, "column": 7}


async def test_run_query_timeout_has_no_position():
    db, _ = make_db([], error=ora("DPY-4024", "DPY-4024: call timeout", 5))
    with pytest.raises(OracleFailure) as ei:
        await run_query(db, "SELECT 1 FROM DUAL")
    assert ei.value.code == "ORACLE_TIMEOUT" and ei.value.position is None


def read_csv(spool) -> tuple[bytes, list[list[str]]]:
    raw = spool.read()
    return raw, list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))


async def test_export_csv_format():
    desc = [col("ID", "DB_TYPE_NUMBER"), col("TEXT", "DB_TYPE_CLOB"), col("BIN", "DB_TYPE_RAW")]
    rows = [
        (Decimal(1), 'a,b "q"\nline2', b"\x01" * 40),
        (Decimal(2), None, None),
        (Decimal(3), "y" * 1500, b"\xff"),
    ]
    db, _ = make_db(rows, desc=desc)
    spool, count = await export_csv(db, "SELECT * FROM T;")
    raw, records = read_csv(spool)
    spool.close()
    assert count == 3
    assert raw.startswith(b"\xef\xbb\xbfID,TEXT,BIN\r\n")
    assert b'"a,b ""q""\nline2"' in raw
    assert records[0] == ["ID", "TEXT", "BIN"]
    assert records[1] == ["1", 'a,b "q"\nline2', "0x" + "01" * 40]  # 32 バイトで切らない
    assert records[2] == ["2", "", ""]
    assert records[3] == ["3", "y" * 1500, "0xFF"]  # 1,000 文字で切らない


async def test_export_csv_all_rows_in_batches():
    db, conn = make_db([(Decimal(i), "v") for i in range(2500)])
    spool, count = await export_csv(db, "SELECT ID, NAME FROM T")
    _, records = read_csv(spool)
    spool.close()
    assert count == 2500 and len(records) == 2501
    assert [c for c in conn.calls if c[0] == "cursor.fetchmany"] == [("cursor.fetchmany", 1000)] * 4


async def test_export_csv_error_midway_raises_with_position():
    db, conn = make_db([(Decimal(i), "v") for i in range(2500)])
    conn.fetch_error = ora("ORA-01722", "ORA-01722: invalid number", 7)
    with pytest.raises(OracleFailure) as ei:
        await export_csv(db, "SELECT ID, NAME FROM T")
    assert ei.value.ora_code == "ORA-01722" and ei.value.position["column"] == 8


async def test_export_csv_rejected():
    db, conn = make_db([])
    with pytest.raises(OracleFailure) as ei:
        await export_csv(db, "SELECT * FROM T FOR UPDATE")
    assert ei.value.code == SQL_REJECTED and conn.calls == []
