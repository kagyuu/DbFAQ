import pytest

from dbfaq_mcp.errors import INVALID_ARGUMENT, ToolFailure
from dbfaq_mcp.identifiers import quote, validate_identifier


@pytest.mark.parametrize("name", ["EMPLOYEES", "my table", "lower", "A" * 128])
def test_valid(name):
    assert validate_identifier(name, "table") == name


@pytest.mark.parametrize("name", ["", "A" * 129, 'a"b', "a\x00b", None])
def test_invalid(name):
    with pytest.raises(ToolFailure) as ei:
        validate_identifier(name, "table")
    assert ei.value.code == INVALID_ARGUMENT
    assert "table" in ei.value.message


def test_quote():
    assert quote("A") == '"A"'
    assert quote("my table") == '"my table"'
