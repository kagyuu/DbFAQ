"""LLM(Ollama)へのアクセス(docs/P003-backend-spec.md §4.8.1、ADR-018)。※CR-007により追加

要求の文・応答の本文はログに出さない。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol

import httpx

from ..config import LlmConfig

logger = logging.getLogger(__name__)

LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
LLM_TIMEOUT = "LLM_TIMEOUT"
LLM_ERROR = "LLM_ERROR"

NOT_CONFIGURED = "LLM は設定されていません"


class LlmFailure(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class LlmAccess(Protocol):
    @property
    def model(self) -> str | None: ...

    async def health(self) -> dict[str, Any]: ...

    async def chat(self, system: str, user: str) -> str: ...

    async def close(self) -> None: ...


def _health(status: str, cfg: LlmConfig | None, message: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "model": cfg.model if cfg else None,
        "base_url": cfg.url if cfg else None,
        "message": message,
    }


class DisabledLlm:
    """`llm` 節が無い・enabled=false のとき。"""

    model = None

    async def health(self) -> dict[str, Any]:
        return _health("disabled", None, NOT_CONFIGURED)

    async def chat(self, system: str, user: str) -> str:
        raise LlmFailure(LLM_UNAVAILABLE, NOT_CONFIGURED)

    async def close(self) -> None:
        pass


def _error_text(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        if isinstance(body, dict) and body.get("error"):
            return str(body["error"])
    except ValueError:
        pass
    return f"HTTP {resp.status_code}"


class OllamaClient:
    def __init__(self, cfg: LlmConfig, transport: httpx.AsyncBaseTransport | None = None):
        self.cfg = cfg
        self._http = httpx.AsyncClient(base_url=cfg.url, transport=transport)

    @property
    def model(self) -> str:
        return self.cfg.model

    async def health(self) -> dict[str, Any]:
        """設定のモデルが使えるか。例外は送出せず status=error で返す。"""
        cfg = self.cfg
        try:
            resp = await self._http.get("/api/tags", timeout=cfg.health_timeout_sec)
        except httpx.ConnectTimeout:
            return _health("error", cfg, "LLM に接続できません: 接続がタイムアウトしました")
        except httpx.TimeoutException:
            return _health("error", cfg, "LLM の応答がタイムアウトしました")
        except httpx.HTTPError as e:
            return _health("error", cfg, f"LLM に接続できません: {e or type(e).__name__}")
        if resp.status_code != 200:
            return _health("error", cfg, f"LLM がエラーを返しました: {_error_text(resp)}")
        try:
            models = resp.json().get("models") or []
        except (ValueError, AttributeError):
            return _health("error", cfg, "LLM の応答の形が不正です")
        wanted = {cfg.model, cfg.model if ":" in cfg.model else cfg.model + ":latest"}
        names = {m.get(k) for m in models if isinstance(m, dict) for k in ("name", "model")}
        if wanted & names:
            return _health("ok", cfg)
        return _health("error", cfg, f"モデル {cfg.model} が LLM にありません")

    async def chat(self, system: str, user: str) -> str:
        cfg = self.cfg
        options: dict[str, Any] = {"temperature": cfg.temperature}
        if cfg.seed is not None:
            options["seed"] = cfg.seed
        if cfg.num_ctx is not None:
            options["num_ctx"] = cfg.num_ctx
        body = {
            "model": cfg.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": options,
        }
        # 接続の確立は health_timeout_sec で打ち切る(届かないホストで timeout_sec まで待たない。P003 §4.8.1)
        timeout = httpx.Timeout(cfg.timeout_sec, connect=cfg.health_timeout_sec)
        try:
            resp = await asyncio.wait_for(self._http.post("/api/chat", json=body, timeout=timeout), cfg.timeout_sec)
        except httpx.ConnectTimeout as e:
            raise LlmFailure(LLM_UNAVAILABLE, "LLM に接続できません: 接続がタイムアウトしました") from e
        except (TimeoutError, httpx.TimeoutException) as e:
            raise LlmFailure(LLM_TIMEOUT, f"LLM の応答がタイムアウトしました({cfg.timeout_sec} 秒)") from e
        except httpx.HTTPError as e:
            raise LlmFailure(LLM_UNAVAILABLE, f"LLM に接続できません: {e or type(e).__name__}") from e
        if resp.status_code != 200:
            text = _error_text(resp)
            if resp.status_code == 404 and "not found" in text:
                raise LlmFailure(LLM_UNAVAILABLE, f"モデル {cfg.model} が LLM にありません")
            raise LlmFailure(LLM_ERROR, f"LLM がエラーを返しました: {text}")
        try:
            content = resp.json()["message"]["content"]
        except (ValueError, KeyError, TypeError) as e:
            raise LlmFailure(LLM_ERROR, "LLM の応答の形が不正です") from e
        if not isinstance(content, str):
            raise LlmFailure(LLM_ERROR, "LLM の応答の形が不正です")
        return content

    async def close(self) -> None:
        await self._http.aclose()


def create_llm(cfg: LlmConfig | None) -> LlmAccess:
    if cfg is None or not cfg.enabled:
        return DisabledLlm()
    return OllamaClient(cfg)
