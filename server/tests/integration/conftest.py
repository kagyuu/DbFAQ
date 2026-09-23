"""結合テスト(docs/P008-test-direction/)の共通フィクスチャ。実 Oracle(HR)と実 MCP 子プロセスを使う。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest
import yaml
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from dbfaq_api.main import create_app
from dbfaq_common.config import load_config

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = Path(os.environ.get("DBFAQ_CONFIG", REPO_ROOT / "config.yaml")).resolve()


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.oracle)


def write_config(tmp_path: Path, **oracle_overrides) -> Path:
    """元の config.yaml を読み、oracle セクションの値を変えて一時ファイルに書き出す。"""
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    data["oracle"].update(oracle_overrides)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def mcp_transport(config_path: Path) -> StdioTransport:
    return StdioTransport(
        command=sys.executable, args=["-m", "dbfaq_mcp"], env={**os.environ, "DBFAQ_CONFIG": str(config_path)}
    )


@pytest.fixture
async def mcp_client():
    async with Client(mcp_transport(CONFIG_PATH)) as client:
        yield client


@pytest.fixture
def base_config():
    return load_config(str(CONFIG_PATH), env={})


def make_app(config, sqlite_path: Path, config_path: Path = CONFIG_PATH):
    """実際の StdioMcpGateway を使う app。MCP 子プロセスには config_path を渡す。"""
    config = config.model_copy(update={"app": config.app.model_copy(update={"sqlite_path": str(sqlite_path)})})
    os.environ["DBFAQ_CONFIG"] = str(config_path)  # create_app が config_file_path() で子プロセスに渡す
    return create_app(config)


@pytest.fixture
async def api_client(tmp_path, base_config):
    app = make_app(base_config, tmp_path / "t.sqlite3")
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t", timeout=120) as c:
            c.app = app  # type: ignore[attr-defined]
            yield c
