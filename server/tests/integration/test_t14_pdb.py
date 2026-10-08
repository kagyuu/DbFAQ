"""T14: PDB の情報とひな型(docs/P008-test-direction/T14-oracle-pdb.md)。※CR-005により追加

※CR-006により、接続ユーザーは読み取り専用ユーザー dbfaq_ro(SELECT_CATALOG_ROLE あり)、対象スキーマは HR。
"""

import pytest

from dbfaq_api.oracle.client import OracleClient
from dbfaq_api.pdb_templates import PDB_TEMPLATES


async def test_get_pdb_info(oracle_client: OracleClient, base_config):
    info = await oracle_client.get_pdb_info()
    sections = {s["key"]: s for s in info["sections"]}
    # 1
    assert list(sections) == ["overview", "ts_quotas", "segments", "tablespaces"]
    overview = dict(sections["overview"]["rows"])
    assert len(sections["overview"]["rows"]) == 10
    assert overview["コンテナ名(PDB)"] == "FREEPDB1"
    assert overview["接続ユーザー"] == base_config.oracle.user.upper()
    assert overview["対象スキーマ"] == "HR"
    assert overview["対象スキーマの既定の表領域"] == "USERS"
    assert overview["バージョン"].startswith("23.")
    # 2(対象スキーマ HR の分)
    assert sections["ts_quotas"]["error"] is None
    assert "USERS" in [r[0] for r in sections["ts_quotas"]["rows"]]
    assert sections["segments"]["error"] is None
    assert {"TABLE", "INDEX", "LOBSEGMENT"} <= {r[0] for r in sections["segments"]["rows"]}
    # 3(※CR-006: dbfaq_ro は DBA_* を読める)
    assert sections["tablespaces"]["error"] is None
    assert "USERS" in [r[0] for r in sections["tablespaces"]["rows"]]


async def test_pdb_api(api_client):
    # 4
    r = await api_client.get("/api/pdb")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["sections"]) == 4
    assert body["fetched_at"].endswith("Z") and body["elapsed_ms"] >= 0


@pytest.mark.parametrize("t", PDB_TEMPLATES, ids=lambda t: t.key)
async def test_templates_run(oracle_client: OracleClient, t):
    # 5(※CR-006: 17 件すべて成功する)
    r = await oracle_client.run_query(t.sql, 500)
    cols = [c["name"] for c in r["columns"]]
    rows = [dict(zip(cols, row, strict=True)) for row in r["rows"]]
    no = t.name[:2]
    if no in ("03", "04"):
        want = "EMPLOYEE_FIGURE.FIGURE" if no == "03" else "HR.EMPLOYEE_FIGURE.FIGURE"
        fig = [x for x in rows if x["TABLE_COLUMN"] == want]
        assert len(fig) == 1
        assert fig[0]["DATA_TYPE"] == "BLOB"
        assert float(fig[0]["SEGMENT_MB"]) > 0 and int(fig[0]["DATA_LENGTH"]) > 0
    if no == "04":
        assert not [x for x in rows if x["TABLE_COLUMN"].startswith("APPOWNER.")]  # 読めない表は出ない
    if no in ("01", "02", "08", "09"):
        assert rows, t.name  # HR(対象スキーマ)の行がある


async def test_unqualified_name_is_target_schema(oracle_client: OracleClient):
    # 5b
    r = await oracle_client.run_query("SELECT COUNT(*) AS N FROM EMPLOYEES", 500)
    assert r["rows"] == [["107"]]
