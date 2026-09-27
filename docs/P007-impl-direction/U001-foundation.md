> **※CR-003 による注記(※P011(CR-003)矛盾点#2にもとづき追加)。** CR-003(U008)で `dbfaq_common` を `dbfaq_api` に統合した。`dbfaq_common/config.py` は `dbfaq_api/config.py`、`dbfaq_common/logging.py` は `dbfaq_api/log.py` に読み替える。現在の構成は `docs/P003-backend-spec.md` §1.2 を正とする。

> **※CR-002 による注記(※P011(CR-002)矛盾点#4にもとづき追加)。** 本書は第 1 リリース時点の実装指示の記録として残す。CR-002(U007)で次のとおり変わった: パッケージは `dbfaq_common`・`dbfaq_api` の 2 つ(`dbfaq_mcp` を削除)、依存から `fastmcp` を削除、`AppSection.mcp_call_timeout_sec` を削除、`test_packages.py` は `dbfaq_mcp` の代わりに `dbfaq_api.oracle` を import。`config_file_path` は `load_config` が設定ファイルの場所を決めるために使う(MCP 子プロセスへの受け渡しは無くなった)。現在の構成は `docs/P003-backend-spec.md` §1.2・§2 を正とする。

あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U001 — foundation

## タスク一覧(OKF副目次)

* 状態は `[ ]`(未着手) / `[~]`(進行中) / `[x]`(完了) の3種類とする。1タスクの作業を開始したら `[~]` に、完了条件をすべて満たしたら `[x]` に更新する。
* このスプリントファイル自体の状態(`docs/P007-impl-direction.md` の該当行)は、全タスクが `[x]` になって初めて `[x]` にする。
* **中断からの再開**: `[~]` のタスクがあれば、該当タスクの【完了条件】を実際に再実行して現状を確認してから続きを行う。
* **先行実装の禁止**: `[ ]` の後続タスクが対象とするファイルには着手しない。

- [x] U001-T1 [Python プロジェクトの初期化](#u001-t1-python-プロジェクトの初期化) — `server/` を uv プロジェクトとして初期化
- [x] U001-T2 [設定ファイルの読み込み](#u001-t2-設定ファイルの読み込み) — `dbfaq_common/config.py` と `config.example.yaml`
- [x] U001-T3 [JSON ログ](#u001-t3-json-ログ) — `dbfaq_common/logging.py`
- [x] U001-T4 [開発用 Oracle の疎通確認](#u001-t4-開発用-oracle-の疎通確認) — ローカル `config.yaml` と疎通確認スクリプト

---

## U001-T1: Python プロジェクトの初期化

### 【目的】

* backend・MCP サーバ・共通部品を入れる Python プロジェクトを用意する。

### 【作成・編集対象ファイル】

* `server/pyproject.toml`、`server/uv.lock`、`server/.python-version`
* `server/src/dbfaq_common/__init__.py`、`server/src/dbfaq_mcp/__init__.py`、`server/src/dbfaq_api/__init__.py`
* `server/tests/unit/__init__.py`(空)、`server/tests/integration/__init__.py`(空)、`server/tests/conftest.py`
* `.gitignore`(追記)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §1.2

### 【実装内容】

* `server/` を `uv init --package` 相当の構成で初期化する(`server/INDEX.md` が既にある場合は消さない)。Python は 3.12(`uv python pin 3.12`)。
* パッケージは `src/` レイアウトで 3 つ(`dbfaq_common`、`dbfaq_mcp`、`dbfaq_api`)。`pyproject.toml` の `[tool.hatch.build.targets.wheel] packages = ["src/dbfaq_common", "src/dbfaq_mcp", "src/dbfaq_api"]`(ビルドバックエンドは hatchling)。
* 依存: `fastapi`、`uvicorn[standard]`、`fastmcp`(4.x)、`oracledb`、`sqlalchemy>=2`、`pydantic>=2`、`pyyaml`。開発依存(`uv add --dev`): `pytest`、`pytest-asyncio`、`httpx`、`ruff`。
* `[tool.pytest.ini_options]`: `testpaths = ["tests"]`、`asyncio_mode = "auto"`、`markers = ["oracle: 実 Oracle(HR)が必要なテスト"]`。
* `.gitignore` に `config.yaml`、`data/`、`server/data/`、`client/node_modules/`、`client/dist/`、`e2e/node_modules/`、`e2e/test-results/`、`e2e/playwright-report/`、`e2e/.baseline-checksum.json` を追記する(`e2e/.baseline-checksum.json` は ※P011矛盾点#7にもとづき追加)。
* `tests/conftest.py` は空のファイル(後続タスクで追加)でよい。

### 【実装してはいけないこと】

* 設計書に無い依存(ORM の拡張、Alembic など)を追加しない。

### 【Unit Test内容】

* テスト対象: パッケージの import。`tests/unit/test_packages.py` で `import dbfaq_common, dbfaq_mcp, dbfaq_api` が成功すること。
* 異常系: なし。
* 合格条件: 1 件合格。

### 【実行コマンド】

* `cd server && uv sync && uv run pytest tests/unit -q`

### 【完了条件】

* 上記コマンドが成功し、1 件合格。

### 【次タスクに進む前の停止条件】

* `uv sync` がネットワーク等で失敗し、3 回試しても解消しない場合は停止して報告する。

---

## U001-T2: 設定ファイルの読み込み

### 【目的】

* `config.yaml` を読み込み、型チェックした設定オブジェクトを返す。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_common/config.py`
* `config.example.yaml`(リポジトリのルート)
* `server/tests/unit/test_config.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §2

### 【実装内容】

* pydantic v2 のモデル:
  * `OracleConfig`: `host: str`、`port: int = Field(1521, ge=1, le=65535)`、`service_name: str`、`user: str`、`password: SecretStr`、`schema_: str | None = Field(None, alias="schema")`、`query_timeout_sec: int = Field(30, ge=1, le=600)`、`connect_timeout_sec: int = Field(10, ge=1, le=600)`、`pool_min: int = Field(1, ge=1)`、`pool_max: int = Field(4, ge=1)`。`model_validator(mode="after")` で `pool_max >= pool_min` を検査。プロパティ `target_schema` は `schema_` があればそれ、無ければ `user.upper()`。プロパティ `dsn` は `f"{host}:{port}/{service_name}"`。
  * `AppSection`: `sqlite_path: str = "./data/dbfaq.sqlite3"`、`log_level: str = "INFO"`、`mcp_call_timeout_sec: int = Field(90, ge=1, le=600)`。
  * `AppConfig`: `oracle: OracleConfig`、`app: AppSection = AppSection()`。
* 関数 `load_config(path: str | None = None, env: Mapping[str, str] | None = None) -> AppConfig`:
  * `env` 省略時は `os.environ`。`path` 省略時は `env.get("DBFAQ_CONFIG", "config.yaml")`。
  * YAML を `yaml.safe_load` で読む。ファイルが無ければ `ConfigError(f"設定ファイルが見つかりません: {path}")`。
  * 上書き: `DBFAQ_ORACLE_HOST`→oracle.host、`DBFAQ_ORACLE_PORT`→oracle.port、`DBFAQ_ORACLE_PASSWORD`→oracle.password、`DBFAQ_SQLITE_PATH`→app.sqlite_path。
  * pydantic の `ValidationError` は `ConfigError` に変換する。メッセージは各エラーの `loc` を `.` でつないだ項目名と `msg` のみ(入力値 `input` は含めない=パスワードが漏れない)。
* 関数 `config_file_path(env=None) -> str`(MCP 子プロセスに渡すため、実際に使ったパスを返す)。
* `config.example.yaml` は P003 §2.1 の内容(password は `"change-me"`)。

### 【実装してはいけないこと】

* パスワードをログ・例外メッセージに含めない。
* 設定項目を P003 §2.1 以外に増やさない。

### 【Unit Test内容】

* テスト対象: `load_config`
* 正常系: 最小限の YAML(必須のみ)で既定値が入る/`schema` 省略時に `target_schema == "HR"`(user=hr)/`dsn` の形式/環境変数 4 種の上書き/`config.example.yaml` 自体が読める。
* 異常系: ファイルが無い → `ConfigError`/`password` 欠落 → `ConfigError` でメッセージに `oracle.password`/`port: 70000` → `ConfigError`/`pool_min: 3, pool_max: 2` → `ConfigError`/パスワード `"s3cr3t-XYZ"` を含む設定で `port` を不正にしたとき、例外メッセージにも `repr(config)` にも `s3cr3t-XYZ` が含まれない。
* ファイルは `tmp_path` に書く。環境変数は `env` 引数で渡す(`os.environ` を触らない)。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/test_config.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U001-T3: JSON ログ

### 【目的】

* backend と MCP サーバで共通の、1 行 1 JSON のログ出力を用意する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_common/logging.py`
* `server/tests/unit/test_logging.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §4.5

### 【実装内容】

* `class JsonFormatter(logging.Formatter)`: `{"ts": ISO8601 UTC(ミリ秒, Z 付き), "level", "logger", "msg", ...extra}` を `json.dumps(ensure_ascii=False, default=str)` で出す。`extra` は `record.__dict__` のうち標準属性以外のキー。例外があれば `"exc"` にスタックトレース文字列。
* `def setup_logging(level: str = "INFO", stream=None) -> None`: ルートロガーのハンドラを 1 つ(`StreamHandler(stream)`、既定 `sys.stdout`)に置き換え、`JsonFormatter` を設定する。MCP サーバは `stream=sys.stderr` で呼ぶ。
* `def mask_secret(text: str, secret: str | None) -> str`: `secret` が空でなければ `text` 中の出現をすべて `***` に置き換える。

### 【実装してはいけないこと】

* 外部のログライブラリ(structlog など)を追加しない。

### 【Unit Test内容】

* 正常系: `io.StringIO` に出したログが JSON として読め、`level`・`msg`・extra のキーを含む/例外付きで `exc` を含む/`setup_logging` を 2 回呼んでもハンドラが 1 つ/`mask_secret` の置換。
* 異常系: `mask_secret(text, None)`・`mask_secret(text, "")` は元のまま。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/test_logging.py -q`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U001-T4: 開発用 Oracle の疎通確認

### 【目的】

* 人間が指定した開発用 Oracle(HR)に、設定ファイルの値で接続できることを確認する。

### 【作成・編集対象ファイル】

* `config.yaml`(リポジトリのルート。**Git 管理外**。コミットしない)
* `server/scripts/check_oracle.py`

### 【参照すべき仕様箇所】

* `docs/P001-requirement.md` §2(開発・テスト用 Oracle)、`docs/P003-backend-spec.md` §2

### 【実装内容】

* `config.yaml` を `config.example.yaml` から作り、`host: localhost`、`port: 1521`、`service_name: FREEPDB1`、`user: hr`、`password` は人間から提示された値、`schema: HR`、`sqlite_path: ./data/dbfaq.sqlite3` にする。
* `server/scripts/check_oracle.py`: `load_config()` で読み、python-oracledb(Thin、同期)で接続し、`SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = :o` を表示して終了コード 0。接続失敗は `full_code` とメッセージを表示して終了コード 1。
* `git status` で `config.yaml` が追跡対象に出ないこと(`.gitignore` 済み)を確認する。

### 【実装してはいけないこと】

* パスワードを `config.yaml` 以外(docs、コード、コミット)に書かない。

### 【Unit Test内容】

* このタスクは外部の Oracle への疎通確認であり、単体テストの対象となる純粋な処理を含まない。テスト可能な部分(設定の読み込み)は U001-T2 で確認済み。確認は下記コマンドの実行結果で行う。

### 【実行コマンド】

* `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py`

### 【完了条件】

* 出力が `7`(HR のテーブル数)で終了コード 0。`git status --porcelain` に `config.yaml` が出ない。

### 【次タスクに進む前の停止条件】

* 接続できない場合は、Oracle コンテナの状態(`docker ps`)を確認し、それでも接続できなければ停止して報告する(Oracle の起動は本スプリントの範囲外)。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
