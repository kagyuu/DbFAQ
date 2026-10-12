"""LLM に渡すデータベースの情報の組み立て(docs/P003-backend-spec.md §4.8.2)。※CR-007により追加

依頼者が LLM から得た回答(必須: スキーマの構造・具体的な要求、補足: データの例・データベースの種類)に従う。
入力はスナップショット(SQLite)の辞書と、データの例(OracleAccess.get_table_rows の結果)。純粋関数にする。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

SAMPLE_VALUE_CHARS = 40
_BINARY_TYPES = {"BLOB", "RAW", "LONG_RAW", "LONG RAW", "BFILE"}

# SC-03 で LLM に渡す辞書ビューと主な列(固定の文)
DICTIONARY_VIEWS = """\
- DBA_DATA_FILES(TABLESPACE_NAME, FILE_NAME, BYTES, MAXBYTES, AUTOEXTENSIBLE, STATUS)
- DBA_FREE_SPACE(TABLESPACE_NAME, BYTES)
- DBA_TABLESPACES(TABLESPACE_NAME, STATUS, CONTENTS, BLOCK_SIZE)
- DBA_TEMP_FREE_SPACE(TABLESPACE_NAME, TABLESPACE_SIZE, ALLOCATED_SPACE, FREE_SPACE)
- DBA_SEGMENTS(OWNER, SEGMENT_NAME, PARTITION_NAME, SEGMENT_TYPE, TABLESPACE_NAME, BYTES, EXTENTS)
- DBA_TS_QUOTAS(USERNAME, TABLESPACE_NAME, BYTES, MAX_BYTES)
- DBA_USERS(USERNAME, ACCOUNT_STATUS, DEFAULT_TABLESPACE, TEMPORARY_TABLESPACE, CREATED, ORACLE_MAINTAINED)
- DBA_OBJECTS(OWNER, OBJECT_NAME, OBJECT_TYPE, STATUS, CREATED, LAST_DDL_TIME)
- DBA_INDEXES(OWNER, INDEX_NAME, TABLE_NAME, STATUS, UNIQUENESS)
- DBA_LOBS(OWNER, TABLE_NAME, COLUMN_NAME, SEGMENT_NAME, SECUREFILE)
- V$SESSION(SID, SERIAL#, USERNAME, STATUS, MACHINE, PROGRAM, SQL_ID, LOGON_TIME, BLOCKING_SESSION, EVENT)
- V$SESSION_LONGOPS(SID, OPNAME, TARGET, SOFAR, TOTALWORK, TIME_REMAINING)
- V$SQL(SQL_ID, SQL_TEXT, EXECUTIONS, ELAPSED_TIME, CPU_TIME, BUFFER_GETS)"""


@dataclass
class LlmContext:
    """LLM に渡す情報(Markdown)と、その要約(API の context)。"""

    text: str
    tables: list[str] = field(default_factory=list)
    sample_rows: int = 0
    truncated: bool = False

    def summary(self) -> dict[str, Any]:
        return {"tables": self.tables, "sample_rows": self.sample_rows, "truncated": self.truncated}


def _database(version: str | None, owner: str) -> str:
    return (
        f"Oracle Database {version or ''}".rstrip()
        + f". Target schema: {owner}. Unqualified table names refer to the target schema."
    )


def _rows_note(num_rows: Any) -> str:
    return f" (about {num_rows} rows)" if num_rows is not None else ""


def _comment(text: Any) -> str:
    return f" -- {' '.join(str(text).split())}" if text else ""


def render_detail(detail: dict[str, Any]) -> str:
    """GET /api/schema/tables/{owner}/{table} と同じ形の詳細から、テーブル 1 つ分の文を作る(列のコメント付き)。"""
    t = detail["table"]
    lines = [f"Table {t['owner']}.{t['name']}{_comment(t.get('comment'))}{_rows_note(t.get('num_rows'))}"]
    for c in detail["columns"]:
        null = "" if c["nullable"] else " NOT NULL"
        lines.append(f"  {c['name']} {c['data_type_display']}{null}{_comment(c.get('comment'))}")
    pk = detail.get("primary_key")
    if pk:
        lines.append(f"  PRIMARY KEY ({', '.join(pk['columns'])})")
    for fk in detail.get("foreign_keys", []):
        if fk.get("ref_table"):
            ref_cols = ", ".join(c or "?" for c in fk["ref_columns"])
            lines.append(
                f"  FOREIGN KEY ({', '.join(fk['columns'])}) REFERENCES {fk['ref_owner']}.{fk['ref_table']}({ref_cols})"
            )
    return "\n".join(lines)


def render_er_table(table: dict[str, Any], relations: Sequence[dict[str, Any]]) -> str:
    """GET /api/schema のテーブルと関連から、テーブル 1 つ分の文を作る(列のコメントは無い)。"""
    lines = [f"Table {table['owner']}.{table['name']}{_comment(table.get('comment'))}{_rows_note(table.get('num_rows'))}"]
    pk = []
    for c in table["columns"]:
        null = "" if c["nullable"] else " NOT NULL"
        lines.append(f"  {c['name']} {c['data_type_display']}{null}")
        if c.get("is_pk"):
            pk.append(c["name"])
    if pk:
        lines.append(f"  PRIMARY KEY ({', '.join(pk)})")
    for r in relations:
        if r["from_owner"] == table["owner"] and r["from_table"] == table["name"] and r.get("to_table"):
            ref_cols = ", ".join(c or "?" for c in r["to_columns"])
            lines.append(
                f"  FOREIGN KEY ({', '.join(r['from_columns'])}) REFERENCES {r['to_owner']}.{r['to_table']}({ref_cols})"
            )
    return "\n".join(lines)


def render_samples(owner: str, table: str, rows_result: dict[str, Any] | None, limit: int) -> tuple[str, int]:
    """データの例。値は 40 文字で切り、バイナリの列は省く。(文, 行数)。"""
    if not rows_result or limit <= 0:
        return "", 0
    columns = rows_result.get("columns") or []
    keep = [i for i, c in enumerate(columns) if str(c.get("data_type", "")).upper() not in _BINARY_TYPES]
    rows = (rows_result.get("rows") or [])[:limit]
    if not rows or not keep:
        return "", 0
    lines = [f"{owner}.{table}:"]
    for row in rows:
        cells = []
        for i in keep:
            v = row[i]
            if v is None:
                text = "NULL"
            else:
                text = " ".join(str(v).split())
                if len(text) > SAMPLE_VALUE_CHARS:
                    text = text[:SAMPLE_VALUE_CHARS] + "…"
            cells.append(f"{columns[i]['name']}={text}")
        lines.append("  " + ", ".join(cells))
    return "\n".join(lines), len(rows)


def _fit(blocks: list[tuple[str, str]], max_chars: int, keep_first: bool) -> tuple[list[str], list[str], bool]:
    """文字数の上限に収まるだけテーブルの文を選ぶ。keep_first なら先頭は必ず入れる。"""
    texts: list[str] = []
    names: list[str] = []
    used = 0
    truncated = False
    for i, (name, text) in enumerate(blocks):
        size = len(text) + 2
        if used + size > max_chars and not (keep_first and i == 0):
            truncated = True
            continue
        texts.append(text)
        names.append(name)
        used += size
    return texts, names, truncated


def build_table_context(
    main: dict[str, Any],
    related: Sequence[dict[str, Any]],
    version: str | None,
    samples: dict[str, Any] | None,
    sample_limit: int,
    max_chars: int,
) -> LlmContext:
    """SC-02: このテーブル(main)と、外部キーでつながるテーブル(related)の詳細から組み立てる。"""
    owner, name = main["table"]["owner"], main["table"]["name"]
    blocks = [(f"{owner}.{name}", render_detail(main))]
    seen = {blocks[0][0]}
    for d in related:
        key = f"{d['table']['owner']}.{d['table']['name']}"
        if key not in seen:
            seen.add(key)
            blocks.append((key, render_detail(d)))
    texts, names, truncated = _fit(blocks, max_chars, keep_first=True)
    sample_text, sample_count = render_samples(owner, name, samples, sample_limit)
    parts = ["# Database", _database(version, owner), "", "# Tables", "\n\n".join(texts)]
    if sample_text:
        parts += ["", "# Sample rows", sample_text]
    return LlmContext("\n".join(parts), names, sample_count, truncated)


def build_pdb_context(er_view: dict[str, Any], version: str | None, owner: str, max_chars: int) -> LlmContext:
    """SC-03: 対象スキーマの全テーブルと辞書ビューから組み立てる。データの例は渡さない。"""
    relations = er_view.get("relations", [])
    blocks = [
        (f"{t['owner']}.{t['name']}", render_er_table(t, relations))
        for t in sorted(er_view.get("tables", []), key=lambda t: t["name"])
    ]
    texts, names, truncated = _fit(blocks, max_chars, keep_first=False)
    parts = ["# Database", _database(version, owner), "", "# Tables", "\n\n".join(texts) or "(none)",
             "", "# Dictionary views", "You may also query these Oracle data dictionary views:", DICTIONARY_VIEWS]
    return LlmContext("\n".join(parts), names, 0, truncated)
