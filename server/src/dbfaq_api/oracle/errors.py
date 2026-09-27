"""Oracle アクセスのエラー(docs/P003-backend-spec.md §3.2)。"""

from __future__ import annotations

import oracledb

from ..log import mask_secret

INVALID_ARGUMENT = "INVALID_ARGUMENT"
NOT_FOUND = "NOT_FOUND"
ORACLE_TIMEOUT = "ORACLE_TIMEOUT"
ORACLE_ERROR = "ORACLE_ERROR"

_TIMEOUT_CODES = {"DPY-4024", "ORA-01013", "ORA-03156"}


class OracleFailure(Exception):
    def __init__(self, code: str, message: str, ora_code: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.ora_code = ora_code


def from_oracle_error(exc: oracledb.Error, secret: str | None) -> OracleFailure:
    err = exc.args[0] if exc.args else exc
    full_code = getattr(err, "full_code", None)
    raw = str(getattr(err, "message", None) or err)
    message = mask_secret(raw.splitlines()[0] if raw else "", secret)
    # DPY-4011 はタイムアウト後の回復に失敗したときにも出る(P003 §3.1 の実機確認)
    if full_code in _TIMEOUT_CODES or (full_code == "DPY-4011" and "timed out" in raw):
        return OracleFailure(ORACLE_TIMEOUT, message or "Oracle の応答がタイムアウトしました", full_code)
    return OracleFailure(ORACLE_ERROR, message, full_code)


def from_os_error(exc: OSError, secret: str | None) -> OracleFailure:
    """python-oracledb が oracledb.Error に包まずに送出する接続の失敗(socket.gaierror など。P202 F007)。"""
    if isinstance(exc, TimeoutError):
        return OracleFailure(ORACLE_TIMEOUT, "Oracle の応答がタイムアウトしました")
    return OracleFailure(ORACLE_ERROR, mask_secret(f"Oracle に接続できません: {exc}", secret))
