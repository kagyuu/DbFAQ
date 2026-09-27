"""T09: Oracle との通信断からの回復(docs/P008-test-direction/T09-api-oracle-recovery.md)。

共有の Oracle 本体は止めず、テスト内の TCP 中継を止めて再開することで通信断と回復を作る。
"""

import asyncio

import httpx

from dbfaq_api.config import load_config

from .conftest import make_app, write_config


class TcpRelay:
    """127.0.0.1 の固定ポート → Oracle の双方向中継。stop() で待ち受けと中継中の接続をすべて切る。"""

    def __init__(self, target_host: str, target_port: int):
        self.target = (target_host, target_port)
        self.port = 0
        self._server: asyncio.Server | None = None
        self._writers: set[asyncio.StreamWriter] = set()

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", self.port)
        self.port = self._server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        assert self._server is not None
        self._server.close()
        for w in list(self._writers):
            w.transport.abort()
        self._writers.clear()
        await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            up_reader, up_writer = await asyncio.open_connection(*self.target)
        except OSError:
            writer.transport.abort()
            return
        self._writers.update((writer, up_writer))

        async def pipe(src: asyncio.StreamReader, dst: asyncio.StreamWriter) -> None:
            try:
                while data := await src.read(65536):
                    dst.write(data)
                    await dst.drain()
            except (ConnectionError, OSError):
                pass
            finally:
                dst.transport.abort()

        await asyncio.gather(pipe(reader, up_writer), pipe(up_reader, writer))
        self._writers.difference_update((writer, up_writer))


async def health_status(c: httpx.AsyncClient) -> str:
    return (await c.get("/api/health")).json()["status"]


async def test_recover_without_restart(tmp_path, base_config):
    relay = TcpRelay(base_config.oracle.host, base_config.oracle.port)
    await relay.start()
    cfg = load_config(str(write_config(tmp_path, host="127.0.0.1", port=relay.port, connect_timeout_sec=3)), env={})
    app = make_app(cfg, tmp_path / "t.sqlite3")
    try:
        async with app.router.lifespan_context(app), httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=120
        ) as c:
            # 1. 通信できる
            assert (await c.post("/api/schema/refresh")).status_code == 200
            assert await health_status(c) == "ok"

            # 2〜3. 通信断: Oracle のエラーになるが、保存済みのスキーマ情報は読める
            await relay.stop()
            h = (await c.get("/api/health")).json()
            assert h["status"] == "degraded" and h["oracle"]["status"] == "error", h
            r = await c.get("/api/schema/tables/HR/EMPLOYEES/rows")
            assert r.status_code in (502, 504), r.text
            assert r.json()["error"]["code"] in ("ORACLE_ERROR", "ORACLE_TIMEOUT")
            assert (await c.get("/api/schema")).status_code == 200

            # 4〜5. 同じポートで再開すると、app を再起動せずに回復する
            await relay.start()
            statuses = []
            for _ in range(3):
                statuses.append(await health_status(c))
                if statuses[-1] == "ok":
                    break
                await asyncio.sleep(1)
            assert statuses[-1] == "ok", statuses

            # 6. データと再読み込みも使える
            r = await c.get("/api/schema/tables/HR/EMPLOYEES/rows")
            assert r.status_code == 200 and len(r.json()["rows"]) == 50, r.text
            assert (await c.post("/api/schema/refresh")).status_code == 200
    finally:
        if relay._server is not None and relay._server.is_serving():
            await relay.stop()
