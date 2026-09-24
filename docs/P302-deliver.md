# 成果物まとめ

## 1. 概要

* アプリケーション: DbFAQ v0.1.0(第 1 リリース)。Oracle のスキーマを MCP サーバ(FastMCP、stdio)経由で読み取り SQLite に保存し、ブラウザで ER 図(拡大縮小・ミニマップ・クリックで詳細へ)とテーブル詳細(スキーマ情報/データのタブ)を表示する。
* 作成日: 2026-09-23(2026-09-24 に CR-001 で更新)。実行モード: `一気通貫`(`docs/.mode`)。
* 結果: 単体テスト 185 件(Python 131、クライアント 54)、結合テスト T01〜T12、受け入れ結合テスト A01〜A08 がすべて合格(docs/test-records/20260923-0350-test-record.md、CR-001 で追加した A01 手順 8・9 と A08 は docs/test-records/20260924-2352-test-record.md)。
* リリース判定: **OK**(11 章。出荷影響「要対応」0 件、未解消の ★FIXME★ 0 件)。

## 2. 参照した成果物

* 仕様: docs/P001-requirement.md、P002-frontend-spec.md、P003-backend-spec.md、P004-traceability-matrix.md、P005-impl-plan.md、P006-test-plan.md
* 指示: docs/P007-impl-direction.md(U001〜U006)、P008-test-direction.md(T01〜T12)、P009-acceptance-direction.md(A01〜A08)
* レビュー・修正: docs/P010-design-review.md、P011-impact-analysis.md、P201-review-report.md、P202-fix-plan.md(fixed/F001〜F006)、P202-fix-plan/P202-fix-resolved.md、P202-fix-plan/P202-fix-unresolved.md(未解決なし)、P204-impact-analysis.md
* テスト記録: docs/test-records/20260923-0315-test-record.md(P103)、20260923-0320-test-record.md(P201 1 回目)、20260923-0350-test-record.md(P205)、20260924-2352-test-record.md(CR-001 の P201)
* 技術: docs/ADR.md(ADR-001〜013)、docs/ArchitectureHandbook.md、./INDEX.md、server/INDEX.md、client/INDEX.md
* 配布資産: compose.yaml、deploy/api.Dockerfile、deploy/web.Dockerfile、deploy/nginx.conf、config.example.yaml、.dockerignore、server/pyproject.toml、client/package.json、README.md、docs/BUILD_HISTORY.md
* 存在しないもの: docs/P000-concept-analysis.md(要求はプロンプトで受領)、.env.example(設定は config.yaml。compose の上書き用の環境変数は 7 章に記載)、(CR は docs/CR.md。CR-001 完了)

## 3. アプリケーション種別と配布方針

* 種別: サービス提供型システム(Web フロントエンド + API サーバ + 子プロセスの MCP サーバ + SQLite。Oracle は外部の既存 DB)。
* 配布方針: Docker Compose(web: nginx で静的配信と `/api` 中継、ホストの 8088 のみ公開/api: uvicorn 1 ワーカー + MCP 子プロセス、非公開、SQLite は名前付きボリューム `dbfaq-data`)。ADR-012。
* 実行前チェック:
  1. P002・P003: あり
  2. P006: あり
  3. テスト記録: あり(3 件)
  4. 修正結果: P202-fix-resolved.md・P202-fix-unresolved.md あり
  5. 種別の推定: 可(上記)
  6. 本書: 新規作成
  7. フロントエンドの接続前提と配布トポロジー: クライアントは相対パス `/api`(`client/src/api/client.ts` の `fetch('/api' + path)`)で同一オリジン前提。配布トポロジーは nginx が同じオリジンで `/api/` を api コンテナへ中継する(`deploy/nginx.conf`)。**一致している**。受け入れ結合テスト A01〜A06 はブラウザ(Playwright)から compose の web(同一オリジン)に対して実行しており、この経路で検証済み。
  8. 再起動耐性: A04 で確認済み(`docker compose restart api`、`down`/`up` でスナップショット保持、`schema_migrations` 1 件、起動時例外なし)。記録: docs/test-records/20260923-0320-test-record.md の A04、docs/test-records/20260923-0350-test-record.md(A01〜A06 を 2 回)。

## 4. 仕様・テスト・テスト実装の対応表

テスト実装の場所: 単体 `server/tests/unit`・`client/src/**/*.test.ts(x)`、結合 `server/tests/integration/test_t0N_*.py`(T01〜T09)・T10/T11 は curl 手順・T12 は compose 手順、受入 `e2e/tests/a0N-*.spec.ts`・`e2e/scripts/*.sh`。証跡は特記なければ docs/test-records/20260923-0350-test-record.md。

| 仕様ID/項目 | 要求ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 | 出荷影響 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | REQ-SCREEN-001 | SC-01 ER 図のノード(列・PK/FK/NOT NULL の印) | P006 §2.1 SC-01 | A01、U004-T4 | `e2e/tests/a01-er-diagram.spec.ts`、`client/src/pages/ErDiagramPage.test.tsx` | PASS | 同上 | OK | - |
| REQ-SCREEN-002 | REQ-SCREEN-002 | リレーションの線(複合 FK も 1 本、制約名ラベル、自己参照) | P006 §2.1 | A01(線 10 本)、U004-T3、U002-T3 | a01、`client/src/er/buildGraph.test.ts`、`server/tests/unit/mcp/test_snapshot.py` | PASS | 同上 | OK | - |
| REQ-SCREEN-003 | REQ-SCREEN-003 | 拡大・縮小・パンのうち、ボタンによる拡大・縮小・全体表示 | P006 §2.1 | A01 手順 4 | a01 | PASS | 同上 | OK | - |
| REQ-SCREEN-003-倍率範囲 | REQ-SCREEN-003 | 倍率の上下限 10%〜200% とホイール・ピンチ操作 | P006 §2.1 | A05(ホイールで倍率が変わることのみ) | a05 large | PASS(一部) | 同上 | NO_TEST_IMPL | 自明: `ErDiagramPage.tsx` で `minZoom={0.1} maxZoom={2}` を React Flow に渡しており、上下限の適用はライブラリの仕様。ホイール操作は A05 で確認 |
| REQ-SCREEN-004 | REQ-SCREEN-004 | 全体の略図(ミニマップ)の表示 | P006 §2.1 | A01 手順 3 | a01 | PASS | 同上 | OK | - |
| REQ-SCREEN-004-操作 | REQ-SCREEN-004 | ミニマップ上のドラッグ・ホイールで表示範囲が移る | P006 §2.1 | - | - | - | - | NO_TEST_IMPL | 自明: `<MiniMap pannable zoomable />` の指定のみで React Flow が提供する機能(自前のロジックなし) |
| REQ-SCREEN-005 | REQ-SCREEN-005 | テーブルのクリックで SC-02 へ | P006 §2.1 | A01 手順 6、U004-T4 | a01、ErDiagramPage.test | PASS | 同上 | OK | - |
| REQ-SCREEN-006 | REQ-SCREEN-006 | テーブル名検索 | P006 §2.1 | A01 手順 5、U004-T4 | a01、`client/src/er/TableSearch.test.tsx` | PASS | 同上 | OK | - |
| REQ-SCREEN-007 | REQ-SCREEN-007 | Oracle から再読み込み(成功通知・失敗時に前回を残す) | P006 §2.1 | A01、A03、U004-T4、U003-T4 | a01、a03、ErDiagramPage.test、`server/tests/unit/api/test_api.py` | PASS | 同上 | OK | - |
| REQ-SCREEN-007-処理中 | REQ-SCREEN-007 | 読み込み中はボタンを押せない表示 | P006 §2.1 | U003-T4(409 の API 側) | test_api.py::test_refresh_in_progress | PASS | 同上 | NO_TEST_IMPL | 自明: ボタンは `loading`・`disabled={refresh.isPending}`(Mantine の Button は loading 中クリック不可)。二重実行はサーバ側でも 409 で防いでおり単体テスト済み |
| REQ-SCREEN-008 | REQ-SCREEN-008 | 未取得・0 件のときの表示 | P006 §2.1 | A01 手順 1、U004-T4 | a01、ErDiagramPage.test | PASS | 同上 | OK | - |
| REQ-SCREEN-009 | REQ-SCREEN-009 | 取得日時の表示 | P006 §2.1 | A01 手順 2、U004-T4 | a01、AppShell.test | PASS | 同上 | OK | - |
| REQ-SCREEN-009-ドラッグ | REQ-SCREEN-009 | ノードのドラッグ(クリック扱いにならない、位置は保存しない) | P006 §2.1「ノードのドラッグ」 | A01 手順 8・9 | `e2e/tests/a01-er-diagram.spec.ts` の「ノードのドラッグ」 | PASS | docs/test-records/20260924-2352-test-record.md | OK | -(CR-001 で追加) |
| REQ-SCREEN-010 | REQ-SCREEN-010 | タブ切替と URL の保持 | P006 §2.1 SC-02 | A02 手順 4・6、U005-T1 | a02、TableDetailPage.test | PASS | 同上 | OK | - |
| REQ-SCREEN-011 | REQ-SCREEN-011 | スキーマ情報タブ | P006 §2.1 | A02 手順 1・2、U005-T2、T06 | a02、SchemaTab.test、test_t06 | PASS | 同上 | OK | - |
| REQ-SCREEN-012 | REQ-SCREEN-012 | 外部キー先・参照元への遷移 | P006 §2.1 | A02 手順 2、U005-T2 | a02、SchemaTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-013 | REQ-SCREEN-013 | データタブのうち 50 行ページ、主キー順/ROWID 順、NULL 表示、取得時間、再読み込み | P006 §2.1 | A02 手順 4〜7、U005-T3、T02 | a02、DataTab.test、test_t02 | PASS | 同上 | OK | - |
| REQ-SCREEN-013-LOB | REQ-SCREEN-013 | LOB・長い文字列の 1,000 文字切り詰めと表示 | P006 §2.1 | U002-T1、U005-T3 | `server/tests/unit/mcp/test_values.py::test_text_truncation`・`::test_bytes`、DataTab.test「null と文字列 "(null)" を区別し、切り詰めたセルに title」 | PASS | 単体テスト | NO_TEST_CASE | 代替検証: HR に LOB 列が無いため結合・受入では確認できない。上記の単体テストで文字列化と画面表示をそれぞれ確認 |
| REQ-SCREEN-014 | REQ-SCREEN-014 | 異常時の表示(テーブル無し、Oracle エラー時もスキーマ情報は使える、0 行) | P006 §2.1 | A02 手順 8、A03、U005 | a02、a03、DataTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-015 | REQ-SCREEN-015 | 共通ヘッダ | P006 §2.1 | A01、U004-T4 | a01、AppShell.test | PASS | 同上 | OK | - |
| REQ-API-001 | REQ-API-001 | GET /api/schema | P006 §2.1 | T06、T10、U003-T4 | test_t06、test_api.py | PASS | 同上 | OK | - |
| REQ-API-002 | REQ-API-002 | POST /api/schema/refresh | P006 §2.1 | T06、T08、T10、A01、A03 | test_t06、test_t08、a01、a03 | PASS | 同上 | OK | - |
| REQ-API-003 | REQ-API-003 | GET /api/schema/tables/{owner}/{table} | P006 §2.1 | T06、T11、A02 | test_t06、a02 | PASS | 同上 | OK | - |
| REQ-API-004 | REQ-API-004 | GET /api/schema/tables/{owner}/{table}/rows(limit 最大 500) | P006 §2.1 | T07、T11、A02 | test_t07、a02 | PASS | 同上 | OK | - |
| REQ-API-005 | REQ-API-005 | GET /api/health | P006 §2.1 | T08、T09、T12、A03 | test_t08、test_t09 | PASS | 同上 | OK | - |
| REQ-MCP-001 | REQ-MCP-001 | get_schema_snapshot | P006 §2.1 | T01、U002-T3 | test_t01、test_snapshot.py | PASS | 同上 | OK | - |
| REQ-MCP-002 | REQ-MCP-002 | get_table_rows(実在確認・クォート・バインド変数) | P006 §2.1 | T02、U002-T4 | test_t02、test_rows.py | PASS | 同上 | OK | - |
| REQ-MCP-003 | REQ-MCP-003 | ping | P006 §2.1 | T04、T08 | test_t04、test_t08 | PASS | 同上 | OK | - |
| REQ-MCP-004 | REQ-MCP-004 | 読み取り専用トランザクションと必ず ROLLBACK | P006 §2.1・§2.2 | T03、A06 手順 1、U002-T2 | test_t03、a06-security.sh、test_db.py | PASS | 同上 | OK | - |
| REQ-ARCH-001 | REQ-ARCH-001 | Oracle へのアクセスはすべて MCP 経由 | - | - | - | - | - | NO_TEST_PLAN | 自明: `server/src/dbfaq_api` に `oracledb` の import が 0 件(2026-09-23 に grep で確認)。backend は Oracle に接続する手段を持たない |
| REQ-ARCH-002 | REQ-ARCH-002 | MCP は stdio、backend の子プロセス | P006 §2.1 | T05、T09、A04 手順 7 | test_t05、test_t09、a04-restart.sh | PASS | 同上 | OK | - |
| REQ-ARCH-003 | REQ-ARCH-003 | スキーマ情報を SQLite に保存し再起動後も保持 | P006 §2.3 | A04、U003-T1・T2 | a04-restart.sh、test_migrate.py | PASS | 同上 | OK | - |
| REQ-ARCH-004 | REQ-ARCH-004 | 接続パラメータを設定ファイル(Git 管理外)に保持 | P006 §2.1 | U001-T2、T12、A06 手順 5 | test_config.py、a06-security.sh | PASS | 同上 | OK | - |
| REQ-ARCH-005 | REQ-ARCH-005 | Python は uv で管理 | - | - | 全 Python テストを `uv run` で実行 | PASS | 同上 | OK | - |
| REQ-ARCH-006 | REQ-ARCH-006 | React / FastAPI / FastMCP / python-oracledb | - | - | ビルドとテスト全体 | PASS | 同上 | OK | - |
| REQ-ARCH-007 | REQ-ARCH-007 | Docker Compose で起動、コンテナから Oracle へは host.docker.internal | P006 §2.2 | T12、A01〜A06 | T12 の手順、run-suite.sh | PASS | 同上 | OK | - |
| REQ-ARCH-008 | REQ-ARCH-008 | MCP の設計は ../OracleSearchMCP を参考にする | - | - | - | - | - | NO_TEST_PLAN | 自明: 設計上の要求であり動作要件ではない。踏襲した箇所(読み取り専用トランザクション、辞書の結合)はコード・P003 に出典を明記 |
| REQ-NFR-001 | REQ-NFR-001 | 性能(HR の ER 図 1 秒・refresh 10 秒・rows + 1 秒、300 表の ER 図 3 秒) | P006 §2.2 | A05 | a05-perf-api.sh、a05-performance.spec.ts | PASS | 同上(HR 表示 299 ms、300 表 2,033 ms 等) | OK | - |
| REQ-NFR-002 | REQ-NFR-002 | タイムアウト(既定 30 秒、設定で変更可) | P006 §2.2 | T04 | test_t04::test_timeout_then_recover(1 秒に設定) | PASS | 同上 | OK | - |
| REQ-NFR-003 | REQ-NFR-003 | 可用性(restart、Oracle 無しでも起動、MCP 子プロセスの再起動) | P006 §2.3 | A03、A04、T08、T09 | a03、a04、test_t08、test_t09 | PASS | 同上 | OK | - |
| REQ-NFR-004 | REQ-NFR-004 | セキュリティのうち認証なしの前提での公開範囲・読み取りのみ・パスワード非露出(TLS は副 ID へ分離) | P006 §2.2 | A06、T12、T04 | a06-security.sh、T12 の手順、test_t04 | PASS | 同上 | OK | - |
| REQ-NFR-004-TLS | REQ-NFR-004 | TLS 終端 | P006 §2.2 | - | - | - | 本書 10 章 | BLOCKED | 本番検証: TLS は運用環境のリバースプロキシで終端する前提(P003 §6)で、本環境に該当構成が無い |
| REQ-NFR-005 | REQ-NFR-005 | スケーラビリティのうち SQLite WAL と refresh の排他(同時 10 名の負荷は副 ID へ分離) | P006 §2.2 | U003-T1・T4 | test_migrate.py::test_foreign_keys_pragma、test_api.py::test_refresh_in_progress | PASS | 単体テスト | OK | - |
| REQ-NFR-005-同時10名 | REQ-NFR-005 | 同時利用者 10 名でエラー 0・性能目標内(P001 §8.4) | P006 §2.2「同時利用」 | A08 | `e2e/scripts/a08-concurrency.sh`(`server/scripts/a08_concurrent_load.py`) | PASS(schema 最大 0.273 s、detail 0.251 s、rows オーバーヘッド 0.095 s、エラー 0) | docs/test-records/20260924-2352-test-record.md | OK | -(CR-001 で追加) |
| REQ-NFR-006 | REQ-NFR-006 | ログ(JSON、backend は stdout、MCP は stderr)と /api/health | P006 §2.2 | T05、U001-T3、A04 手順 6 | test_t05、test_logging.py | PASS | 同上 | OK | - |
| REQ-TEST-001 | REQ-TEST-001 | テスト方針(pytest / Vitest / 結合 / Playwright、HR を変更しない、2 回実行) | P006 | 全体 | 全テスト、A06 のチェックサム、A07 | PASS | 同上 | OK | - |

* P004 の全 39 要求 ID が上表に現れることを確認した。
* P004 §2 の過剰実装 3 件(ヘッダの Oracle 状態表示、ページ番号の URL 保持、関数索引の式の表示)も実装・テスト済み(A01・A03、A02、test_snapshot.py)。要求書へ追加するか残すかは人間の判断事項として 10 章に記載する。

## 5. バージョン情報とビルド履歴

| 対象 | バージョンの定義 | 実行時の確認方法 |
|---|---|---|
| backend・MCP サーバ | `server/pyproject.toml` の `project.version = "0.1.0"`、`dbfaq_api.__version__` | `curl http://localhost:8088/api/health` の `backend.version` |
| フロントエンド | `client/package.json` の `version = "0.1.0"` | 画面には表示しない(10 章) |
| E2E | `e2e/package.json` の `version = "0.1.0"` | - |

* ビルド履歴: [docs/BUILD_HISTORY.md](./BUILD_HISTORY.md)(B001〜B004)。CR-001 はテストの追加だけでアプリケーションの画面・API・データ契約を変えていないため、版数は 0.1.0 のまま。B001〜B003 の作業ツリーは 9579d85 としてコミット済み。B004(CR-001)の変更はその次のコミットに含まれる。

## 6. 配布資産一覧

| 資産 | 内容 | 状態 |
|---|---|---|
| `compose.yaml` | web(8088 公開)・api(非公開、host-gateway、config.yaml を読み取り専用マウント、ボリューム `dbfaq-data:/data`、healthcheck)、両方 `restart: unless-stopped` | 整備済み・起動確認済み |
| `deploy/api.Dockerfile` | python:3.12-slim + uv、非 root(uid 10001)、uvicorn 1 ワーカー | 整備済み・ビルド確認済み |
| `deploy/web.Dockerfile`、`deploy/nginx.conf` | node:22 でビルド → nginx:1.27、`/api/` 中継(120 秒)、SPA フォールバック | 整備済み・ビルド確認済み |
| `config.example.yaml` | 設定ファイルのひな型 | 整備済み |
| `.dockerignore` | config.yaml・data・node_modules 等を除外 | 整備済み(イメージにパスワードが入らないことを A06 で確認) |
| `README.md` | 概要と最短の起動手順 | 整備済み |
| マイグレーション | api の起動時に自動適用(`schema_migrations` による差分適用) | 整備済み・再起動耐性を A04 で確認 |

## 7. 起動・実行手順

### Docker Compose 起動手順

1. 前提ソフトウェア: Docker Engine と Docker Compose v2。Oracle(19c 以降を想定。検証は 23.26)に TCP で到達できること。
2. 設定ファイルを作る: `cp config.example.yaml config.yaml` として、`oracle.host`・`port`・`service_name`・`user`・`password`・`schema` を記入する(`config.yaml` は Git 管理外。ファイルの権限はサーバの運用者だけが読めるようにする)。
3. 環境変数(任意): `DBFAQ_PORT`(公開ポート。既定 8088)、`DBFAQ_ORACLE_HOST`(コンテナから見た Oracle のホスト。既定 `host.docker.internal` = Docker ホスト。Oracle が別サーバならそのホスト名)。`DBFAQ_ORACLE_PASSWORD` でパスワードを上書きすることもできる。
4. ビルドと起動: `docker compose up -d --build`
5. ヘルスチェック: `curl http://localhost:8088/api/health` → `"status":"ok"`(`oracle.status` が `error` なら `message` と `docker compose logs api` を確認)。`docker compose ps` で api が `healthy`。
6. 初期データ: SQLite のマイグレーションは起動時に自動適用される。スキーマ情報はブラウザで [Oracle から読み込む] を押して取り込む(または `curl -X POST http://localhost:8088/api/schema/refresh`)。
7. 動作確認: ブラウザで `http://<サーバ>:8088/` を開き、ER 図が表示され、テーブルをクリックして詳細が見られること。
8. 停止・再起動: `docker compose down`(スナップショットはボリュームに残る)/`docker compose down -v`(ボリュームも削除)/`docker compose restart`。
9. バックアップ: SQLite は Oracle から再読み込みで作り直せる派生データのため必須ではない。必要なら `docker compose cp api:/data/dbfaq.sqlite3 ./backup.sqlite3`。

### 実運用に向けた推奨

* Oracle の接続ユーザーは読み取り専用ユーザーにする(例: `CREATE USER dbfaq_ro ...; GRANT CREATE SESSION TO dbfaq_ro; GRANT SELECT ON <schema>.<table> TO dbfaq_ro;` と、辞書を読むための `SELECT_CATALOG_ROLE` 等は環境に合わせて付与)。アプリは読み取り専用トランザクションで防いでいるが、二重の防御になる。対象スキーマは `oracle.schema` で指定する。
* 認証が無いため、ネットワーク(ファイアウォール・リバースプロキシ)でアクセス元を制限する。TLS が必要なら前段のリバースプロキシで終端する。

## 8. テスト実行手順

| 種類 | コマンド | 合格条件 |
|---|---|---|
| Python 単体 | `cd server && uv run pytest tests/unit -q` | 131 passed |
| クライアント単体 | `cd client && npm ci && npm test` | 54 passed |
| クライアントのビルド | `cd client && npm run build` | 成功 |
| 結合 T01〜T09(実 Oracle) | `cd server && uv run pytest tests/integration -v` | 17 passed(`config.yaml` の Oracle に接続できること) |
| 結合 T10・T11 | backend(8000)と `npx vite --port 5173` を起動し、`docs/P008-test-direction/T10-*.md`・`T11-*.md` の curl を実行 | 各手順が期待どおり |
| 結合 T12 | `docs/P008-test-direction/T12-compose-stack.md` の手順 | 各手順が期待どおり |
| 受け入れ結合 A01〜A08 | `cd e2e && npm ci && npx playwright install chromium` の後、`bash e2e/scripts/run-suite.sh`(A01〜A06・A08)を 2 回実行して出力を比較 | すべて PASS で 2 回の出力が同一 |

* テスト結果の格納先: `docs/test-records/`、Playwright の失敗時の証跡は `e2e/test-results/`・`e2e/playwright-report/`。
* 注意: `run-suite.sh` は `docker compose down -v` でボリュームを消してから始める(ベースライン復元)。運用中の環境では実行しない。

## 9. 最終確認結果

* 2026-09-23 03:30〜03:50 に P205 として全テストを実行: 単体 185 件合格、T01〜T09 を 2 回続けて 17 passed、T10〜T12 合格、A01〜A06 を 2 回続けて全 PASS・出力同一(A07 PASS)。
* compose でのビルド・起動・ヘルスチェック・画面表示を実際に確認済み(Docker は利用可能だった)。
* HR のデータはスイートの前後でチェックサムが一致(A06)。
* 2026-09-24 23:47〜23:52 に CR-001 として、A01(ドラッグの手順 8・9 を追加)〜A06・A08(同時 10 名、新規)を 2 回続けて実行し、すべて PASS・出力同一(A07 PASS)(docs/test-records/20260924-2352-test-record.md)。アプリケーションコードは変えていないため、単体・結合は B003 の結果を引き継ぐ(単体 Python 131 件は 2026-09-24 に再実行して合格)。

## 10. 未整備事項・人間による確認事項

### 10.1 出荷影響「要対応」(0 件)

* なし。以前の 2 件(REQ-SCREEN-009-ドラッグ、REQ-NFR-005-同時10名)は CR-001 でテストを追加し、合格した(4 章)。

### 10.2 本番検証・代替検証・自明とした項目

* 本番検証: REQ-NFR-004-TLS(TLS 終端は前段のリバースプロキシ。稼働前に運用側で確認する)。
* 代替検証: REQ-SCREEN-013-LOB(HR に LOB が無い。単体テストで確認)。
* 自明: REQ-SCREEN-003-倍率範囲、REQ-SCREEN-004-操作、REQ-SCREEN-007-処理中、REQ-ARCH-001、REQ-ARCH-008(理由は 4 章)。

### 10.3 既知の制約(判断済み)

* ★ACCEPTED★ LOB を全体でメモリに読み込む(ADR-005)/★ACCEPTED★ OFFSET 方式のページ送り(ADR-006)。詳細は docs/ArchitectureHandbook.md §9。
* Oracle に接続できないとき、画面・API のメッセージは `DPY-4005: timed out waiting for the connection pool ...` となり、根本原因(接続拒否など)は直接は分からない(F006 の残課題)。ヘッダの Oracle 状態と `docker compose logs api` で判断する。
* 同時の Oracle 問い合わせが `pool_max`(既定 4)を超えると、超えた分は `connect_timeout_sec`(既定 10 秒)待って DPY-4005 で失敗する(F006 による変更。以前は無期限に待った)。
* uvicorn は 1 ワーカー固定(ADR-001)。同時 10 名は A08 で確認済み。ただし api の起動直後など接続プールが広がる前は、データタブの応答が遅くなる(A08 の単独実行でオーバーヘッドの最大 0.916 秒。目標 1 秒に対して余裕が小さい)。気になる場合は `config.yaml` の `pool_min` を上げる。
* 接続拒否の検証(T08)以外の Oracle 障害(ネットワーク断の途中など)は未検証。
* 開発・テストで使った接続ユーザー hr は書き込み権限を持つ。本番は読み取り専用ユーザーを推奨(7 章)。
* フロントエンドのバージョンは画面に表示していない(backend のバージョンは `/api/health` で確認できる)。
* ヘッドレスのブラウザ環境によっては ER 図の 🔑・🔗 が絵文字フォントの不足で表示されない(Windows・macOS の通常のブラウザでは表示される)。

### 10.4 要求書に無い実装(P004 §2 の過剰実装)

* ヘッダの Oracle 状態表示(60 秒ごとの health 取得)、データタブのページ番号の URL 保持、関数索引の式の表示。いずれも実装・テスト済み。要求書に追加するか、削るかを人間が判断する(CR の起票候補)。

### 10.5 ★FIXME★ 一覧(58 件。未解消 0 件)

**未解消の★FIXME★: 0件。** 2026-09-24 に人間が下表の 58 件をすべて確認し、Agent の想定をそのまま受け入れた。各箇所の ★FIXME★ は ★ACCEPTED★ に書き換え、検討内容・承認理由・残存リスクを同じ行に記載した。同じ判断で `server/src/dbfaq_mcp/snapshot.py` の `iso_utc` の注記(#50 と同じ論点)も ★ACCEPTED★ にした。#57 は指示文中の手順の説明であり、印ではないため書き換えていない。

下表は受け入れの記録として残す。「CR 起票候補か」の ○ は、受け入れの前提(業務の条件)が変わったときに CR で見直す候補を示す。

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 1 | `docs/P001-requirement.md` 1. アプリケーションの概要 | 解決する課題 / 運用中にクエリを組み立てるとき、テーブル間の関係や列の定義を確認する手段が SQL*Plus などでのデータディクショナリ検索しかなく、手間がかかる。ER 図とテーブル詳細を画面で確認できるようにし、将来の FAQ(ク… | ○ |
| 2 | `docs/P001-requirement.md` 1. アプリケーションの概要 | 対象DB / Oracle Database。接続先は1つで、設定ファイルで指定する  接続先を1つに限定したのはAgentの想定 | ○ |
| 3 | `docs/P001-requirement.md` 2. システムの前提 | 想定ユーザー数 / 同時利用者 1〜10名程度 | ○ |
| 4 | `docs/P001-requirement.md` 2. システムの前提 | 想定スキーマ規模 / 1スキーマあたりテーブル 〜300、列 〜5,000 まで ER 図を実用的な速さで表示できること | ○ |
| 5 | `docs/P001-requirement.md` 2. システムの前提 | 認証・権限管理 / なし(人間の指示)。社内ネットワーク内の限られた端末からだけアクセスされる前提とする  ネットワーク側でアクセス元を制限する前提はAgentの想定 | ○ |
| 6 | `docs/P001-requirement.md` 2. システムの前提 | コンテナから Oracle への接続 / Oracle がホスト上で動いている場合、コンテナからは `localhost` で届かないため、compose 用の設定ファイルでは `host.docker.internal`(`extra… | - |
| 7 | `docs/P001-requirement.md` 3.1 全体アーキテクチャ | MCP サーバは単体でも `uv run` で起動でき、Claude Desktop などの stdio 対応 MCP クライアントから使うこともできる  単体利用はAgentの想定(第1リリースの必須要件ではない) | ○ |
| 8 | `docs/P001-requirement.md` 3.2 フロントエンド(人間の指示: おまかせ) | elkjs / ER 図の自動レイアウト(テーブルの配置と、リレーション線が重なりにくい配置) | - |
| 9 | `docs/P001-requirement.md` 3.2 フロントエンド(人間の指示: おまかせ) | Mantine / タブ、表、ボタン、通知などの UI 部品 | - |
| 10 | `docs/P001-requirement.md` 3.2 フロントエンド(人間の指示: おまかせ) | npm / フロントエンドの依存管理 | - |
| 11 | `docs/P001-requirement.md` 3.3 バックエンド・MCP サーバ | Python 3.12 / CLAUDE.md の方針  バージョンはAgentの想定 | - |
| 12 | `docs/P001-requirement.md` 3.3 バックエンド・MCP サーバ | uv / Python のパッケージ管理(人間の指示)。backend と MCP サーバを1つの uv プロジェクト(`server/`)で管理する  プロジェクト構成はAgentの想定(P003 §1.2) | - |
| 13 | `docs/P001-requirement.md` 3.3 バックエンド・MCP サーバ | SQLAlchemy 2.x + SQLite / 人間の指示(SQLite)。ORM でテーブル定義とテストを簡単にする | - |
| 14 | `docs/P001-requirement.md` 3.3 バックエンド・MCP サーバ | pydantic-settings + PyYAML / `config.yaml` の読み込みと型チェック | - |
| 15 | `docs/P001-requirement.md` SC-01 ER 図 | 出力 / テーブルのノード / 対象はテーブルのみ(ビューは ER 図に含めない) ビューを除外したのはAgentの想定。テーブル名、テーブルのコメント、列の一覧(列名・データ型・主キー/外部キーの印・NOT NULL の印) | ○ |
| 16 | `docs/P001-requirement.md` SC-01 ER 図 | 出力 / リレーションの線 / 外部キー 1 本(複合外部キーも 1 本)につき 1 本。子テーブルから親テーブルへ向かう。線の近くに制約名を表示する | - |
| 17 | `docs/P001-requirement.md` SC-01 ER 図 | 操作 / 拡大・縮小 / マウスホイール、ピンチ、画面上のボタン(+ / − / 全体表示)。倍率は 10%〜200% | - |
| 18 | `docs/P001-requirement.md` SC-01 ER 図 | 操作 / ノードのドラッグ / テーブルの位置を手で動かせる。位置は保存しない(再表示すると自動レイアウトに戻る) | - |
| 19 | `docs/P001-requirement.md` SC-01 ER 図 | 操作 / テーブル名検索 / 入力したテーブル名のノードへ表示を移し、強調する | - |
| 20 | `docs/P001-requirement.md` SC-02 テーブル詳細 | 操作 / タブ切替 / 「スキーマ情報」「データ」。選択中のタブは URL のクエリ(`?tab=data`)に持ち、再読み込みしても保たれる | - |
| 21 | `docs/P001-requirement.md` スキーマ情報タブ(SQLite から表示) | 出力 / 一意制約 / 制約名と列 | - |
| 22 | `docs/P001-requirement.md` スキーマ情報タブ(SQLite から表示) | 出力 / インデックス / インデックス名、一意かどうか、列 | - |
| 23 | `docs/P001-requirement.md` スキーマ情報タブ(SQLite から表示) | 出力 / 行数の目安 / 統計情報の NUM_ROWS と統計の取得日(統計が無ければ「統計なし」) | - |
| 24 | `docs/P001-requirement.md` データタブ(Oracle から MCP 経由で表示。SQLite には保存しない) | 出力 / データの表 / 列名を見出しにした表。1 ページ 50 行 | ○ |
| 25 | `docs/P001-requirement.md` データタブ(Oracle から MCP 経由で表示。SQLite には保存しない) | 出力 / 並び順 / 主キーの昇順(主キーが無いテーブルは ROWID 順)。ページをまたいで行の順番が変わらないようにするため | - |
| 26 | `docs/P001-requirement.md` データタブ(Oracle から MCP 経由で表示。SQLite には保存しない) | 出力 / 値の表示 / NULL は「(null)」と区別して表示する。日付は `YYYY-MM-DD HH:MM:SS`。LOB と長い文字列は先頭 1,000 文字で切って省略記号を付ける | - |
| 27 | `docs/P001-requirement.md` データタブ(Oracle から MCP 経由で表示。SQLite には保存しない) | 操作 / ページ送り / 前へ / 次へ。次のページがあるかどうかで「次へ」を押せるかを決める(全件数は数えない。大きなテーブルで COUNT(*) を避けるため) | - |
| 28 | `docs/P001-requirement.md` 8.1 性能 | ER 図の表示(SQLite から) / HR(7 テーブル)で 1 秒以内。300 テーブルで 3 秒以内 | ○ |
| 29 | `docs/P001-requirement.md` 8.1 性能 | スキーマの再読み込み(Oracle から) / HR で 10 秒以内 | - |
| 30 | `docs/P001-requirement.md` 8.1 性能 | データタブの 1 ページ表示 / Oracle の処理時間 + 1 秒以内 | - |
| 31 | `docs/P001-requirement.md` 8.1 性能 | Oracle 問い合わせのタイムアウト / 既定 30 秒。`config.yaml` で変更できる | ○ |
| 32 | `docs/P001-requirement.md` 8.2 可用性 | 単一ホストの Docker Compose で動かす。冗長化はしない | ○ |
| 33 | `docs/P001-requirement.md` 8.2 可用性 | MCP サーバの子プロセスが異常終了した場合、backend は次の呼び出し時に起動し直す | - |
| 34 | `docs/P001-requirement.md` 8.3 セキュリティ | 実運用では、接続ユーザーを読み取り専用ユーザー(`CREATE SESSION` と対象テーブルへの `SELECT` 権限のみ)にすることを導入手順書で推奨する | ○ |
| 35 | `docs/P001-requirement.md` 8.3 セキュリティ | TLS はアプリでは終端しない。必要なら運用環境のリバースプロキシで終端する | ○ |
| 36 | `docs/P001-requirement.md` 8.4 スケーラビリティ・同時利用者数 | 同時利用者 10 名程度を想定する。SQLite は WAL モードで使う。スキーマの再読み込みが同時に要求された場合は 1 つだけ実行し、ほかは実行中であることを返す | ○ |
| 37 | `docs/P001-requirement.md` 8.5 ログ出力と監視 | 外部の監視基盤との連携はしない。`GET /api/health` を外部の監視から使える形にしておく | ○ |
| 38 | `docs/P001-requirement.md` 9. テスト方針 | 受入テスト**: docker compose で全体を起動し、Playwright でブラウザ操作(初回読み込み → ER 図表示 → 拡大縮小・ミニマップ → テーブルをクリック → スキーマ情報タブ → データタブのページ送り →… | - |
| 39 | `docs/P002-frontend-spec.md` 1.1 レイアウト | Oracle 状態 / `GET /api/health` の `oracle.status` を色付きの丸で表示(ok=緑、error=赤、確認中=灰)。マウスを乗せると DB バージョン・接続先(host:port/service、… | - |
| 40 | `docs/P002-frontend-spec.md` 1.2 ルーティング | `/tables/:owner/:table?tab=data&page=N` / SC-02 データタブ / `page` は 1 始まり。省略時・不正値(整数でない、1 未満)のときは 1  ページ番号を URL に持たせるのはAg… | - |
| 41 | `docs/P002-frontend-spec.md` 2.1.2 ER 図の描画規則 | 列数の多いテーブル / 列が 30 を超える場合は先頭 30 列を表示し、末尾に「… 他 N 列」と表示する | - |
| 42 | `docs/P002-frontend-spec.md` 2.1.2 ER 図の描画規則 | 別スキーマへの外部キー / 参照先テーブルがノードに無い(`to_owner` が対象スキーマと異なる)場合、線は描かない。SC-02 の外部キー一覧には表示する | - |
| 43 | `docs/P002-frontend-spec.md` 2.1.2 ER 図の描画規則 | 自動レイアウト / elkjs の `layered` アルゴリズム、方向は左→右(親テーブルが右)。ノードの幅・高さは列数とテーブル名の長さから算出する | - |
| 44 | `docs/P002-frontend-spec.md` 2.1.3 操作 | テーブル名検索 / 入力中に候補(テーブル名の部分一致、大文字小文字を区別しない、最大 20 件)を表示する。候補を選ぶと、そのノードを画面中央に移動・拡大(倍率 100%)し、2 秒間強調表示する。Enter で先頭候補を選ぶ。候補の… | - |
| 45 | `docs/P002-frontend-spec.md` 2.2.4 入力のバリデーション | URL の `page` / 1 以上の整数。`(page-1)*50` が 100,000 以下 / 1 として扱う。上限超えは 1 として扱う | - |
| 46 | `docs/P002-frontend-spec.md` 3.5 `GET /api/schema/tables/{owner}/{table}/rows` | `offset` / 整数 / 0 / 0 以上 100,000 以下  上限はAgentの想定(大きな OFFSET は Oracle 側で遅くなるため) | - |
| 47 | `docs/P002-frontend-spec.md` 3.6 セル値の表示用文字列(rows) | INTERVAL / Python の表現を文字列化(例 `3 days, 4:00:00`) | ○ |
| 48 | `docs/P002-frontend-spec.md` 3.6 セル値の表示用文字列(rows) | 上記以外(XMLTYPE、JSON、VECTOR、オブジェクト型など) / 文字列化して先頭 1,000 文字 | ○ |
| 49 | `docs/P002-frontend-spec.md` 4.2 テーブル定義 | column_name / TEXT / NOT NULL / 関数索引は式の文字列(ALL_IND_EXPRESSIONS) | - |
| 50 | `docs/P003-backend-spec.md` 3.5 ツール `get_schema_snapshot` | `LAST_ANALYZED` は Oracle の DATE(タイムゾーンなし)。DB サーバの時刻として UTC とみなして `Z` を付ける  DB のタイムゾーン設定によってはずれる | ○ |
| 51 | `docs/P003-backend-spec.md` 4.2 状態の保持 | 再読み込みの実行中フラグ / アプリケーション(プロセス) / `asyncio.Lock`。`locked()` なら 409 を返す。uvicorn は 1 ワーカーで動かす前提(複数ワーカーにすると MCP 子プロセスもワーカーご… | - |
| 52 | `docs/P003-backend-spec.md` 6. 非機能要件の実現と委譲 | 可用性: バックアップ / SQLite は再読み込みで作り直せる派生データなので、アプリはバックアップ機能を持たない  / ボリュームの扱いは P302 の手順書 | ○ |
| 53 | `docs/P005-impl-plan.md` U001 foundation | インフラ / 開発・テスト用 Oracle は既存のコンテナ(`oracle-db-free`)を使う。本プロジェクトの compose には含めない  P001 §2 の「人間が指定した既存の Oracle」に従う | - |
| 54 | `docs/P006-test-plan.md` 2.2 非機能観点 | 性能(規模) / 300 表・5,000 列の偽スナップショットを SQLite に入れ、`GET /api/schema` < 3 秒、ブラウザでの ER 図表示 < 3 秒 / システム(P009)  大規模な実 Oracle スキ… | ○ |
| 55 | `docs/P006-test-plan.md` 3.1 テスト環境 | frontend の API / Vitest では `fetch` を偽物(`vi.fn` で差し替える)にする。MSW は使わない | - |
| 56 | `docs/P006-test-plan.md` 3.3 実行コマンド(予定) | 以下は予定であり、P102/P103 で実際に実行して確認した後に P007/P008 の各文書・P101 に確定版を記載する  未実行 | -(確定したコマンドは P101 §5・本書 8 章に記載済み) |
| 57 | `docs/P007-impl-direction/U003-backend-api.md` 【次タスクに進む前の停止条件】 | 3 回自己修正しても合格しない場合は停止して報告する。子プロセスの終了検出が FastMCP の仕様上できない等、設計の前提が崩れた場合は  を付けて記録し、再接続の挙動を最小限(次の呼び出しで必ず作り直す)にして進む。 | -(指示文中の手順の説明で、想定で補った記述ではない) |
| 58 | `docs/ArchitectureHandbook.md` 9. 既知の制約・技術的負債 | `LAST_ANALYZED` は DB のタイムゾーンを UTC とみなしている (P003 §3.5)。 | ○ |

* 補足: `docs/P001-requirement.md` §3.3 の「SQLAlchemy 2.x + SQLite / ORM で…」は、設計(P003 §1.2、ADR-008)で ORM を使わず SQLAlchemy Core にした。P001 の記述は更新していない(要件定義の確定後の変更のため)。

### 10.6 その他

* B001〜B003 は 9579d85 としてコミット済み。★FIXME★ の受け入れと CR-001 の変更はその次のコミットに含まれる。リモートへのプッシュは人間の判断で行う。
* `e2e/scripts/run-suite.sh` はボリュームを消すため、運用環境では実行しない。

## 11. リリース判定

**OK**

根拠:

* テスト: 単体・結合・受け入れ結合がすべて合格(9 章)。CR-001 で追加した A01 手順 8・9 と A08 も 2 回続けて合格し、スイートの再実行性(A07)も確認した。未解決の障害なし(P202-fix-unresolved.md)。配布資産は整備済みで、compose での起動を実際に確認した。
* 出荷影響「要対応」: **0 件**(10.1)。以前の 2 件は CR-001 で解消した。
* 本番検証・代替検証・自明: 理由を記載済み(10.2)。判定の根拠には数えない。本番検証の REQ-NFR-004-TLS は稼働前に運用側で確認する。
* 未解消の ★FIXME★: **0 件**(10.5)。58 件は 2026-09-24 に人間が全件受け入れ、★ACCEPTED★ にした。
* 4 章の対応表で状態が OK 以外の行は、NO_TEST_IMPL 3 件(自明)・NO_TEST_CASE 1 件(代替検証)・NO_TEST_PLAN 2 件(自明)・BLOCKED 1 件(本番検証の REQ-NFR-004-TLS)で、いずれも理由を記載済み。
