import pytest

from dbfaq_api.oracle.errors import SQL_REJECTED, OracleFailure
from dbfaq_api.oracle.sql_guard import check_select, normalize_sql


@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT 1 FROM DUAL;", "SELECT 1 FROM DUAL"),
        ("SELECT 1 FROM DUAL ;  \n", "SELECT 1 FROM DUAL "),
        ("  select 1 from dual", "  select 1 from dual"),  # 先頭は変えない(エラー位置を保つ)
        ("with a as (select 1 x from dual) select x from a", "with a as (select 1 x from dual) select x from a"),
        ("SELECT 'DELETE' FROM DUAL", "SELECT 'DELETE' FROM DUAL"),
        ("SELECT 'it''s; DROP' FROM DUAL", "SELECT 'it''s; DROP' FROM DUAL"),
        ('SELECT "UPDATE" FROM T', 'SELECT "UPDATE" FROM T'),
        ("SELECT 1 FROM DUAL -- drop table x", "SELECT 1 FROM DUAL -- drop table x"),
        ("SELECT /* delete; */ 1 FROM DUAL", "SELECT /* delete; */ 1 FROM DUAL"),
        ("SELECT q'[;DROP]' FROM DUAL", "SELECT q'[;DROP]' FROM DUAL"),
        ("SELECT Q'#a'b#' FROM DUAL", "SELECT Q'#a'b#' FROM DUAL"),
        ("SELECT /*+ FULL(t) */ * FROM T t", "SELECT /*+ FULL(t) */ * FROM T t"),
        ("-- コメント\nSELECT 1 FROM DUAL", "-- コメント\nSELECT 1 FROM DUAL"),
        ("SELECT CREATED_AT, UPDATED_BY, LAST_UPDATE_DATE FROM T", "SELECT CREATED_AT, UPDATED_BY, LAST_UPDATE_DATE FROM T"),
        ("SELECT 1 x FROM DUAL", "SELECT 1 x FROM DUAL"),
        ("SELECT 1　FROM DUAL", "SELECT 1　FROM DUAL"),  # 全角空白
    ],
)
def test_allowed(sql, expected):
    assert check_select(sql) == expected


@pytest.mark.parametrize(
    "sql, fragment",
    [
        ("UPDATE HR.EMPLOYEES SET SALARY = 1", "先頭: UPDATE"),
        ("delete from t", "先頭: DELETE"),
        ("INSERT INTO T VALUES (1)", "先頭: INSERT"),
        ("MERGE INTO T USING S ON (1=1) WHEN MATCHED THEN UPDATE SET X=1", "先頭: MERGE"),
        ("DROP TABLE T", "先頭: DROP"),
        ("TRUNCATE TABLE T", "先頭: TRUNCATE"),
        ("CREATE TABLE T (X NUMBER)", "先頭: CREATE"),
        ("GRANT SELECT ON T TO U", "先頭: GRANT"),
        ("COMMIT", "先頭: COMMIT"),
        ("BEGIN NULL; END;", "PL/SQL"),
        ("DECLARE X NUMBER; BEGIN NULL; END;", "PL/SQL"),
        ("SELECT 1 FROM DUAL WHERE 1 = (SELECT DBMS_SQL.OPEN_CURSOR FROM DUAL)", "PL/SQL"),
        ("SELECT 'x' FROM DUAL WHERE EXECUTE IMMEDIATE", "PL/SQL"),
        ("SELECT 1 FROM DUAL; SELECT 2 FROM DUAL", "複数の文"),
        ("SELECT 1 FROM DUAL;;", "複数の文"),
        ("SELECT * FROM T FOR UPDATE", "FOR UPDATE"),
        ("SELECT * FROM T FOR  update  NOWAIT", "FOR UPDATE"),
        ("WITH x AS (DELETE FROM T) SELECT * FROM x", "DELETE"),
        ("SELECT 1 FROM DUAL WHERE 1 = 1 /* x */ AND LOCK TABLE", "LOCK TABLE"),
        ("SELECT f(1) FROM DUAL WHERE ROLLBACK", "ROLLBACK"),
        ("   ", "SQL を入力"),
        ("-- only comment", "先頭: なし"),
        ("(SELECT 1 FROM DUAL)", "先頭: なし"),
    ],
)
def test_rejected(sql, fragment):
    with pytest.raises(OracleFailure) as ei:
        check_select(sql)
    assert ei.value.code == SQL_REJECTED
    assert fragment in ei.value.message


def test_normalize():
    normalized, ranges = normalize_sql('select  "my col" , \'a\' -- c\n from t')
    assert normalized == "SELECT \"MY COL\" , '' FROM T"
    assert normalized[ranges[0][0] : ranges[0][1]] == '"MY COL"'
