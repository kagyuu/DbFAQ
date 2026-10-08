"""保存済み Query の API(docs/P002-frontend-spec.md §3.10〜§3.13)。※CR-005により追加"""

import logging

import pytest

from dbfaq_api.pdb_templates import PDB_TEMPLATES

from .test_api import assert_error, client, oracle  # noqa: F401  (フィクスチャ)

EMP = {"scope": "table", "owner": "HR", "table": "EMPLOYEES"}
SQL = "SELECT * FROM HR.EMPLOYEES WHERE LAST_NAME = 'King-SECRET-LITERAL'"


async def create(client, **kw):  # noqa: F811
    body = {**EMP, "name": "部署50", "description": "説明", "sql": SQL, **kw}
    return await client.post("/api/saved-queries", json=body)


async def test_templates_seeded_on_startup(client):  # noqa: F811
    r = await client.get("/api/saved-queries", params={"scope": "pdb"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == len(PDB_TEMPLATES) == 17
    assert all(i["is_template"] and i["owner"] is None and i["table"] is None for i in items)
    assert items[0]["name"] == "01. USERS 表領域の大きさ"


async def test_create_list_update_delete(client, oracle):  # noqa: F811
    r = await create(client, name="  部署50  ", description="  説明  ")
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["name"] == "部署50" and item["description"] == "説明" and item["sql"] == SQL
    assert item["scope"] == "table" and item["owner"] == "HR" and item["table"] == "EMPLOYEES"
    assert item["is_template"] is False and item["created_at"].endswith("Z")
    r = await client.get("/api/saved-queries", params=EMP)
    assert r.json()["items"] == [item]
    other = await client.get("/api/saved-queries", params={**EMP, "table": "DEPARTMENTS"})
    assert other.json()["items"] == []
    r = await client.put(f"/api/saved-queries/{item['id']}", json={"name": "改名", "description": "", "sql": "SELECT 1 FROM DUAL"})
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["sql"]) == ("改名", "SELECT 1 FROM DUAL")
    r = await client.delete(f"/api/saved-queries/{item['id']}")
    assert r.status_code == 204 and r.content == b""
    assert_error(await client.delete(f"/api/saved-queries/{item['id']}"), 404, "SAVED_QUERY_NOT_FOUND")
    assert_error(await client.put(f"/api/saved-queries/{item['id']}", json={"name": "x", "description": "", "sql": "x"}),
                 404, "SAVED_QUERY_NOT_FOUND")
    assert oracle.calls == []  # Oracle にはアクセスしない


async def test_sql_is_not_checked_on_save(client):  # noqa: F811
    r = await create(client, sql="DELETE FROM HR.EMPLOYEES")  # 実行時に検査する(P002 §3.11)
    assert r.status_code == 201


async def test_name_conflict(client):  # noqa: F811
    first = (await create(client)).json()
    err = assert_error(await create(client), 409, "QUERY_NAME_CONFLICT")
    assert "部署50" in err["message"]
    assert (await create(client, table="DEPARTMENTS")).status_code == 201
    assert (await create(client, scope="pdb", owner=None, table=None)).status_code == 201
    second = (await create(client, name="別名")).json()
    assert_error(await client.put(f"/api/saved-queries/{second['id']}", json={"name": "部署50", "description": "", "sql": SQL}),
                 409, "QUERY_NAME_CONFLICT")
    assert first["id"] != second["id"]


@pytest.mark.parametrize(
    "body",
    [
        {"scope": "view"},
        {"owner": None},
        {"table": None},
        {"scope": "pdb"},  # owner・table を指定している
        {"owner": ""},
        {"table": "x" * 129},
        {"name": "   "},
        {"name": "あ" * 101},
        {"description": "x" * 1001},
        {"sql": "  \n "},
        {"sql": "x" * 100_001},
        {"name": None},
    ],
)
async def test_create_validation(client, body):  # noqa: F811
    assert_error(await create(client, **body), 422, "VALIDATION_ERROR")


async def test_create_max_lengths_ok(client):  # noqa: F811
    r = await create(client, name="あ" * 100, description="x" * 1000)
    assert r.status_code == 201


@pytest.mark.parametrize(
    "params",
    [{}, {"scope": "x"}, {"scope": "table"}, {"scope": "table", "owner": "HR"}, {"scope": "pdb", "owner": "HR"},
     {"scope": "table", "owner": "HR", "table": "x" * 129}],
)
async def test_list_validation(client, params):  # noqa: F811
    assert_error(await client.get("/api/saved-queries", params=params), 422, "VALIDATION_ERROR")


async def test_put_requires_all_fields_and_valid_id(client):  # noqa: F811
    item = (await create(client)).json()
    assert_error(await client.put(f"/api/saved-queries/{item['id']}", json={"name": "x", "sql": "x"}), 422, "VALIDATION_ERROR")
    assert_error(await client.put("/api/saved-queries/0", json={"name": "x", "description": "", "sql": "x"}),
                 422, "VALIDATION_ERROR")
    assert_error(await client.delete("/api/saved-queries/abc"), 422, "VALIDATION_ERROR")


async def test_logs_do_not_contain_name_or_sql(client, caplog):  # noqa: F811
    caplog.set_level(logging.INFO)
    await create(client, name="名前-SECRET")
    text = "\n".join(str(r.__dict__) for r in caplog.records)
    assert "saved query created" in text
    assert "King-SECRET-LITERAL" not in text and "名前-SECRET" not in text
