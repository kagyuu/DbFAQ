"""ALL_TAB_COLUMNS の値からデータ型の表記を作る(docs/P003-backend-spec.md §3.4)。"""

from __future__ import annotations


def format_data_type(
    data_type: str,
    data_length: int | None,
    data_precision: int | None,
    data_scale: int | None,
    char_length: int | None,
    char_used: str | None,
) -> str:
    if data_type in ("VARCHAR2", "CHAR"):
        suffix = " CHAR" if char_used == "C" else ""
        return f"{data_type}({char_length}{suffix})"
    if data_type in ("NVARCHAR2", "NCHAR"):
        return f"{data_type}({char_length})"
    if data_type == "NUMBER":
        if data_precision is None and data_scale is None:
            return "NUMBER"
        if data_precision is None:
            return f"NUMBER(*,{data_scale})"
        if not data_scale:
            return f"NUMBER({data_precision})"
        return f"NUMBER({data_precision},{data_scale})"
    if data_type == "FLOAT":
        return "FLOAT" if data_precision is None else f"FLOAT({data_precision})"
    if data_type == "RAW":
        return f"RAW({data_length})"
    return data_type
