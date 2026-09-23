import pytest

from dbfaq_api.db import create_sqlite_engine
from dbfaq_api.migrate import apply_all
from dbfaq_api.snapshot_repo import SnapshotRepository

from .fixtures import hr_snapshot


@pytest.fixture
def repo(tmp_path):
    engine = create_sqlite_engine(str(tmp_path / "t.sqlite3"))
    apply_all(engine, lambda: "2026-09-23T00:00:00Z")
    return SnapshotRepository(engine)


def test_not_loaded(repo):
    assert repo.get_er_view("HR") == {"loaded": False, "snapshot": None, "tables": [], "relations": []}
    assert repo.table_exists("HR", "EMPLOYEES") is None
    assert repo.get_table_detail("HR", "EMPLOYEES") is None


def test_replace_and_er_view(repo):
    summary = repo.replace(hr_snapshot())
    assert summary == {"owner": "HR", "fetched_at": "2026-09-23T01:15:02Z", "oracle_version": "23.26.3.0.0",
                       "table_count": 4, "relation_count": 4}
    view = repo.get_er_view("HR")
    assert view["loaded"] is True
    assert view["snapshot"] == summary
    assert [t["name"] for t in view["tables"]] == ["COUNTRIES", "EMPLOYEES", "JOB_HISTORY", "REGIONS"]
    emp = view["tables"][1]
    assert [c["name"] for c in emp["columns"]] == ["EMPLOYEE_ID", "LAST_NAME", "EMAIL", "MANAGER_ID", "DEPT_CODE", "SALARY"]
    by = {c["name"]: c for c in emp["columns"]}
    assert by["EMPLOYEE_ID"]["is_pk"] and not by["EMPLOYEE_ID"]["is_fk"]
    assert by["MANAGER_ID"]["is_fk"] and by["DEPT_CODE"]["is_fk"]
    assert by["EMPLOYEE_ID"]["nullable"] is False
    rel = {r["name"]: r for r in view["relations"]}
    assert list(rel) == sorted(rel)
    assert rel["EMP_MANAGER_FK"] == {"name": "EMP_MANAGER_FK", "from_owner": "HR", "from_table": "EMPLOYEES",
                                     "from_columns": ["MANAGER_ID"], "to_owner": "HR", "to_table": "EMPLOYEES",
                                     "to_columns": ["EMPLOYEE_ID"]}
    assert rel["EMP_EXT_FK"]["to_owner"] == "OTHER"


def test_table_detail(repo):
    repo.replace(hr_snapshot())
    d = repo.get_table_detail("HR", "EMPLOYEES")
    assert d["table"] == {"owner": "HR", "name": "EMPLOYEES", "comment": "employees table", "num_rows": 107,
                          "last_analyzed": "2026-09-22T08:12:32Z", "iot": False}
    assert d["primary_key"] == {"name": "EMP_EMP_ID_PK", "columns": ["EMPLOYEE_ID"]}
    assert d["unique_keys"] == [{"name": "EMP_EMAIL_UK", "columns": ["EMAIL"]}]
    fks = {f["name"]: f for f in d["foreign_keys"]}
    assert fks["EMP_MANAGER_FK"]["ref_in_snapshot"] is True
    assert fks["EMP_EXT_FK"]["ref_in_snapshot"] is False and fks["EMP_EXT_FK"]["delete_rule"] == "CASCADE"
    refs = {r["name"]: r for r in d["referenced_by"]}
    assert set(refs) == {"EMP_MANAGER_FK", "JHIST_EMP_FK"}
    assert refs["JHIST_EMP_FK"] == {"name": "JHIST_EMP_FK", "from_owner": "HR", "from_table": "JOB_HISTORY",
                                    "from_columns": ["EMPLOYEE_ID"], "columns": ["EMPLOYEE_ID"]}
    cols = {c["name"]: c for c in d["columns"]}
    assert cols["EMPLOYEE_ID"]["pk_position"] == 1 and cols["SALARY"]["pk_position"] is None
    assert cols["SALARY"]["data_default"] == "0"
    idx = {i["name"]: i for i in d["indexes"]}
    assert idx["EMP_SAL_IX"]["columns"] == [{"name": "SALARY", "descending": True}]
    assert idx["EMP_UPPER_IX"]["columns"][0]["name"] == 'UPPER("LAST_NAME")'
    jh = repo.get_table_detail("HR", "JOB_HISTORY")
    assert {c["name"]: c["pk_position"] for c in jh["columns"]} == {"EMPLOYEE_ID": 1, "START_DATE": 2}
    assert repo.get_table_detail("HR", "COUNTRIES")["table"]["iot"] is True
    assert repo.get_table_detail("HR", "REGIONS")["referenced_by"][0]["name"] == "COUNTR_REG_FK"


def test_replace_twice_keeps_latest(repo):
    repo.replace(hr_snapshot("2026-09-23T01:00:00Z"))
    repo.replace(hr_snapshot("2026-09-23T02:00:00Z"))
    with repo.engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM snapshots").scalar() == 1
        assert conn.exec_driver_sql("SELECT COUNT(*) FROM db_tables").scalar() == 4
    assert repo.get_summary("HR")["fetched_at"] == "2026-09-23T02:00:00Z"


def test_other_owner_untouched(repo):
    repo.replace(hr_snapshot(owner="OTHER"))
    repo.replace(hr_snapshot())
    assert repo.get_summary("OTHER") is not None
    assert repo.get_summary("HR") is not None


def test_table_exists(repo):
    repo.replace(hr_snapshot())
    assert repo.table_exists("HR", "EMPLOYEES") is True
    assert repo.table_exists("HR", "NOPE") is False
    assert repo.table_exists("SCOTT", "EMP") is False


def test_failed_replace_keeps_previous(repo):
    repo.replace(hr_snapshot("2026-09-23T01:00:00Z"))
    bad = hr_snapshot("2026-09-23T02:00:00Z")
    bad["tables"][2]["columns"][0]["name"] = None  # NOT NULL 違反
    with pytest.raises(Exception):
        repo.replace(bad)
    assert repo.get_summary("HR")["fetched_at"] == "2026-09-23T01:00:00Z"
    assert len(repo.get_er_view("HR")["tables"]) == 4
