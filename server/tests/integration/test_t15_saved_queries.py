"""T15: 保存済み Query とスナップショットの置き換え(docs/P008-test-direction/T15-api-saved-queries.md)。※CR-005により追加

Oracle には接続しない(偽の Oracle アクセスで refresh の結果を切り替える。HR を変更しない方針のため)。
SQLite は 1 つのファイルを 2 回の起動にまたがって使う。
"""

import datetime as dt
from contextlib import asynccontextmanager

import httpx

from dbfaq_api.config import AppConfig, AppSection, OracleConfig
from dbfaq_api.main import create_app
from dbfaq_api.pdb_templates import PDB_TEMPLATES
from tests.fakes import FakeOracle
from tests.unit.api.fixtures import hr_snapshot

NOW = dt.datetime(2026, 10, 7, 12, 0, tzinfo=dt.UTC)
EMP = {"scope": "table", "owner": "HR", "table": "EMPLOYEES"}


def snapshot_a():
    return hr_snapshot(fetched_at="2026-10-07T01:00:00Z")


def snapshot_b():
    s = hr_snapshot(fetched_at="2026-10-07T02:00:00Z")
    s["tables"] = [t for t in s["tables"] if t["name"] != "EMPLOYEES"]
    for t in s["tables"]:
        t["constraints"] = [c for c in t["constraints"] if c.get("ref_table") != "EMPLOYEES"]
    return s


@asynccontextmanager
async def started(sqlite_path, oracle):
    cfg = AppConfig(
        oracle=OracleConfig(host="dbhost", service_name="FREEPDB1", user="hr", password="pw", schema="HR"),
        app=AppSection(sqlite_path=str(sqlite_path)),
    )
    app = create_app(cfg, oracle=oracle, now=lambda: NOW)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c,
    ):
        yield c


async def test_saved_queries_across_refresh_and_restart(tmp_path):
    db = tmp_path / "dbfaq.sqlite3"
    oracle = FakeOracle({"get_schema_snapshot": snapshot_a()})
    async with started(db, oracle) as c:
        # 1
        pdb = (await c.get("/api/saved-queries", params={"scope": "pdb"})).json()["items"]
        assert len(pdb) == len(PDB_TEMPLATES) == 17 and all(q["is_template"] for q in pdb)
        # 2
        assert (await c.post("/api/schema/refresh")).status_code == 200
        r = await c.post("/api/saved-queries", json={**EMP, "name": "部署50", "sql": "SELECT 1 FROM DUAL"})
        assert r.status_code == 201
        saved = r.json()
        r = await c.post("/api/saved-queries", json={**EMP, "name": "部署50", "sql": "SELECT 2 FROM DUAL"})
        assert r.status_code == 409 and r.json()["error"]["code"] == "QUERY_NAME_CONFLICT"
        r = await c.post("/api/saved-queries", json={**EMP, "table": "DEPARTMENTS", "name": "部署50", "sql": "SELECT 3 FROM DUAL"})
        assert r.status_code == 201
        # 3
        items = (await c.get("/api/saved-queries", params=EMP)).json()["items"]
        assert items == [saved]
        # 4
        oracle.responses["get_schema_snapshot"] = snapshot_b()
        assert (await c.post("/api/schema/refresh")).status_code == 200
        r = await c.get("/api/schema/tables/HR/EMPLOYEES")
        assert r.status_code == 404 and r.json()["error"]["code"] == "TABLE_NOT_FOUND"
        assert (await c.get("/api/saved-queries", params=EMP)).json()["items"] == [saved]
        # 5(ひな型を 1 件削除、1 件改名)
        assert (await c.delete(f"/api/saved-queries/{pdb[0]['id']}")).status_code == 204
        r = await c.put(f"/api/saved-queries/{pdb[1]['id']}", json={"name": "改名", "description": "", "sql": pdb[1]["sql"]})
        assert r.status_code == 200

    async with started(db, oracle) as c:  # 同じ SQLite ファイルで 2 回目の起動
        pdb2 = (await c.get("/api/saved-queries", params={"scope": "pdb"})).json()["items"]
        assert len(pdb2) == 16
        names = {q["name"] for q in pdb2}
        assert pdb[0]["name"] not in names and pdb[1]["name"] not in names and "改名" in names
        # 6
        oracle.responses["get_schema_snapshot"] = snapshot_a()
        assert (await c.post("/api/schema/refresh")).status_code == 200
        assert (await c.get("/api/schema/tables/HR/EMPLOYEES")).status_code == 200
        assert (await c.get("/api/saved-queries", params=EMP)).json()["items"] == [saved]
        r = await c.put(f"/api/saved-queries/{saved['id']}", json={"name": "部署50", "description": "", "sql": "SELECT 9 FROM DUAL"})
        assert r.status_code == 200 and r.json()["sql"] == "SELECT 9 FROM DUAL"
        assert (await c.delete(f"/api/saved-queries/{saved['id']}")).status_code == 204
        assert (await c.delete(f"/api/saved-queries/{saved['id']}")).status_code == 404
