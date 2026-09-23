"""T07: rows API(docs/P008-test-direction/T07-api-rows.md)。"""

import sqlite3


async def test_rows_api(api_client, tmp_path):
    assert (await api_client.post("/api/schema/refresh")).status_code == 200

    r = await api_client.get("/api/schema/tables/HR/EMPLOYEES/rows?offset=100&limit=50")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["rows"]) == 7 and body["has_next"] is False
    assert (body["owner"], body["table"]) == ("HR", "EMPLOYEES")
    assert isinstance(body["elapsed_ms"], int) and body["elapsed_ms"] >= 0

    r = await api_client.get("/api/schema/tables/HR/EMPLOYEES/rows?limit=501")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"

    r = await api_client.get("/api/schema/tables/HR/NO_SUCH/rows")
    assert r.status_code == 404 and r.json()["error"]["code"] == "TABLE_NOT_FOUND"

    # Oracle 側で削除されたテーブルの再現: スナップショットにだけ存在する表を足す
    with sqlite3.connect(tmp_path / "t.sqlite3") as conn:
        sid = conn.execute("SELECT id FROM snapshots WHERE owner = 'HR'").fetchone()[0]
        conn.execute("INSERT INTO db_tables (snapshot_id, name, iot) VALUES (?, 'GHOST', 0)", (sid,))
    r = await api_client.get("/api/schema/tables/HR/GHOST/rows")
    assert r.status_code == 502, r.text
    assert r.json()["error"]["code"] == "ORACLE_ERROR"
    assert r.json()["error"]["ora_code"] == "ORA-00942"
