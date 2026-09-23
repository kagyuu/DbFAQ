import json
from types import SimpleNamespace

import oracledb

from dbfaq_mcp.errors import ORACLE_ERROR, ORACLE_TIMEOUT, ToolFailure, from_oracle_error


def ora(full_code: str, message: str) -> oracledb.DatabaseError:
    return oracledb.DatabaseError(SimpleNamespace(full_code=full_code, message=message))


def test_to_json():
    d = json.loads(ToolFailure("NOT_FOUND", "m").to_json())
    assert d == {"code": "NOT_FOUND", "message": "m", "ora_code": None}


def test_oracle_error():
    f = from_oracle_error(ora("ORA-00942", "ORA-00942: table or view does not exist\nHelp: x"), None)
    assert f.code == ORACLE_ERROR
    assert f.ora_code == "ORA-00942"
    assert f.message == "ORA-00942: table or view does not exist"


def test_timeouts():
    assert from_oracle_error(ora("DPY-4024", "DPY-4024: call timeout"), None).code == ORACLE_TIMEOUT
    assert (
        from_oracle_error(ora("DPY-4011", "DPY-4011: closed\nsocket timed out while recovering"), None).code
        == ORACLE_TIMEOUT
    )
    assert from_oracle_error(ora("DPY-4011", "DPY-4011: the database closed the connection"), None).code == ORACLE_ERROR


def test_secret_masked():
    f = from_oracle_error(ora("ORA-01017", "ORA-01017: invalid pw hunter2"), "hunter2")
    assert "hunter2" not in f.message
    assert "***" in f.message
