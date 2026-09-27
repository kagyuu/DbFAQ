from pathlib import Path

import pytest

from dbfaq_api.config import ConfigError, load_config

REPO_ROOT = Path(__file__).resolve().parents[3]

MINIMAL = """
oracle:
  host: dbhost
  service_name: FREEPDB1
  user: hr
  password: "{pw}"
"""


def write(tmp_path: Path, text: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_minimal_defaults(tmp_path):
    cfg = load_config(write(tmp_path, MINIMAL.format(pw="x")), env={})
    assert cfg.oracle.port == 1521
    assert cfg.oracle.query_timeout_sec == 30
    assert cfg.oracle.pool_min == 1 and cfg.oracle.pool_max == 4
    assert cfg.app.sqlite_path == "./data/dbfaq.sqlite3"
    assert cfg.oracle.target_schema == "HR"
    assert cfg.oracle.dsn == "dbhost:1521/FREEPDB1"


def test_legacy_mcp_setting_is_ignored(tmp_path):
    # CR-002 で廃止した app.mcp_call_timeout_sec が残っている古い config.yaml も読める
    cfg = load_config(write(tmp_path, MINIMAL.format(pw="x") + "app:\n  mcp_call_timeout_sec: 90\n"), env={})
    assert not hasattr(cfg.app, "mcp_call_timeout_sec")


def test_explicit_schema(tmp_path):
    cfg = load_config(write(tmp_path, MINIMAL.format(pw="x") + "  schema: OTHER\n"), env={})
    assert cfg.oracle.target_schema == "OTHER"


def test_env_overrides(tmp_path):
    env = {
        "DBFAQ_ORACLE_HOST": "host.docker.internal",
        "DBFAQ_ORACLE_PORT": "1522",
        "DBFAQ_ORACLE_PASSWORD": "from-env",
        "DBFAQ_SQLITE_PATH": "/data/x.sqlite3",
    }
    cfg = load_config(write(tmp_path, MINIMAL.format(pw="x")), env=env)
    assert cfg.oracle.host == "host.docker.internal"
    assert cfg.oracle.port == 1522
    assert cfg.oracle.password.get_secret_value() == "from-env"
    assert cfg.app.sqlite_path == "/data/x.sqlite3"


def test_path_from_env(tmp_path):
    path = write(tmp_path, MINIMAL.format(pw="x"))
    cfg = load_config(env={"DBFAQ_CONFIG": path})
    assert cfg.oracle.host == "dbhost"


def test_example_file_is_valid():
    cfg = load_config(str(REPO_ROOT / "config.example.yaml"), env={})
    assert cfg.oracle.service_name == "FREEPDB1"


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="見つかりません"):
        load_config(str(tmp_path / "nope.yaml"), env={})


def test_missing_password(tmp_path):
    text = "oracle:\n  host: h\n  service_name: s\n  user: u\n"
    with pytest.raises(ConfigError) as ei:
        load_config(write(tmp_path, text), env={})
    assert "oracle.password" in str(ei.value)


def test_port_out_of_range(tmp_path):
    with pytest.raises(ConfigError, match="oracle.port"):
        load_config(write(tmp_path, MINIMAL.format(pw="x") + "  port: 70000\n"), env={})


def test_pool_min_greater_than_max(tmp_path):
    text = MINIMAL.format(pw="x") + "  pool_min: 3\n  pool_max: 2\n"
    with pytest.raises(ConfigError, match="pool_max"):
        load_config(write(tmp_path, text), env={})


def test_password_never_leaks(tmp_path):
    secret = "s3cr3t-XYZ"
    cfg = load_config(write(tmp_path, MINIMAL.format(pw=secret)), env={})
    assert secret not in repr(cfg)
    assert secret not in str(cfg.model_dump())
    with pytest.raises(ConfigError) as ei:
        load_config(write(tmp_path, MINIMAL.format(pw=secret) + "  port: 0\n"), env={})
    assert secret not in str(ei.value)
