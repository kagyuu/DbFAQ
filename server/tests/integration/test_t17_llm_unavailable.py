"""T17: LLM に届かないとき(docs/P008-test-direction/T17-llm-unavailable.md)。※CR-007により追加"""

import time

import httpx
import pytest

from dbfaq_api.config import load_config
from dbfaq_api.main import create_app

from .conftest import write_config


async def _client_for(tmp_path, llm_section):
    import yaml

    path = write_config(tmp_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if llm_section is None:
        data.pop("llm", None)
    else:
        data["llm"] = {**(data.get("llm") or {}), **llm_section}
    data.setdefault("app", {})["sqlite_path"] = str(tmp_path / "t.sqlite3")
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return create_app(load_config(str(path), env={}))


async def _run(app, fn):
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=60) as c,
    ):
        return await fn(c)


EMP = {"scope": "table", "owner": "HR", "table": "EMPLOYEES", "request": "社員の数"}


async def _check(c):
    started = time.perf_counter()
    h = (await c.get("/api/health")).json()
    elapsed = time.perf_counter() - started
    await c.post("/api/schema/refresh")
    gen = await c.post("/api/llm/sql", json=EMP)
    q = await c.post("/api/query", json={"sql": "SELECT COUNT(*) FROM HR.EMPLOYEES"})
    return h, elapsed, gen, q


async def test_unreachable(tmp_path):
    # 1・4
    app = await _client_for(tmp_path, {"base_url": "http://127.0.0.1:9", "health_timeout_sec": 3})
    h, elapsed, gen, q = await _run(app, _check)
    assert h["llm"]["status"] == "error" and "LLM に接続できません" in h["llm"]["message"]
    assert h["status"] == "ok" and elapsed < 4
    assert gen.status_code == 503 and gen.json()["error"]["code"] == "LLM_UNAVAILABLE"
    assert q.status_code == 200


@pytest.mark.llm
async def test_model_missing(tmp_path):
    # 2(開発用の Ollama を使う)
    app = await _client_for(tmp_path, {"model": "no-such-model:latest"})
    h, _, gen, _ = await _run(app, _check)
    assert h["llm"]["status"] == "error"
    assert "モデル no-such-model:latest が LLM にありません" in h["llm"]["message"]
    assert gen.status_code == 503 and gen.json()["error"]["code"] == "LLM_UNAVAILABLE"


async def test_not_configured(tmp_path):
    # 3
    app = await _client_for(tmp_path, None)
    h, _, gen, q = await _run(app, _check)
    assert h["llm"] == {"status": "disabled", "model": None, "base_url": None, "message": "LLM は設定されていません"}
    assert gen.status_code == 503 and "設定されていません" in gen.json()["error"]["message"]
    assert q.status_code == 200
