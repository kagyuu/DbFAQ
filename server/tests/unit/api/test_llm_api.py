"""POST /api/llm/sql と health の llm(docs/P002-frontend-spec.md §3.7・§3.15)。※CR-007により追加"""

import httpx
import pytest

from dbfaq_api.config import AppConfig, AppSection, LlmConfig, OracleConfig
from dbfaq_api.llm.client import LlmFailure
from dbfaq_api.main import create_app
from dbfaq_api.oracle.errors import OracleFailure
from tests.fakes import FakeLlm, FakeOracle

from .fixtures import hr_snapshot
from .test_api import NOW, assert_error

EMP = {"scope": "table", "owner": "HR", "table": "EMPLOYEES"}
REQ = "給与の高い社員を上位5人-SECRET-REQUEST"
DEFAULT_LLM = LlmConfig()
SAMPLE = {"columns": [{"name": "EMPLOYEE_ID", "data_type": "NUMBER"}, {"name": "LAST_NAME", "data_type": "VARCHAR"}],
          "rows": [["100", "King-SECRET-DATA"]]}


def make(tmp_path, oracle, llm, llm_cfg=DEFAULT_LLM):
    cfg = AppConfig(
        oracle=OracleConfig(host="dbhost", service_name="FREEPDB1", user="hr", password="pw", schema="HR"),
        app=AppSection(sqlite_path=str(tmp_path / "t.sqlite3")),
        llm=llm_cfg,
    )
    return create_app(cfg, oracle=oracle, now=lambda: NOW, llm_access=llm)


@pytest.fixture
def oracle():
    return FakeOracle({
        "get_schema_snapshot": hr_snapshot(),
        "get_table_rows": SAMPLE,
        "ping": {"version": "23.26.3.0.0", "user": "HR", "current_schema": "HR"},
    })


@pytest.fixture
def llm():
    return FakeLlm("Sure.\n```sql\nSELECT LAST_NAME FROM HR.EMPLOYEES\nORDER BY SALARY DESC\nFETCH FIRST 5 ROWS ONLY;\n```")


async def run(tmp_path, oracle, llm, fn, llm_cfg=DEFAULT_LLM, refresh=True):
    app = make(tmp_path, oracle, llm, llm_cfg)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c,
    ):
        if refresh:
            await c.post("/api/schema/refresh")
        return await fn(c)


async def test_generate_table_scope(tmp_path, oracle, llm, capsys):

    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": f"  {REQ}  "})

    r = await run(tmp_path, oracle, llm, fn)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sql"] == "SELECT LAST_NAME FROM HR.EMPLOYEES\nORDER BY SALARY DESC\nFETCH FIRST 5 ROWS ONLY"
    assert body["guard"] == {"ok": True, "message": None}
    assert body["model"] == "fake-model" and body["elapsed_ms"] >= 0
    assert body["context"] == {"tables": ["HR.EMPLOYEES", "HR.JOB_HISTORY"], "sample_rows": 1, "truncated": False}
    system, user = llm.calls[0]
    assert "exactly one Oracle SQL query" in system
    assert "Oracle Database 23.26.3.0.0. Target schema: HR." in user and "Table HR.EMPLOYEES" in user
    assert "LAST_NAME=King-SECRET-DATA" in user and user.endswith(f"# Request\n{REQ}\n")
    assert ("get_table_rows", {"owner": "HR", "table": "EMPLOYEES", "offset": 0, "limit": 3}) in oracle.calls
    logs = capsys.readouterr().out  # ログは 1 行 1 JSON で標準出力に出る
    assert '"msg": "llm sql"' in logs and '"guard_ok": true' in logs
    assert "SECRET-REQUEST" not in logs and "SECRET-DATA" not in logs and "FETCH FIRST" not in logs


async def test_generate_pdb_scope_and_no_samples(tmp_path, oracle, llm):
    async def fn(c):
        return await c.post("/api/llm/sql", json={"scope": "pdb", "request": "USERS 表領域の大きさ"})

    r = await run(tmp_path, oracle, llm, fn)
    assert r.status_code == 200
    assert r.json()["context"]["sample_rows"] == 0
    assert "# Dictionary views" in llm.calls[0][1]
    assert not [c for c in oracle.calls if c[0] == "get_table_rows"]


async def test_sample_rows_zero_and_sample_failure(tmp_path, oracle, llm):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": "x"})

    r = await run(tmp_path, oracle, llm, fn, LlmConfig(sample_rows=0))
    assert r.json()["context"]["sample_rows"] == 0
    assert not [c for c in oracle.calls if c[0] == "get_table_rows"]
    oracle.responses["get_table_rows"] = OracleFailure("ORACLE_ERROR", "ORA-00942", "ORA-00942")
    r = await run(tmp_path, oracle, llm, fn)
    assert r.status_code == 200 and r.json()["context"]["sample_rows"] == 0  # データの例なしで続ける


async def test_guard_rejected_sql_is_returned(tmp_path, oracle):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": "x"})

    r = await run(tmp_path, oracle, FakeLlm("```sql\nDELETE FROM HR.EMPLOYEES\n```"), fn)
    assert r.status_code == 200
    body = r.json()
    assert body["sql"] == "DELETE FROM HR.EMPLOYEES" and body["guard"]["ok"] is False and body["guard"]["message"]


@pytest.mark.parametrize(
    "answer, status, code",
    [
        (LlmFailure("LLM_UNAVAILABLE", "LLM に接続できません: refused"), 503, "LLM_UNAVAILABLE"),
        (LlmFailure("LLM_TIMEOUT", "LLM の応答がタイムアウトしました"), 504, "LLM_TIMEOUT"),
        (LlmFailure("LLM_ERROR", "LLM がエラーを返しました: x"), 502, "LLM_ERROR"),
        ("I cannot help with that.```\n```", 502, "LLM_ERROR"),
    ],
)
async def test_llm_errors(tmp_path, oracle, answer, status, code):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": "x"})

    assert_error(await run(tmp_path, oracle, FakeLlm(answer), fn), status, code)


async def test_llm_not_configured(tmp_path, oracle, llm):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": "x"})

    err = assert_error(await run(tmp_path, oracle, llm, fn, None), 503, "LLM_UNAVAILABLE")
    assert "設定されていません" in err["message"] and llm.calls == []


@pytest.mark.parametrize(
    "body, status, code",
    [
        ({**EMP, "request": "   "}, 422, "VALIDATION_ERROR"),
        ({**EMP, "request": "あ" * 2001}, 422, "VALIDATION_ERROR"),
        ({"scope": "table", "owner": "HR", "request": "x"}, 422, "VALIDATION_ERROR"),
        ({"scope": "pdb", "owner": "HR", "request": "x"}, 422, "VALIDATION_ERROR"),
        ({**EMP, "table": "NO_SUCH", "request": "x"}, 404, "TABLE_NOT_FOUND"),
    ],
)
async def test_validation_and_not_found(tmp_path, oracle, llm, body, status, code):
    async def fn(c):
        return await c.post("/api/llm/sql", json=body)

    assert_error(await run(tmp_path, oracle, llm, fn), status, code)
    assert llm.calls == []


async def test_schema_not_loaded(tmp_path, oracle, llm):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": "x"})

    assert_error(await run(tmp_path, oracle, llm, fn, refresh=False), 404, "SCHEMA_NOT_LOADED")


@pytest.mark.parametrize(
    "llm_obj, llm_cfg, expected",
    [
        (FakeLlm(), LlmConfig(), {"status": "ok", "model": "fake-model", "base_url": "http://llm", "message": None}),
        (FakeLlm(health={"status": "error", "model": "m", "base_url": "u", "message": "LLM に接続できません: x"}),
         LlmConfig(), {"status": "error", "model": "m", "base_url": "u", "message": "LLM に接続できません: x"}),
        (FakeLlm(health=RuntimeError("boom")), LlmConfig(),
         {"status": "error", "model": "fake-model", "base_url": None, "message": "内部エラーが発生しました"}),
        (None, None, {"status": "disabled", "model": None, "base_url": None, "message": "LLM は設定されていません"}),
    ],
)
async def test_health_llm(tmp_path, oracle, llm_obj, llm_cfg, expected):
    async def fn(c):
        return await c.get("/api/health")

    r = await run(tmp_path, oracle, llm_obj, fn, llm_cfg, refresh=False)
    body = r.json()
    assert r.status_code == 200 and body["llm"] == expected
    assert body["status"] == "ok"  # 最上位の status は Oracle だけで決める


# ※CR-008により追加: LLM とのやりとり(P002 §3.15)
async def test_exchange_in_response(tmp_path, oracle, llm, capsys):
    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": REQ})

    body = (await run(tmp_path, oracle, llm, fn)).json()
    system, user = llm.calls[0]
    assert body["exchange"] == {"system": system, "user": user, "reply": llm.answer}
    assert body["exchange"]["user"].startswith("# Database") and REQ in body["exchange"]["user"]
    logs = capsys.readouterr().out
    assert "SECRET-REQUEST" not in logs and "exactly one Oracle SQL query" not in logs  # ログに出さない


@pytest.mark.parametrize(
    "answer, status, reply",
    [
        (LlmFailure("LLM_UNAVAILABLE", "LLM に接続できません: refused"), 503, None),
        (LlmFailure("LLM_TIMEOUT", "LLM の応答がタイムアウトしました"), 504, None),
        ("I cannot help with that.```\n```", 502, "I cannot help with that.```\n```"),
    ],
)
async def test_exchange_in_llm_errors(tmp_path, oracle, answer, status, reply):
    llm_obj = FakeLlm(answer)

    async def fn(c):
        return await c.post("/api/llm/sql", json={**EMP, "request": REQ})

    r = await run(tmp_path, oracle, llm_obj, fn)
    assert r.status_code == status
    ex = r.json()["error"]["exchange"]
    assert ex["system"] == llm_obj.calls[0][0] and ex["user"] == llm_obj.calls[0][1] and ex["reply"] == reply


@pytest.mark.parametrize(
    "body, llm_cfg",
    [({**EMP, "request": "x"}, None), ({**EMP, "request": "  "}, DEFAULT_LLM), ({**EMP, "table": "NO", "request": "x"}, DEFAULT_LLM)],
)
async def test_no_exchange_before_request(tmp_path, oracle, llm, body, llm_cfg):
    async def fn(c):
        return await c.post("/api/llm/sql", json=body)

    r = await run(tmp_path, oracle, llm, fn, llm_cfg)
    assert r.status_code in (503, 422, 404) and "exchange" not in r.json()["error"]
