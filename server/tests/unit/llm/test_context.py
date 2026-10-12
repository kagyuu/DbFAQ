"""LLM に渡す情報(docs/P003-backend-spec.md §4.8.2)。※CR-007により追加"""

import pytest

from dbfaq_api.db import create_sqlite_engine
from dbfaq_api.llm.context import build_pdb_context, build_table_context, render_samples
from dbfaq_api.migrate import apply_all
from dbfaq_api.snapshot_repo import SnapshotRepository
from tests.unit.api.fixtures import hr_snapshot


@pytest.fixture
def repo(tmp_path):
    engine = create_sqlite_engine(str(tmp_path / "t.sqlite3"))
    apply_all(engine, lambda: "2026-10-13T00:00:00Z")
    r = SnapshotRepository(engine)
    r.replace(hr_snapshot())
    return r


SAMPLES = {
    "columns": [{"name": "EMPLOYEE_ID", "data_type": "NUMBER"}, {"name": "LAST_NAME", "data_type": "VARCHAR"},
                {"name": "PHOTO", "data_type": "BLOB"}],
    "rows": [["100", "King", "0xFFD8"], ["101", "x" * 60, None], ["102", None, None], ["103", "a", None]],
}


def test_table_context_structure_and_samples(repo):
    main = repo.get_table_detail("HR", "EMPLOYEES")
    related = [repo.get_table_detail("HR", "JOB_HISTORY")]
    ctx = build_table_context(main, related, "23.26.3.0.0", SAMPLES, 3, 12000)
    text = ctx.text
    assert text.startswith("# Database\nOracle Database 23.26.3.0.0. Target schema: HR.")
    assert "Table HR.EMPLOYEES -- employees table (about 107 rows)" in text
    assert "  EMPLOYEE_ID NUMBER(6) NOT NULL -- Primary key" in text
    assert "  MANAGER_ID NUMBER(6)\n" in text  # NULL 可の列
    assert "  PRIMARY KEY (EMPLOYEE_ID)" in text
    assert "  FOREIGN KEY (MANAGER_ID) REFERENCES HR.EMPLOYEES(EMPLOYEE_ID)" in text
    assert "  FOREIGN KEY (DEPT_CODE) REFERENCES OTHER.DEPTS(CODE)" in text  # 別スキーマの参照も構造として渡す
    assert "  PRIMARY KEY (EMPLOYEE_ID, START_DATE)" in text  # JOB_HISTORY の複合主キー
    assert "# Sample rows\nHR.EMPLOYEES:\n  EMPLOYEE_ID=100, LAST_NAME=King\n" in text  # BLOB の列は省く
    assert f"LAST_NAME={'x' * 40}…" in text and "LAST_NAME=NULL" in text
    assert "EMPLOYEE_ID=103" not in text  # 3 行まで
    assert ctx.summary() == {"tables": ["HR.EMPLOYEES", "HR.JOB_HISTORY"], "sample_rows": 3, "truncated": False}


def test_table_context_without_samples_and_truncation(repo):
    main = repo.get_table_detail("HR", "EMPLOYEES")
    related = [repo.get_table_detail("HR", "JOB_HISTORY"), repo.get_table_detail("HR", "EMPLOYEES")]
    ctx = build_table_context(main, related, None, None, 3, 1000)
    assert "# Sample rows" not in ctx.text and ctx.sample_rows == 0
    assert ctx.tables[0] == "HR.EMPLOYEES" and len(ctx.tables) == len(set(ctx.tables))  # 重複なし
    tiny = build_table_context(main, related, None, SAMPLES, 0, 12000)
    assert tiny.sample_rows == 0  # sample_rows=0 なら送らない
    cut = build_table_context(main, related, None, None, 3, 1000 - 900)
    assert cut.tables == ["HR.EMPLOYEES"] and cut.truncated is True  # 先頭のテーブルは必ず残す


def test_render_samples_edge_cases():
    assert render_samples("HR", "T", None, 3) == ("", 0)
    assert render_samples("HR", "T", {"columns": [{"name": "B", "data_type": "BLOB"}], "rows": [["0x00"]]}, 3) == ("", 0)
    assert render_samples("HR", "T", {"columns": [{"name": "A", "data_type": "NUMBER"}], "rows": []}, 3) == ("", 0)


def test_pdb_context(repo):
    view = repo.get_er_view("HR")
    ctx = build_pdb_context(view, "23.26.3.0.0", "HR", 12000)
    assert ctx.tables == ["HR.COUNTRIES", "HR.EMPLOYEES", "HR.JOB_HISTORY", "HR.REGIONS"]
    assert "  FOREIGN KEY (REGION_ID) REFERENCES HR.REGIONS(REGION_ID)" in ctx.text
    assert "# Dictionary views" in ctx.text and "DBA_DATA_FILES(" in ctx.text and "V$SESSION(" in ctx.text
    assert ctx.sample_rows == 0 and "# Sample rows" not in ctx.text
    small = build_pdb_context(view, None, "HR", 1000 - 800)
    assert small.truncated is True and len(small.tables) < 4
