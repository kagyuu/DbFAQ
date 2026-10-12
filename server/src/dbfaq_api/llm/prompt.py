"""LLM への指示と、応答からの SQL の取り出し(docs/P003-backend-spec.md §4.8.3)。※CR-007により追加"""

from __future__ import annotations

import re

SYSTEM_PROMPT = (
    "You are an expert in Oracle SQL. Write exactly one Oracle SQL query (SELECT, or WITH ... SELECT) that answers "
    "the user's request, using only the tables, views and columns described.\n"
    "Rules:\n"
    "- Exactly one statement. Do not put a semicolon at the end.\n"
    "- Never use INSERT, UPDATE, DELETE, MERGE, DDL, PL/SQL blocks or FOR UPDATE.\n"
    "- Qualify tables with the schema name.\n"
    "- Use FETCH FIRST n ROWS ONLY to limit the number of rows.\n"
    "- Use Oracle functions (EXTRACT, TO_CHAR, TRUNC, etc.) for dates.\n"
    "- Give readable aliases to computed columns.\n"
    "Answer with only the SQL in one ```sql code block."
)

# ```言語名 本文``` 。言語名は 1 語(SELECT・WITH で始まる 1 行のブロックは言語名なしとして扱う)
_CODE_BLOCK = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)(.*?)```", re.DOTALL)
_SQL_HEADS = {"SELECT", "WITH"}


def build_user_prompt(context_text: str, request: str) -> str:
    return f"{context_text}\n\n# Request\n{request.strip()}\n"


def extract_sql(text: str) -> str:
    """応答の最初のコードブロック(無ければ全文)から、末尾のセミコロン・空白を除いた SQL を返す。空なら ''。"""
    m = _CODE_BLOCK.search(text)
    if m:
        lang, body = m.group(1), m.group(2)
        sql = lang + body if lang.upper() in _SQL_HEADS else body
    else:
        sql = text
    sql = sql.strip()
    while sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql
