"""プロンプトと SQL の取り出し(docs/P003-backend-spec.md §4.8.3)。※CR-007により追加"""

import pytest

from dbfaq_api.llm.prompt import SYSTEM_PROMPT, build_user_prompt, extract_sql


@pytest.mark.parametrize(
    "text, sql",
    [
        ("```sql\nSELECT 1\nFROM DUAL;\n```", "SELECT 1\nFROM DUAL"),
        ("Here:\n```\nSELECT 2 FROM DUAL\n```\nDone", "SELECT 2 FROM DUAL"),
        ("```SQL SELECT 3 FROM DUAL```", "SELECT 3 FROM DUAL"),
        ("  SELECT 4 FROM DUAL ;; ", "SELECT 4 FROM DUAL"),
        ("```sql\nSELECT 5 FROM DUAL\n```\n```sql\nSELECT 6 FROM DUAL\n```", "SELECT 5 FROM DUAL"),
        ("```SELECT 7 FROM DUAL```", "SELECT 7 FROM DUAL"),
        ("```with a as (select 1 x from dual) select x from a```", "with a as (select 1 x from dual) select x from a"),
        ("```sql\n```", ""),
        ("", ""),
    ],
)
def test_extract_sql(text, sql):
    assert extract_sql(text) == sql


def test_prompts():
    assert "exactly one Oracle SQL query" in SYSTEM_PROMPT and "```sql" in SYSTEM_PROMPT
    assert "FOR UPDATE" in SYSTEM_PROMPT and "semicolon" in SYSTEM_PROMPT
    assert build_user_prompt("# Database\nX", "  社員数  ") == "# Database\nX\n\n# Request\n社員数\n"
