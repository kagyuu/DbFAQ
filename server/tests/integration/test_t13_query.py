"""T13: 利用者の SELECT の実行・エラー位置・CSV(docs/P008-test-direction/T13-oracle-query.md)。※CR-004により追加"""

import csv
import io

import pytest

from dbfaq_api.oracle.client import OracleClient
from dbfaq_api.oracle.errors import OracleFailure

CROSS = "SELECT a.EMPLOYEE_ID A_ID, b.EMPLOYEE_ID B_ID FROM HR.EMPLOYEES a CROSS JOIN HR.EMPLOYEES b ORDER BY 1, 2"


async def test_run_query(oracle_client: OracleClient):
    # 1
    r = await oracle_client.run_query(
        "SELECT EMPLOYEE_ID, LAST_NAME, HIRE_DATE, COMMISSION_PCT FROM HR.EMPLOYEES WHERE EMPLOYEE_ID = 100;", 500
    )
    assert r["rows"] == [["100", "King", "2013-06-17 00:00:00", None]]
    assert r["has_more"] is False and r["row_count"] == 1
    assert [c["name"] for c in r["columns"]] == ["EMPLOYEE_ID", "LAST_NAME", "HIRE_DATE", "COMMISSION_PCT"]
    # 2
    r = await oracle_client.run_query(CROSS, 500)
    assert r["row_count"] == 500 and len(r["rows"]) == 500 and r["has_more"] is True and r["max_rows"] == 500
    assert r["rows"][0] == ["100", "100"] and r["rows"][499] == ["104", "171"]  # 499 = 4 × 107 + 71
    # 3
    r = await oracle_client.run_query("SELECT 1 FROM HR.EMPLOYEES WHERE 1 = 0", 500)
    assert r["rows"] == [] and len(r["columns"]) == 1


@pytest.mark.parametrize(
    "sql, ora_code, position",
    [
        # 4
        ("SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1", "ORA-00904", {"offset": 33, "line": 3, "column": 7}),
        # 5(日本語を含む SQL でも文字単位)
        ("-- 日本語コメント\nSELECT ほげ FROM HR.EMPLOYEES", "ORA-00904", {"offset": 18, "line": 2, "column": 8}),
        # 6
        ("SELECT * FROM HR.NO_SUCH_TABLE", "ORA-00942", {"offset": 17, "line": 1, "column": 18}),  # 表名の位置
    ],
)
async def test_run_query_error_position(oracle_client: OracleClient, sql, ora_code, position):
    with pytest.raises(OracleFailure) as ei:
        await oracle_client.run_query(sql, 500)
    assert ei.value.code == "ORACLE_ERROR"
    assert ei.value.ora_code == ora_code
    assert ei.value.position == position


async def test_export_csv(oracle_client: OracleClient):
    # 7
    spool, count = await oracle_client.export_csv(CROSS)
    try:
        raw = spool.read()
    finally:
        spool.close()
    assert count == 11_449
    assert raw.startswith(b"\xef\xbb\xbfA_ID,B_ID\r\n")
    assert raw.count(b"\r\n") == 11_450
    records = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    assert len(records) == 11_450 and records[1] == ["100", "100"] and records[-1] == ["206", "206"]


async def test_query_api(api_client):
    # 8
    r = await api_client.post("/api/query", json={"sql": "SELECT EMPLOYEE_ID FROM HR.EMPLOYEES WHERE EMPLOYEE_ID = 100"})
    assert r.status_code == 200, r.text
    assert r.json()["rows"] == [["100"]]
    r = await api_client.post("/api/query", json={"sql": "SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1"})
    assert r.status_code == 502
    err = r.json()["error"]
    assert err["ora_code"] == "ORA-00904" and err["position"] == {"offset": 33, "line": 3, "column": 7}
    r = await api_client.post("/api/query", json={"sql": "DELETE FROM HR.EMPLOYEES"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "SQL_REJECTED"
    r = await api_client.post("/api/query/csv", json={"sql": CROSS})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["x-row-count"] == "11449"
    assert r.content.count(b"\r\n") == 11_450
