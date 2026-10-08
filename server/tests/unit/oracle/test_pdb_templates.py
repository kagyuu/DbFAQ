"""PDB の Query のひな型(docs/P003-backend-spec.md §4.7)。※CR-005により追加"""

import pytest

from dbfaq_api.oracle.sql_guard import check_select
from dbfaq_api.pdb_templates import NEEDS_DBA, PDB_TEMPLATES


@pytest.mark.parametrize("t", PDB_TEMPLATES, ids=lambda t: t.key)
def test_template_passes_sql_guard(t):
    assert check_select(t.sql) == t.sql  # 末尾のセミコロンも無い


def test_keys_and_names_are_unique_and_numbered():
    assert len({t.key for t in PDB_TEMPLATES}) == len(PDB_TEMPLATES) == 17
    assert len({t.name for t in PDB_TEMPLATES}) == len(PDB_TEMPLATES)
    assert [t.name[:3] for t in PDB_TEMPLATES] == [f"{i:02d}." for i in range(1, 18)]
    assert all(t.key.startswith("pdb.") for t in PDB_TEMPLATES)


def test_required_templates_exist():
    names = [t.name for t in PDB_TEMPLATES]
    assert "01. USERS 表領域の大きさ" in names
    assert "03. LOB 領域の大きさと実データの合計(テーブル.カラムごと)" in names


@pytest.mark.parametrize("t", PDB_TEMPLATES, ids=lambda t: t.key)
def test_privilege_note_matches_views(t):
    needs = any(v in t.sql.lower() for v in ("dba_", "v$"))
    assert (NEEDS_DBA in t.description) == needs
