"""開発用 Oracle への疎通確認。対象スキーマのテーブル数を表示する(U001-T4)。"""

import sys

import oracledb

from dbfaq_api.config import load_config


def main() -> int:
    cfg = load_config().oracle
    try:
        with oracledb.connect(user=cfg.user, password=cfg.password.get_secret_value(), dsn=cfg.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = :o", o=cfg.target_schema)
                print(cur.fetchone()[0])
    except oracledb.Error as e:
        err = e.args[0]
        print(f"{getattr(err, 'full_code', '')} {getattr(err, 'message', e)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
