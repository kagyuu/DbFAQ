"""テスト用のスナップショット(MCP の get_schema_snapshot の戻り値の形。P003 §3.5)。"""

from __future__ import annotations

import copy


def column(cid, name, display="NUMBER(6)", nullable=True, data_type="NUMBER", default=None, comment=None):
    return {
        "column_id": cid, "name": name, "data_type": data_type, "data_type_display": display,
        "data_length": 22, "data_precision": 6, "data_scale": 0, "char_length": 0, "char_used": None,
        "nullable": nullable, "data_default": default, "comment": comment,
    }


def pk(name, *cols):
    return {"name": name, "type": "P", "columns": list(cols), "ref_owner": None, "ref_table": None,
            "ref_columns": None, "delete_rule": None}


def uk(name, *cols):
    return {**pk(name, *cols), "type": "U"}


def fk(name, cols, ref_owner, ref_table, ref_cols, rule="NO ACTION"):
    return {"name": name, "type": "R", "columns": cols, "ref_owner": ref_owner, "ref_table": ref_table,
            "ref_columns": ref_cols, "delete_rule": rule}


def index(name, cols, unique=False, itype="NORMAL"):
    return {"name": name, "unique": unique, "index_type": itype,
            "columns": [{"name": c.removesuffix(" DESC"), "descending": c.endswith(" DESC")} for c in cols]}


def table(name, columns, constraints=(), indexes=(), comment=None, num_rows=None, iot=False):
    return {"name": name, "comment": comment, "num_rows": num_rows, "last_analyzed": "2026-09-22T08:12:32Z",
            "iot": iot, "columns": list(columns), "constraints": list(constraints), "indexes": list(indexes)}


def hr_snapshot(fetched_at="2026-09-23T01:15:02Z", owner="HR"):
    return copy.deepcopy({
        "owner": owner,
        "oracle_version": "23.26.3.0.0",
        "fetched_at": fetched_at,
        "tables": [
            table("COUNTRIES",
                  [column(1, "COUNTRY_ID", "CHAR(2)", False, "CHAR"), column(2, "REGION_ID", "NUMBER")],
                  [pk("COUNTRY_C_ID_PK", "COUNTRY_ID"), fk("COUNTR_REG_FK", ["REGION_ID"], owner, "REGIONS", ["REGION_ID"])],
                  [index("COUNTRY_C_ID_PK", ["COUNTRY_ID"], True, "IOT - TOP")], iot=True),
            table("EMPLOYEES",
                  [column(1, "EMPLOYEE_ID", nullable=False, comment="Primary key"),
                   column(2, "LAST_NAME", "VARCHAR2(25)", False, "VARCHAR2"),
                   column(3, "EMAIL", "VARCHAR2(25)", False, "VARCHAR2"),
                   column(4, "MANAGER_ID"),
                   column(5, "DEPT_CODE", "VARCHAR2(10)", data_type="VARCHAR2"),
                   column(6, "SALARY", "NUMBER(8,2)", default="0")],
                  [pk("EMP_EMP_ID_PK", "EMPLOYEE_ID"), uk("EMP_EMAIL_UK", "EMAIL"),
                   fk("EMP_MANAGER_FK", ["MANAGER_ID"], owner, "EMPLOYEES", ["EMPLOYEE_ID"]),
                   fk("EMP_EXT_FK", ["DEPT_CODE"], "OTHER", "DEPTS", ["CODE"], "CASCADE")],
                  [index("EMP_EMP_ID_PK", ["EMPLOYEE_ID"], True), index("EMP_SAL_IX", ["SALARY DESC"]),
                   index("EMP_UPPER_IX", ['UPPER("LAST_NAME")'], itype="FUNCTION-BASED NORMAL")],
                  comment="employees table", num_rows=107),
            table("JOB_HISTORY",
                  [column(1, "EMPLOYEE_ID", nullable=False), column(2, "START_DATE", "DATE", False, "DATE")],
                  [pk("JHIST_PK", "EMPLOYEE_ID", "START_DATE"),
                   fk("JHIST_EMP_FK", ["EMPLOYEE_ID"], owner, "EMPLOYEES", ["EMPLOYEE_ID"])]),
            table("REGIONS", [column(1, "REGION_ID", "NUMBER", False)], [pk("REG_ID_PK", "REGION_ID")]),
        ],
    })
