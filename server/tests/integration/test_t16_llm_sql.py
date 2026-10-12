"""T16: 自然言語から LLM で SQL を作成(docs/P008-test-direction/T16-llm-sql.md)。※CR-007により追加

実 Oracle(HR)と開発用の Ollama(config.yaml の llm)を使う。LLM の SQL の文字列そのものは比べない(P006 §3.1)。
"""

import httpx
import pytest

from dbfaq_api.main import create_app

pytestmark = pytest.mark.llm


@pytest.fixture
async def client(tmp_path, base_config):
    assert base_config.llm is not None, "config.yaml に llm 節が要る(T16 の前提)"
    config = base_config.model_copy(
        update={"app": base_config.app.model_copy(update={"sqlite_path": str(tmp_path / "t.sqlite3")})}
    )
    app = create_app(config)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=300) as c,
    ):
        yield c


def _is_select(sql: str) -> bool:
    return sql.lstrip().upper().startswith(("SELECT", "WITH"))


async def test_llm_sql_end_to_end(client, base_config):
    # 1
    h = (await client.get("/api/health")).json()
    assert h["llm"]["status"] == "ok", h["llm"]
    assert h["llm"]["model"] == base_config.llm.model and h["status"] == "ok"
    # 2
    assert (await client.post("/api/schema/refresh")).status_code == 200
    emp = {"scope": "table", "owner": "HR", "table": "EMPLOYEES"}
    # 3・4
    r = await client.post("/api/llm/sql", json={**emp, "request": "給与の高い社員を上位5人、姓と部署名と給与を表示"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["guard"]["ok"] is True, body
    assert _is_select(body["sql"])
    assert body["context"]["tables"][0] == "HR.EMPLOYEES" and "HR.DEPARTMENTS" in body["context"]["tables"]
    assert body["context"]["sample_rows"] == 3 and body["elapsed_ms"] > 0
    q = await client.post("/api/query", json={"sql": body["sql"]})
    assert q.status_code == 200, (body["sql"], q.text)
    assert 1 <= q.json()["row_count"] <= 5
    # 5
    r = await client.post("/api/llm/sql", json={**emp, "request": "部署ごとの社員数を多い順に"})
    assert r.status_code == 200 and r.json()["guard"]["ok"] is True, r.text
    q = await client.post("/api/query", json={"sql": r.json()["sql"]})
    assert q.status_code == 200 and q.json()["row_count"] >= 1, (r.json()["sql"], q.text)
    # 6
    r = await client.post("/api/llm/sql", json={"scope": "pdb", "request": "USERS 表領域の合計サイズ(MB)"})
    assert r.status_code == 200 and r.json()["guard"]["ok"] is True, r.text
    assert r.json()["context"]["sample_rows"] == 0
    q = await client.post("/api/query", json={"sql": r.json()["sql"]})
    assert q.status_code == 200, (r.json()["sql"], q.text)
