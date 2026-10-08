"""PDB の情報の読み取り(docs/P003-backend-spec.md §3.12)。※CR-005により追加"""

from decimal import Decimal
from types import SimpleNamespace

import oracledb
import pytest

from dbfaq_api.config import OracleConfig
from dbfaq_api.oracle import pdb as pdb_mod
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import ORACLE_TIMEOUT, OracleFailure
from dbfaq_api.oracle.pdb import SECTIONS, get_pdb_info

from .fakes import FakeConnection, FakePool, col

CFG = OracleConfig(host="h", service_name="s", user="hr", password="pw-SECRET")
OVERVIEW = ("FREEPDB1", "FREEPDB1", "freepdb1", "DBFAQ_RO", "HR", "AL32UTF8", "AL16UTF16")
TABLESPACES_SQL = pdb_mod._TARGET_TABLESPACES_SQL


def ora(full_code, message):
    return oracledb.DatabaseError(SimpleNamespace(full_code=full_code, message=message, offset=0))


def make_db(overrides=None):
    overrides = overrides or {}

    def responder(sql, params):
        if sql == TABLESPACES_SQL:
            return overrides.get("tablespaces_of_target", ([col("D", "DB_TYPE_VARCHAR"), col("T", "DB_TYPE_VARCHAR")], [("USERS", "TEMP")]))
        key = next(k for k, _, s in SECTIONS if s == sql)
        if key in overrides:
            return overrides[key]
        if key == "overview":
            return [col(f"C{i}", "DB_TYPE_VARCHAR") for i in range(7)], [OVERVIEW]
        if key == "ts_quotas":
            return ([col("TABLESPACE_NAME", "DB_TYPE_VARCHAR"), col("USED_MB", "DB_TYPE_NUMBER"),
                     col("MAX_MB", "DB_TYPE_VARCHAR")], [("USERS", Decimal(154), "UNLIMITED")])
        if key == "segments":
            return ([col("SEGMENT_TYPE", "DB_TYPE_VARCHAR"), col("SEGMENTS", "DB_TYPE_NUMBER"),
                     col("SIZE_MB", "DB_TYPE_NUMBER")], [("LOBSEGMENT", Decimal(1), Decimal("152.25"))])
        return ora("ORA-00942", 'ORA-00942: table or view "SYS"."DBA_DATA_FILES" does not exist')

    conn = FakeConnection(responder=responder, version="23.26.3.0.0")
    return Database(CFG, pool_factory=lambda **kw: FakePool(conn)), conn


async def test_sections_and_section_error():
    db, conn = make_db()
    info = await get_pdb_info(db)
    assert [s["key"] for s in info["sections"]] == ["overview", "ts_quotas", "segments", "tablespaces"]
    ov = info["sections"][0]
    assert ov["error"] is None
    assert [c["name"] for c in ov["columns"]] == ["ITEM", "VALUE"]
    assert ov["rows"] == [
        ["コンテナ名(PDB)", "FREEPDB1"], ["DB 名", "FREEPDB1"], ["サービス名", "freepdb1"], ["バージョン", "23.26.3.0.0"],
        ["接続ユーザー", "DBFAQ_RO"], ["対象スキーマ", "HR"], ["文字セット", "AL32UTF8"], ["各国語文字セット", "AL16UTF16"],
        ["対象スキーマの既定の表領域", "USERS"], ["対象スキーマの一時表領域", "TEMP"],
    ]
    assert len(ov["truncated"]) == 10
    assert info["sections"][1]["rows"] == [["USERS", "154", "UNLIMITED"]]
    assert info["sections"][2]["columns"][2] == {"name": "SIZE_MB", "data_type": "NUMBER"}
    ts = info["sections"][3]
    assert ts["rows"] == [] and ts["columns"] == []
    assert ts["error"]["code"] == "ORACLE_ERROR" and ts["error"]["ora_code"] == "ORA-00942"
    # 1 回の読み取り専用トランザクションで、最後に ROLLBACK
    assert conn.calls[0] == ("execute", "SET TRANSACTION READ ONLY")
    assert conn.calls[-1] == ("rollback",)


async def test_error_in_middle_section_does_not_stop_others():
    db, _ = make_db({"overview": ora("ORA-01031", "ORA-01031: insufficient privileges")})
    info = await get_pdb_info(db)
    assert info["sections"][0]["error"]["ora_code"] == "ORA-01031"
    assert info["sections"][1]["error"] is None and info["sections"][1]["rows"]


async def test_timeout_fails_whole():
    db, _ = make_db({"segments": ora("DPY-4024", "DPY-4024: call timeout of 30000 ms exceeded")})
    with pytest.raises(OracleFailure) as ei:
        await get_pdb_info(db)
    assert ei.value.code == ORACLE_TIMEOUT


# ※CR-006により追加
async def test_target_tablespaces_without_privilege_only_affects_two_rows():
    db, _ = make_db({"tablespaces_of_target": ora("ORA-00942", "ORA-00942: table or view does not exist")})
    info = await get_pdb_info(db)
    ov = info["sections"][0]
    assert ov["error"] is None
    assert ov["rows"][-2:] == [["対象スキーマの既定の表領域", "(権限が無いため取得できません)"],
                               ["対象スキーマの一時表領域", "(権限が無いため取得できません)"]]
    assert ov["rows"][0] == ["コンテナ名(PDB)", "FREEPDB1"]
    assert info["sections"][1]["error"] is None


async def test_target_tablespaces_timeout_fails_whole():
    db, _ = make_db({"tablespaces_of_target": ora("DPY-4024", "DPY-4024: call timeout")})
    with pytest.raises(OracleFailure):
        await get_pdb_info(db)


def test_schema_sections_use_current_schema():
    for key, _, sql in SECTIONS:
        if key in ("ts_quotas", "segments"):
            assert "CURRENT_SCHEMA" in sql and "user_" not in sql.lower()
