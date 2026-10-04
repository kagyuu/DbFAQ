"""利用者の SQL の検査(docs/P003-backend-spec.md §3.10、ADR-015)。

../OracleSearchMCP/app/src/guard/(sql-lexer.ts・sql-guard.ts)の移植。
正規化した文字列は判定にだけ使い、実行には元の SQL を使う。
"""

from __future__ import annotations

import re

from .errors import SQL_REJECTED, OracleFailure

_ALT_QUOTE_PAIRS = {"[": "]", "{": "}", "(": ")", "<": ">"}

_FORBIDDEN_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "LOCK TABLE",
)

_IDENTIFIER_CHAR = re.compile(r"[A-Za-z0-9_$#]")
_FIRST_TOKEN = re.compile(r"[A-Za-z_$#][A-Za-z0-9_$#]*")
_SPACE = re.compile(r"[\s　]")


def normalize_sql(sql: str) -> tuple[str, list[tuple[int, int]]]:
    """判定用の文字列(コメント・文字列を潰し、空白を畳み、大文字化)と、引用符付き識別子の範囲を返す。"""
    src = sql
    n = len(src)
    out: list[str] = []
    raw_ranges: list[tuple[int, int]] = []
    i = 0
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        # N1: 行コメント
        if ch == "-" and nxt == "-":
            end = src.find("\n", i + 2)
            i = n if end == -1 else end
            out.append(" ")
            continue
        # N2: ブロックコメント(ヒント句 /*+ */ は残す)
        if ch == "/" and nxt == "*":
            end = src.find("*/", i + 2)
            stop = n if end == -1 else end + 2
            if i + 2 < n and src[i + 2] == "+":
                out.append(src[i:stop])
            else:
                out.append(" ")
            i = stop
            continue
        # N4: 代替引用符 q'X...X'
        if ch in "qQ" and nxt == "'" and i + 2 < n:
            delim = src[i + 2]
            closing = _ALT_QUOTE_PAIRS.get(delim, delim)
            end = src.find(closing + "'", i + 3)
            i = n if end == -1 else end + 2
            out.append("''")
            continue
        # N3: 文字列リテラル('' はエスケープ)
        if ch == "'":
            i += 1
            while i < n:
                if src[i] == "'":
                    if i + 1 < n and src[i + 1] == "'":
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append("''")
            continue
        # N5: 引用符付き識別子は残して範囲を記録する
        if ch == '"':
            end = src.find('"', i + 1)
            stop = n if end == -1 else end + 1
            start = sum(len(p) for p in out)
            out.append(src[i:stop])
            raw_ranges.append((start, start + (stop - i)))
            i = stop
            continue
        out.append(ch)
        i += 1

    # N6: 空白の畳み込み・トリム・大文字化。範囲は畳み込み後の位置へ写す
    joined = "".join(out)
    collapsed: list[str] = []
    index_map = [-1] * len(joined)
    last_was_space = True
    for k, c in enumerate(joined):
        if _SPACE.match(c):
            if not last_was_space:
                collapsed.append(" ")
                last_was_space = True
            continue
        index_map[k] = len(collapsed)
        collapsed.append(c)
        last_was_space = False
    while collapsed and collapsed[-1] == " ":
        collapsed.pop()
    normalized = "".join(collapsed).upper()

    ranges: list[tuple[int, int]] = []
    for rs, re_ in raw_ranges:
        mapped = [index_map[k] for k in range(rs, re_) if index_map[k] >= 0]
        if mapped:
            ranges.append((mapped[0], mapped[-1] + 1))
    return normalized, ranges


def _inside(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in ranges)


def _find_token(haystack: str, phrase: str, ranges: list[tuple[int, int]]) -> int:
    """phrase を独立した語として含む最初の位置(引用符付き識別子の中は除く)。無ければ -1。"""
    start = 0
    while True:
        at = haystack.find(phrase, start)
        if at == -1:
            return -1
        before = haystack[at - 1] if at > 0 else ""
        after_index = at + len(phrase)
        after = haystack[after_index] if after_index < len(haystack) else ""
        boundary = not _IDENTIFIER_CHAR.match(before or " ") and not _IDENTIFIER_CHAR.match(after or " ")
        if boundary and not _inside(at, ranges):
            return at
        start = at + 1


def _strip_trailing_semicolon(sql: str) -> str:
    return sql.rstrip().removesuffix(";")


def _reject(message: str) -> None:
    raise OracleFailure(SQL_REJECTED, message)


def check_select(sql: str) -> str:
    """SQL が SELECT・WITH の 1 文であることを確かめ、実行用の SQL(末尾の空白とセミコロン 1 個を除く)を返す。

    違反は OracleFailure(SQL_REJECTED)。先頭は変えない(エラー位置を元の SQL の位置と一致させるため)。
    """
    if not isinstance(sql, str) or not sql.strip():
        _reject("SQL を入力してください")
    normalized, ranges = normalize_sql(sql)
    m = _FIRST_TOKEN.match(normalized)
    head = m.group(0) if m else ""

    # G1: PL/SQL ブロック・動的 SQL
    if head in ("BEGIN", "DECLARE") or any(
        _find_token(normalized, p, ranges) != -1 for p in ("EXECUTE IMMEDIATE", "DBMS_SQL")
    ):
        _reject("PL/SQL ブロックと動的 SQL は実行できません")
    # G2: 先頭の語
    if head not in ("SELECT", "WITH"):
        _reject(f"SELECT または WITH で始まる問い合わせだけを実行できます(先頭: {head or 'なし'})")
    # G3: 複文(末尾のセミコロン 1 個のみ許す)
    semicolons = [k for k, c in enumerate(normalized) if c == ";" and not _inside(k, ranges)]
    if len(semicolons) > 1 or (semicolons and normalized[semicolons[0] + 1 :].strip()):
        _reject("複数の文は実行できません")
    # G4: 行ロック
    if _find_token(normalized, "FOR UPDATE", ranges) != -1:
        _reject("FOR UPDATE(行ロック)は使えません")
    # G5: DML・DDL・トランザクション制御
    for keyword in _FORBIDDEN_KEYWORDS:
        if _find_token(normalized, keyword, ranges) != -1:
            _reject(f"更新・定義・トランザクション制御のキーワード({keyword})を含む SQL は実行できません")
    return _strip_trailing_semicolon(sql)
