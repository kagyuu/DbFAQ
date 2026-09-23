# server/ INDEX

Python の uv プロジェクト(Python 3.12)。MCP サーバ・backend・共通部品の 3 パッケージ(ADR-007)。

- pyproject.toml — 依存と pytest の設定(マーカー `oracle`)
- uv.lock / .python-version — ロックファイルと Python のバージョン
- src/dbfaq_common/ — 共通部品
  - config.py — `config.yaml` の読み込み(環境変数での上書き、パスワードは SecretStr)
  - logging.py — 1 行 1 JSON のログ、`mask_secret`
- src/dbfaq_mcp/ — Oracle 用 MCP サーバ(FastMCP、stdio。`python -m dbfaq_mcp`)
  - __main__.py — 起動(ログは stderr)
  - server.py — ツール `get_schema_snapshot`・`get_table_rows`・`ping` の登録とエラーの JSON 化
  - db.py — 非同期接続プールと読み取り専用トランザクション(`run_readonly`)
  - dictionary.py — データディクショナリの問い合わせ Q-00〜Q-05
  - snapshot.py — スナップショットの組み立て(`build_snapshot`)
  - rows.py — テーブルデータのページ取得(主キー順/ROWID 順、OFFSET)
  - values.py — セル値の表示用文字列化
  - type_format.py — データ型の表記(`NUMBER(8,2)` など)
  - identifiers.py — 識別子の検証とクォート
  - errors.py — `ToolFailure` とエラーコード、Oracle エラーの変換
- src/dbfaq_api/ — backend(FastAPI。`uvicorn --factory dbfaq_api.main:create_app`)
  - main.py — アプリの組み立て(lifespan でマイグレーションと MCP 起動)、例外ハンドラ、アクセスログ
  - routers/schema.py — `/api/schema`、`/api/schema/refresh`、`/api/schema/tables/{owner}/{table}`、`.../rows`
  - routers/health.py — `/api/health`
  - services.py — API の内部処理、MCP エラー → API エラーの変換
  - mcp_gateway.py — MCP 子プロセス(stdio)とのセッション維持・再起動
  - snapshot_repo.py — SQLite へのスナップショットの保存・読み出し(SQLAlchemy Core)
  - db.py — SQLite エンジン(foreign_keys、WAL、busy_timeout)
  - migrate.py — 管理テーブル付きの差分マイグレーション
  - migrations/0001_init.sql — 初期スキーマ
  - schemas.py — API のレスポンス型(pydantic)
  - errors.py — API エラーとエラーコード
- scripts/check_oracle.py — 開発用 Oracle への疎通確認
- tests/ — テスト
  - fakes.py — backend 用の偽ゲートウェイ
  - unit/ — 単体テスト(Oracle 不要)。`mcp/`(MCP サーバ)、`api/`(backend。`echo_mcp.py` はゲートウェイ試験用の小さな MCP サーバ)、`test_config.py`・`test_logging.py`・`test_compose.py`
  - integration/ — 結合テスト T01〜T09(実 Oracle HR・実 MCP 子プロセス)。`conftest.py` に共通フィクスチャ
