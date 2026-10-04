"""HR の全テーブルの行数とチェックサムを JSON で出力する(P009 A01・A06。読み取り専用トランザクションで実行)。

LOB 列を持つ表は、SQL の ORA_HASH では LOB を連結できない(ORA-22835)ため、全行を取得して Python の
SHA-256 で計算する(P202 F009)。
"""

import hashlib
import json
import sys

import oracledb

from dbfaq_api.config import load_config


LOB_TYPES = {"BLOB", "CLOB", "NCLOB"}


def lob_table_checksum(cur, owner: str, table: str, columns: list[str]) -> dict:
    """全行を ROWID 順に取得し、値の repr を SHA-256 にかける(LOB は bytes/str で受け取る)。"""
    cols = ", ".join(f'"{c}"' for c in columns)
    cur.execute(f'SELECT {cols} FROM "{owner}"."{table}" ORDER BY ROWID')
    h = hashlib.sha256()
    count = 0
    for row in cur:
        h.update(repr(tuple(v.read() if hasattr(v, "read") else v for v in row)).encode("utf-8"))
        count += 1
    return {"count": count, "checksum": "sha256:" + h.hexdigest()}


def main() -> int:
    cfg = load_config().oracle
    owner = cfg.target_schema
    with oracledb.connect(user=cfg.user, password=cfg.password.get_secret_value(), dsn=cfg.dsn) as conn:
        cur = conn.cursor()
        cur.execute("SET TRANSACTION READ ONLY")
        try:
            cur.execute("SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = :o ORDER BY TABLE_NAME", o=owner)
            tables = [r[0] for r in cur.fetchall()]
            result = {}
            for t in tables:
                cur.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS WHERE OWNER = :o AND TABLE_NAME = :t"
                    " ORDER BY COLUMN_ID",
                    o=owner, t=t,
                )
                columns = cur.fetchall()
                if any(dtype in LOB_TYPES for _, dtype in columns):
                    result[t] = lob_table_checksum(cur, owner, t, [c for c, _ in columns])
                    continue
                cols = " || '|' || ".join(f'"{c}"' for c, _ in columns)
                cur.execute(f'SELECT COUNT(*), SUM(ORA_HASH({cols})) FROM "{owner}"."{t}"')
                count, total = cur.fetchone()
                result[t] = {"count": int(count), "checksum": str(total)}
        finally:
            conn.rollback()
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
