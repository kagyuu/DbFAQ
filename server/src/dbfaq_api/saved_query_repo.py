"""保存済み Query の保存・読み出しと、PDB のひな型の登録(docs/P003-backend-spec.md §4.6・§4.7、ADR-016)。※CR-005により追加

保存先は scope と owner・table_name の文字列で持ち、スナップショットのテーブルとは結ばない。
そのためスナップショットを置き換えてテーブルが無くなっても行は残り、同じ名前のテーブルが戻れば同じ行が一覧に出る。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from .pdb_templates import PdbTemplate

TEMPLATE_NAME_SUFFIX = " (ひな型)"

_COLUMNS = "id, scope, owner, table_name, name, description, sql, template_key, created_at, updated_at"


class NameConflict(Exception):
    """同じ保存先に同じ名前の保存済み Query がある。"""


def _key(scope: str, owner: str | None, table: str | None) -> tuple[str, str]:
    # PDB の保存先は空文字列で持つ(NULL だと UNIQUE が効かないため。P002 §4.2)
    return ("", "") if scope == "pdb" else (owner or "", table or "")


def _item(row: Any) -> dict[str, Any]:
    pdb = row.scope == "pdb"
    return {
        "id": row.id,
        "scope": row.scope,
        "owner": None if pdb else row.owner,
        "table": None if pdb else row.table_name,
        "name": row.name,
        "description": row.description,
        "sql": row.sql,
        "is_template": row.template_key is not None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _is_name_conflict(e: IntegrityError) -> bool:
    return "UNIQUE" in str(e.orig) and "saved_queries.name" in str(e.orig)


class SavedQueryRepository:
    def __init__(self, engine: Engine, now: Callable[[], str]):
        self.engine = engine
        self.now = now

    def list(self, scope: str, owner: str | None = None, table: str | None = None) -> list[dict[str, Any]]:
        o, t = _key(scope, owner, table)
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    f"SELECT {_COLUMNS} FROM saved_queries "
                    "WHERE scope = :scope AND owner = :owner AND table_name = :table ORDER BY name, id"
                ),
                {"scope": scope, "owner": o, "table": t},
            ).all()
        return [_item(r) for r in rows]

    def get(self, query_id: int) -> dict[str, Any] | None:
        with self.engine.connect() as conn:
            row = conn.execute(text(f"SELECT {_COLUMNS} FROM saved_queries WHERE id = :id"), {"id": query_id}).first()
        return _item(row) if row else None

    def _insert(self, conn: Connection, scope: str, owner: str, table: str, name: str, description: str, sql: str,
                template_key: str | None) -> Any:
        ts = self.now()
        return conn.execute(
            text(
                "INSERT INTO saved_queries "
                "(scope, owner, table_name, name, description, sql, template_key, created_at, updated_at) "
                "VALUES (:scope, :owner, :table, :name, :description, :sql, :template_key, :ts, :ts) "
                f"RETURNING {_COLUMNS}"
            ),
            {"scope": scope, "owner": owner, "table": table, "name": name, "description": description, "sql": sql,
             "template_key": template_key, "ts": ts},
        ).one()

    def create(self, scope: str, owner: str | None, table: str | None, name: str, description: str, sql: str,
               template_key: str | None = None) -> dict[str, Any]:
        o, t = _key(scope, owner, table)
        try:
            with self.engine.begin() as conn:
                row = self._insert(conn, scope, o, t, name, description, sql, template_key)
        except IntegrityError as e:
            if _is_name_conflict(e):
                raise NameConflict(name) from e
            raise
        return _item(row)

    def update(self, query_id: int, name: str, description: str, sql: str) -> dict[str, Any] | None:
        try:
            with self.engine.begin() as conn:
                row = conn.execute(
                    text(
                        "UPDATE saved_queries SET name = :name, description = :description, sql = :sql, "
                        f"updated_at = :ts WHERE id = :id RETURNING {_COLUMNS}"
                    ),
                    {"id": query_id, "name": name, "description": description, "sql": sql, "ts": self.now()},
                ).first()
        except IntegrityError as e:
            if _is_name_conflict(e):
                raise NameConflict(name) from e
            raise
        return _item(row) if row else None

    def delete(self, query_id: int) -> bool:
        with self.engine.begin() as conn:
            return conn.execute(text("DELETE FROM saved_queries WHERE id = :id"), {"id": query_id}).rowcount > 0

    def seed_templates(self, templates: Iterable[PdbTemplate]) -> list[str]:
        """登録記録の無いひな型だけを PDB の保存済み Query として登録し、登録したキーを返す(P003 §4.7)。"""
        seeded: list[str] = []
        with self.engine.begin() as conn:
            done = {r[0] for r in conn.execute(text("SELECT template_key FROM query_template_seeds"))}
            names = {r[0] for r in conn.execute(text("SELECT name FROM saved_queries WHERE scope = 'pdb'"))}
            for t in templates:
                if t.key in done:
                    continue
                name = t.name if t.name not in names else t.name + TEMPLATE_NAME_SUFFIX
                self._insert(conn, "pdb", "", "", name, t.description, t.sql, t.key)
                conn.execute(
                    text("INSERT INTO query_template_seeds (template_key, seeded_at) VALUES (:k, :ts)"),
                    {"k": t.key, "ts": self.now()},
                )
                names.add(name)
                seeded.append(t.key)
        return seeded
