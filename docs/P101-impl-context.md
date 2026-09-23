# P101 実装コンテキスト

Executor が着手前に読む要約。まずこの文書と、着手するスプリントの `docs/P007-impl-direction/U00N-*.md` を読む。迷ったら下の「詳細仕様の場所」を見る。

## 1. ソースツリーの状態

* `server/INDEX.md`・`client/INDEX.md`: (実装前)のプレースホルダ(P020)。コード格納先は `server/`(Python、uv)、`client/`(npm)、`deploy/`・`compose.yaml`・`e2e/`。
* ルートの `config.yaml` は Git 管理外(U001-T4 で作る)。パスワードはここ以外に書かない。

## 2. 遵守すべき技術的決定(`docs/ADR.md`)

| ADR | 要点 |
| --- | --- |
| ADR-001 | MCP サーバは backend の子プロセス(stdio)で常駐。backend は Oracle に直接つながない |
| ADR-002 | SQLite のマイグレーションは `schema_migrations` による差分適用 |
| ADR-003 | スナップショットは owner ごとに 1 件、1 トランザクションで置き換え |
| ADR-004 | 同一オリジン(Vite proxy / nginx)。CORS は使わない |
| ADR-005 | セル値は MCP で表示用文字列に(fetch_decimals、fetch_lobs=False) |
| ADR-006 | データは主キー順(無ければ ROWID)の OFFSET、件数は数えない |
| ADR-007 | Python は `server/` の 1 つの uv プロジェクトに 3 パッケージ |
| ADR-008 | SQLite は SQLAlchemy Core |
| ADR-009 | React 19 + TS + Vite + Mantine + TanStack Query + React Router |
| ADR-010 | ER 図は @xyflow/react + elkjs |
| ADR-011 | python-oracledb Thin、読み取り専用トランザクション + 必ず ROLLBACK |
| ADR-012 | compose は web(8088 公開)と api(非公開)、Oracle は外部(host.docker.internal) |
| ADR-013 | 設定は `config.yaml` + 環境変数上書き、パスワードは SecretStr |

## 3. これから着手するスプリント

* 全スプリント(U001〜U006)の P102 が完了。次は P103(P008 の T01〜T12 を一括実行)。
* 各スプリントの P102 が終わるたびに本書の「着手するスプリント」を更新する。全スプリント完了後に P103(P008 の T01〜T12 を一括実行)。

## 4. 詳細仕様の場所

| 知りたいこと | 場所 |
| --- | --- |
| 画面の振る舞い・API の外部仕様・エラーコード | `docs/P002-frontend-spec.md` §2・§3 |
| SQLite のテーブル定義 | `docs/P002-frontend-spec.md` §4.2 |
| 設定ファイル | `docs/P003-backend-spec.md` §2 |
| MCP ツールと辞書の問い合わせ | `docs/P003-backend-spec.md` §3 |
| backend の内部処理・MCP エラーの変換表 | `docs/P003-backend-spec.md` §4 |
| マイグレーション | `docs/P003-backend-spec.md` §5 |
| テストデータ方針・HR の期待値 | `docs/P006-test-plan.md` §3、`docs/ArchitectureHandbook.md` §7 |
| 参考実装(TypeScript) | `../OracleSearchMCP/app/src/`(`db/readonly-tx.ts`、`repositories/schema-metadata.ts`、`repositories/foreign-keys.ts`) |

## 5. 確定したコマンド

P102 で実際に実行して確認したもの(2026-09-23):

| 目的 | コマンド | 結果 |
| --- | --- | --- |
| Python 単体テスト | `cd server && uv run pytest tests/unit -q` | 131 件合格(Oracle 不要) |
| Python 1 件だけ | `cd server && uv run pytest tests/unit/mcp/test_type_format.py -q` | 14 件合格 |
| クライアント単体テスト | `cd client && npm test` | 54 件合格 |
| クライアントのビルド | `cd client && npm run build` | 成功 |
| 開発用 Oracle の疎通 | `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` | `7` |
| backend(開発) | `cd server && DBFAQ_CONFIG=../config.yaml uv run uvicorn --factory dbfaq_api.main:create_app --port 8000` | `/api/health` が ok |
| frontend(開発) | `cd client && npx vite --port 5173 --strictPort` | `/api` は 8000 へ中継 |
| compose | `docker compose up -d --build` → `curl localhost:8088/api/health` | api healthy、Oracle ok(host.docker.internal 経由) |
| 受入テストの疎通 | `cd e2e && npx playwright test tests/smoke.spec.ts` | 2 件合格 |
