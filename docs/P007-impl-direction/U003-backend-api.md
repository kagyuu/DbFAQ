あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U003 — backend-api

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U003-T1 [SQLite とマイグレーション](#u003-t1-sqlite-とマイグレーション) — `db.py`・`migrate.py`・`migrations/0001_init.sql`
- [x] U003-T2 [スナップショットのリポジトリ](#u003-t2-スナップショットのリポジトリ) — `snapshot_repo.py`
- [x] U003-T3 [エラー・レスポンス型・MCP ゲートウェイ](#u003-t3-エラーレスポンス型mcp-ゲートウェイ) — `errors.py`・`schemas.py`・`mcp_gateway.py`
- [x] U003-T4 [サービスと API](#u003-t4-サービスと-api) — `services.py`・`routers/`・`main.py`

---

## U003-T1: SQLite とマイグレーション

### 【目的】

* SQLite のエンジンと、管理テーブル付きの差分適用マイグレーションを作る。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/db.py`、`server/src/dbfaq_api/migrate.py`、`server/src/dbfaq_api/migrations/0001_init.sql`
* `server/pyproject.toml`(`migrations/*.sql` をパッケージに含める設定。hatchling は src 配下の非 .py も既定で含むので、含まれることをテストで確認するだけでよい)
* `server/tests/unit/api/__init__.py`、`server/tests/unit/api/test_migrate.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §5、`docs/P002-frontend-spec.md` §4.2

### 【実装内容】

* `db.py`:
  * `def create_sqlite_engine(path: str) -> Engine`: 親ディレクトリを `mkdir(parents=True, exist_ok=True)`。`create_engine(f"sqlite:///{path}")`。`event.listens_for(engine, "connect")` で `PRAGMA foreign_keys=ON`、`PRAGMA journal_mode=WAL`、`PRAGMA busy_timeout=5000`。
* `0001_init.sql`: P002 §4.2 の 7 テーブル(`snapshots`、`db_tables`、`db_columns`、`db_constraints`、`db_constraint_columns`、`db_indexes`、`db_index_columns`)を `CREATE TABLE` で作る(列・型・制約・`ON DELETE CASCADE`・UNIQUE・CHECK は表のとおり)。加えて `CREATE INDEX ix_db_constraints_ref ON db_constraints(ref_owner, ref_table)`。
* `migrate.py`:
  * `def apply_all(engine: Engine, now: Callable[[], str], migrations_dir: Path = 既定の migrations ディレクトリ) -> list[str]`: 戻り値は今回適用したバージョンのリスト。
  * 手順: `CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)` → 適用済みの version を読む → `migrations_dir` の `*.sql` をファイル名順に、未適用のものだけ、**1 ファイル = 1 トランザクション**で実行(SQLite の DBAPI 接続の `executescript` は暗黙に COMMIT するため使わない。SQL を `;` で文に分割し、`BEGIN` → 各文 `exec_driver_sql` → `INSERT INTO schema_migrations` → `COMMIT`。失敗時は `ROLLBACK` して `MigrationError(version, 原因)` を送出)。version はファイル名の拡張子なし(例 `0001_init`)。`applied_at` は引数 `now()` の値(内部で時計を読まない)。
  * SQL の分割は「`;` で分けて空白だけの断片を捨てる」単純な方式でよい(トリガーなど `;` を含む DDL は使わない前提。コメントに明記)。

### 【実装してはいけないこと】

* Alembic などのマイグレーションツールを導入しない。
* `CREATE TABLE IF NOT EXISTS` で冪等性を代用しない(管理テーブルで判定する)。

### 【Unit Test内容】

* テスト対象: `apply_all`(`tmp_path` の SQLite ファイル)
* 正常系: 初回で `["0001_init"]` を返し 7 テーブル + `schema_migrations` ができる/**同じファイルに 2 回目**の `apply_all` は `[]` を返し例外にならない/別のエンジンを作り直して(=再起動相当)3 回目も `[]`/一時ディレクトリに `0002_add.sql`(`ALTER TABLE snapshots ADD COLUMN note TEXT;`)を置いて適用 → 次の実行では再適用されない/`PRAGMA foreign_keys` が 1。
* 異常系: 不正な SQL のファイル(`0002_bad.sql`)→ `MigrationError`、`schema_migrations` に `0002_bad` が無く、そのファイル内の前半の文(`CREATE TABLE t1(x);`)もロールバックされている。
* パッケージに SQL が含まれることの確認: `importlib.resources.files("dbfaq_api") / "migrations" / "0001_init.sql"` が存在する。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/api/test_migrate.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U003-T2: スナップショットのリポジトリ

### 【目的】

* MCP から受け取ったスナップショットの保存(置き換え)と、ER 図用・テーブル詳細用の読み出しを作る。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/snapshot_repo.py`
* `server/tests/unit/api/test_snapshot_repo.py`、`server/tests/unit/api/fixtures.py`(テスト用のスナップショット dict を作る関数)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §4.3、`docs/P002-frontend-spec.md` §3.2、§3.4、§4.2、MCP の戻り値 `docs/P003-backend-spec.md` §3.5

### 【実装内容】

* SQLAlchemy Core の `text()` または `Table` 定義で書く(ORM は使わない)。
* `class SnapshotRepository(engine)`:
  * `replace(snapshot: dict) -> dict`: `with engine.begin() as conn:` の中で `DELETE FROM snapshots WHERE owner=:owner` → snapshots に 1 行挿入(`table_count`=テーブル数、`relation_count`=型 R の制約数)→ テーブルごとに db_tables、列を db_columns(executemany)、制約を db_constraints + db_constraint_columns(`ref_column_name` は `ref_columns` の同じ位置)、インデックスを db_indexes + db_index_columns に挿入。戻り値はスナップショットの概要 dict(`owner, fetched_at, oracle_version, table_count, relation_count`)。途中で例外が起きたらトランザクションごと元に戻る(`engine.begin()` の挙動)。`BEGIN IMMEDIATE` にするため、接続取得時に `conn.exec_driver_sql("BEGIN IMMEDIATE")` を使う形でもよいが、`engine.begin()` で十分なら不要(単一ワーカー前提)。
  * `get_summary(owner) -> dict | None`
  * `get_er_view(owner) -> dict`: P002 §3.2 の本文(`loaded`、`snapshot`、`tables`、`relations`)。SELECT はテーブル・列・制約・制約列の **4 回**で済ませ、Python で組み立てる。`is_pk`/`is_fk` の判定は P003 §4.3 のとおり。
  * `get_table_detail(owner, table) -> dict | None`: P002 §3.4 の本文。テーブルが無ければ None。`referenced_by` は同じスナップショット内の型 R 制約のうち `ref_owner=owner AND ref_table=table`。`ref_in_snapshot` は参照先テーブルが同じスナップショット内にあるか(`ref_owner == snapshot.owner` かつテーブルが存在)。`pk_position` は主キー制約内の位置(無ければ None)。`nullable`・`iot`・`unique`・`descending` は bool で返す。
  * `table_exists(owner, table) -> bool | None`: スナップショットが無ければ None、あれば存在するか。
* 並び順は P002 §3.2・§3.4 の指定どおり(テーブル名・制約名・インデックス名の昇順、列は column_id 昇順、制約列・インデックス列は position 昇順)。

### 【実装してはいけないこと】

* リポジトリの中で現在時刻を取らない(`fetched_at` は MCP から来た値をそのまま保存する)。
* テーブルごとに SELECT を発行する N+1 を作らない(`get_er_view`)。

### 【Unit Test内容】

* テスト対象: `SnapshotRepository`(`tmp_path` の SQLite に `apply_all` 済み)
* `fixtures.py` に HR 相当の小さなスナップショット(REGIONS、COUNTRIES、EMPLOYEES、JOB_HISTORY。自己参照 FK、複合主キー、UK、関数索引、別スキーマ参照 FK を 1 つずつ含む)を作る関数を置く。
* 正常系: `replace` → `get_er_view` の tables/relations 件数と並び、`is_pk`・`is_fk`/`get_table_detail` の primary_key・unique_keys・foreign_keys(`ref_in_snapshot` true と false)・referenced_by・indexes・`pk_position`/`replace` を 2 回 → 1 件だけ残り内容が新しい方/別 owner のスナップショットは消さない/未取得で `get_er_view` → `loaded=false`/`table_exists` の None・True・False。
* 異常系: 途中で失敗するスナップショット(列の `name` が None → NOT NULL 違反)で `replace` → 例外、かつ前回のスナップショットがそのまま読める。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/api/test_snapshot_repo.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U003-T3: エラー・レスポンス型・MCP ゲートウェイ

### 【目的】

* API のエラー形式、レスポンス型、MCP サーバ(子プロセス)と話すゲートウェイを作る。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/errors.py`、`server/src/dbfaq_api/schemas.py`、`server/src/dbfaq_api/mcp_gateway.py`
* `server/tests/unit/api/test_gateway.py`、`server/tests/fakes.py`(`FakeGateway`)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3.1〜§3.7、`docs/P003-backend-spec.md` §4.1、§4.4

### 【実装内容】

* `errors.py`: `class ApiError(Exception)`(`code`、`message`、`http_status`、`ora_code=None`)。コード定数と HTTP の対応(P002 §3.1)。`class McpToolError(Exception)`(`code`、`message`、`ora_code`)。`class McpUnavailable(Exception)`。
* `schemas.py`: P002 §3.2〜§3.7 のレスポンスを pydantic モデルで定義(`ErViewResponse`、`RefreshResponse`、`TableDetailResponse`、`RowsResponse`、`HealthResponse`、`ErrorResponse`)。MCP の戻り値の検証用に `McpSnapshot`(P003 §3.5 の形。`extra="forbid"` にしない=将来の項目追加に耐える)。
* `mcp_gateway.py`:
  * `class Gateway(Protocol)`: `async def call(self, tool: str, args: dict, timeout: float | None = None) -> dict`、`async def start(self)`、`async def close(self)`。
  * `class StdioMcpGateway`: `__init__(self, config_path: str, call_timeout: float, env: dict | None = None, command: list[str] | None = None)`。`command` 既定は `[sys.executable, "-m", "dbfaq_mcp"]`。
    * `start()`: `fastmcp.Client(StdioTransport(command=command[0], args=command[1:], env={**os.environ, **(env or {}), "DBFAQ_CONFIG": config_path}))` を作って `await client.__aenter__()`。10 秒で終わらなければ `McpUnavailable`。失敗は `McpUnavailable` に変換してログ(backend の起動自体は呼び出し側で継続する)。
    * `call()`: クライアントが無ければ `asyncio.Lock` の中で `start()`。`await client.call_tool(tool, args, timeout=timeout or call_timeout, raise_on_error=False)`。
      * `result.is_error` → 本文テキスト(`result.content[0].text`)を JSON として解析し `McpToolError(code, message, ora_code)`。解析できなければ `McpToolError("INTERNAL_ERROR", "内部エラーが発生しました", None)`。
      * 成功 → `result.structured_content` があればそれ、無ければ `result.data`。dict でなければ `McpToolError("INTERNAL_ERROR", ...)`。
      * 待ち時間の超過(`asyncio.TimeoutError`、`McpError` のうちタイムアウトを示すもの、`httpx`/anyio 由来のタイムアウト)→ `McpToolError("ORACLE_TIMEOUT", "Oracle の応答がタイムアウトしました", None)`。このときセッションは維持する。
      * 通信不能(`anyio.ClosedResourceError`、`anyio.BrokenResourceError`、`BrokenPipeError`、`ConnectionError`、`RuntimeError`(クライアント未接続)、`McpError`(接続が閉じた))→ セッションを閉じて `self._client = None`、`McpUnavailable` を送出(次の呼び出しで起動し直す)。
    * `close()`: `await client.__aexit__(None, None, None)`(例外は握りつぶしてログ)。
  * 例外の型は FastMCP 4.x の実際の送出型を確認して合わせること。確認した型をコメントに書く。
* `tests/fakes.py`: `class FakeGateway`: `responses: dict[str, dict | Exception | Callable]` を持ち、`call` で登録された応答を返す(Exception なら送出)。呼び出し履歴 `calls` を記録。`async def start/close` は何もしない。

### 【実装してはいけないこと】

* backend から Oracle に直接接続しない。
* リクエストごとに子プロセスを起動しない。

### 【Unit Test内容】

* テスト対象: `StdioMcpGateway`(**実際の子プロセス**として、テスト用の小さな FastMCP サーバ `tests/unit/api/echo_mcp.py` を起動する。Oracle には繋がない。ツール: `echo(x)` → `{"x": x}`、`fail()` → `ToolError('{"code":"NOT_FOUND","message":"m","ora_code":null}')`、`bad_error()` → `ToolError("not json")`、`sleep(sec)`、`crash()` → `os._exit(1)`)。`command=[sys.executable, str(echo_mcp.py)]` で差し替える。
* 正常系: `echo` が dict を返す/2 回目の呼び出しで子プロセスを再起動しない(同じ PID。echo サーバに `pid()` ツールを用意して確認)/並行 5 回の `echo` がすべて正しい値。
* 異常系: `fail` → `McpToolError(code="NOT_FOUND")`/`bad_error` → `McpToolError(code="INTERNAL_ERROR")`/`sleep(3)` を timeout=1 → `McpToolError(code="ORACLE_TIMEOUT")`/`crash` の後の呼び出し → 1 回目は `McpUnavailable`、その次の呼び出しは成功(PID が変わる)/存在しないコマンドで start → `McpUnavailable`。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/api/test_gateway.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。子プロセスの終了検出が FastMCP の仕様上できない等、設計の前提が崩れた場合は ★FIXME★ を付けて記録し、再接続の挙動を最小限(次の呼び出しで必ず作り直す)にして進む。

---

## U003-T4: サービスと API

### 【目的】

* API 5 本を実装し、FastAPI アプリとして起動できるようにする。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/services.py`、`server/src/dbfaq_api/routers/__init__.py`、`routers/schema.py`、`routers/health.py`、`server/src/dbfaq_api/main.py`
* `server/tests/unit/api/test_api.py`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3、`docs/P003-backend-spec.md` §4.1〜§4.5

### 【実装内容】

* `main.py`: `def create_app(config: AppConfig | None = None, gateway: Gateway | None = None, now: Callable[[], datetime] | None = None) -> FastAPI`。
  * config 省略時は `load_config()`。`setup_logging(config.app.log_level)`(stdout)。
  * lifespan: `engine = create_sqlite_engine(config.app.sqlite_path)` → `apply_all(engine, now=...)` → `app.state.repo = SnapshotRepository(engine)` → gateway 省略時は `StdioMcpGateway(config_file_path(), config.app.mcp_call_timeout_sec)` を作り `start()` を試みる(`McpUnavailable` はログだけ出して続行)→ `app.state.refresh_lock = asyncio.Lock()` → yield → `gateway.close()`、`engine.dispose()`。
  * 例外ハンドラ: `ApiError` → P002 §3.1 の形/`RequestValidationError` → 422 `VALIDATION_ERROR`(message は `"{loc の最後}: {msg}"` をカンマ連結)/`Exception` → 500 `INTERNAL_ERROR`。
  * リクエストログのミドルウェア(メソッド、パス、ステータス、ms)。
  * モジュール末尾に `app = create_app` は置かず、uvicorn は `--factory` で `dbfaq_api.main:create_app` を起動する。
* `services.py`: `class SchemaService(repo, gateway, config, refresh_lock)`:
  * `er_view()`、`async refresh()`、`table_detail(owner, table)`、`async rows(owner, table, offset, limit)`、`async health(now)` — P003 §4.3 の手順どおり。MCP のエラーから API エラーへの変換は P003 §4.1 の表どおり(`McpUnavailable` → 503、`NOT_FOUND` は refresh と rows で文言を変える)。SQLite の読み書きは `starlette.concurrency.run_in_threadpool` で呼ぶ。
* `routers/schema.py`: `GET /api/schema`、`POST /api/schema/refresh`、`GET /api/schema/tables/{owner}/{table}`、`GET /api/schema/tables/{owner}/{table}/rows`(`offset: int = Query(0, ge=0, le=100000)`、`limit: int = Query(50, ge=1, le=500)`、パスは `Path(min_length=1, max_length=128)`)。
* `routers/health.py`: `GET /api/health`。
* `response_model` に `schemas.py` の型を付ける。

### 【実装してはいけないこと】

* P002 §3 に無いエンドポイント・項目を追加しない。
* CORS ミドルウェアを追加しない(P003 §7)。
* `config` のパスワードを応答・ログに出さない。

### 【Unit Test内容】

* テスト対象: 各 API(`httpx.AsyncClient(transport=ASGITransport(app))`、`FakeGateway`、`tmp_path` の SQLite。lifespan を動かすため `asgi_lifespan.LifespanManager` を使うか、`async with app.router.lifespan_context(app)` を使う)
* `GET /api/schema`: 未取得で `loaded=false`/refresh 後に tables・relations。
* `POST /api/schema/refresh`: FakeGateway の snapshot で 200、`table_count`/ゲートウェイが `McpToolError(ORACLE_ERROR, ora_code=ORA-01017)` → 502 で `ora_code`、既存スナップショットが残る/`ORACLE_TIMEOUT` → 504/`McpUnavailable` → 503/`NOT_FOUND` → 502 で「スキーマ … が見つかりません」/**実行中に 2 本目** → 409(1 本目の FakeGateway の応答を `asyncio.Event` で止めておき、その間に 2 本目を送る)。
* `GET /api/schema/tables/...`: 詳細 200/未取得 404 `SCHEMA_NOT_LOADED`/無い表 404 `TABLE_NOT_FOUND`/owner 違い 404/129 文字 422。
* `GET .../rows`: 200 で `owner`・`table` が付く、FakeGateway に渡った引数/offset -1・100001、limit 0・501 → 422 `VALIDATION_ERROR`/無い表は MCP を呼ばずに 404/MCP の `NOT_FOUND` → 502 `ora_code=ORA-00942`/503/504。
* `GET /api/health`: ok/`McpUnavailable` → degraded、mcp=error、oracle=error/`ORACLE_ERROR` → mcp=ok、oracle=error/応答全体の文字列にパスワード(テスト用の値)が含まれない。
* 共通: エラー応答が `{"error": {"code","message", ...}}` の形/応答に `access-control-allow-origin` ヘッダが無い。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit -q`
* 起動確認: `cd server && DBFAQ_CONFIG=../config.yaml uv run uvicorn --factory dbfaq_api.main:create_app --port 8000` を起動し、別の端末で `curl -s localhost:8000/api/health` が 200 を返すこと(確認後に停止する)。

### 【完了条件】

* `tests/unit` 全体がすべて合格し、起動確認で `/api/health` が `"status": "ok"` を返す。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
