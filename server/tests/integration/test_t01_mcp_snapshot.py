"""T01: MCP の get_schema_snapshot が HR を正しく読み取る(docs/P008-test-direction/T01-mcp-snapshot-hr.md)。"""

import json

HR_TABLES = ["COUNTRIES", "DEPARTMENTS", "EMPLOYEES", "JOBS", "JOB_HISTORY", "LOCATIONS", "REGIONS"]


async def test_hr_snapshot(mcp_client):
    s = (await mcp_client.call_tool("get_schema_snapshot", {})).data
    assert s["owner"] == "HR"
    assert [t["name"] for t in s["tables"]] == HR_TABLES
    assert sum(len(t["columns"]) for t in s["tables"]) == 35
    kinds = [c["type"] for t in s["tables"] for c in t["constraints"]]
    assert kinds.count("P") == 7
    assert kinds.count("U") == 1
    assert kinds.count("R") == 10
    assert sum(len(t["indexes"]) for t in s["tables"]) == 19

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


async def test_unknown_schema(mcp_client):
    r = await mcp_client.call_tool("get_schema_snapshot", {"owner": "NO_SUCH_SCHEMA"}, raise_on_error=False)
    assert r.is_error
    assert json.loads(r.content[0].text)["code"] == "NOT_FOUND"
