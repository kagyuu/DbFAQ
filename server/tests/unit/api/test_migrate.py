import importlib.resources
import shutil
import sqlite3

import pytest

from dbfaq_api.db import create_sqlite_engine
from dbfaq_api.migrate import MIGRATIONS_DIR, MigrationError, apply_all

TABLES = {"snapshots", "db_tables", "db_columns", "db_constraints", "db_constraint_columns", "db_indexes",
          "db_index_columns", "schema_migrations"}


def now():
    return "2026-09-23T00:00:00Z"


def tables(path):
    with sqlite3.connect(path) as c:
        return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")} - {"sqlite_sequence"}


def test_first_apply(tmp_path):
    db = tmp_path / "t.sqlite3"
    assert apply_all(create_sqlite_engine(str(db)), now) == ["0001_init"]
    assert tables(db) == TABLES


def test_second_and_third_apply_are_noops(tmp_path):
    db = str(tmp_path / "t.sqlite3")
    apply_all(create_sqlite_engine(db), now)
    assert apply_all(create_sqlite_engine(db), now) == []
    assert apply_all(create_sqlite_engine(db), now) == []  # 再起動相当


def test_additional_migration_applied_once(tmp_path):
    mdir = tmp_path / "m"
    mdir.mkdir()
    shutil.copy(MIGRATIONS_DIR / "0001_init.sql", mdir)
    (mdir / "0002_add.sql").write_text("ALTER TABLE snapshots ADD COLUMN note TEXT;\n", encoding="utf-8")
    db = str(tmp_path / "t.sqlite3")
    assert apply_all(create_sqlite_engine(db), now, mdir) == ["0001_init", "0002_add"]
    assert apply_all(create_sqlite_engine(db), now, mdir) == []


def test_bad_migration_rolls_back(tmp_path):
    mdir = tmp_path / "m"
    mdir.mkdir()
    shutil.copy(MIGRATIONS_DIR / "0001_init.sql", mdir)
    (mdir / "0002_bad.sql").write_text("CREATE TABLE t1(x);\nTHIS IS NOT SQL;\n", encoding="utf-8")
    db = str(tmp_path / "t.sqlite3")
    with pytest.raises(MigrationError) as ei:
        apply_all(create_sqlite_engine(db), now, mdir)
    assert ei.value.version == "0002_bad"
    assert "t1" not in tables(db)
    with sqlite3.connect(db) as c:
        assert [r[0] for r in c.execute("SELECT version FROM schema_migrations")] == ["0001_init"]


def test_foreign_keys_pragma(tmp_path):
    engine = create_sqlite_engine(str(tmp_path / "t.sqlite3"))
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_sql_is_packaged():
    assert (importlib.resources.files("dbfaq_api") / "migrations" / "0001_init.sql").is_file()
