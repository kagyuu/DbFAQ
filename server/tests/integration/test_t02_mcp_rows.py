"""T02: MCP の get_table_rows(docs/P008-test-direction/T02-mcp-rows-hr.md)。"""

import json
import re

import pytest


async def rows(client, table, offset, limit=50, owner="HR"):
    return (await client.call_tool("get_table_rows", {"owner": owner, "table": table, "offset": offset, "limit": limit})).data


async def test_employees_pages(mcp_client):
    p1 = await rows(mcp_client, "EMPLOYEES", 0)
    assert len(p1["rows"]) == 50 and p1["has_next"] is True
    assert p1["rows"][0][0] == "100"
    assert p1["order_basis"] == "PRIMARY_KEY" and p1["order_by"] == ["EMPLOYEE_ID"]
    p2 = await rows(mcp_client, "EMPLOYEES", 50)
    assert len(p2["rows"]) == 50 and p2["has_next"] is True
    p3 = await rows(mcp_client, "EMPLOYEES", 100)
    assert len(p3["rows"]) == 7 and p3["has_next"] is False
    assert p3["rows"][-1][0] == "206"
    ids = [r[0] for p in (p1, p2, p3) for r in p["rows"]]
    assert len(ids) == 107 and len(set(ids)) == 107


async def test_value_formats(mcp_client):
    p = await rows(mcp_client, "EMPLOYEES", 0)
    names = [c["name"] for c in p["columns"]]
    hire = names.index("HIRE_DATE")
    comm = names.index("COMMISSION_PCT")
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", r[hire]) for r in p["rows"])
    assert any(r[comm] is None for r in p["rows"])
    types = {c["data_type"] for c in p["columns"]}
    assert {"NUMBER", "VARCHAR", "DATE"} <= types


async def test_composite_pk_order(mcp_client):
    p = await rows(mcp_client, "JOB_HISTORY", 0, 10)
    assert len(p["rows"]) == 10
    assert p["order_by"] == ["EMPLOYEE_ID", "START_DATE"]
    keys = [(int(r[0]), r[1]) for r in p["rows"]]
    assert keys == sorted(keys)


@pytest.mark.parametrize(
    "args, code",
    [
        ({"owner": "HR", "table": "NO_SUCH_TABLE"}, "NOT_FOUND"),
        ({"owner": "HR", "table": "EMPLOYEES", "limit": 501}, "INVALID_ARGUMENT"),
        ({"owner": "HR", "table": 'A"B'}, "INVALID_ARGUMENT"),
        ({"owner": "hr", "table": "EMPLOYEES"}, "NOT_FOUND"),
    ],
)
async def test_errors(mcp_client, args, code):
    r = await mcp_client.call_tool("get_table_rows", args, raise_on_error=False)
    assert r.is_error
    assert json.loads(r.content[0].text)["code"] == code
