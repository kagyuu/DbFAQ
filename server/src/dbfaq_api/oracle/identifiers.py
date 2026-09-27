"""Oracle 識別子の検証とクォート(docs/P003-backend-spec.md §3.3)。"""

from __future__ import annotations

from .errors import INVALID_ARGUMENT, OracleFailure

MAX_IDENTIFIER_LENGTH = 128


def validate_identifier(name: object, field: str) -> str:
    if not isinstance(name, str):
        raise OracleFailure(INVALID_ARGUMENT, f"{field} が不正です: 文字列ではありません")
    if not 1 <= len(name) <= MAX_IDENTIFIER_LENGTH:
        raise OracleFailure(INVALID_ARGUMENT, f"{field} が不正です: 1〜{MAX_IDENTIFIER_LENGTH} 文字で指定してください")
    if "\x00" in name or '"' in name:
        raise OracleFailure(INVALID_ARGUMENT, f'{field} が不正です: NUL 文字と " は使えません')
    return name


def quote(name: str) -> str:
    """validate_identifier 済みの名前を二重引用符で囲む。"""
    return f'"{name}"'
