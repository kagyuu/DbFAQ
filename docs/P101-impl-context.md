# P101 実装コンテキスト

Executor が着手前に読む要約。まずこの文書と、着手するスプリントの `docs/P007-impl-direction/U00N-*.md` を読む。迷ったら下の「詳細仕様の場所」を見る。

## 1. ソースツリーの状態

* `server/INDEX.md`・`client/INDEX.md`: 実装済みの目次(P104。`server/INDEX.md` は CR-002 の U007 後の構成に更新済み)。コード格納先は `server/`(Python、uv)、`client/`(npm)、`deploy/`・`compose.yaml`・`e2e/`。
* ルートの `config.yaml` は Git 管理外(U001-T4 で作る)。パスワードはここ以外に書かない。

## 2. 遵守すべき技術的決定(`docs/ADR.md`)

| ADR | 要点 |
| --- | --- |
| ADR-002 | SQLite のマイグレーションは `schema_migrations` による差分適用 |
| ADR-003 | スナップショットは owner ごとに 1 件、1 トランザクションで置き換え |
| ADR-004 | 同一オリジン(Vite proxy / nginx)。CORS は使わない |
| ADR-005 | セル値は backend で表示用文字列に(fetch_decimals、fetch_lobs=False) |
| ADR-006 | データは主キー順(無ければ ROWID)の OFFSET、件数は数えない |
| ADR-007 | Python は `server/` の 1 つの uv プロジェクトに 1 パッケージ(`dbfaq_api`。CR-003 で `dbfaq_common` を統合) |
| ADR-008 | SQLite は SQLAlchemy Core |
| ADR-009 | React 19 + TS + Vite + Mantine + TanStack Query + React Router |
| ADR-010 | ER 図は @xyflow/react + elkjs |
| ADR-011 | python-oracledb Thin、読み取り専用トランザクション + 必ず ROLLBACK(CR-004 で、利用者の SQL は ADR-015 の検査を通したものだけ実行する) |
| ADR-012 | compose は web(8088 公開)と api(非公開)、Oracle は外部(host.docker.internal) |
| ADR-013 | 設定は `config.yaml` + 環境変数上書き、パスワードは SecretStr |
| ADR-015 | 利用者の SQL(Query タブ)は `oracle/sql_guard.py` の字句検査 + 読み取り専用トランザクション。SQL を包まずに `fetchmany(501)`。CSV は一時ファイルに書き終えてから返す(CR-004) |
| ADR-016 | 保存済み Query(`saved_queries`)はスナップショットと外部キーで結ばず `scope`・`owner`・`table_name` の文字列で照合。PDB のひな型は起動時に `query_template_seeds` で 1 回だけ登録(CR-005) |
| ADR-014 | backend が `dbfaq_api/oracle` の `OracleClient`(python-oracledb の非同期プール)で Oracle に直接接続する。MCP は使わない。uvicorn 1 ワーカー(ADR-001 は CR-002 で廃止し `docs/ADR_master.md` へ) |

## 3. これから着手するスプリント

* **CR-002(2026-09-27)**: U007 oracle-in-backend(`docs/P007-impl-direction/U007-oracle-in-backend.md`)は P102 完了、P103 実行済み(`docs/test-records/20260927-0233-test-record.md`)。U001〜U006 は完了済み。U007 はコードの移設が中心で、SQL・トランザクション・値の文字列化の規則は変えない。
* **CR-003(2026-09-27)**: U008 merge-common(`docs/P007-impl-direction/U008-merge-common.md`)に着手する。`dbfaq_common` の 2 モジュールを `dbfaq_api/config.py`・`dbfaq_api/log.py` に移して import を直すだけで、処理の中身は変えない。
* U007 の完了後、P103 で P008 の再オープンした項目(T01〜T04・T06・T08・T09・T12。変更の無い T07・T10・T11 も回帰として一括実行する)を実行する。
* **CR-004(2026-10-04)**: U009 query-tab(`docs/P007-impl-direction/U009-query-tab.md`)に着手する。backend(T1 SQL の検査 → T2 実行・エラー位置・CSV → T3 API)→ frontend(T4 ひな形 → T5 Query タブ)→ T6 nginx・受入テスト の順。参考実装は `../OracleSearchMCP/app/src/guard/`。`err.offset` は UTF-8 のバイト位置(`docs/ArchitectureHandbook.md` §9)。完了後、P103 で T13 と T03(Query の経路)を実行し、T01〜T12 を回帰として再実行する。
* **CR-005(2026-10-07)**: U010 saved-queries-pdb(`docs/P007-impl-direction/U010-saved-queries-pdb.md`)に着手する。backend(T1 マイグレーション 0002・リポジトリ・ひな型の登録 → T2 PDB 情報 → T3 API 5 本)→ frontend(T4 API クライアント・`SavedQueries` → T5 `QueryTab` の共用化・`PdbIcon`・SC-03)→ T6 受入テスト A10 の順。ひな型の SQL は `server/src/dbfaq_api/pdb_templates.py`(設計時に作成し、開発用 Oracle で検査・実行を確認済み)。hr は DBA_* ・V$SESSION を読めない(`docs/ArchitectureHandbook.md` §9)。完了後、P103 で T14・T15 を実行し、T01〜T13 を回帰として再実行する。
* 各スプリントの P102 が終わるたびに本書の「着手するスプリント」を更新する。全スプリント完了後に P103(P008 の T01〜T12 を一括実行)。

## 4. 詳細仕様の場所

| 知りたいこと | 場所 |
| --- | --- |
| 画面の振る舞い・API の外部仕様・エラーコード | `docs/P002-frontend-spec.md` §2・§3 |
| SQLite のテーブル定義 | `docs/P002-frontend-spec.md` §4.2 |
| 設定ファイル | `docs/P003-backend-spec.md` §2 |
| Oracle アクセス(`dbfaq_api/oracle`)と辞書の問い合わせ | `docs/P003-backend-spec.md` §3 |
| backend の内部処理・`OracleFailure` → API エラーの変換表 | `docs/P003-backend-spec.md` §4 |
| マイグレーション | `docs/P003-backend-spec.md` §5 |
| テストデータ方針・HR の期待値 | `docs/P006-test-plan.md` §3、`docs/ArchitectureHandbook.md` §7 |
| 参考実装(TypeScript) | `../OracleSearchMCP/app/src/`(`db/readonly-tx.ts`、`repositories/schema-metadata.ts`、`repositories/foreign-keys.ts`、`guard/sql-lexer.ts`・`guard/sql-guard.ts`(CR-004)) |
| 保存済み Query・PDB(CR-005) | `docs/P002-frontend-spec.md` §2.1(アイコン)・§2.2.8・§2.3・§3.10〜§3.14・§4.2、`docs/P003-backend-spec.md` §3.12・§4.6・§4.7・§5.4 |
| Query タブ(CR-004) | `docs/P002-frontend-spec.md` §2.2.6・§2.2.7・§3.8・§3.9、`docs/P003-backend-spec.md` §3.10・§3.11 |

## 5. 確定したコマンド

P102 で実際に実行して確認したもの(2026-09-23):

| 目的 | コマンド | 結果 |
| --- | --- | --- |
| Python 単体テスト | `cd server && uv run pytest tests/unit -q` | 122 件合格(Oracle 不要。CR-002 で MCP のテストを削除・移動して 131 → 122。2026-09-27 確認) |
| Python 1 件だけ | `cd server && uv run pytest tests/unit/oracle/test_type_format.py -q` | 14 件合格(CR-002 で `tests/unit/mcp/` から移動。2026-09-27 確認) |
| クライアント単体テスト | `cd client && npm test` | 54 件合格 |
| クライアントのビルド | `cd client && npm run build` | 成功 |
| 開発用 Oracle の疎通 | `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` | `8`(※P202 F010(CR-004)。HR に EMPLOYEE_FIGURE が加わった) |
| backend(開発) | `cd server && DBFAQ_CONFIG=../config.yaml uv run uvicorn --factory dbfaq_api.main:create_app --port 8000` | `/api/health` が ok |
| frontend(開発) | `cd client && npx vite --port 5173 --strictPort` | `/api` は 8000 へ中継 |
| compose | `docker compose up -d --build` → `curl localhost:8088/api/health` | api healthy、Oracle ok(host.docker.internal 経由) |
| 受入テストの疎通 | `cd e2e && npx playwright test tests/smoke.spec.ts` | 2 件合格 |
