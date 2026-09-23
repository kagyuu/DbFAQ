"""HR の全テーブルの行数とチェックサムを JSON で出力する(P009 A01・A06。読み取り専用トランザクションで実行)。"""

import json
import sys

import oracledb

from dbfaq_common.config import load_config


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
                    "SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE OWNER = :o AND TABLE_NAME = :t ORDER BY COLUMN_ID",
                    o=owner, t=t,
                )
                cols = " || '|' || ".join(f'"{c[0]}"' for c in cur.fetchall())
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
