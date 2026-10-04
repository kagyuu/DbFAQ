import datetime as dt
from decimal import Decimal

from dbfaq_api.oracle.values import format_cell, format_row


def test_none():
    assert format_cell(None, "DB_TYPE_VARCHAR") == (None, False)


def test_decimal():
    assert format_cell(Decimal(24000), "DB_TYPE_NUMBER") == ("24000", False)
    assert format_cell(Decimal("0.15"), "DB_TYPE_NUMBER") == ("0.15", False)
    assert format_cell(Decimal("1E+3"), "DB_TYPE_NUMBER") == ("1000", False)
    assert format_cell(Decimal("-0"), "DB_TYPE_NUMBER") == ("0", False)


def test_float():
    assert format_cell(1.5, "DB_TYPE_BINARY_DOUBLE") == ("1.5", False)


def test_date_and_timestamp():
    v = dt.datetime(2013, 6, 17, 1, 2, 3, 456789)
    assert format_cell(v, "DB_TYPE_DATE") == ("2013-06-17 01:02:03", False)
    assert format_cell(v, "DB_TYPE_TIMESTAMP") == ("2013-06-17 01:02:03.456789", False)


def test_timestamp_tz():
    v = dt.datetime(2026, 1, 2, 3, 4, 5, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    assert format_cell(v, "DB_TYPE_TIMESTAMP_TZ") == ("2026-01-02 03:04:05.000000 +09:00", False)


def test_timedelta():
    assert format_cell(dt.timedelta(days=3, hours=4), "DB_TYPE_INTERVAL_DS") == ("3 days, 4:00:00", False)


def test_text_truncation():
    assert format_cell("a" * 1000, "DB_TYPE_VARCHAR") == ("a" * 1000, False)
    text, cut = format_cell("a" * 1001, "DB_TYPE_CLOB")
    assert cut is True
    assert text == "a" * 1000 + "…"


def test_bytes():
    assert format_cell(b"\x01" * 32, "DB_TYPE_RAW") == ("0x" + "01" * 32, False)
    text, cut = format_cell(b"\xab" * 33, "DB_TYPE_BLOB")
    assert cut is True
    assert text == "0x" + "AB" * 32 + "…"


def test_format_row():
    cells, truncated = format_row(["x" * 1001, None, Decimal(1)], ["DB_TYPE_CLOB", "DB_TYPE_VARCHAR", "DB_TYPE_NUMBER"])
    assert cells[1] is None and cells[2] == "1"
    assert truncated == [0]


def test_full_does_not_truncate():
    from dbfaq_api.oracle.values import format_cell

    assert format_cell("x" * 1500, "DB_TYPE_CLOB", full=True) == ("x" * 1500, False)
    assert format_cell(b"\xab" * 40, "DB_TYPE_RAW", full=True) == ("0x" + "AB" * 40, False)
    assert format_cell("x" * 1500, "DB_TYPE_CLOB")[1] is True  # 既定は従来どおり切り詰める
