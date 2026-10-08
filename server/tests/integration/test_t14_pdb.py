"""T14: PDB の情報とひな型(docs/P008-test-direction/T14-oracle-pdb.md)。※CR-005により追加"""

import pytest

from dbfaq_api.oracle.client import OracleClient
from dbfaq_api.oracle.errors import OracleFailure
from dbfaq_api.pdb_templates import PDB_TEMPLATES

# 開発用 Oracle の hr で成功が期待できるひな型(権限不要)。それ以外は成功か ORA-00942/ORA-01031
NO_PRIVILEGE = {"02", "03", "08", "09", "10", "11", "12", "13"}
PRIVILEGE_ERRORS = {"ORA-00942", "ORA-01031"}


async def test_get_pdb_info(oracle_client: OracleClient):
    info = await oracle_client.get_pdb_info()
    sections = {s["key"]: s for s in info["sections"]}
    # 1
    assert list(sections) == ["overview", "ts_quotas", "segments", "tablespaces"]
    overview = dict(sections["overview"]["rows"])
    assert len(sections["overview"]["rows"]) == 10
    assert overview["コンテナ名(PDB)"] == "FREEPDB1"
    assert overview["接続ユーザー"] == "HR"
    assert overview["既定の表領域"] == "USERS"
    assert overview["バージョン"].startswith("23.")
    # 2
    assert sections["ts_quotas"]["error"] is None
    assert "USERS" in [r[0] for r in sections["ts_quotas"]["rows"]]
    assert sections["segments"]["error"] is None
    assert {"TABLE", "INDEX", "LOBSEGMENT"} <= {r[0] for r in sections["segments"]["rows"]}
    # 3(hr は DBA_* を読めない)
    assert sections["tablespaces"]["error"]["ora_code"] == "ORA-00942"
    assert sections["tablespaces"]["rows"] == []


async def test_pdb_api(api_client):
    # 4
    r = await api_client.get("/api/pdb")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["sections"]) == 4
    assert body["fetched_at"].endswith("Z") and body["elapsed_ms"] >= 0


@pytest.mark.parametrize("t", PDB_TEMPLATES, ids=lambda t: t.key)
async def test_templates_run(oracle_client: OracleClient, t):
    # 5
    no = t.name[:2]
    try:
        r = await oracle_client.run_query(t.sql, 500)
    except OracleFailure as e:
        assert no not in NO_PRIVILEGE, f"{t.name}: {e.message}"
        assert e.code == "ORACLE_ERROR" and e.ora_code in PRIVILEGE_ERRORS, f"{t.name}: {e.ora_code} {e.message}"
        return
    if no == "03":
        cols = [c["name"] for c in r["columns"]]
        rows = [dict(zip(cols, row, strict=True)) for row in r["rows"]]
        fig = [x for x in rows if x["TABLE_COLUMN"] == "EMPLOYEE_FIGURE.FIGURE"]
        assert len(fig) == 1
        assert fig[0]["DATA_TYPE"] == "BLOB"
        assert float(fig[0]["SEGMENT_MB"]) > 0 and int(fig[0]["DATA_LENGTH"]) > 0
