# ArchitectureHandbook.md

後続の Agent(Executor・Reviewer Loop・Refactor)が P001〜P009 を毎回読み直さずに技術的な要点を把握するための要約。詳細は原本(`docs/P00N-*.md`)を正とする。

## 1. アプリケーション概要

* アプリケーション名: DbFAQ
* 一言で言うと: Oracle のスキーマを MCP 経由で読み取って SQLite に保存し、ブラウザで ER 図(拡大縮小・ミニマップ・クリックで詳細へ)とテーブル詳細(スキーマ情報/データのタブ)を見せる運用者向けツール。第 1 リリース。FAQ(保存クエリ)の実行は将来 CR で追加する。
* 参照元: `docs/P001-requirement.md`

## 2. 全体構成図

```mermaid
graph LR
  B[ブラウザ] -->|HTTP :8088| W[web: nginx<br/>client の静的ファイル + /api 中継]
  W -->|http://api:8000| A[api: FastAPI dbfaq_api<br/>uvicorn 1 ワーカー]
  A -->|SQLAlchemy Core| S[(SQLite /data/dbfaq.sqlite3)]
  A -->|MCP stdio| M[dbfaq_mcp 子プロセス<br/>FastMCP]
  M -->|python-oracledb Thin<br/>読み取り専用トランザクション| O[(Oracle 既存<br/>host.docker.internal:1521/FREEPDB1)]
```

* 開発時: Vite(5173)の proxy → uvicorn(8000)。Oracle は `localhost:1521`。

## 3. 技術スタック

| レイヤ | 技術 | バージョン | 選定理由の参照先 |
| --- | --- | --- | --- |
| フロントエンド | React + TypeScript + Vite、Mantine、TanStack Query、React Router | React 19.x、Mantine 9.x | ADR-009 |
| ER 図 | @xyflow/react(React Flow)+ elkjs | 12.x / 0.12.x | ADR-010 |
| バックエンド | FastAPI(Python 3.12、uv) | 導入時の最新 | ADR-007 |
| MCP | FastMCP(stdio、backend の子プロセス) | 4.x | ADR-001 |
| Oracle アクセス | python-oracledb Thin、読み取り専用トランザクション | 導入時の最新 | ADR-011、ADR-005、ADR-006 |
| データベース(アプリ) | SQLite(WAL)+ SQLAlchemy Core、独自の差分マイグレーション | Python 同梱の sqlite3 / SQLAlchemy 2.x | ADR-008、ADR-002、ADR-003 |
| 設定 | YAML(`config.yaml`)+ 環境変数上書き、pydantic | - | ADR-013 |
| 認証 | なし(社内ネットワーク前提) | - | P001 §2 |
| インフラ/デプロイ | Docker Compose(web: nginx、api)、Oracle は外部 | - | ADR-012、ADR-004 |

## 4. ディレクトリ構成の方針

* `server/` — Python の uv プロジェクト 1 つ(`src/dbfaq_common`、`src/dbfaq_mcp`、`src/dbfaq_api`、`tests/unit`、`tests/integration`、`scripts/`)。ビルド: `uv`。
* `client/` — フロントエンド(`src/api`、`src/er`、`src/pages`、`src/components`)。ビルド: `npm`。
* `deploy/` — `api.Dockerfile`、`web.Dockerfile`、`nginx.conf`。`compose.yaml` はルート。
* `e2e/` — Playwright の受入テストとスクリプト(`scripts/reset-and-up.sh` ほか)。
* 目次: `server/INDEX.md`、`client/INDEX.md`(ソースツリーごと)、`./INDEX.md`(全体。P301)。
* `config.yaml`(ルート、Git 管理外)に開発用 Oracle の接続情報。ひな型は `config.example.yaml`。

## 5. データモデルの要点

* SQLite: `snapshots`(owner ごとに最新 1 件)→ `db_tables` → `db_columns` / `db_constraints`(P・U・R)→ `db_constraint_columns` / `db_indexes` → `db_index_columns`。すべて ON DELETE CASCADE。管理用に `schema_migrations`。定義は `docs/P002-frontend-spec.md` §4。
* refresh は 1 トランザクションで旧スナップショット削除 + 挿入(失敗時は前回が残る)。テーブルデータ(rows)は保存しない。
* 状態のスコープ: スナップショット=SQLite(永続)、MCP セッション・refresh のロック=api プロセスのメモリ、Oracle 接続プール=MCP 子プロセス。`docs/P003-backend-spec.md` §4.2。

## 6. API/画面構成の要点

* 画面: SC-01 ER 図(`/`)、SC-02 テーブル詳細(`/tables/:owner/:table?tab=schema|data&page=N`)。`docs/P002-frontend-spec.md` §2。
* API: `GET /api/schema`、`POST /api/schema/refresh`、`GET /api/schema/tables/{owner}/{table}`、`GET /api/schema/tables/{owner}/{table}/rows?offset&limit`、`GET /api/health`。外部仕様は P002 §3、内部処理は P003 §4.3。
* MCP ツール: `get_schema_snapshot`、`get_table_rows`、`ping`(P003 §3.5・§3.6・§3.8)。
* エラー形式 `{"error":{"code","message","ora_code?"}}`。コード一覧は P002 §3.1、MCP→API の対応は P003 §4.1。

## 7. 実装・テストの単位

* スプリント: U001 foundation → U002 mcp-server → U003 backend-api → U004 frontend-er → U005 frontend-detail → U006 deploy(`docs/P005-impl-plan.md`)。
* 単体: pytest(`server/tests/unit`、偽ゲートウェイ・一時 SQLite)、Vitest(`client`)。
* 結合(P008 T01〜T12): 実 Oracle HR・実 MCP 子プロセス(pytest マーカー `oracle`)、Vite proxy、compose。
* 受入(P009 A01〜A07): compose の web(8088)に Playwright。スイート開始前に `docker compose down -v`。HR は読み取りのみで、前後のチェックサムが一致すること。
* HR の期待値: 7 表、35 列、PK 7、UK 1、FK 10(自己参照 EMP_MANAGER_FK を含む)、インデックス 19、EMPLOYEES 107 行、COUNTRIES は IOT。

## 8. 横断的関心事

* 認証・認可: なし。公開は web のポートのみ(ADR-012)。
* 読み取りのみの保証: MCP の全ツールが `SET TRANSACTION READ ONLY` → 実行 → 必ず ROLLBACK。任意 SQL のツールは無い。識別子は検証 + 実在確認 + クォート(ADR-011)。
* エラーハンドリング: MCP は `ToolError` に JSON(code/message/ora_code)、backend が API エラーに変換。MCP 通信不能は 503 で、次の呼び出しで子プロセスを起動し直す。
* ログ: 1 行 1 JSON。backend は stdout、MCP は stderr(stdout は MCP の通信路。print 禁止)。パスワード・テーブルデータは出さない。
* 設定: `DBFAQ_CONFIG`(既定 `./config.yaml`)、上書き `DBFAQ_ORACLE_HOST`・`DBFAQ_ORACLE_PORT`・`DBFAQ_ORACLE_PASSWORD`・`DBFAQ_SQLITE_PATH`。パスワードは SecretStr。

## 9. 既知の制約・技術的負債

* ★ACCEPTED★ LOB 全体をメモリに読み込む(ADR-005)。検討: SQL 側での切り詰め/不採用理由: SELECT * の組み直しが複雑/残存リスク: 巨大 LOB でメモリを使う(limit を下げて回避)。
* ★ACCEPTED★ OFFSET 方式のページ送り(ADR-006)。検討: キーセット方式/不採用理由: 主キー無し・複合主キーで複雑、ページ直接移動ができない/残存リスク: 深いページが遅い(offset 上限 100,000)、同時更新で行がずれて見える。
* uvicorn は 1 ワーカー前提(MCP 子プロセスとロックがプロセス内のため。ADR-001)。
* `LAST_ANALYZED` は DB のタイムゾーンを UTC とみなしている ★FIXME★(P003 §3.5)。
* 大規模スキーマ(300 表)の性能は偽データでのみ確認する(P006 §2.2)。
* 開発・テスト用の接続ユーザー hr は書き込み権限を持つ(読み取り専用トランザクションで防いでいる)。実運用は読み取り専用ユーザーを推奨。
* 実機で判明した python-oracledb の挙動: `call_timeout` 超過時、`DPY-4024` だけでなく `DPY-4011`(`timed out` を含む)になることがある(2026-09-23 確認。最小再現: 非同期プールの接続で `call_timeout=1000` にして `DBMS_SESSION.SLEEP(3)`)。

## 10. 関連ドキュメントへのリンク

* `docs/P001-requirement.md` 〜 `docs/P009-acceptance-direction.md`
* `docs/ADR.md`
* `server/INDEX.md`、`client/INDEX.md`、`./INDEX.md`
