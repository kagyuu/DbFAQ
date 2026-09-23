import io
import json
import logging

from dbfaq_common.logging import mask_secret, setup_logging


def _lines(buf: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]


def test_json_line_with_extra():
    buf = io.StringIO()
    setup_logging("INFO", stream=buf)
    logging.getLogger("t").info("hello", extra={"tables": 7})
    rec = _lines(buf)[-1]
    assert rec["level"] == "INFO"
    assert rec["msg"] == "hello"
    assert rec["logger"] == "t"
    assert rec["tables"] == 7
    assert rec["ts"].endswith("Z")


def test_exception_is_included():
    buf = io.StringIO()
    setup_logging("INFO", stream=buf)
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("t").exception("failed")
    rec = _lines(buf)[-1]
    assert "ValueError: boom" in rec["exc"]


def test_setup_twice_keeps_single_handler():
    setup_logging("INFO", stream=io.StringIO())
    setup_logging("DEBUG", stream=io.StringIO())
    assert len(logging.getLogger().handlers) == 1
    assert logging.getLogger().level == logging.DEBUG


def test_mask_secret():
    assert mask_secret("user/pw@host pw", "pw") == "user/***@host ***"


def test_mask_secret_empty():
    assert mask_secret("abc", None) == "abc"
    assert mask_secret("abc", "") == "abc"
