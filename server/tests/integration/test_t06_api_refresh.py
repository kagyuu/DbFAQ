"""T06: backend→MCP→Oracle→SQLite のスキーマ再読み込み(docs/P008-test-direction/T06-api-refresh-schema.md)。"""

import sqlite3


async def test_refresh_and_read(api_client, tmp_path):
    r = await api_client.get("/api/schema")
    assert r.json()["loaded"] is False

    r = await api_client.post("/api/schema/refresh")
    assert r.status_code == 200, r.text
    snap = r.json()["snapshot"]
    assert (snap["owner"], snap["table_count"], snap["relation_count"]) == ("HR", 7, 10)

    view = (await api_client.get("/api/schema")).json()
    names = [t["name"] for t in view["tables"]]
    assert names == sorted(names) and len(names) == 7
    assert len(view["relations"]) == 10
    emp = {c["name"]: c for c in next(t for t in view["tables"] if t["name"] == "EMPLOYEES")["columns"]}
    assert emp["EMPLOYEE_ID"]["is_pk"] is True
    assert emp["DEPARTMENT_ID"]["is_fk"] is True

    d = (await api_client.get("/api/schema/tables/HR/EMPLOYEES")).json()
    assert d["primary_key"]["name"] == "EMP_EMP_ID_PK"
    assert [u["name"] for u in d["unique_keys"]] == ["EMP_EMAIL_UK"]
    assert [f["name"] for f in d["foreign_keys"]] == ["EMP_DEPT_FK", "EMP_JOB_FK", "EMP_MANAGER_FK"]
    assert {x["name"] for x in d["referenced_by"]} == {"DEPT_MGR_FK", "JHIST_EMP_FK", "EMP_MANAGER_FK"}
    assert len(d["indexes"]) == 6
    assert d["table"]["num_rows"] == 107

    r = await api_client.post("/api/schema/refresh")
    assert r.status_code == 200
    with sqlite3.connect(tmp_path / "t.sqlite3") as conn:
        assert conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1
