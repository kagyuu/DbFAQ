"""LLM アクセス(docs/P003-backend-spec.md §4.8.1)。※CR-007により追加"""

import asyncio
import json

import httpx
import pytest

from dbfaq_api.config import LlmConfig
from dbfaq_api.llm.client import LLM_ERROR, LLM_TIMEOUT, LLM_UNAVAILABLE, LlmFailure, OllamaClient, create_llm

CFG = LlmConfig(model="gemma4:e2b-it-qat", timeout_sec=2, health_timeout_sec=1)


def client(handler, cfg=CFG):
    return OllamaClient(cfg, transport=httpx.MockTransport(handler))


def tags(*names):
    return httpx.Response(200, json={"models": [{"name": n, "model": n} for n in names]})


async def test_health_ok_and_latest_suffix():
    assert (await client(lambda r: tags("gemma4:e2b-it-qat")).health())["status"] == "ok"
    cfg = LlmConfig(model="codegemma")
    h = await client(lambda r: tags("codegemma:latest"), cfg).health()
    assert h == {"status": "ok", "model": "codegemma", "base_url": "http://localhost:11434", "message": None}


@pytest.mark.parametrize(
    "handler, message",
    [
        (lambda r: tags("gemma3:1b"), "モデル gemma4:e2b-it-qat が LLM にありません"),
        (lambda r: (_ for _ in ()).throw(httpx.ConnectError("refused")), "LLM に接続できません"),
        (lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("slow")), "LLM の応答がタイムアウトしました"),
        (lambda r: (_ for _ in ()).throw(httpx.ConnectTimeout("drop")), "LLM に接続できません: 接続がタイムアウトしました"),
        (lambda r: httpx.Response(500, json={"error": "boom"}), "LLM がエラーを返しました: boom"),
        (lambda r: httpx.Response(200, text="not json"), "LLM の応答の形が不正です"),
    ],
)
async def test_health_errors(handler, message):
    h = await client(handler).health()
    assert h["status"] == "error" and message in h["message"]


async def test_chat_request_and_content():
    seen = {}

    def handler(r):
        seen["path"] = r.url.path
        seen["body"] = json.loads(r.content)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "```sql\nSELECT 1 FROM DUAL\n```"}})

    out = await client(handler).chat("sys", "usr")
    assert out == "```sql\nSELECT 1 FROM DUAL\n```"
    assert seen["path"] == "/api/chat"
    assert seen["body"] == {
        "model": "gemma4:e2b-it-qat",
        "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}],
        "stream": False,
        "options": {"temperature": 0.0, "seed": 42, "num_ctx": 8192},
    }


@pytest.mark.parametrize(
    "handler, code",
    [
        (lambda r: (_ for _ in ()).throw(httpx.ConnectError("refused")), LLM_UNAVAILABLE),
        (lambda r: httpx.Response(404, json={"error": "model 'x' not found"}), LLM_UNAVAILABLE),
        (lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("slow")), LLM_TIMEOUT),
        (lambda r: (_ for _ in ()).throw(httpx.ConnectTimeout("drop")), LLM_UNAVAILABLE),
        (lambda r: httpx.Response(500, json={"error": "out of memory"}), LLM_ERROR),
        (lambda r: httpx.Response(200, json={"done": True}), LLM_ERROR),
    ],
)
async def test_chat_errors(handler, code):
    with pytest.raises(LlmFailure) as ei:
        await client(handler).chat("s", "u")
    assert ei.value.code == code


async def test_chat_total_timeout():
    async def slow(r):
        await asyncio.sleep(5)
        return httpx.Response(200, json={"message": {"content": "x"}})

    cfg = LlmConfig(timeout_sec=1)
    with pytest.raises(LlmFailure) as ei:
        await OllamaClient(cfg, transport=httpx.MockTransport(slow)).chat("s", "u")
    assert ei.value.code == LLM_TIMEOUT


async def test_disabled():
    llm = create_llm(None)
    assert (await llm.health())["status"] == "disabled"
    assert (await create_llm(LlmConfig(enabled=False)).health())["model"] is None
    with pytest.raises(LlmFailure) as ei:
        await llm.chat("s", "u")
    assert ei.value.code == LLM_UNAVAILABLE and "設定されていません" in ei.value.message
