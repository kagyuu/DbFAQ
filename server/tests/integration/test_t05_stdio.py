"""T05: MCP サーバの標準出力は JSON-RPC のみ(docs/P008-test-direction/T05-mcp-stdio-hygiene.md)。"""

import json
import os
import subprocess
import sys

from .conftest import CONFIG_PATH

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t05", "version": "0"}},
}


def test_stdout_is_jsonrpc_only():
    proc = subprocess.Popen(
        [sys.executable, "-m", "dbfaq_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "DBFAQ_CONFIG": str(CONFIG_PATH)},
        text=True,
    )
    out, err = proc.communicate(json.dumps(INIT) + "\n", timeout=20)
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines, f"stdout が空です。stderr: {err[:500]}"
    for line in lines:
        assert json.loads(line)["jsonrpc"] == "2.0"
    json_logs = []
    for line in err.splitlines():
        try:
            json_logs.append(json.loads(line))
        except ValueError:
            continue  # FastMCP 自体が出す JSON でない行は許容する
    assert json_logs, f"stderr に JSON のログ行がありません。stderr: {err[:500]}"
    for rec in json_logs:
        assert "level" in rec and "msg" in rec
