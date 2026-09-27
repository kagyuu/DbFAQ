"""T08: Oracle に届かない設定(docs/P008-test-direction/T08-api-oracle-unreachable.md)。"""

import httpx

from dbfaq_api.config import load_config

from .conftest import make_app, write_config


async def test_unreachable(tmp_path, base_config):
    db = tmp_path / "t.sqlite3"
    app = make_app(base_config, db)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=120) as c:
            assert (await c.post("/api/schema/refresh")).status_code == 200
            f0 = (await c.get("/api/schema")).json()["snapshot"]["fetched_at"]

    bad_path = write_config(tmp_path, port=1, connect_timeout_sec=3)
    bad = load_config(str(bad_path), env={})
    app = make_app(bad, db)
    async with app.router.lifespan_context(app):  # 起動に成功する
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=120) as c:
            view = (await c.get("/api/schema")).json()
            assert view["loaded"] is True and len(view["tables"]) == 7

            r = await c.post("/api/schema/refresh")
            assert r.status_code in (502, 504), r.text
            assert r.json()["error"]["code"] in ("ORACLE_ERROR", "ORACLE_TIMEOUT")

            assert (await c.get("/api/schema")).json()["snapshot"]["fetched_at"] == f0

            h = (await c.get("/api/health")).json()
            assert h["status"] == "degraded"
            assert "mcp" not in h
            assert h["oracle"]["status"] == "error" and h["oracle"]["message"]
