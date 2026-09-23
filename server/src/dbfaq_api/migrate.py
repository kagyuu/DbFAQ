"""管理テーブル付きの差分マイグレーション(docs/P003-backend-spec.md §5.2、ADR-002)。

SQL ファイルは「;」で文に分割して 1 文ずつ実行する単純な方式。トリガーなど
文の中に「;」を含む DDL は使わない前提。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy import Engine

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


class MigrationError(Exception):
    def __init__(self, version: str, cause: Exception):
        super().__init__(f"マイグレーション {version} の適用に失敗しました: {cause}")
        self.version = version


def _statements(sql: str) -> list[str]:
    lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def apply_all(engine: Engine, now: Callable[[], str], migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    applied_now: list[str] = []
    raw = engine.raw_connection()
    dbapi = raw.driver_connection
    saved_isolation = dbapi.isolation_level
    try:
        dbapi.isolation_level = None  # BEGIN/COMMIT を自分で発行する(終わったら元に戻す。接続はプールに返るため)
        cur = dbapi.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        done = {row[0] for row in cur.execute("SELECT version FROM schema_migrations")}
        for path in sorted(migrations_dir.glob("*.sql")):
            version = path.stem
            if version in done:
                continue
            try:
                cur.execute("BEGIN")
                for stmt in _statements(path.read_text(encoding="utf-8")):
                    cur.execute(stmt)
                cur.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)", (version, now()))
                cur.execute("COMMIT")
            except Exception as e:
                cur.execute("ROLLBACK")
                raise MigrationError(version, e) from e
            applied_now.append(version)
        cur.close()
    finally:
        dbapi.isolation_level = saved_isolation
        raw.close()
    return applied_now
