> **※CR-002 により廃止。** 本スプリントで作った MCP サーバ(`dbfaq_mcp`)は U007 で廃止し、Oracle アクセスのモジュールは `server/src/dbfaq_api/oracle/` に移した(`ToolFailure` は `OracleFailure` に改名)。本書は第 1 リリース時点の実装指示の記録として残す。現在の構成は `docs/P003-backend-spec.md` と `U007-oracle-in-backend.md` を正とする。

あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U002 — mcp-server

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U002-T1 [純粋関数(識別子・型表記・値の文字列化・エラー)](#u002-t1-純粋関数識別子型表記値の文字列化エラー) — `identifiers.py`・`type_format.py`・`values.py`・`errors.py`
- [x] U002-T2 [接続プールと読み取り専用トランザクション](#u002-t2-接続プールと読み取り専用トランザクション) — `db.py`
- [x] U002-T3 [スキーマのスナップショット](#u002-t3-スキーマのスナップショット) — `dictionary.py`・`snapshot.py`
- [x] U002-T4 [テーブルデータのページ取得](#u002-t4-テーブルデータのページ取得) — `rows.py`
- [x] U002-T5 [MCP サーバとツール登録](#u002-t5-mcp-サーバとツール登録) — `server.py`・`__main__.py`

---

## U002-T1: 純粋関数(識別子・型表記・値の文字列化・エラー)

### 【目的】

* Oracle に依存しない変換・検証の処理を先に作り、単体テストで固める。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_mcp/identifiers.py`、`type_format.py`、`values.py`、`errors.py`
* `server/tests/unit/mcp/test_identifiers.py`、`test_type_format.py`、`test_values.py`、`test_errors.py`(`server/tests/unit/mcp/__init__.py` も作る)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.2、§3.3、§3.4、§3.7、`docs/P002-frontend-spec.md` §3.6

### 【実装内容】

* `errors.py`:
  * `class ToolFailure(Exception)`: 属性 `code: str`、`message: str`、`ora_code: str | None`。`to_json() -> str` は `json.dumps({"code","message","ora_code"}, ensure_ascii=False)`(ora_code が None のときもキーは出す)。
  * `def from_oracle_error(exc: oracledb.Error, secret: str | None) -> ToolFailure`: `err = exc.args[0]`、`full_code = getattr(err, "full_code", None)`。`full_code in {"DPY-4024","ORA-01013","ORA-03156"}` または(`full_code == "DPY-4011"` かつ `"timed out"` がメッセージに含まれる)→ `ORACLE_TIMEOUT`。それ以外 → `ORACLE_ERROR`(ora_code = full_code)。メッセージは `str(err.message)` の 1 行目を `mask_secret` したもの(`dbfaq_common.logging.mask_secret`)。
  * 定数 `INVALID_ARGUMENT`、`NOT_FOUND`、`ORACLE_TIMEOUT`、`ORACLE_ERROR`、`INTERNAL_ERROR`。
* `identifiers.py`:
  * `def validate_identifier(name: str, field: str) -> str`: `isinstance(name, str)`、1〜128 文字、`"\x00"` と `'"'` を含まない。違反は `ToolFailure(INVALID_ARGUMENT, f"{field} が不正です: ...")`。そのまま返す。
  * `def quote(name: str) -> str`: `validate_identifier` 済みの前提で `f'"{name}"'`。
* `type_format.py`: `def format_data_type(data_type, data_length, data_precision, data_scale, char_length, char_used) -> str` — P003 §3.4 の表どおり。
* `values.py`:
  * 定数 `MAX_TEXT = 1000`、`MAX_BYTES = 32`、`ELLIPSIS = "…"`。
  * `def format_cell(value, db_type_name: str) -> tuple[str | None, bool]`: 戻り値は(表示文字列、切り詰めたか)。P003 §3.7 の表どおり。`db_type_name` は `cursor.description` の `type_code.name`(例 `DB_TYPE_DATE`、`DB_TYPE_TIMESTAMP`、`DB_TYPE_TIMESTAMP_TZ`、`DB_TYPE_TIMESTAMP_LTZ`)。DATE は `%Y-%m-%d %H:%M:%S`、TIMESTAMP 系は `%Y-%m-%d %H:%M:%S.%f`、tzinfo があれば `" +HH:MM"` を付ける(`value.strftime("%z")` を `+HH:MM` に整形)。Decimal は `format(v, "f")`、`-0` は `"0"`。
  * `def format_row(row: Sequence, type_names: Sequence[str]) -> tuple[list[str | None], list[int]]`: セルごとに `format_cell` し、切り詰めた列インデックスのリストも返す。

### 【実装してはいけないこと】

* Oracle に接続するコードをこのタスクで書かない。

### 【Unit Test内容】

* identifiers: 正常 `EMPLOYEES`、`my table`(空白)、`lower`、128 文字 / 異常 空文字、129 文字、`a"b`、`a\x00b`、`None` → すべて `ToolFailure` で code `INVALID_ARGUMENT`。`quote("A")=='"A"'`。
* type_format: `VARCHAR2(20)`(char_used B)、`VARCHAR2(20 CHAR)`、`CHAR(2)`、`NVARCHAR2(10)`、`NUMBER`、`NUMBER(*,0)`、`NUMBER(6)`、`NUMBER(8,2)`、`FLOAT(126)`、`FLOAT`、`RAW(16)`、`DATE`、`TIMESTAMP(6)`、`CLOB`。
* values: `None`→(None, False)/`Decimal("24000")`→"24000"/`Decimal("0.15")`/`Decimal("1E+3")`→"1000"/`Decimal("-0")`→"0"/`float 1.5`/DATE の datetime/TIMESTAMP の datetime(マイクロ秒)/tz 付き datetime(+09:00)/`timedelta`/1,000 文字ちょうど(切らない)と 1,001 文字(切って `…`、True)/bytes 32 バイト(切らない)と 33 バイト(`0x` + 64 桁 + `…`)/`format_row` の truncated インデックス。
* errors: `ToolFailure.to_json` が JSON で 3 キーを持つ/`from_oracle_error` に偽の Error 相当(`full_code` と `message` を持つオブジェクトを args[0] に入れた `oracledb.DatabaseError`)を渡して `ORA-00942`→ORACLE_ERROR、`DPY-4024`→ORACLE_TIMEOUT、`DPY-4011`+`timed out`→ORACLE_TIMEOUT、`DPY-4011`(timed out 無し)→ORACLE_ERROR、メッセージ中の secret が `***` になる。
  * 偽の Error の作り方: `types.SimpleNamespace(full_code="ORA-00942", message="ORA-00942: table or view does not exist")` を `oracledb.DatabaseError(ns)` の引数にする。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/mcp -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U002-T2: 接続プールと読み取り専用トランザクション

### 【目的】

* Oracle への接続プールと、全ツール共通の「読み取り専用トランザクションで実行して必ずロールバックする」仕組みを作る。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_mcp/db.py`
* `server/tests/unit/mcp/test_db.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.1

### 【実装内容】

* モジュールの読み込み時に `oracledb.defaults.fetch_decimals = True`、`oracledb.defaults.fetch_lobs = False`。
* `class Database`:
  * `__init__(self, cfg: OracleConfig, pool_factory=oracledb.create_pool_async)`。プールはまだ作らない。
  * `async def _get_pool(self)`: 未作成なら `asyncio.Lock` の中で `pool_factory(user=cfg.user, password=cfg.password.get_secret_value(), dsn=cfg.dsn, min=cfg.pool_min, max=cfg.pool_max, tcp_connect_timeout=cfg.connect_timeout_sec)` を作る。
  * `async def run_readonly(self, fn: Callable[[AsyncConnection], Awaitable[T]]) -> T`: `async with pool.acquire() as conn:` → `conn.call_timeout = cfg.query_timeout_sec * 1000` → `await conn.execute("SET TRANSACTION READ ONLY")` → `try: return await fn(conn)` → `finally:` で `await conn.rollback()`(失敗は `logger.warning` のみで握りつぶす。元の例外を上書きしない)。
  * `oracledb.Error` は `from_oracle_error(exc, secret=password)` の `ToolFailure` に変換して送出する(`ToolFailure` はそのまま通す)。
  * `async def close(self)`: プールがあれば `await pool.close(force=True)`。
* 呼び出し順序は P003 §3.1 のコード例どおり。

### 【実装してはいけないこと】

* `SET TRANSACTION READ ONLY` を省略する経路を作らない(テスト用のバイパスも作らない)。
* 接続をツールをまたいで使い回さない(毎回プールから借りる)。

### 【Unit Test内容】

* テスト対象: `Database.run_readonly`(偽のプール・接続を使う。偽物は `execute`・`rollback` の呼び出しを記録するクラスを自作する。`acquire()` は async コンテキストマネージャを返す)
* 正常系: 呼び出し順が `SET TRANSACTION READ ONLY` → fn → rollback/`call_timeout` が `query_timeout_sec*1000`/プールは 2 回呼んでも 1 回だけ作られる。
* 異常系: fn が例外 → rollback が呼ばれ、元の例外が送出される/rollback が例外でも元の例外が送出される/`SET TRANSACTION` が失敗 → fn は呼ばれない/fn が `oracledb.DatabaseError`(ORA-00942)→ `ToolFailure(ORACLE_ERROR, ora_code="ORA-00942")`。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/mcp/test_db.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U002-T3: スキーマのスナップショット

### 【目的】

* データディクショナリを 6 回の問い合わせで読み、P003 §3.5 のスナップショット JSON を組み立てる。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_mcp/dictionary.py`、`server/src/dbfaq_mcp/snapshot.py`
* `server/tests/unit/mcp/test_snapshot.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.5、§3.4、`../OracleSearchMCP/app/src/repositories/schema-metadata.ts`(結合の書き方の参考)

### 【実装内容】

* `dictionary.py`: 各問い合わせを `async def fetch_xxx(conn, owner) -> list[dict]` で実装(列名は小文字キーの dict に変換)。SQL は P003 §3.5 の Q-00〜Q-05。すべて `:owner` のバインド変数。
  * Q-01 の条件: `t.OWNER = :owner AND t.NESTED = 'NO' AND t.SECONDARY = 'N' AND t.DROPPED = 'NO' AND (t.IOT_TYPE IS NULL OR t.IOT_TYPE = 'IOT')`、`LEFT JOIN ALL_TAB_COMMENTS c ON c.OWNER = t.OWNER AND c.TABLE_NAME = t.TABLE_NAME`。
  * Q-02: `ALL_TAB_COLUMNS col LEFT JOIN ALL_COL_COMMENTS cc ON cc.OWNER=col.OWNER AND cc.TABLE_NAME=col.TABLE_NAME AND cc.COLUMN_NAME=col.COLUMN_NAME WHERE col.OWNER=:owner ORDER BY col.TABLE_NAME, col.COLUMN_ID`。
  * Q-03: `c.CONSTRAINT_NAME, c.TABLE_NAME, c.CONSTRAINT_TYPE, c.DELETE_RULE, c.R_OWNER, rc.TABLE_NAME AS R_TABLE_NAME, cc.COLUMN_NAME, cc.POSITION, rcc.COLUMN_NAME AS R_COLUMN_NAME`(結合は `../OracleSearchMCP` と同じ。`rcc.POSITION = cc.POSITION`)。`ORDER BY c.TABLE_NAME, c.CONSTRAINT_NAME, cc.POSITION`。一意制約・主キーの `cc.POSITION` は NULL のことがあるので、NULL のときは出現順で 1 から振る。
  * Q-04: `ALL_INDEXES i JOIN ALL_IND_COLUMNS ic ON ic.INDEX_OWNER=i.OWNER AND ic.INDEX_NAME=i.INDEX_NAME WHERE i.TABLE_OWNER=:owner` — `i.TABLE_NAME, i.INDEX_NAME, i.UNIQUENESS, i.INDEX_TYPE, ic.COLUMN_NAME, ic.COLUMN_POSITION, ic.DESCEND`。
  * Q-05: `ALL_IND_EXPRESSIONS WHERE TABLE_OWNER=:owner` — `INDEX_NAME, COLUMN_POSITION, COLUMN_EXPRESSION`(LONG 型。文字列で受け取れる)。
* `snapshot.py`:
  * `def build_snapshot(owner, oracle_version, fetched_at: datetime, tables, columns, constraints, indexes, expressions) -> dict` — **純粋関数**(引数の行リストだけから組み立てる。現在時刻は引数 `fetched_at` で受け取り、内部で `datetime.now()` を呼ばない)。
    * テーブルは名前の昇順。Q-01 に無いテーブルの列・制約・インデックスは捨てる(ビュー等)。
    * 列は `column_id` 昇順。`nullable` は `NULLABLE == 'Y'`。`data_default` は `strip()` して空なら None。`data_type_display` は `format_data_type`。
    * 制約は名前ごとにまとめ、`columns`・`ref_columns` を position 順に並べる。型 R 以外は `ref_owner`・`ref_table`・`ref_columns`・`delete_rule` を None にする。
    * インデックスは名前ごとにまとめ、列は position 順。`descending` は `DESCEND == 'DESC'`。Q-05 に同じ(index_name, position)があれば、列名を式の文字列に置き換える。
    * `last_analyzed`(naive datetime)は UTC とみなして `YYYY-MM-DDTHH:MM:SSZ`。`fetched_at` も同形式。`iot` は `IOT_TYPE == 'IOT'`。
  * `async def get_schema_snapshot(db: Database, owner: str | None, default_owner: str, now: Callable[[], datetime]) -> dict`: owner を決め(`validate_identifier`)、`db.run_readonly` の中で Q-00(0 件なら `ToolFailure(NOT_FOUND, f"スキーマ {owner} が見つかりません")`)→ Q-01〜Q-05 を実行し、`conn.version` と `now()` を渡して `build_snapshot`。

### 【実装してはいけないこと】

* テーブルごとに問い合わせを発行しない(問い合わせは 6 回固定)。
* ビューを tables に含めない。

### 【Unit Test内容】

* テスト対象: `build_snapshot`(偽の行データ。HR の EMPLOYEES・DEPARTMENTS 相当の行を手で書く)
* 正常系: テーブルの並び/列の並びと `data_type_display`/主キー・一意制約・外部キーのまとめ/**複合外部キー**(2 列、position 順)/**自己参照外部キー**(EMP_MANAGER_FK)/**別スキーマへの外部キー**(ref_owner が別)/**関数索引**の式の置き換え/降順インデックス/Q-01 に無いテーブル(ビュー)の列が捨てられる/主キーの無いテーブル/`data_default` の空白除去/`last_analyzed` の Z 形式/空スキーマ(tables 0)。
* 異常系: `get_schema_snapshot` で owner に `"` → INVALID_ARGUMENT(偽の db で。run_readonly は呼ばれない)。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/mcp/test_snapshot.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U002-T4: テーブルデータのページ取得

### 【目的】

* 指定したテーブルのデータを、主キー順(無ければ ROWID 順)に 1 ページ取得する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_mcp/rows.py`
* `server/tests/unit/mcp/test_rows.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.6、§3.7

### 【実装内容】

* 定数 `MAX_OFFSET = 100_000`、`MAX_LIMIT = 500`。
* `def build_rows_sql(owner: str, table: str, pk_columns: list[str]) -> tuple[str, str]`: 純粋関数。戻り値は(SQL、order_basis)。主キーあり: `SELECT * FROM "O"."T" ORDER BY "C1", "C2" OFFSET :off ROWS FETCH NEXT :n ROWS ONLY`、`PRIMARY_KEY`。なし: `... ORDER BY ROWID ...`、`ROWID`。識別子は `quote`。
* `async def get_table_rows(db, owner, table, offset, limit, clock=time.perf_counter) -> dict`:
  1. `validate_identifier`(owner、table)。`0 <= offset <= MAX_OFFSET`、`1 <= limit <= MAX_LIMIT` でなければ `INVALID_ARGUMENT`。
  2. `db.run_readonly` の中で: `SELECT IOT_TYPE FROM ALL_TABLES WHERE OWNER=:o AND TABLE_NAME=:t` → 0 件なら `NOT_FOUND`(「テーブル {owner}.{table} が見つかりません」)。
  3. 主キー列: `SELECT cc.COLUMN_NAME FROM ALL_CONSTRAINTS c JOIN ALL_CONS_COLUMNS cc ON cc.OWNER=c.OWNER AND cc.CONSTRAINT_NAME=c.CONSTRAINT_NAME WHERE c.OWNER=:o AND c.TABLE_NAME=:t AND c.CONSTRAINT_TYPE='P' ORDER BY cc.POSITION`。
  4. `build_rows_sql` の SQL を `off=offset, n=limit+1` で実行し、`t0=clock()` と `clock()` の差をミリ秒の整数に。
  5. `type_names = [d.type_code.name for d in cursor.description]`、`columns = [{"name": d.name, "data_type": name.removeprefix("DB_TYPE_")}]`。
  6. 取得行が `limit` を超えたら `has_next=True`、超えた行は捨てる。各行を `format_row`。
  7. 戻り値: `{"columns","rows","truncated","offset","limit","has_next","order_basis","order_by","elapsed_ms"}`。`order_by` は主キー列のリスト、ROWID のときは `["ROWID"]`。

### 【実装してはいけないこと】

* 件数(COUNT(*))を数えない。
* offset・limit を SQL 文字列に埋め込まない(バインド変数で渡す)。

### 【Unit Test内容】

* テスト対象: `build_rows_sql`(純粋関数)、`get_table_rows`(偽の db・接続・カーソル)
* 正常系: 単一主キー・複合主キーの ORDER BY/主キーなしで ROWID/小文字・空白を含む名前のクォート/`limit+1` 行返ると has_next=True でちょうど limit 行/limit 行以下なら has_next=False/columns の data_type から `DB_TYPE_` が除かれる/elapsed_ms が偽の clock の差(例 0.0→0.0385 で 38)。
* 異常系: offset -1・100,001、limit 0・501 → INVALID_ARGUMENT(db は呼ばれない)/テーブルが無い → NOT_FOUND。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/mcp/test_rows.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U002-T5: MCP サーバとツール登録

### 【目的】

* FastMCP でツール 3 本を公開し、`python -m dbfaq_mcp` で stdio サーバとして起動できるようにする。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_mcp/server.py`、`server/src/dbfaq_mcp/__main__.py`
* `server/tests/unit/mcp/test_server.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.1、§3.2、§3.5、§3.6、§3.8

### 【実装内容】

* `server.py`:
  * `def create_server(cfg: AppConfig, db: Database | None = None) -> FastMCP`: `mcp = FastMCP("dbfaq-oracle")`。db 省略時は `Database(cfg.oracle)`。
  * ツール(`@mcp.tool`、すべて `async def`、戻り値 `dict`):
    * `get_schema_snapshot(owner: str | None = None)` → `snapshot.get_schema_snapshot(db, owner, cfg.oracle.target_schema, now=lambda: datetime.now(timezone.utc))`
    * `get_table_rows(owner: str, table: str, offset: int = 0, limit: int = 50)` → `rows.get_table_rows(...)`
    * `ping()` → `db.run_readonly` で `SELECT USER, SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM DUAL` と `conn.version` → `{"version","user","current_schema"}`
  * 共通のラッパ `_call(coro)`: `ToolFailure` は `raise ToolError(f.to_json())`。その他の例外は `logger.exception` のうえ `raise ToolError(ToolFailure(INTERNAL_ERROR, "内部エラーが発生しました").to_json())`。
  * ツールの説明文(docstring)は日本語で 1〜2 行。
* `__main__.py`: `cfg = load_config()`、`setup_logging(cfg.app.log_level, stream=sys.stderr)`、`create_server(cfg).run()`(既定の stdio トランスポート)。**標準出力に何も print しない**。

### 【実装してはいけないこと】

* ツールを 3 本以外に追加しない(任意 SQL の実行ツールは第1リリースの範囲外)。
* HTTP トランスポートを実装しない。

### 【Unit Test内容】

* テスト対象: `create_server` のツール(FastMCP のインメモリクライアント `fastmcp.Client(mcp)` で呼ぶ。db は偽物)
* 正常系: ツール一覧が 3 本/`ping` が偽 db の値を返す/`get_table_rows` が偽の `rows.get_table_rows` の結果を返す(`monkeypatch` で差し替え)。
* 異常系: 偽 db が `ToolFailure(NOT_FOUND)` を送出 → クライアント側で `is_error=True`(`raise_on_error=False`)、エラー本文の JSON の code が `NOT_FOUND`/想定外の `RuntimeError` → code `INTERNAL_ERROR` で、メッセージに RuntimeError の文言が含まれない。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/mcp -q`

### 【完了条件】

* `tests/unit/mcp` がすべて合格。かつ `cd server && DBFAQ_CONFIG=../config.yaml timeout 5 uv run python -m dbfaq_mcp < /dev/null; echo $?` で起動時例外が出ない(stdin が閉じると終了する)。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
