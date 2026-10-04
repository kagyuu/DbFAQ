"""T01: OracleClient.get_schema_snapshot が HR を正しく読み取る(docs/P008-test-direction/T01-oracle-snapshot-hr.md)。"""

import pytest

from dbfaq_api.oracle.errors import NOT_FOUND, OracleFailure

# P202 F010(CR-004): HR に EMPLOYEE_FIGURE が加わり 8 表を新しいベースラインにした(人間の指示 2026-10-04)
HR_TABLES = ["COUNTRIES", "DEPARTMENTS", "EMPLOYEES", "EMPLOYEE_FIGURE", "JOBS", "JOB_HISTORY", "LOCATIONS", "REGIONS"]


async def test_hr_snapshot(oracle_client):
    s = await oracle_client.get_schema_snapshot(None)
    assert s["owner"] == "HR"
    assert [t["name"] for t in s["tables"]] == HR_TABLES
    assert sum(len(t["columns"]) for t in s["tables"]) == 38
    kinds = [c["type"] for t in s["tables"] for c in t["constraints"]]
    assert kinds.count("P") == 8
    assert kinds.count("U") == 1
    assert kinds.count("R") == 11
    assert sum(len(t["indexes"]) for t in s["tables"]) == 20

    tables = {t["name"]: t for t in s["tables"]}
    emp_cols = {c["name"]: c for c in tables["EMPLOYEES"]["columns"]}
    assert emp_cols["EMPLOYEE_ID"]["data_type_display"] == "NUMBER(6)"
    assert emp_cols["EMPLOYEE_ID"]["nullable"] is False
    assert emp_cols["SALARY"]["data_type_display"] == "NUMBER(8,2)"
    emp_cons = {c["name"]: c for c in tables["EMPLOYEES"]["constraints"]}
    mgr = emp_cons["EMP_MANAGER_FK"]
    assert (mgr["ref_table"], mgr["columns"], mgr["ref_columns"]) == ("EMPLOYEES", ["MANAGER_ID"], ["EMPLOYEE_ID"])
    assert "EMP_EMAIL_UK" in emp_cons
    jh = {c["name"]: c for c in tables["JOB_HISTORY"]["constraints"]}
    assert jh["JHIST_EMP_ID_ST_DATE_PK"]["columns"] == ["EMPLOYEE_ID", "START_DATE"]
    assert tables["COUNTRIES"]["iot"] is True


async def test_unknown_schema(oracle_client):
    with pytest.raises(OracleFailure) as ei:
        await oracle_client.get_schema_snapshot("NO_SUCH_SCHEMA")
    assert ei.value.code == NOT_FOUND
