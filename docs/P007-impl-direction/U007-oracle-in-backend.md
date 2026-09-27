> **※CR-003 による注記(※P011(CR-003)矛盾点#2にもとづき追加)。** CR-003(U008)で `dbfaq_common` を `dbfaq_api` に統合した。`dbfaq_common/config.py` は `dbfaq_api/config.py`、`dbfaq_common/logging.py` は `dbfaq_api/log.py` に読み替える。現在の構成は `docs/P003-backend-spec.md` §1.2 を正とする。

あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U007 — oracle-in-backend(※CR-002により追加)

MCP サーバ(`dbfaq_mcp`、U002 の成果物)と MCP ゲートウェイ(`dbfaq_api/mcp_gateway.py`、U003 の一部)を廃止し、Oracle アクセスを backend のパッケージ `dbfaq_api/oracle` に移す。**処理の中身(SQL、読み取り専用トランザクション、識別子の扱い、値の表示形式、Oracle エラーの変換規則)は変えない。** 変更要求: `docs/P901-cr-direction/CR-002.md`。

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U007-T1 [Oracle アクセスのモジュールを移す](#u007-t1-oracle-アクセスのモジュールを移す) — `dbfaq_mcp/*.py` → `dbfaq_api/oracle/*.py`、`ToolFailure` → `OracleFailure`
- [x] U007-T2 [OracleClient](#u007-t2-oracleclient) — `dbfaq_api/oracle/client.py`(3 つの処理の入口、疎通確認の 5 秒)
- [x] U007-T3 [backend を Oracle の直接呼び出しに切り替える](#u007-t3-backend-を-oracle-の直接呼び出しに切り替える) — `services.py`・`main.py`・`errors.py`・`schemas.py`、MCP 関係の削除、依存・設定
- [x] U007-T4 [frontend の health の型](#u007-t4-frontend-の-health-の型) — `types.ts`・`fetchMock.ts` から `mcp` を除く
- [x] U007-T5 [配布物と受入テストのスクリプト](#u007-t5-配布物と受入テストのスクリプト) — Dockerfile・compose のコメント、`a04-restart.sh` の手順 7

---

## U007-T1: Oracle アクセスのモジュールを移す

### 【目的】

* MCP サーバの中にあった Oracle アクセスの処理を、backend のパッケージへそのまま移す(履歴を追えるよう `git mv` を使う)。

### 【作成・編集対象ファイル】

* `git mv server/src/dbfaq_mcp/{db,dictionary,errors,identifiers,rows,snapshot,type_format,values}.py server/src/dbfaq_api/oracle/`、`server/src/dbfaq_api/oracle/__init__.py` を新規作成(docstring のみ)
* `git mv server/tests/unit/mcp/{fakes,test_db,test_errors,test_identifiers,test_rows,test_snapshot,test_type_format,test_values}.py server/tests/unit/oracle/`、`server/tests/unit/oracle/__init__.py`(空)
* 移したファイルの import と docstring

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.2、§3.1〜§3.8

### 【実装内容】

* `errors.py`: `ToolFailure` を `OracleFailure` に改名する。`to_json()` と定数 `INTERNAL_ERROR` を削除する(想定外の例外は API の例外ハンドラが 500 にする。P003 §3.2)。`from_oracle_error` の戻り値の型も `OracleFailure` にする。変換規則は変えない。
* 他のモジュールの `ToolFailure` を `OracleFailure` に置き換える。相対 import(`from .errors import ...`)はそのままでよい。
* docstring の「MCP ツールのエラー」などの MCP の語を、Oracle アクセスの語に直す。

### 【実装してはいけないこと】

* SQL、トランザクションの手順、値の文字列化、識別子の検証の規則を変えない。
* このタスクで `dbfaq_mcp/server.py`・`__main__.py`・`mcp_gateway.py` を消さない(T3 で消す)。

### 【Unit Test内容】

* 移した単体テストの import を `dbfaq_api.oracle.*` に、`ToolFailure` を `OracleFailure` に直す。`test_errors.py` の `to_json` の検証は削除する(機能を削除したため)。それ以外の期待値は変えない。
* 合格条件: `tests/unit/oracle` がすべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/oracle -q`

### 【完了条件】

* 上記コマンドが合格し、`server/src/dbfaq_api/oracle/` に 8 モジュールと `__init__.py` がある。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U007-T2: OracleClient

### 【目的】

* スキーマの読み取り・テーブルデータの取得・疎通確認の 3 つの処理の入口を 1 つのクラスにまとめ、backend から直接呼べるようにする(旧 MCP のツール 3 本に相当)。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/client.py`(新規)
* `server/src/dbfaq_api/oracle/db.py`(`run_readonly` に問い合わせの上限を渡せるようにする)
* `server/tests/unit/oracle/test_client.py`(新規)、`server/tests/unit/oracle/test_db.py`(追記)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.1、§3.5、§3.6、§3.8、§3.9

### 【実装内容】

* `db.py`: `run_readonly(fn, timeout_sec: int | None = None)`。`timeout_sec` が指定されたらその秒数、無ければ `query_timeout_sec` を `call_timeout`(ミリ秒)にする。
* `client.py`:
  * 定数 `HEALTH_TIMEOUT_SEC = 5`。
  * `class OracleAccess(Protocol)`: `async get_schema_snapshot(owner: str | None) -> dict`、`async get_table_rows(owner, table, offset, limit) -> dict`、`async ping() -> dict`、`async close() -> None`。
  * `class OracleClient`: `__init__(self, cfg: OracleConfig, db: Database | None = None, now: Callable[[], datetime] = UTC の現在時刻)`。
    * `get_schema_snapshot(owner)` → `snapshot.get_schema_snapshot(db, owner, cfg.target_schema, now)`。
    * `get_table_rows(owner, table, offset, limit)` → `rows.get_table_rows(db, ...)`。
    * `ping()` → 旧 `dbfaq_mcp/server.py` の `ping` と同じ問い合わせを `db.run_readonly(work, timeout_sec=HEALTH_TIMEOUT_SEC)` で実行し、`{"version", "user", "current_schema"}` を返す。
    * `close()` → `db.close()`。

### 【実装してはいけないこと】

* `asyncio.wait_for` などで Oracle の処理を途中で取り消さない(P003 §3.8 の ★ACCEPTED★)。
* このタスクで API 側(`services.py` など)を変えない。

### 【Unit Test内容】

* `test_db.py`: `timeout_sec=5` を渡すと `call_timeout == 5000`、渡さなければ `query_timeout_sec × 1000`。
* `test_client.py`(偽のプール `tests/unit/oracle/fakes.py` を使う):
  * `ping()` が `{"version": "23.26.3.0.0", "user": "HR", "current_schema": "HR"}` を返し、`SET TRANSACTION READ ONLY` → SELECT → `rollback` の順で呼ばれ、`call_timeout == 5000`。
  * `get_table_rows` が引数をそのまま `rows.get_table_rows` に渡す(monkeypatch)。
  * `get_schema_snapshot(None)` が設定の `target_schema` を使う(monkeypatch で `snapshot.get_schema_snapshot` の引数を確かめる)。
  * Oracle のエラー(偽の `oracledb.DatabaseError`)が `OracleFailure` になって送出される。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/oracle -q`

### 【完了条件】

* 上記コマンドが合格する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U007-T3: backend を Oracle の直接呼び出しに切り替える

### 【目的】

* backend が `OracleClient` を直接使うようにし、MCP に関係するコード・依存・設定を削除する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/services.py`、`main.py`、`errors.py`、`schemas.py`
* 削除: `server/src/dbfaq_api/mcp_gateway.py`、`server/src/dbfaq_mcp/`(残りの `__init__.py`・`__main__.py`・`server.py`)、`server/tests/unit/api/test_gateway.py`、`server/tests/unit/api/echo_mcp.py`、`server/tests/unit/mcp/`(残りの `__init__.py`・`test_server.py`)
* `server/tests/fakes.py`、`server/tests/unit/api/test_api.py`、`server/tests/unit/api/fixtures.py`(docstring)、`server/tests/unit/test_packages.py`
* `server/src/dbfaq_common/config.py`、`server/src/dbfaq_common/logging.py`(docstring)、`config.example.yaml`、`server/tests/unit/test_config.py`
* `server/pyproject.toml`、`server/uv.lock`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §2、§4.1〜§4.5、`docs/P002-frontend-spec.md` §3.1、§3.7

### 【実装内容】

* `errors.py`: `MCP_UNAVAILABLE`、`McpToolError`、`McpUnavailable` を削除する。
* `services.py`:
  * `SchemaService(repo, oracle: OracleAccess, config, refresh_lock)`。
  * `_mcp_to_api` を `_to_api_error(e: OracleFailure, context, owner="")` に改め、対応は P003 §4.1 の表どおり(`ORACLE_ERROR`/`ORACLE_TIMEOUT`/`NOT_FOUND`(rows・refresh)/`INVALID_ARGUMENT`)。それ以外のコードは来ないが、来たら `INTERNAL_ERROR`。
  * refresh: `await self.oracle.get_schema_snapshot(self.owner)`。`McpSnapshot` による検証は削除する(P003 §4.3)。
  * rows: `await self.oracle.get_table_rows(owner, table, offset, limit)`。
  * health: `await self.oracle.ping()`。`OracleFailure` なら oracle=error。応答から `mcp` を除き、`status` は oracle だけで決める。`HEALTH_TIMEOUT_SEC` は `oracle/client.py` に移ったので `services.py` からは削除する。
* `main.py`: `create_app(config=None, oracle: OracleAccess | None = None, now=None)`。lifespan で `oracle` が無ければ `OracleClient(config.oracle)` を作る(接続はしない)。終了時に `await oracle.close()`。MCP の起動・`McpUnavailable` の扱い・`config_file_path` の import を削除する。
* `schemas.py`: `HealthResponse` から `mcp` を削除。`McpColumn`〜`McpSnapshot` を削除。docstring から MCP の語を除く。
* `config.py`: `AppSection.mcp_call_timeout_sec` を削除する(既存の `config.yaml` に残っていても pydantic の既定で無視される)。`config.example.yaml` の該当行を削除する。
* `pyproject.toml`: 依存から `fastmcp` を、`[tool.hatch.build.targets.wheel] packages` から `src/dbfaq_mcp` を削除し、`description` を「DbFAQ backend (FastAPI)」にする。`uv lock` で `uv.lock` を更新する。
* `tests/fakes.py`: `FakeGateway` を `FakeOracle` に置き換える。`responses: dict[str, Any]`(キーは `get_schema_snapshot`・`get_table_rows`・`ping`)、`calls: list[tuple[str, dict]]`。値が例外なら送出、callable なら呼ぶ(awaitable なら await)。
* `test_api.py`: `FakeOracle` を使う。`McpToolError(code, ...)` は `OracleFailure(code, ...)` に置き換える。`MCP_UNAVAILABLE` の場合分けと `test_health_mcp_down` は削除する。`test_health_ok` で `"mcp" not in body` を確かめる。`test_health_oracle_error` の `mcp` の検証を削除する。`test_rows_unknown_table_does_not_call_mcp` は `..._does_not_call_oracle` に改名する。
* `test_config.py`: `mcp_call_timeout_sec` の検証を削除し、「`app.mcp_call_timeout_sec: 90` が残っている古い設定ファイルも読める」テストを追加する。
* `test_packages.py`: `dbfaq_mcp` の import を削除し、`dbfaq_api.oracle` の import を加える。

### 【実装してはいけないこと】

* API のパス・パラメータ・エラー形式・`mcp` 以外の応答項目を変えない。
* SQLite の処理(`snapshot_repo.py`・`migrate.py`・`db.py`)を変えない。

### 【Unit Test内容】

* 上記の書き換え後、`tests/unit` 全体が合格する。
* `grep -rn -i "mcp" server/src server/tests server/pyproject.toml config.example.yaml` が 0 件(`OracleSearchMCP` への参照を除く)。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv lock && uv sync && uv run pytest tests/unit -q && uv run ruff check src tests`
* `grep -rn -i "mcp" server/src server/tests server/pyproject.toml config.example.yaml | grep -v OracleSearchMCP`(出力なし)

### 【完了条件】

* 単体テストと ruff が合格し、MCP の参照が残っていない。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U007-T4: frontend の health の型

### 【目的】

* `GET /api/health` の応答から `mcp` が無くなったことを frontend の型とテスト用の偽データに反映する。

### 【作成・編集対象ファイル】

* `client/src/api/types.ts`、`client/src/test/fetchMock.ts`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3.7

### 【実装内容】

* `HealthResponse` の型から `mcp` を削除する。`fetchMock.ts` の health の偽データから `mcp` を削除する。
* 画面(`OracleStatus.tsx`)は `oracle` だけを見ているので変えない。

### 【実装してはいけないこと】

* 画面の表示・操作を変えない。

### 【Unit Test内容】

* 既存の Vitest がすべて合格し、型チェック(ビルド)が通る。

### 【実行コマンド】

* `cd client && npm test && npm run build`

### 【完了条件】

* 上記が合格する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U007-T5: 配布物と受入テストのスクリプト

### 【目的】

* コンテナ構成の説明と受入テストのスクリプトから MCP 子プロセスの前提を除く。

### 【作成・編集対象ファイル】

* `deploy/api.Dockerfile`(先頭と CMD の上のコメント)、`compose.yaml`(先頭のコメント)
* `e2e/scripts/a04-restart.sh`(手順 7 を「MCP 子プロセスの強制終了からの回復」から「api コンテナに `dbfaq_mcp` のプロセスが無いこと」の確認に置き換える)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.1、§4.2、`docs/P009-acceptance-direction/A04-restart-resilience.md`

### 【実装内容】

* `api.Dockerfile`: 先頭のコメントを「backend(FastAPI)のイメージ」に、CMD の上のコメントを「refresh のロックと Oracle の接続プールがプロセス内にあるため 1 ワーカー固定(ADR-014)」にする。コマンドは変えない。
* `compose.yaml`: 先頭のコメントの「api(FastAPI + MCP 子プロセス)」を「api(FastAPI)」にする。
* `a04-restart.sh`: A04 手順 7 を、`docker compose exec -T api python -c ...` で `/proc/*/cmdline` を走査し `dbfaq_mcp` を含むプロセスの数を数えて `0` であること、かつ `/api/health` の status が `ok` であることの確認に置き換える(`docs/P009-acceptance-direction/A04-restart-resilience.md` 手順 7)。

### 【実装してはいけないこと】

* compose のサービス構成・ポート・ボリューム・環境変数を変えない(`tests/unit/test_compose.py` が引き続き合格すること)。

### 【Unit Test内容】

* `cd server && uv run pytest tests/unit/test_compose.py -q` が合格。`docker compose build` が成功する。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/test_compose.py -q && cd .. && docker compose build`

### 【完了条件】

* 上記が成功する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
