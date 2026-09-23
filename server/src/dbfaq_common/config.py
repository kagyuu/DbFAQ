"""config.yaml の読み込み(docs/P003-backend-spec.md §2、ADR-013)。"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator

DEFAULT_CONFIG_PATH = "config.yaml"

# 環境変数 → (セクション, 項目)
_ENV_OVERRIDES = {
    "DBFAQ_ORACLE_HOST": ("oracle", "host"),
    "DBFAQ_ORACLE_PORT": ("oracle", "port"),
    "DBFAQ_ORACLE_PASSWORD": ("oracle", "password"),
    "DBFAQ_SQLITE_PATH": ("app", "sqlite_path"),
}


class ConfigError(Exception):
    """設定ファイルが無い、または内容が不正。メッセージにパスワードの値を含めない。"""


class OracleConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    host: str
    port: int = Field(1521, ge=1, le=65535)
    service_name: str
    user: str
    password: SecretStr
    schema_: str | None = Field(None, alias="schema")
    query_timeout_sec: int = Field(30, ge=1, le=600)
    connect_timeout_sec: int = Field(10, ge=1, le=600)
    pool_min: int = Field(1, ge=1)
    pool_max: int = Field(4, ge=1)

    @model_validator(mode="after")
    def _check_pool(self) -> OracleConfig:
        if self.pool_max < self.pool_min:
            raise ValueError("pool_max は pool_min 以上にしてください")
        return self

    @property
    def target_schema(self) -> str:
        return self.schema_ or self.user.upper()

    @property
    def dsn(self) -> str:
        return f"{self.host}:{self.port}/{self.service_name}"


class AppSection(BaseModel):
    sqlite_path: str = "./data/dbfaq.sqlite3"
    log_level: str = "INFO"
    mcp_call_timeout_sec: int = Field(90, ge=1, le=600)


class AppConfig(BaseModel):
    oracle: OracleConfig
    app: AppSection = AppSection()


def config_file_path(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    return env.get("DBFAQ_CONFIG", DEFAULT_CONFIG_PATH)


def _format_validation_error(err: ValidationError) -> str:
    # 入力値(input)は含めない。パスワードが漏れないようにするため。
    parts = []
    for e in err.errors():
        loc = ".".join(str(x) for x in e["loc"])
        parts.append(f"{loc}: {e['msg']}")
    return "設定ファイルの内容が不正です: " + "; ".join(parts)


def load_config(path: str | None = None, env: Mapping[str, str] | None = None) -> AppConfig:
    env = os.environ if env is None else env
    path = path or config_file_path(env)
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"設定ファイルが見つかりません: {path}")
    try:
        data: Any = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"設定ファイルを YAML として読めません: {path}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"設定ファイルの形式が不正です: {path}")

    for var, (section, key) in _ENV_OVERRIDES.items():
        value = env.get(var)
        if value:
            sec = data.setdefault(section, {})
            if isinstance(sec, dict):
                sec[key] = value
    try:
        return AppConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigError(_format_validation_error(e)) from None
