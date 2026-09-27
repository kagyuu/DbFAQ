# server/ INDEX

Python の uv プロジェクト(Python 3.12)。backend の 1 パッケージ `dbfaq_api`(ADR-007。CR-003 で共通部品 `dbfaq_common` を統合)。Oracle へは backend が直接接続する(ADR-014。CR-002 で MCP サーバを廃止)。

- pyproject.toml — 依存と pytest の設定(マーカー `oracle`)
- uv.lock / .python-version — ロックファイルと Python のバージョン
- src/dbfaq_api/ — backend(FastAPI。`uvicorn --factory dbfaq_api.main:create_app`)
  - main.py — アプリの組み立て(lifespan でマイグレーションと `OracleClient` の作成・終了)、例外ハンドラ、アクセスログ
  - config.py — `config.yaml` の読み込み(環境変数での上書き、パスワードは SecretStr)。CR-003 で `dbfaq_common` から移設
  - log.py — 1 行 1 JSON のログ、`mask_secret`。CR-003 で `dbfaq_common/logging.py` から移設
  - routers/schema.py — `/api/schema`、`/api/schema/refresh`、`/api/schema/tables/{owner}/{table}`、`.../rows`
  - routers/health.py — `/api/health`
  - services.py — API の内部処理、`OracleFailure` → API エラーの変換
  - oracle/ — Oracle アクセス(CR-002 で `dbfaq_mcp` から移設)
    - client.py — `OracleClient`(スキーマの読み取り・テーブルデータ・疎通確認の入口)と `OracleAccess` プロトコル
    - db.py — 非同期接続プールと読み取り専用トランザクション(`run_readonly`)
    - dictionary.py — データディクショナリの問い合わせ Q-00〜Q-05
    - snapshot.py — スナップショットの組み立て(`build_snapshot`)
    - rows.py — テーブルデータのページ取得(主キー順/ROWID 順、OFFSET)
    - values.py — セル値の表示用文字列化
    - type_format.py — データ型の表記(`NUMBER(8,2)` など)
    - identifiers.py — 識別子の検証とクォート
    - errors.py — `OracleFailure` とエラーコード、Oracle エラーの変換
  - snapshot_repo.py — SQLite へのスナップショットの保存・読み出し(SQLAlchemy Core)
  - db.py — SQLite エンジン(foreign_keys、WAL、busy_timeout)
  - migrate.py — 管理テーブル付きの差分マイグレーション
  - migrations/0001_init.sql — 初期スキーマ
  - schemas.py — API のレスポンス型(pydantic)
  - errors.py — API エラーとエラーコード
- scripts/check_oracle.py — 開発用 Oracle への疎通確認
- scripts/hr_checksum.py — HR のチェックサム(受入テスト A06 のベースライン)
- scripts/a08_concurrent_load.py — 受入テスト A08(同時利用者 10 名の負荷)。CR-001 で追加
- tests/ — テスト
  - fakes.py — backend 用の偽の Oracle アクセス(`FakeOracle`)
  - unit/ — 単体テスト(Oracle 不要)。`oracle/`(Oracle アクセス。偽のプールを使う)、`api/`(backend)、`test_config.py`・`test_logging.py`・`test_compose.py`
  - integration/ — 結合テスト T01〜T04・T06〜T09(実 Oracle HR。T09 はテスト内の TCP 中継で通信断を作る)。`conftest.py` に共通フィクスチャ
