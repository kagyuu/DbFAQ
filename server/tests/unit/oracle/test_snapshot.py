import datetime as dt
from decimal import Decimal

import pytest

from dbfaq_api.oracle.errors import INVALID_ARGUMENT, OracleFailure
from dbfaq_api.oracle.snapshot import build_snapshot, get_schema_snapshot

NOW = dt.datetime(2026, 9, 23, 1, 15, 2, tzinfo=dt.UTC)


def t(name, iot=None, num_rows=None, comments=None, last=None):
    return {"table_name": name, "num_rows": num_rows, "last_analyzed": last, "iot_type": iot, "comments": comments}


def c(table, cid, name, dtype="NUMBER", prec=None, scale=None, nullable="Y", default=None, length=22, clen=0, cused=None):
    return {
        "table_name": table, "column_id": Decimal(cid), "column_name": name, "data_type": dtype,
        "data_length": length, "data_precision": prec, "data_scale": scale, "char_length": clen,
        "char_used": cused, "nullable": nullable, "data_default": default, "comments": None,
    }


def k(table, name, ctype, col, pos, r_owner=None, r_table=None, r_col=None, rule=None):
    return {
        "constraint_name": name, "table_name": table, "constraint_type": ctype, "delete_rule": rule,
        "r_owner": r_owner, "r_table_name": r_table, "column_name": col, "position": pos, "r_column_name": r_col,
    }


def i(table, name, col, pos, unique="NONUNIQUE", itype="NORMAL", desc="ASC"):
    return {"table_name": table, "index_name": name, "uniqueness": unique, "index_type": itype,
            "column_name": col, "column_position": pos, "descend": desc}


TABLES = [
    t("EMPLOYEES", num_rows=Decimal(107), comments="employees", last=dt.datetime(2026, 9, 22, 8, 12, 32)),
    t("COUNTRIES", iot="IOT"),
    t("JOB_HISTORY"),
    t("NOPK"),
]
COLUMNS = [
    c("EMPLOYEES", 2, "LAST_NAME", "VARCHAR2", length=25, clen=25, cused="B", nullable="N"),
    c("EMPLOYEES", 1, "EMPLOYEE_ID", prec=6, scale=0, nullable="N"),
    c("EMPLOYEES", 3, "MANAGER_ID", prec=6, scale=0),
    c("EMPLOYEES", 4, "SALARY", prec=8, scale=2, default="  0 \n"),
    c("EMPLOYEES", 5, "DEPT_CODE", "VARCHAR2", length=10, clen=10, cused="B"),
    c("EMPLOYEES", 6, "DEPT_NO", prec=4, scale=0),
    c("COUNTRIES", 1, "COUNTRY_ID", "CHAR", length=2, clen=2, cused="B", nullable="N"),
    c("JOB_HISTORY", 1, "EMPLOYEE_ID", prec=6, scale=0, nullable="N"),
    c("JOB_HISTORY", 2, "START_DATE", "DATE", nullable="N", length=7),
    c("NOPK", 1, "X", default="   "),
    c("EMP_VIEW", 1, "X"),  # ビューの列は捨てる
]
CONSTRAINTS = [
    k("EMPLOYEES", "EMP_EMP_ID_PK", "P", "EMPLOYEE_ID", 1),
    k("EMPLOYEES", "EMP_MANAGER_FK", "R", "MANAGER_ID", 1, "HR", "EMPLOYEES", "EMPLOYEE_ID", "NO ACTION"),
    k("EMPLOYEES", "EMP_DEPT2_FK", "R", "DEPT_NO", 2, "OTHER", "DEPTS", "NO", "CASCADE"),
    k("EMPLOYEES", "EMP_DEPT2_FK", "R", "DEPT_CODE", 1, "OTHER", "DEPTS", "CODE", "CASCADE"),
    k("EMPLOYEES", "EMP_NAME_UK", "U", "LAST_NAME", None),
    k("JOB_HISTORY", "JHIST_PK", "P", "START_DATE", 2),
    k("JOB_HISTORY", "JHIST_PK", "P", "EMPLOYEE_ID", 1),
    k("EMP_VIEW", "V_PK", "P", "X", 1),
]
INDEXES = [
    i("EMPLOYEES", "EMP_UPPER_IX", "SYS_NC00007$", 1, itype="FUNCTION-BASED NORMAL"),
    i("EMPLOYEES", "EMP_EMP_ID_PK", "EMPLOYEE_ID", 1, unique="UNIQUE"),
    i("EMPLOYEES", "EMP_SAL_IX", "SALARY", 1, desc="DESC"),
    i("COUNTRIES", "COUNTRY_C_ID_PK", "COUNTRY_ID", 1, unique="UNIQUE", itype="IOT - TOP"),
]
EXPRESSIONS = [{"index_name": "EMP_UPPER_IX", "column_position": 1, "column_expression": 'UPPER("LAST_NAME")'}]


@pytest.fixture
def snap():
    return build_snapshot("HR", "23.26.3.0.0", NOW, TABLES, COLUMNS, CONSTRAINTS, INDEXES, EXPRESSIONS)


def table(snap, name):
    return next(x for x in snap["tables"] if x["name"] == name)


def test_header(snap):
    assert snap["owner"] == "HR"
    assert snap["fetched_at"] == "2026-09-23T01:15:02Z"
    assert [x["name"] for x in snap["tables"]] == ["COUNTRIES", "EMPLOYEES", "JOB_HISTORY", "NOPK"]


def test_columns_order_and_types(snap):
    emp = table(snap, "EMPLOYEES")
    assert [x["name"] for x in emp["columns"]] == ["EMPLOYEE_ID", "LAST_NAME", "MANAGER_ID", "SALARY", "DEPT_CODE", "DEPT_NO"]
    assert emp["columns"][0]["data_type_display"] == "NUMBER(6)"
    assert emp["columns"][0]["nullable"] is False
    assert emp["columns"][1]["data_type_display"] == "VARCHAR2(25)"
    assert emp["columns"][3]["data_type_display"] == "NUMBER(8,2)"
    assert emp["columns"][3]["data_default"] == "0"
    assert emp["num_rows"] == 107
    assert emp["last_analyzed"] == "2026-09-22T08:12:32Z"
    assert table(snap, "NOPK")["columns"][0]["data_default"] is None


def test_iot(snap):
    assert table(snap, "COUNTRIES")["iot"] is True
    assert table(snap, "EMPLOYEES")["iot"] is False


def test_constraints(snap):
    emp = table(snap, "EMPLOYEES")
    by = {x["name"]: x for x in emp["constraints"]}
    assert [x["name"] for x in emp["constraints"]] == sorted(by)
    assert by["EMP_EMP_ID_PK"]["type"] == "P" and by["EMP_EMP_ID_PK"]["ref_columns"] is None
    self_fk = by["EMP_MANAGER_FK"]
    assert (self_fk["ref_owner"], self_fk["ref_table"], self_fk["ref_columns"]) == ("HR", "EMPLOYEES", ["EMPLOYEE_ID"])
    composite = by["EMP_DEPT2_FK"]
    assert composite["columns"] == ["DEPT_CODE", "DEPT_NO"]
    assert composite["ref_columns"] == ["CODE", "NO"]
    assert composite["ref_owner"] == "OTHER"
    assert composite["delete_rule"] == "CASCADE"
    assert by["EMP_NAME_UK"]["columns"] == ["LAST_NAME"]
    assert table(snap, "JOB_HISTORY")["constraints"][0]["columns"] == ["EMPLOYEE_ID", "START_DATE"]
    assert table(snap, "NOPK")["constraints"] == []


def test_indexes(snap):
    emp = {x["name"]: x for x in table(snap, "EMPLOYEES")["indexes"]}
    assert emp["EMP_UPPER_IX"]["columns"] == [{"name": 'UPPER("LAST_NAME")', "descending": False}]
    assert emp["EMP_SAL_IX"]["columns"][0]["descending"] is True
    assert emp["EMP_EMP_ID_PK"]["unique"] is True
    assert table(snap, "COUNTRIES")["indexes"][0]["index_type"] == "IOT - TOP"


def test_view_rows_dropped(snap):
    assert all(x["name"] != "EMP_VIEW" for x in snap["tables"])


def test_empty_schema():
    s = build_snapshot("EMPTY", "23", NOW, [], [], [], [], [])
    assert s["tables"] == []


async def test_invalid_owner_does_not_touch_db():
    class NoDb:
        async def run_readonly(self, fn):
            raise AssertionError("must not be called")

    with pytest.raises(OracleFailure) as ei:
        await get_schema_snapshot(NoDb(), 'A"B', "HR", now=lambda: NOW)
    assert ei.value.code == INVALID_ARGUMENT
