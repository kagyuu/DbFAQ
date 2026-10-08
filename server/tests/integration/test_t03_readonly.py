"""T03: 読み取り専用トランザクションの実効性(docs/P008-test-direction/T03-oracle-readonly.md)。"""

import pytest

from dbfaq_api.oracle.client import OracleClient
from dbfaq_api.oracle.db import Database
from dbfaq_api.oracle.errors import OracleFailure

CHECKSUM = "SELECT COUNT(*), SUM(ORA_HASH(EMPLOYEE_ID || '|' || SALARY || '|' || EMAIL)) FROM HR.EMPLOYEES"


async def checksum(db: Database):
    async def work(conn):
        cur = conn.cursor()
        await cur.execute(CHECKSUM)
        return tuple(await cur.fetchall())[0]

    return await db.run_readonly(work)


async def test_dml_rejected_and_data_unchanged(base_config, oracle_client: OracleClient):
    db = Database(base_config.oracle)
    try:
        before = await checksum(db)

        async def update(conn):
            try:
                await conn.execute("UPDATE HR.EMPLOYEES SET SALARY = SALARY + 1 WHERE EMPLOYEE_ID = 100")
            finally:
                await conn.rollback()  # 万一成功してしまった場合にも元に戻す

        with pytest.raises(OracleFailure) as ei:
            await db.run_readonly(update)
        # 読み取り専用トランザクション(ORA-01456)。※CR-006により、読み取り専用ユーザー dbfaq_ro では
        # 権限で先に拒否される(23ai は ORA-41900、以前の版は ORA-01031)。どれでも更新は起きない
        assert ei.value.ora_code in {"ORA-01456", "ORA-41900", "ORA-01031"}

        await oracle_client.get_schema_snapshot(None)
        for offset in (0, 50, 100):
            await oracle_client.get_table_rows("HR", "EMPLOYEES", offset, 50)
        await oracle_client.ping()

        # ※CR-004により追加: Query の経路(T03 手順 3)
        await oracle_client.run_query("SELECT * FROM HR.EMPLOYEES", 500)
        spool, _ = await oracle_client.export_csv("SELECT * FROM HR.EMPLOYEES")
        spool.close()
        for sql in ("UPDATE HR.EMPLOYEES SET SALARY = SALARY + 1", "DELETE FROM HR.EMPLOYEES"):
            with pytest.raises(OracleFailure) as ei:
                await oracle_client.run_query(sql, 500)
            assert ei.value.code == "SQL_REJECTED"

        assert await checksum(db) == before
    finally:
        await db.close()
