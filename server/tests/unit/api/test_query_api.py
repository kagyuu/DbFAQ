import io
import json

import pytest

from dbfaq_api.oracle.errors import OracleFailure
from tests.fakes import FakeOracle

from .test_api import assert_error, client  # noqa: F401  (client はフィクスチャ)

RESULT = {
    "columns": [{"name": "EMPLOYEE_ID", "data_type": "NUMBER"}, {"name": "COMMISSION_PCT", "data_type": "NUMBER"}],
    "rows": [["100", None]],
    "truncated": [[]],
    "row_count": 1,
    "has_more": False,
    "max_rows": 500,
    "elapsed_ms": 7,
}
SQL = "SELECT EMPLOYEE_ID, COMMISSION_PCT FROM HR.EMPLOYEES WHERE LAST_NAME = 'King-SECRET-LITERAL'"


@pytest.fixture
def oracle():
    return FakeOracle({"run_query": RESULT, "export_csv": lambda a: (io.BytesIO(b"\xef\xbb\xbfA\r\n1\r\n"), 1)})


async def test_query_ok(client, oracle):  # noqa: F811
    r = await client.post("/api/query", json={"sql": SQL})
    assert r.status_code == 200, r.text
    assert r.json() == RESULT
    assert oracle.calls == [("run_query", {"sql": SQL, "max_rows": 500})]


@pytest.mark.parametrize("body", [{}, {"sql": ""}, {"sql": "   \n"}, {"sql": "x" * 100_001}, {"sql": 1}])
async def test_query_validation(client, oracle, body):  # noqa: F811
    assert_error(await client.post("/api/query", json=body), 422, "VALIDATION_ERROR")
    assert_error(await client.post("/api/query/csv", json=body), 422, "VALIDATION_ERROR")
    assert oracle.calls == []


async def test_query_max_length_ok(client, oracle):  # noqa: F811
    r = await client.post("/api/query", json={"sql": "SELECT 1 FROM DUAL" + " " * (100_000 - 18)})
    assert r.status_code == 200


@pytest.mark.parametrize(
    "exc, status, code",
    [
        (OracleFailure("SQL_REJECTED", "複数の文は実行できません"), 422, "SQL_REJECTED"),
        (OracleFailure("ORACLE_TIMEOUT", "Oracle の応答がタイムアウトしました"), 504, "ORACLE_TIMEOUT"),
        (OracleFailure("ORACLE_ERROR", "ORA-00942: table or view does not exist", "ORA-00942"), 502, "ORACLE_ERROR"),
    ],
)
async def test_query_errors(client, oracle, exc, status, code):  # noqa: F811
    oracle.responses["run_query"] = exc
    oracle.responses["export_csv"] = exc
    for path in ("/api/query", "/api/query/csv"):
        err = assert_error(await client.post(path, json={"sql": SQL}), status, code)
        assert err["message"] == exc.message
        assert "position" not in err


async def test_query_error_position(client, oracle):  # noqa: F811
    pos = {"offset": 33, "line": 3, "column": 7}
    oracle.responses["run_query"] = OracleFailure("ORACLE_ERROR", 'ORA-00904: "BAR": invalid identifier', "ORA-00904", pos)
    err = assert_error(await client.post("/api/query", json={"sql": SQL}), 502, "ORACLE_ERROR")
    assert err == {"code": "ORACLE_ERROR", "message": 'ORA-00904: "BAR": invalid identifier', "ora_code": "ORA-00904",
                   "position": pos}


async def test_csv_ok(client, oracle):  # noqa: F811
    r = await client.post("/api/query/csv", json={"sql": SQL})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"] == 'attachment; filename="query.csv"'
    assert r.headers["x-row-count"] == "1"
    assert r.content == b"\xef\xbb\xbfA\r\n1\r\n"


async def test_csv_file_is_closed_after_send(client, oracle):  # noqa: F811
    f = io.BytesIO(b"x" * 200_000)
    oracle.responses["export_csv"] = (f, 3)
    r = await client.post("/api/query/csv", json={"sql": SQL})
    assert len(r.content) == 200_000
    assert f.closed


async def test_query_log_has_no_sql_text(client, oracle, caplog):  # noqa: F811
    caplog.set_level("INFO")
    await client.post("/api/query", json={"sql": SQL})
    oracle.responses["run_query"] = OracleFailure("ORACLE_ERROR", "ORA-00904: x", "ORA-00904")
    await client.post("/api/query", json={"sql": SQL})
    q = [r for r in caplog.records if r.getMessage() in ("query", "query failed")]
    assert len(q) == 2
    assert q[0].sql_chars == len(SQL) and q[0].row_count == 1 and q[0].has_more is False
    assert q[1].ora_code == "ORA-00904"
    dumped = json.dumps([r.__dict__ for r in caplog.records], default=str)
    assert "SECRET-LITERAL" not in dumped and "COMMISSION_PCT" not in dumped
