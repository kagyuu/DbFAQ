import socket
from types import SimpleNamespace

import oracledb

from dbfaq_api.oracle.errors import ORACLE_ERROR, ORACLE_TIMEOUT, from_oracle_error, from_os_error


def ora(full_code: str, message: str) -> oracledb.DatabaseError:
    return oracledb.DatabaseError(SimpleNamespace(full_code=full_code, message=message))


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


def test_os_error():
    f = from_os_error(socket.gaierror(-2, "Name or service not known"), "pw")
    assert f.code == ORACLE_ERROR and f.ora_code is None
    assert "Name or service not known" in f.message


def test_os_error_masks_secret():
    assert "pw-123" not in from_os_error(OSError("failed for pw-123"), "pw-123").message


def test_os_timeout():
    assert from_os_error(TimeoutError(), None).code == ORACLE_TIMEOUT
