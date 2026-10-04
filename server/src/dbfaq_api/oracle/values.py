"""セル値の表示用文字列化(docs/P003-backend-spec.md §3.7、ADR-005)。"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from decimal import Decimal

MAX_TEXT = 1000
MAX_BYTES = 32
ELLIPSIS = "…"

_TIMESTAMP_TYPES = {"DB_TYPE_TIMESTAMP", "DB_TYPE_TIMESTAMP_TZ", "DB_TYPE_TIMESTAMP_LTZ"}


def _tz_suffix(value: dt.datetime) -> str:
    if value.tzinfo is None:
        return ""
    z = value.strftime("%z")  # +0900
    return f" {z[:3]}:{z[3:5]}" if z else ""


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) > MAX_TEXT:
        return text[:MAX_TEXT] + ELLIPSIS, True
    return text, False


def format_cell(value: object, db_type_name: str, full: bool = False) -> tuple[str | None, bool]:
    """表示用の文字列と、切り詰めたかどうか。full=True なら切り詰めない(CSV。P003 §3.11)。"""
    if value is None:
        return None, False
    if isinstance(value, bool):
        return str(value), False
    if isinstance(value, Decimal):
        if value.is_zero():
            return "0", False
        return format(value, "f"), False
    if isinstance(value, float):
        return repr(value), False
    if isinstance(value, int):
        return str(value), False
    if isinstance(value, dt.datetime):
        fmt = "%Y-%m-%d %H:%M:%S.%f" if db_type_name in _TIMESTAMP_TYPES else "%Y-%m-%d %H:%M:%S"
        return value.strftime(fmt) + _tz_suffix(value), False
    if isinstance(value, dt.date):
        return value.strftime("%Y-%m-%d"), False
    if isinstance(value, dt.timedelta):
        return str(value), False
    if isinstance(value, str):
        return (value, False) if full else _truncate(value)
    if isinstance(value, (bytes, bytearray)):
        if full:
            return "0x" + bytes(value).hex().upper(), False
        head = "0x" + bytes(value[:MAX_BYTES]).hex().upper()
        if len(value) > MAX_BYTES:
            return head + ELLIPSIS, True
        return head, False
    return (str(value), False) if full else _truncate(str(value))


def format_row(row: Sequence[object], type_names: Sequence[str]) -> tuple[list[str | None], list[int]]:
    cells: list[str | None] = []
    truncated: list[int] = []
    for i, (value, type_name) in enumerate(zip(row, type_names, strict=True)):
        text, cut = format_cell(value, type_name)
        cells.append(text)
        if cut:
            truncated.append(i)
    return cells, truncated
