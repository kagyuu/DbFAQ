"""保存済み Query のリポジトリとひな型の登録(docs/P003-backend-spec.md §4.6・§4.7)。※CR-005により追加"""

import pytest

from dbfaq_api.db import create_sqlite_engine
from dbfaq_api.migrate import apply_all
from dbfaq_api.pdb_templates import PDB_TEMPLATES, PdbTemplate
from dbfaq_api.saved_query_repo import NameConflict, SavedQueryRepository
from dbfaq_api.snapshot_repo import SnapshotRepository

from .fixtures import hr_snapshot


class Clock:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return f"2026-10-07T12:00:{self.n:02d}Z"


def startup(path):
    """backend の起動処理(マイグレーション + ひな型の登録)と同じことをする。"""
    engine = create_sqlite_engine(str(path))
    apply_all(engine, lambda: "2026-10-07T00:00:00Z")
    repo = SavedQueryRepository(engine, Clock())
    return engine, repo, repo.seed_templates(PDB_TEMPLATES)


@pytest.fixture
def repo(tmp_path):
    return startup(tmp_path / "t.sqlite3")[1]


def test_create_and_list_by_target(repo):
    a = repo.create("table", "HR", "EMPLOYEES", "部署50", "部署 50 の社員", "SELECT 1 FROM DUAL")
    repo.create("table", "HR", "EMPLOYEES", "a-先頭", "", "SELECT 2 FROM DUAL")
    repo.create("table", "HR", "DEPARTMENTS", "部署50", "", "SELECT 3 FROM DUAL")
    repo.create("table", "HR", "employees", "部署50", "", "SELECT 4 FROM DUAL")  # 大文字小文字の違うテーブル名は別
    assert a == {
        "id": a["id"], "scope": "table", "owner": "HR", "table": "EMPLOYEES", "name": "部署50",
        "description": "部署 50 の社員", "sql": "SELECT 1 FROM DUAL", "is_template": False,
        "created_at": a["created_at"], "updated_at": a["created_at"],
    }
    assert [q["name"] for q in repo.list("table", "HR", "EMPLOYEES")] == ["a-先頭", "部署50"]
    assert [q["sql"] for q in repo.list("table", "HR", "DEPARTMENTS")] == ["SELECT 3 FROM DUAL"]
    assert [q["sql"] for q in repo.list("table", "HR", "employees")] == ["SELECT 4 FROM DUAL"]
    assert repo.list("table", "HR", "JOBS") == []


def test_pdb_scope_has_no_owner_table(repo):
    q = repo.create("pdb", None, None, "部署50", "", "SELECT 1 FROM DUAL")  # テーブルと同じ名前でも別の保存先
    assert q["owner"] is None and q["table"] is None
    assert q in repo.list("pdb")


def test_name_conflict_in_same_target(repo):
    repo.create("table", "HR", "EMPLOYEES", "部署50", "", "SELECT 1 FROM DUAL")
    with pytest.raises(NameConflict):
        repo.create("table", "HR", "EMPLOYEES", "部署50", "", "SELECT 2 FROM DUAL")
    with pytest.raises(NameConflict):
        repo.create("pdb", None, None, PDB_TEMPLATES[0].name, "", "SELECT 2 FROM DUAL")


def test_update_and_delete(repo):
    a = repo.create("table", "HR", "EMPLOYEES", "a", "", "SELECT 1 FROM DUAL")
    b = repo.create("table", "HR", "EMPLOYEES", "b", "", "SELECT 2 FROM DUAL")
    u = repo.update(a["id"], "a2", "説明", "SELECT 9 FROM DUAL")
    assert (u["name"], u["description"], u["sql"], u["created_at"]) == ("a2", "説明", "SELECT 9 FROM DUAL", a["created_at"])
    assert u["updated_at"] > a["updated_at"]
    with pytest.raises(NameConflict):
        repo.update(a["id"], "b", "", "x")
    assert repo.update(9999, "x", "", "x") is None
    assert repo.delete(b["id"]) is True
    assert repo.delete(b["id"]) is False
    assert repo.get(b["id"]) is None
    assert [q["name"] for q in repo.list("table", "HR", "EMPLOYEES")] == ["a2"]


def test_saved_queries_survive_snapshot_replacement(tmp_path):
    """テーブルが無くなっても残り、同じ名前のテーブルが戻れば同じ行が一覧に出る(CR-005)。"""
    engine, repo, _ = startup(tmp_path / "t.sqlite3")
    snaps = SnapshotRepository(engine)
    snaps.replace(hr_snapshot())
    saved = repo.create("table", "HR", "EMPLOYEES", "部署50", "", "SELECT 1 FROM DUAL")
    without = hr_snapshot(fetched_at="2026-10-07T01:00:00Z")
    without["tables"] = [t for t in without["tables"] if t["name"] != "EMPLOYEES"]
    snaps.replace(without)
    assert snaps.table_exists("HR", "EMPLOYEES") is False
    assert repo.list("table", "HR", "EMPLOYEES") == [saved]
    snaps.replace(hr_snapshot(fetched_at="2026-10-07T02:00:00Z"))
    assert snaps.table_exists("HR", "EMPLOYEES") is True
    assert repo.list("table", "HR", "EMPLOYEES") == [saved]


def test_templates_seeded_once(tmp_path):
    path = tmp_path / "t.sqlite3"
    _, repo, seeded = startup(path)
    assert seeded == [t.key for t in PDB_TEMPLATES]
    items = repo.list("pdb")
    assert [q["name"] for q in items] == sorted(t.name for t in PDB_TEMPLATES)
    assert all(q["is_template"] for q in items)
    # 削除・改名したひな型は次の起動で戻さない
    repo.delete(items[0]["id"])
    repo.update(items[1]["id"], "改名したひな型", "", items[1]["sql"])
    _, repo2, seeded2 = startup(path)
    assert seeded2 == []
    names = [q["name"] for q in repo2.list("pdb")]
    assert len(names) == len(PDB_TEMPLATES) - 1
    assert items[0]["name"] not in names and "改名したひな型" in names


def test_new_template_key_is_added_and_name_clash_gets_suffix(repo):
    repo.create("pdb", None, None, "99. 新しいひな型", "", "SELECT 1 FROM DUAL")  # 利用者が先に同じ名前で保存していた
    new = PdbTemplate("pdb.new", "99. 新しいひな型", "説明", "SELECT 2 FROM DUAL")
    assert repo.seed_templates([*PDB_TEMPLATES, new]) == ["pdb.new"]
    by_name = {q["name"]: q for q in repo.list("pdb")}
    assert by_name["99. 新しいひな型"]["is_template"] is False
    assert by_name["99. 新しいひな型 (ひな型)"]["sql"] == "SELECT 2 FROM DUAL"
    assert repo.seed_templates([*PDB_TEMPLATES, new]) == []
