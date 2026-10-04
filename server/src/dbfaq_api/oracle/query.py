"""利用者の SELECT の実行と CSV(docs/P003-backend-spec.md §3.11、ADR-015)。"""

from __future__ import annotations

import csv
import io
import tempfile
import time
from collections.abc import Callable
from typing import IO, Any

import oracledb

from .db import Database
from .errors import from_oracle_error
from .sql_guard import check_select
from .values import format_cell, format_row

MAX_ROWS = 500
CSV_BATCH = 1000
CSV_SPOOL_BYTES = 8 * 1024 * 1024


def _columns(description: Any) -> tuple[list[dict[str, str]], list[str]]:
    type_names = [d.type_code.name for d in description]
    columns = [
        {"name": d.name, "data_type": name.removeprefix("DB_TYPE_")}
        for d, name in zip(description, type_names, strict=True)
    ]
    return columns, type_names


async def run_query(
    db: Database,
    sql: str,
    max_rows: int = MAX_ROWS,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """SELECT を実行し、先頭 max_rows 行と、それを超える行があったかを返す。SQL は包まない。"""
    to_run = check_select(sql)

    async def work(conn: Any) -> dict[str, Any]:
        cur = conn.cursor()
        try:
            cur.arraysize = max_rows + 1
            cur.prefetchrows = max_rows + 1
            t0 = clock()
            try:
                await cur.execute(to_run)
                fetched = await cur.fetchmany(max_rows + 1)
            except oracledb.Error as e:
                raise from_oracle_error(e, db.secret, to_run) from e
            elapsed_ms = int((clock() - t0) * 1000)
            columns, type_names = _columns(cur.description)
        finally:
            cur.close()
        rows: list[list[str | None]] = []
        truncated: list[list[int]] = []
        for row in fetched[:max_rows]:
            cells, cut = format_row(row, type_names)
            rows.append(cells)
            truncated.append(cut)
        return {
            "columns": columns,
            "rows": rows,
            "truncated": truncated,
            "row_count": len(rows),
            "has_more": len(fetched) > max_rows,
            "max_rows": max_rows,
            "elapsed_ms": elapsed_ms,
        }

    return await db.run_readonly(work)


async def export_csv(db: Database, sql: str) -> tuple[IO[bytes], int]:
    """SELECT の全行を CSV(UTF-8 BOM 付き、CRLF、見出し行あり、切り詰めなし)にして一時ファイルに書く。

    先頭に戻したファイルと行数を返す。失敗したらファイルを閉じて例外を送出する(応答を始める前)。
    """
    to_run = check_select(sql)
    # 呼び出し側(API の応答)が送り終えてから閉じるため、with を使わない
    spool = tempfile.SpooledTemporaryFile(max_size=CSV_SPOOL_BYTES)  # noqa: SIM115

    async def work(conn: Any) -> int:
        text = io.TextIOWrapper(spool, encoding="utf-8-sig", newline="")
        writer = csv.writer(text, lineterminator="\r\n")
        count = 0
        cur = conn.cursor()
        try:
            cur.arraysize = CSV_BATCH
            try:
                await cur.execute(to_run)
                columns, type_names = _columns(cur.description)
                writer.writerow([c["name"] for c in columns])
                while batch := await cur.fetchmany(CSV_BATCH):
                    for row in batch:
                        writer.writerow(
                            ["" if v is None else format_cell(v, t, full=True)[0] for v, t in zip(row, type_names)]
                        )
                    count += len(batch)
            except oracledb.Error as e:
                raise from_oracle_error(e, db.secret, to_run) from e
        finally:
            cur.close()
            text.flush()
            text.detach()  # spool を閉じずに TextIOWrapper だけを外す
        return count

    try:
        count = await db.run_readonly(work)
    except BaseException:
        spool.close()
        raise
    spool.seek(0)
    return spool, count
