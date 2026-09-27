import asyncio
import datetime as dt

import httpx
import pytest

from dbfaq_api.config import AppConfig, AppSection, OracleConfig
from dbfaq_api.main import create_app
from dbfaq_api.oracle.errors import OracleFailure
from tests.fakes import FakeOracle

from .fixtures import hr_snapshot

SECRET = "pw-SECRET-123"
NOW = dt.datetime(2026, 9, 23, 1, 20, tzinfo=dt.UTC)

ROWS = {
    "columns": [{"name": "EMPLOYEE_ID", "data_type": "NUMBER"}],
    "rows": [["100"]], "truncated": [[]], "offset": 0, "limit": 50, "has_next": False,
    "order_basis": "PRIMARY_KEY", "order_by": ["EMPLOYEE_ID"], "elapsed_ms": 5,
}


@pytest.fixture
def oracle():
    return FakeOracle({
        "get_schema_snapshot": hr_snapshot(),
        "get_table_rows": ROWS,
        "ping": {"version": "23.26.3.0.0", "user": "HR", "current_schema": "HR"},
    })


@pytest.fixture
async def client(tmp_path, oracle):
    cfg = AppConfig(
        oracle=OracleConfig(host="dbhost", service_name="FREEPDB1", user="hr", password=SECRET, schema="HR"),
        app=AppSection(sqlite_path=str(tmp_path / "t.sqlite3")),
    )
    app = create_app(cfg, oracle=oracle, now=lambda: NOW)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            yield c


def assert_error(resp, status, code):
    assert resp.status_code == status, resp.text
    assert resp.json()["error"]["code"] == code
    return resp.json()["error"]


async def test_schema_not_loaded(client):
    r = await client.get("/api/schema")
    assert r.status_code == 200
    assert r.json() == {"loaded": False, "snapshot": None, "tables": [], "relations": []}
    assert "access-control-allow-origin" not in r.headers


async def test_refresh_then_schema(client, oracle):
    r = await client.post("/api/schema/refresh")
    assert r.status_code == 200
    assert r.json()["snapshot"]["table_count"] == 4
    assert oracle.calls[0] == ("get_schema_snapshot", {"owner": "HR"})
    view = (await client.get("/api/schema")).json()
    assert view["loaded"] is True
    assert len(view["tables"]) == 4 and len(view["relations"]) == 4


async def test_refresh_oracle_error_keeps_previous(client, oracle):
    await client.post("/api/schema/refresh")
    oracle.responses["get_schema_snapshot"] = OracleFailure("ORACLE_ERROR", "ORA-01017: invalid credential", "ORA-01017")
    err = assert_error(await client.post("/api/schema/refresh"), 502, "ORACLE_ERROR")
    assert err["ora_code"] == "ORA-01017"
    assert (await client.get("/api/schema")).json()["snapshot"]["fetched_at"] == "2026-09-23T01:15:02Z"


@pytest.mark.parametrize(
    "exc, status, code",
    [
        (OracleFailure("ORACLE_TIMEOUT", "timeout"), 504, "ORACLE_TIMEOUT"),
        (OracleFailure("UNEXPECTED_CODE", "x"), 500, "INTERNAL_ERROR"),
    ],
)
async def test_refresh_errors(client, oracle, exc, status, code):
    oracle.responses["get_schema_snapshot"] = exc
    assert_error(await client.post("/api/schema/refresh"), status, code)


async def test_refresh_schema_not_found(client, oracle):
    oracle.responses["get_schema_snapshot"] = OracleFailure("NOT_FOUND", "x")
    err = assert_error(await client.post("/api/schema/refresh"), 502, "ORACLE_ERROR")
    assert "スキーマ HR が見つかりません" in err["message"]


async def test_refresh_in_progress(client, oracle):
    release = asyncio.Event()

    async def slow(args):
        await release.wait()
        return hr_snapshot()

    oracle.responses["get_schema_snapshot"] = slow
    first = asyncio.create_task(client.post("/api/schema/refresh"))
    await asyncio.sleep(0.1)
    assert_error(await client.post("/api/schema/refresh"), 409, "REFRESH_IN_PROGRESS")
    release.set()
    assert (await first).status_code == 200


async def test_table_detail(client):
    assert_error(await client.get("/api/schema/tables/HR/EMPLOYEES"), 404, "SCHEMA_NOT_LOADED")
    await client.post("/api/schema/refresh")
    r = await client.get("/api/schema/tables/HR/EMPLOYEES")
    assert r.status_code == 200
    body = r.json()
    assert body["primary_key"]["name"] == "EMP_EMP_ID_PK"
    assert {x["name"] for x in body["referenced_by"]} == {"EMP_MANAGER_FK", "JHIST_EMP_FK"}
    assert_error(await client.get("/api/schema/tables/HR/NOPE"), 404, "TABLE_NOT_FOUND")
    assert_error(await client.get("/api/schema/tables/SCOTT/EMPLOYEES"), 404, "TABLE_NOT_FOUND")
    assert_error(await client.get(f"/api/schema/tables/HR/{'A' * 129}"), 422, "VALIDATION_ERROR")


async def test_rows(client, oracle):
    await client.post("/api/schema/refresh")
    r = await client.get("/api/schema/tables/HR/EMPLOYEES/rows?offset=50&limit=20")
    assert r.status_code == 200
    assert r.json()["owner"] == "HR" and r.json()["table"] == "EMPLOYEES"
    assert oracle.calls[-1] == ("get_table_rows", {"owner": "HR", "table": "EMPLOYEES", "offset": 50, "limit": 20})


@pytest.mark.parametrize("query", ["offset=-1", "offset=100001", "limit=0", "limit=501", "offset=abc"])
async def test_rows_validation(client, query):
    await client.post("/api/schema/refresh")
    err = assert_error(await client.get(f"/api/schema/tables/HR/EMPLOYEES/rows?{query}"), 422, "VALIDATION_ERROR")
    assert query.split("=")[0] in err["message"]


async def test_rows_unknown_table_does_not_call_oracle(client, oracle):
    await client.post("/api/schema/refresh")
    before = len(oracle.calls)
    assert_error(await client.get("/api/schema/tables/HR/NOPE/rows"), 404, "TABLE_NOT_FOUND")
    assert len(oracle.calls) == before


@pytest.mark.parametrize(
    "exc, status, code, ora",
    [
        (OracleFailure("NOT_FOUND", "x"), 502, "ORACLE_ERROR", "ORA-00942"),
        (OracleFailure("ORACLE_TIMEOUT", "t"), 504, "ORACLE_TIMEOUT", None),
        (OracleFailure("INVALID_ARGUMENT", "table が不正です"), 422, "VALIDATION_ERROR", None),
    ],
)
async def test_rows_errors(client, oracle, exc, status, code, ora):
    await client.post("/api/schema/refresh")
    oracle.responses["get_table_rows"] = exc
    err = assert_error(await client.get("/api/schema/tables/HR/EMPLOYEES/rows"), status, code)
    assert err.get("ora_code") == ora


async def test_health_ok(client):
    r = await client.get("/api/health")
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ok"
    assert "mcp" not in body
    assert body["oracle"] == {"status": "ok", "version": "23.26.3.0.0", "user": "HR", "message": None}
    assert body["config"] == {"host": "dbhost", "port": 1521, "service_name": "FREEPDB1", "user": "hr",
                              "schema": "HR", "query_timeout_sec": 30}
    assert body["checked_at"] == "2026-09-23T01:20:00Z"
    assert SECRET not in r.text


async def test_health_oracle_error(client, oracle):
    oracle.responses["ping"] = OracleFailure("ORACLE_ERROR", "ORA-12541: no listener", "ORA-12541")
    body = (await client.get("/api/health")).json()
    assert body["status"] == "degraded"
    assert body["oracle"]["status"] == "error"
    assert body["oracle"]["message"].startswith("ORA-12541")


async def test_health_unexpected_error_is_still_200(client, oracle):
    oracle.responses["ping"] = RuntimeError("boom")
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded" and r.json()["oracle"]["status"] == "error"
    assert "boom" not in r.text
