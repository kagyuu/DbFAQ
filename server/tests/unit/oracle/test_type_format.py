import pytest

from dbfaq_api.oracle.type_format import format_data_type


@pytest.mark.parametrize(
    "args, expected",
    [
        (("VARCHAR2", 20, None, None, 20, "B"), "VARCHAR2(20)"),
        (("VARCHAR2", 80, None, None, 20, "C"), "VARCHAR2(20 CHAR)"),
        (("CHAR", 2, None, None, 2, "B"), "CHAR(2)"),
        (("NVARCHAR2", 20, None, None, 10, "C"), "NVARCHAR2(10)"),
        (("NUMBER", 22, None, None, 0, None), "NUMBER"),
        (("NUMBER", 22, None, 0, 0, None), "NUMBER(*,0)"),
        (("NUMBER", 22, 6, 0, 0, None), "NUMBER(6)"),
        (("NUMBER", 22, 8, 2, 0, None), "NUMBER(8,2)"),
        (("FLOAT", 22, 126, None, 0, None), "FLOAT(126)"),
        (("FLOAT", 22, None, None, 0, None), "FLOAT"),
        (("RAW", 16, None, None, 0, None), "RAW(16)"),
        (("DATE", 7, None, None, 0, None), "DATE"),
        (("TIMESTAMP(6)", 11, None, 6, 0, None), "TIMESTAMP(6)"),
        (("CLOB", 4000, None, None, 0, None), "CLOB"),
    ],
)
def test_format(args, expected):
    assert format_data_type(*args) == expected
