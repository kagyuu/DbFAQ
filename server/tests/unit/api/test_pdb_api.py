"""GET /api/pdb(docs/P002-frontend-spec.md §3.14)。※CR-005により追加"""

import pytest

from dbfaq_api.oracle.errors import OracleFailure

from .test_api import assert_error, client, oracle  # noqa: F401  (フィクスチャ)

INFO = {
    "sections": [
        {"key": "overview", "title": "概要", "columns": [{"name": "ITEM", "data_type": "VARCHAR"}, {"name": "VALUE", "data_type": "VARCHAR"}],
         "rows": [["コンテナ名(PDB)", "FREEPDB1"]], "truncated": [[]], "error": None},
        {"key": "tablespaces", "title": "表領域の使用状況", "columns": [], "rows": [], "truncated": [],
         "error": {"code": "ORACLE_ERROR", "message": "ORA-00942: table or view does not exist", "ora_code": "ORA-00942"}},
    ]
}


async def test_pdb_info(client, oracle):  # noqa: F811
    oracle.responses["get_pdb_info"] = INFO
    r = await client.get("/api/pdb")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sections"] == INFO["sections"]
    assert body["fetched_at"] == "2026-09-23T01:20:00Z"
    assert isinstance(body["elapsed_ms"], int)


@pytest.mark.parametrize(
    "exc, status, code",
    [
        (OracleFailure("ORACLE_ERROR", "ORA-12541: no listener", "ORA-12541"), 502, "ORACLE_ERROR"),
        (OracleFailure("ORACLE_TIMEOUT", "timeout"), 504, "ORACLE_TIMEOUT"),
    ],
)
async def test_pdb_info_whole_error(client, oracle, exc, status, code):  # noqa: F811
    oracle.responses["get_pdb_info"] = exc
    assert_error(await client.get("/api/pdb"), status, code)
