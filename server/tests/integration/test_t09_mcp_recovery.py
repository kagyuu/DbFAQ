"""T09: MCP 子プロセスの強制終了からの回復(docs/P008-test-direction/T09-api-mcp-recovery.md)。"""

import asyncio
import os
import signal


def mcp_children() -> list[int]:
    me = os.getpid()
    found = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/stat") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read()
        except OSError:
            continue
        if ppid == me and b"dbfaq_mcp" in cmd:
            found.append(int(pid))
    return found


async def test_recover_after_kill(api_client):
    assert (await api_client.get("/api/health")).json()["status"] == "ok"
    assert (await api_client.post("/api/schema/refresh")).status_code == 200
    [pid] = mcp_children()
    os.kill(pid, signal.SIGKILL)
    for _ in range(50):
        if pid not in mcp_children():
            break
        await asyncio.sleep(0.1)

    statuses = []
    for _ in range(3):
        body = (await api_client.get("/api/health")).json()
        statuses.append(body["status"])
        if body["status"] == "ok":
            break
        await asyncio.sleep(1)
    assert statuses[-1] == "ok", statuses
    new = mcp_children()
    assert new and pid not in new

    r = await api_client.get("/api/schema/tables/HR/EMPLOYEES/rows")
    assert r.status_code == 200
