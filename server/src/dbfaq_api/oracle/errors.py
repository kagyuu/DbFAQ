"""Oracle アクセスのエラー(docs/P003-backend-spec.md §3.2)。"""

from __future__ import annotations

import oracledb

from ..log import mask_secret

INVALID_ARGUMENT = "INVALID_ARGUMENT"
NOT_FOUND = "NOT_FOUND"
ORACLE_TIMEOUT = "ORACLE_TIMEOUT"
ORACLE_ERROR = "ORACLE_ERROR"
SQL_REJECTED = "SQL_REJECTED"

_TIMEOUT_CODES = {"DPY-4024", "ORA-01013", "ORA-03156"}


class OracleFailure(Exception):
    def __init__(self, code: str, message: str, ora_code: str | None = None, position: dict[str, int] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.ora_code = ora_code
        self.position = position


def error_position(sql: str, byte_offset: object) -> dict[str, int] | None:
    """Oracle のエラー位置(実行した SQL の UTF-8 のバイト位置)を、文字位置・行・列に変換する(P003 §3.11)。

    位置 0(位置を持たないエラーと区別できない)、文字の途中、SQL の長さ超過は None。
    """
    if not isinstance(byte_offset, int) or byte_offset <= 0:
        return None
    encoded = sql.encode("utf-8")
    if byte_offset > len(encoded):
        return None
    try:
        offset = len(encoded[:byte_offset].decode("utf-8"))
    except UnicodeDecodeError:
        return None
    line_start = sql.rfind("\n", 0, offset) + 1
    return {"offset": offset, "line": sql.count("\n", 0, offset) + 1, "column": offset - line_start + 1}


def from_oracle_error(exc: oracledb.Error, secret: str | None, sql: str | None = None) -> OracleFailure:
    """sql を渡すと(利用者の SQL の実行・取得のエラー)、Oracle が返したエラー位置を position に付ける。"""
    err = exc.args[0] if exc.args else exc
    full_code = getattr(err, "full_code", None)
    raw = str(getattr(err, "message", None) or err)
    message = mask_secret(raw.splitlines()[0] if raw else "", secret)
    # DPY-4011 はタイムアウト後の回復に失敗したときにも出る(P003 §3.1 の実機確認)
    if full_code in _TIMEOUT_CODES or (full_code == "DPY-4011" and "timed out" in raw):
        return OracleFailure(ORACLE_TIMEOUT, message or "Oracle の応答がタイムアウトしました", full_code)
    position = error_position(sql, getattr(err, "offset", None)) if sql is not None else None
    return OracleFailure(ORACLE_ERROR, message, full_code, position)


def from_os_error(exc: OSError, secret: str | None) -> OracleFailure:
    """python-oracledb が oracledb.Error に包まずに送出する接続の失敗(socket.gaierror など。P202 F007)。"""
    if isinstance(exc, TimeoutError):
        return OracleFailure(ORACLE_TIMEOUT, "Oracle の応答がタイムアウトしました")
    return OracleFailure(ORACLE_ERROR, mask_secret(f"Oracle に接続できません: {exc}", secret))
