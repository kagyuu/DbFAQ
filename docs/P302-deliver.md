# 成果物まとめ

## 1. 概要

* アプリケーション: DbFAQ v0.5.0(第 1 リリース + CR-001〜CR-006)。Oracle のスキーマを backend(FastAPI)が python-oracledb で直接読み取り SQLite に保存し(CR-002 で MCP サーバを廃止)、ブラウザで ER 図(拡大縮小・ミニマップ・クリックで詳細へ)とテーブル詳細(スキーマ情報/データ/Query のタブ)を表示する。Query タブ(CR-004)では、スキーマ情報からひな形(外部キーで JOIN)を作って任意の SELECT 文を実行し、先頭 500 行を表で、全行を CSV で得る。CR-005 で、Query の SQL を名前と説明付きでテーブルごとに保存・復元できるようにし(テーブルが無くなっても残り、同名のテーブルが戻れば再び使える)、ER 図の画面のドラム缶のアイコンから開く PDB 画面(PDB 情報と、テーブルに属さない Query。運用 Query のひな型 17 件)を追加した。CR-006 で、推奨の接続ユーザーを読み取り専用ユーザー `dbfaq_ro` にし(開発・テストもこのユーザー)、PDB 画面とひな型を対象スキーマ(`oracle.schema`)基準にした。README に `dbfaq_ro` を作る理由・作り方・`config.yaml` への登録を載せた。
* 作成日: 2026-09-23(2026-09-24 に CR-001、2026-09-27 に CR-002、2026-09-28 に CR-003、2026-10-04 に CR-004、2026-10-07 に CR-005、2026-10-09 に CR-006 で更新)。実行モード: `一気通貫`(`docs/.mode`)。
* 結果: 単体テスト 182 件(Python 128、クライアント 54)、結合テスト T01〜T04・T06〜T12(T05 は CR-002 で廃止)、受け入れ結合テスト A01〜A08 がすべて合格(CR-002 の P205: docs/test-records/20260927-0244-test-record.md。CR-003 後も再実行して合格: docs/test-records/20260927-2358-test-record.md、20260928-0001-test-record.md)。
* CR-004 後の結果: 単体テスト 292 件(Python 203、クライアント 89)、結合テスト T01〜T04・T06〜T13、受け入れ結合テスト A01〜A09 がすべて合格(P205: docs/test-records/20261004-2110-test-record.md。HR のベースラインは 8 表。P202 F010)。
* CR-005 後の結果: 単体テスト 389 件(Python 278、クライアント 111)、結合テスト T01〜T04・T06〜T15、受け入れ結合テスト A01〜A10 がすべて合格(P103: docs/test-records/20261007-0100-test-record.md、P205: docs/test-records/20261007-0130-test-record.md)。
* CR-006 後の結果: 単体テスト 397 件(Python 286、クライアント 111)、結合テスト T01〜T04・T06〜T15、受け入れ結合テスト A01〜A10 が、接続ユーザー `dbfaq_ro` ですべて合格(P103: docs/test-records/20261009-0047-test-record.md、P201: docs/test-records/20261009-0051-test-record.md)。
* リリース判定: **OK**(11 章。出荷影響「要対応」0 件。CR-006 の ★FIXME★ 3 件は 2026-10-09 に依頼者が受け入れ、未解消 0 件)。

## 2. 参照した成果物

* 仕様: docs/P001-requirement.md、P002-frontend-spec.md、P003-backend-spec.md、P004-traceability-matrix.md、P005-impl-plan.md、P006-test-plan.md
* 指示: docs/P007-impl-direction.md(U001〜U011)、P008-test-direction.md(T01〜T15。T05 は廃止)、P009-acceptance-direction.md(A01〜A10)
* レビュー・修正: docs/P010-design-review.md、P011-impact-analysis.md、P201-review-report.md、P202-fix-plan.md(fixed/F001〜F012)、P202-fix-plan/P202-fix-resolved.md、P202-fix-plan/P202-fix-unresolved.md(未解決なし)、P204-impact-analysis.md
* テスト記録: docs/test-records/20260923-0315-test-record.md(P103)、20260923-0320-test-record.md(P201 1 回目)、20260923-0350-test-record.md(P205)、20260924-2352-test-record.md(CR-001 の P201)、20260927-0233-test-record.md(CR-002 の P103)、20260927-0238-test-record.md(CR-002 の P201 1 回目)、20260927-0244-test-record.md(CR-002 の P205)、20260927-2358-test-record.md(CR-003 の P103)、20260928-0001-test-record.md(CR-003 の P201)、20261004-1430・1440・2110(CR-004)、20261007-0100(CR-005 の P103)・20261007-0115(CR-005 の P201 1 回目)・20261007-0130(CR-005 の P205)、20261009-0047(CR-006 の P103)・20261009-0051(CR-006 の P201)
* 技術: docs/ADR.md(ADR-002〜017)、docs/ADR_master.md(廃止した ADR-001)、docs/ArchitectureHandbook.md、./INDEX.md、server/INDEX.md、client/INDEX.md
* 配布資産: compose.yaml、deploy/api.Dockerfile、deploy/web.Dockerfile、deploy/nginx.conf、config.example.yaml、.dockerignore、server/pyproject.toml、client/package.json、README.md、docs/BUILD_HISTORY.md
* 存在しないもの: docs/P000-concept-analysis.md(要求はプロンプトで受領)、.env.example(設定は config.yaml。compose の上書き用の環境変数は 7 章に記載)、(CR は docs/CR.md。CR-001・CR-002 完了、CR-003 は P904 で完了にする)

## 3. アプリケーション種別と配布方針

* 種別: サービス提供型システム(Web フロントエンド + API サーバ + SQLite。Oracle は外部の既存 DB。CR-002 で子プロセスの MCP サーバを廃止)。
* 配布方針: Docker Compose(web: nginx で静的配信と `/api` 中継、ホストの 8088 のみ公開/api: uvicorn 1 ワーカー(Oracle の接続プールをプロセス内に持つ)、非公開、SQLite は名前付きボリューム `dbfaq-data`)。ADR-012。
* 実行前チェック:
  1. P002・P003: あり
  2. P006: あり
  3. テスト記録: あり(7 件)
  4. 修正結果: P202-fix-resolved.md・P202-fix-unresolved.md あり
  5. 種別の推定: 可(上記)
  6. 本書: 既存(CR-002・CR-003 で差分を更新)
  7. フロントエンドの接続前提と配布トポロジー: クライアントは相対パス `/api`(`client/src/api/client.ts` の `fetch('/api' + path)`)で同一オリジン前提。配布トポロジーは nginx が同じオリジンで `/api/` を api コンテナへ中継する(`deploy/nginx.conf`)。**一致している**。受け入れ結合テスト A01〜A06 はブラウザ(Playwright)から compose の web(同一オリジン)に対して実行しており、この経路で検証済み。
  8. 再起動耐性: A04 で確認済み(`docker compose restart api`、`down`/`up` でスナップショット保持、`schema_migrations` 1 件、起動時例外なし)。記録: docs/test-records/20260923-0320-test-record.md の A04、docs/test-records/20260923-0350-test-record.md(A01〜A06 を 2 回)。CR-002 後も docs/test-records/20260927-0244-test-record.md で 2 回確認(A04 手順 7 で MCP の子プロセスが無いことも確認)。CR-002 で Oracle に届かない間の停止が止まる問題が見つかり、F008 で直した(`docker compose stop` 1 秒)。CR-003 後も docs/test-records/20260928-0001-test-record.md で 2 回確認。

## 4. 仕様・テスト・テスト実装の対応表

テスト実装の場所: 単体 `server/tests/unit`・`client/src/**/*.test.ts(x)`、結合 `server/tests/integration/test_t0N_*.py`(T01〜T09)・T10/T11 は curl 手順・T12 は compose 手順、受入 `e2e/tests/a0N-*.spec.ts`・`e2e/scripts/*.sh`。証跡は特記なければ docs/test-records/20260927-0244-test-record.md(CR-002 の P205。全テストを再実行した)。

| 仕様ID/項目 | 要求ID | 仕様内容 | 対応するテスト計画 | 対応するテスト指示 | 対応するテスト実装/実行コマンド | 最新結果 | 証跡 | 状態 | 出荷影響 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | REQ-SCREEN-001 | SC-01 ER 図のノード(列・PK/FK/NOT NULL の印) | P006 §2.1 SC-01 | A01、U004-T4 | `e2e/tests/a01-er-diagram.spec.ts`、`client/src/pages/ErDiagramPage.test.tsx` | PASS | 同上 | OK | - |
| REQ-SCREEN-002 | REQ-SCREEN-002 | リレーションの線(複合 FK も 1 本、制約名ラベル、自己参照) | P006 §2.1 | A01(線 10 本)、U004-T3、U002-T3 | a01、`client/src/er/buildGraph.test.ts`、`server/tests/unit/oracle/test_snapshot.py` | PASS | 同上 | OK | - |
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
| REQ-SCREEN-009-ドラッグ | REQ-SCREEN-009 | ノードのドラッグ(クリック扱いにならない、位置は保存しない) | P006 §2.1「ノードのドラッグ」 | A01 手順 8・9 | `e2e/tests/a01-er-diagram.spec.ts` の「ノードのドラッグ」 | PASS | 同上 | OK | -(CR-001 で追加) |
| REQ-SCREEN-010 | REQ-SCREEN-010 | タブ切替と URL の保持 | P006 §2.1 SC-02 | A02 手順 4・6、U005-T1 | a02、TableDetailPage.test | PASS | 同上 | OK | - |
| REQ-SCREEN-011 | REQ-SCREEN-011 | スキーマ情報タブ | P006 §2.1 | A02 手順 1・2、U005-T2、T06 | a02、SchemaTab.test、test_t06 | PASS | 同上 | OK | - |
| REQ-SCREEN-012 | REQ-SCREEN-012 | 外部キー先・参照元への遷移 | P006 §2.1 | A02 手順 2、U005-T2 | a02、SchemaTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-013 | REQ-SCREEN-013 | データタブのうち 50 行ページ、主キー順/ROWID 順、NULL 表示、取得時間、再読み込み | P006 §2.1 | A02 手順 4〜7、U005-T3、T02 | a02、DataTab.test、test_t02 | PASS | 同上 | OK | - |
| REQ-SCREEN-013-LOB | REQ-SCREEN-013 | LOB・長い文字列の 1,000 文字切り詰めと表示 | P006 §2.1 | U002-T1、U005-T3 | `server/tests/unit/oracle/test_values.py::test_text_truncation`・`::test_bytes`、DataTab.test「null と文字列 "(null)" を区別し、切り詰めたセルに title」 | PASS | 単体テスト | NO_TEST_CASE | 代替検証: HR に LOB 列が無いため結合・受入では確認できない。上記の単体テストで文字列化と画面表示をそれぞれ確認 |
| REQ-SCREEN-014 | REQ-SCREEN-014 | 異常時の表示(テーブル無し、Oracle エラー時もスキーマ情報は使える、0 行) | P006 §2.1 | A02 手順 8、A03、U005 | a02、a03、DataTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-015 | REQ-SCREEN-015 | 共通ヘッダ | P006 §2.1 | A01、U004-T4 | a01、AppShell.test | PASS | 同上 | OK | - |
| REQ-SCREEN-016 | REQ-SCREEN-016 | Query タブ: SELECT 文の入力・実行、結果の表(先頭 500 行、打ち切りの表示、行数・取得時間、0 行)(CR-004) | P006 §2.1「SC-02 Query タブ」「SELECT の実行」 | A09 手順 1・4・5、T13、U009-T2・T5 | `e2e/tests/a09-query-tab.spec.ts`、`server/tests/integration/test_t13_query.py`、`client/src/pages/QueryTab.test.tsx`、`server/tests/unit/oracle/test_query.py` | PASS | docs/test-records/20261004-2110-test-record.md | OK | - |
| REQ-SCREEN-017 | REQ-SCREEN-017 | Query タブ: ひな形、外部キーのチェックボックスで JOIN(CR-004) | P006 §2.1「frontend のひな形」 | A09 手順 1・3・4、U009-T4・T5 | a09、`client/src/query/template.test.ts`、QueryTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-018 | REQ-SCREEN-018 | Query タブ: ORA エラーとエラー位置(行・文字)(CR-004) | P006 §2.1「エラー位置の変換」 | A09 手順 7・8、T13 手順 4〜6、U009-T2・T5 | a09、test_t13、test_query.py::test_error_position、QueryTab.test | PASS | 同上 | OK | - |
| REQ-SCREEN-019 | REQ-SCREEN-019 | Query タブ: 全行の CSV ダウンロード(CR-004) | P006 §2.1「CSV」 | A09 手順 6、T13 手順 7・8、U009-T2・T3・T5 | a09、test_t13、test_query.py、`server/tests/unit/api/test_query_api.py`、QueryTab.test | PASS | 同上 | OK | - |
| REQ-API-001 | REQ-API-001 | GET /api/schema | P006 §2.1 | T06、T10、U003-T4 | test_t06、test_api.py | PASS | 同上 | OK | - |
| REQ-API-002 | REQ-API-002 | POST /api/schema/refresh | P006 §2.1 | T06、T08、T10、A01、A03 | test_t06、test_t08、a01、a03 | PASS | 同上 | OK | - |
| REQ-API-003 | REQ-API-003 | GET /api/schema/tables/{owner}/{table} | P006 §2.1 | T06、T11、A02 | test_t06、a02 | PASS | 同上 | OK | - |
| REQ-API-004 | REQ-API-004 | GET /api/schema/tables/{owner}/{table}/rows(limit 最大 500) | P006 §2.1 | T07、T11、A02 | test_t07、a02 | PASS | 同上 | OK | - |
| REQ-API-006 | REQ-API-006 | POST /api/query(CR-004) | P006 §2.1 | T13、T10・T11(Vite の中継)、U009-T3 | test_t13、test_query_api.py | PASS | 同上 | OK | - |
| REQ-API-007 | REQ-API-007 | POST /api/query/csv(CR-004。nginx の待ち時間 600 秒) | P006 §2.1 | T13、T12(nginx 経由)、A09 手順 6、U009-T3・T6 | test_t13、test_query_api.py、a09 | PASS | 同上 | OK | - |
| REQ-ORA-005 | REQ-ORA-005 | SELECT 文の実行と SQL の検査(SELECT・WITH の 1 文のみ)(CR-004) | P006 §2.1「SQL の検査」・§2.2「読み取りのみ」 | T03(Query の経路)、A06 手順 6、U009-T1 | test_t03、a06-security.sh、`server/tests/unit/oracle/test_sql_guard.py` | PASS | 同上 | OK | - |
| REQ-API-005 | REQ-API-005 | GET /api/health(CR-002 で `mcp` を削除。常に 200) | P006 §2.1 | T08、T09、T10、T12、A03、U007-T3 | test_t08、test_t09、test_api.py::test_health_ok・::test_health_unexpected_error_is_still_200 | PASS | 同上 | OK | - |
| REQ-ORA-001 | REQ-ORA-001 | スキーマの読み取り(旧 REQ-MCP-001) | P006 §2.1 | T01、U007-T2 | test_t01、test_snapshot.py、test_client.py | PASS | 同上 | OK | - |
| REQ-ORA-002 | REQ-ORA-002 | テーブルデータの取得(実在確認・クォート・バインド変数)(旧 REQ-MCP-002) | P006 §2.1 | T02、U007-T2 | test_t02、test_rows.py、test_client.py | PASS | 同上 | OK | - |
| REQ-ORA-003 | REQ-ORA-003 | 疎通確認(旧 REQ-MCP-003) | P006 §2.1 | T04、T08、U007-T2 | test_t04、test_t08、test_client.py::test_ping | PASS | 同上 | OK | - |
| REQ-ORA-004 | REQ-ORA-004 | 読み取り専用トランザクションと必ず ROLLBACK(旧 REQ-MCP-004) | P006 §2.1・§2.2 | T03、A06 手順 1、U007-T1 | test_t03、a06-security.sh、test_db.py | PASS | 同上 | OK | - |
| REQ-ARCH-001 | REQ-ARCH-001 | Oracle へは backend が直接接続する。MCP は使わない(CR-002 で変更) | P006 §2.3 | T01〜T04・T06〜T09、A04 手順 7、U007-T3 | 結合テスト(`OracleClient` を直接使用)、a04-restart.sh(`dbfaq_mcp` のプロセス数 0)、`grep -rn -i mcp server/src`(`OracleSearchMCP` の出典表記のみ) | PASS | 同上 | OK | - |
| REQ-SCREEN-020 | REQ-SCREEN-020 | Query タブで SQL を名前・説明付きでテーブルごとに保存(名前の重複は不可)(CR-005) | P006 §2.1「保存済み Query の API」「frontend の保存済み Query」 | A10 手順 2〜4、T15 手順 2・3、U010-T1・T3・T4 | a10、test_t15、test_saved_queries_api.py、SavedQueries.test.tsx | PASS | docs/test-records/20261007-0130-test-record.md | OK | - |
| REQ-SCREEN-021 | REQ-SCREEN-021 | 保存済み Query の一覧と復元(編集中は確認)(CR-005) | 同上 | A10 手順 5・7、U010-T4・T5 | a10、SavedQueries.test.tsx、QueryTab.test.tsx | PASS | 同上 | OK | - |
| REQ-SCREEN-022 | REQ-SCREEN-022 | 上書き保存・名前と説明の変更・削除(CR-005) | 同上 | A10 手順 6・8、T15 手順 6、U010-T3・T4 | a10、test_t15、SavedQueries.test.tsx | PASS | 同上 | OK | - |
| REQ-SCREEN-023 | REQ-SCREEN-023 | テーブルが無くなっても保存済み Query を残し、同名のテーブルが戻れば使える(CR-005) | P006 §2.1「テーブルが無くなって戻ったとき」 | T15 手順 4〜6、U010-T1 | test_t15、test_saved_query_repo.py::test_saved_queries_survive_snapshot_replacement | PASS | docs/test-records/20261007-0100-test-record.md | OK | -(実 Oracle の HR を変えない方針のため、偽の Oracle アクセス + 実ファイルの SQLite で確認。P006 §2.1 の ★ACCEPTED★) |
| REQ-SCREEN-024 | REQ-SCREEN-024 | SC-01 のドラム缶のアイコン、クリックで SC-03(CR-005) | P006 §2.1「SC-01 の PDB のアイコン・SC-03」 | A10 手順 9、U010-T5 | a10、ErDiagramPage.test.tsx | PASS | docs/test-records/20261007-0130-test-record.md | OK | - |
| REQ-SCREEN-025 | REQ-SCREEN-025 | SC-03 PDB 情報タブ(権限の無い項目だけエラー)(CR-005。CR-006 で対象スキーマ基準) | P006 §2.1「PDB 情報」 | A10 手順 10、T14 手順 1〜4、U010-T2・T5 | a10、test_t14、test_pdb.py、PdbPage.test.tsx | PASS | 同上 | OK | -(CR-006 で `dbfaq_ro` により正常系も確認。docs/test-records/20261009-0047-test-record.md) |
| REQ-SCREEN-026 | REQ-SCREEN-026 | SC-03 Query タブ(CR-005) | 同上 | A10 手順 11〜14、U010-T5 | a10、PdbPage.test.tsx | PASS | 同上 | OK | - |
| REQ-SCREEN-027 | REQ-SCREEN-027 | PDB の Query のひな型 17 件を最初から登録(CR-005。CR-006 で対象スキーマ基準・未変更のひな型の更新) | P006 §2.1「ひな型の登録」「PDB のひな型の実行」 | T14 手順 5、T15 手順 1・5、A10 手順 11〜13、U010-T1 | test_t14、test_t15、test_pdb_templates.py、a10 | PASS | 同上 | OK | -(CR-006 で 17 件すべての成功を確認。T14) |
| REQ-API-008〜011 | REQ-API-008〜011 | 保存済み Query の API 4 本(CR-005) | P006 §2.1「保存済み Query の API」 | T15、T11(Vite の中継)、U010-T3 | test_t15、test_saved_queries_api.py | PASS | docs/test-records/20261007-0100-test-record.md | OK | - |
| REQ-API-012 | REQ-API-012 | GET /api/pdb(CR-005) | P006 §2.1「PDB 情報」 | T14、T11・T12(中継)、U010-T3 | test_t14、test_pdb_api.py | PASS | 同上 | OK | - |
| REQ-ORA-006 | REQ-ORA-006 | PDB の情報を決まった SELECT で項目ごとに読む(CR-005) | 同上 | T14、U010-T2 | test_t14、test_pdb.py | PASS | 同上 | OK | - |
| REQ-DOC-001 | REQ-DOC-001 | README に読み取り専用ユーザー dbfaq_ro を作る理由・作成の SQL・config.yaml への登録(CR-006) | - | - | README.md「Oracle に読み取り専用ユーザー dbfaq_ro を作る」(作成の SQL は依頼者が開発用 Oracle で実行済みのもの) | 確認済み | README.md | OK | - |
| REQ-ARCH-003 | REQ-ARCH-003 | スキーマ情報と保存済み Query(CR-005)を SQLite に保存し再起動後も保持 | P006 §2.3 | A04(手順 8 は CR-005)、U003-T1・T2、U010-T1 | a04-restart.sh、test_migrate.py、test_saved_query_repo.py | PASS | docs/test-records/20261007-0130-test-record.md | OK | - |
| REQ-ARCH-004 | REQ-ARCH-004 | 接続パラメータを設定ファイル(Git 管理外)に保持 | P006 §2.1 | U001-T2、T12、A06 手順 5 | test_config.py、a06-security.sh | PASS | 同上 | OK | - |
| REQ-ARCH-005 | REQ-ARCH-005 | Python は uv で管理 | - | - | 全 Python テストを `uv run` で実行 | PASS | 同上 | OK | - |
| REQ-ARCH-006 | REQ-ARCH-006 | React / FastAPI / python-oracledb(CR-002 で FastMCP を削除。api イメージに `fastmcp` が無いことを確認) | - | - | ビルドとテスト全体 | PASS | 同上 | OK | - |
| REQ-ARCH-007 | REQ-ARCH-007 | Docker Compose で起動、コンテナから Oracle へは host.docker.internal | P006 §2.2 | T12、A01〜A06 | T12 の手順、run-suite.sh | PASS | 同上 | OK | - |
| REQ-ARCH-008 | REQ-ARCH-008 | Oracle アクセスの設計は ../OracleSearchMCP を参考にする | - | - | - | - | - | NO_TEST_PLAN | 自明: 設計上の要求であり動作要件ではない。踏襲した箇所(読み取り専用トランザクション、辞書の結合)はコード・P003 に出典を明記 |
| REQ-NFR-001 | REQ-NFR-001 | 性能(HR の ER 図 1 秒・refresh 10 秒・rows + 1 秒、300 表の ER 図 3 秒、Query + 1 秒(CR-004。A05 手順 3b のオーバーヘッド 0.012 秒)) | P006 §2.2 | A05 | a05-perf-api.sh、a05-performance.spec.ts | PASS | 同上(HR 表示 240・267 ms、300 表 1,787・1,812 ms、refresh 0.10 s 等) | OK | - |
| REQ-NFR-002 | REQ-NFR-002 | タイムアウト(既定 30 秒、設定で変更可) | P006 §2.2 | T04 | test_t04::test_timeout_then_recover(1 秒に設定) | PASS | 同上 | OK | - |
| REQ-NFR-003 | REQ-NFR-003 | 可用性(restart、Oracle 無しでも起動、Oracle が戻れば再起動なしで回復)(CR-002 で変更) | P006 §2.3 | A03、A04、T08、T09 | a03、a04、test_t08、test_t09(TCP 中継で通信断と回復) | PASS | 同上 | OK | - |
| REQ-NFR-004 | REQ-NFR-004 | セキュリティのうち認証なしの前提での公開範囲・読み取りのみ・パスワード非露出(TLS は副 ID へ分離) | P006 §2.2 | A06、T12、T04 | a06-security.sh、T12 の手順、test_t04 | PASS | 同上 | OK | - |
| REQ-NFR-004-TLS | REQ-NFR-004 | TLS 終端 | P006 §2.2 | - | - | - | 本書 10 章 | BLOCKED | 本番検証: TLS は運用環境のリバースプロキシで終端する前提(P003 §6)で、本環境に該当構成が無い |
| REQ-NFR-005 | REQ-NFR-005 | スケーラビリティのうち SQLite WAL と refresh の排他(同時 10 名の負荷は副 ID へ分離) | P006 §2.2 | U003-T1・T4 | test_migrate.py::test_foreign_keys_pragma、test_api.py::test_refresh_in_progress | PASS | 単体テスト | OK | - |
| REQ-NFR-005-同時10名 | REQ-NFR-005 | 同時利用者 10 名でエラー 0・性能目標内(P001 §8.4) | P006 §2.2「同時利用」 | A08 | `e2e/scripts/a08-concurrency.sh`(`server/scripts/a08_concurrent_load.py`) | PASS(2 回: schema 最大 0.269・0.236 s、detail 0.217・0.205 s、rows オーバーヘッド 0.072・0.064 s、エラー 0) | 同上 | OK | -(CR-001 で追加) |
| REQ-NFR-006 | REQ-NFR-006 | ログ(JSON、backend は stdout)と /api/health(CR-002 で MCP の stderr を削除) | P006 §2.2 | U001-T3、A04 手順 6、A06 | test_logging.py、a04-restart.sh、a06-security.sh(ログにパスワードなし) | PASS | 同上 | OK | - |
| REQ-TEST-001 | REQ-TEST-001 | テスト方針(pytest / Vitest / 結合 / Playwright、HR を変更しない、2 回実行) | P006 | 全体 | 全テスト、A06 のチェックサム、A07 | PASS | 同上 | OK | - |

* P004 の全要求 ID(CR-005 で REQ-SCREEN-020〜027・REQ-API-008〜012・REQ-ORA-006 を追加して 59 件)が上表に現れることを確認した。以前の記述: 全 38 要求 ID が上表に現れることを確認した(CR-002 で REQ-MCP-001〜004 を REQ-ORA-001〜004 に改め、REQ-ARCH-002 を削除)。
* P004 §2 の過剰実装 3 件(ヘッダの Oracle 状態表示、ページ番号の URL 保持、関数索引の式の表示)も実装・テスト済み(A01・A03、A02、test_snapshot.py)。要求書へ追加するか残すかは人間の判断事項として 10 章に記載する。

## 5. バージョン情報とビルド履歴

| 対象 | バージョンの定義 | 実行時の確認方法 |
|---|---|---|
| backend | `server/pyproject.toml` の `project.version = "0.5.0"`、`dbfaq_api.__version__`(FastAPI の `version` も同じ値を使う) | `curl http://localhost:8088/api/health` の `backend.version` |
| フロントエンド | `client/package.json` の `version = "0.5.0"` | 画面には表示しない(10 章) |
| E2E | `e2e/package.json` の `version = "0.1.0"` | - |

* ビルド履歴: [docs/BUILD_HISTORY.md](./BUILD_HISTORY.md)(B001〜B016)。CR-006 は API の形を変えないが、`GET /api/pdb` の内容(概要の項目名、表領域の割り当て・セグメントの使用量が対象スキーマの分になる)と、Query のスキーマ名の無い表名の解釈(カレントスキーマを対象スキーマにする)が変わるため、MINOR を上げて **0.5.0** にした(backend・frontend)。CR-005 は API(保存済み Query の 4 本と `GET /api/pdb`、エラーコード `SAVED_QUERY_NOT_FOUND`・`QUERY_NAME_CONFLICT`)とデータモデル(SQLite の `saved_queries`・`query_template_seeds`。マイグレーション 0002)を追加した。既存の API・テーブルは変えていない後方互換の機能追加のため MINOR を上げて **0.4.0** にした(backend・frontend)。CR-004 は API を追加した(`POST /api/query`・`POST /api/query/csv`、エラーの任意項目 `position`、エラーコード `SQL_REJECTED`。既存の API は変えていない。`docs/P903-cr-records/CR-004.md` で「API契約変更」に分類)後方互換の機能追加のため MINOR を上げて **0.3.0** にした(backend・frontend)。CR-001 はテストの追加だけでアプリケーションの画面・API・データ契約を変えていないため、版数は 0.1.0 のまま。CR-002 は API 契約を変えた(`GET /api/health` から `mcp` を削除、エラーコード `MCP_UNAVAILABLE` を削除。`docs/P903-cr-records/CR-002.md` で「API契約変更」に分類)ため、MAJOR が 0 の間の規則により MINOR を上げて **0.2.0** にした(backend・frontend。E2E は変更が無いため 0.1.0 のまま)。CR-003 は API・画面・データ契約を変えない内部構成の変更(パッケージの統合)のため PATCH を上げて **0.2.1** にした(backend・frontend は同じ版数で揃えている。frontend のコードは変えていない)。B001〜B003 の作業ツリーは 9579d85 としてコミット済み。B004(CR-001)の変更はその次のコミットに含まれる。

## 6. 配布資産一覧

| 資産 | 内容 | 状態 |
|---|---|---|
| `compose.yaml` | web(8088 公開)・api(非公開、host-gateway、config.yaml を読み取り専用マウント、ボリューム `dbfaq-data:/data`、healthcheck)、両方 `restart: unless-stopped` | 整備済み・起動確認済み |
| `deploy/api.Dockerfile` | python:3.12-slim + uv、非 root(uid 10001)、uvicorn 1 ワーカー。CR-002 後はイメージに `dbfaq_mcp`・`fastmcp` が無い | 整備済み・ビルド確認済み |
| `deploy/web.Dockerfile`、`deploy/nginx.conf` | node:22 でビルド → nginx:1.27、`/api/` 中継(120 秒。CR-004 で `/api/query/csv` だけ 600 秒・バッファなし)、SPA フォールバック | 整備済み・ビルド確認済み |
| `config.example.yaml` | 設定ファイルのひな型(CR-002 で `app.mcp_call_timeout_sec` を削除。古い `config.yaml` に残っていても無視される) | 整備済み |
| `.dockerignore` | config.yaml・data・node_modules 等を除外 | 整備済み(イメージにパスワードが入らないことを A06 で確認) |
| `README.md` | 概要と最短の起動手順 | 整備済み |
| マイグレーション | api の起動時に自動適用(`schema_migrations` による差分適用)。CR-005 で 0002(保存済み Query)を追加。起動時に PDB のひな型を 1 回だけ登録する | 整備済み・再起動耐性を A04 で確認(0001 だけ適用済みの既存のボリュームに 0002 だけが適用されることも確認。docs/test-records/20261007-0100-test-record.md) |

## 7. 起動・実行手順

### Docker Compose 起動手順

1. 前提ソフトウェア: Docker Engine と Docker Compose v2。Oracle(19c 以降を想定。検証は 23.26)に TCP で到達できること。
2. 接続ユーザーを作る(※CR-006により追加): Oracle の PDB に読み取り専用ユーザー `dbfaq_ro` を作る(`CREATE SESSION`、`SELECT_CATALOG_ROLE`、対象スキーマの表への `READ`)。理由と SQL は README.md「Oracle に読み取り専用ユーザー dbfaq_ro を作る」。
3. 設定ファイルを作る: `cp config.example.yaml config.yaml` として、`oracle.host`・`port`・`service_name`・`user`(`dbfaq_ro`)・`password`・`schema`(対象スキーマ)を記入する(`config.yaml` は Git 管理外。ファイルの権限はサーバの運用者だけが読めるようにする)。
4. 環境変数(任意): `DBFAQ_PORT`(公開ポート。既定 8088)、`DBFAQ_ORACLE_HOST`(コンテナから見た Oracle のホスト。既定 `host.docker.internal` = Docker ホスト。Oracle が別サーバならそのホスト名)。`DBFAQ_ORACLE_PASSWORD` でパスワードを上書きすることもできる。
5. ビルドと起動: `docker compose up -d --build`
6. ヘルスチェック: `curl http://localhost:8088/api/health` → `"status":"ok"`(`oracle.status` が `error` なら `message` と `docker compose logs api` を確認)。`docker compose ps` で api が `healthy`。
7. 初期データ: SQLite のマイグレーションは起動時に自動適用される。スキーマ情報はブラウザで [Oracle から読み込む] を押して取り込む(または `curl -X POST http://localhost:8088/api/schema/refresh`)。
8. 動作確認: ブラウザで `http://<サーバ>:8088/` を開き、ER 図が表示され、テーブルをクリックして詳細が見られること。
9. 停止・再起動: `docker compose down`(スナップショットはボリュームに残る)/`docker compose down -v`(ボリュームも削除)/`docker compose restart`。
10. バックアップ(※CR-005により変更): **保存済み Query は利用者が作ったデータで、Oracle からは作り直せない**ため、定期的にバックアップする(スナップショットは再読み込みで作り直せる)。SQLite は WAL モードのため、api を止めてから複写するか、SQLite のオンラインバックアップを使う。
   * 止めて複写する: `docker compose stop api && docker compose cp api:/data/. ./backup-$(date +%Y%m%d)/ && docker compose start api`(`dbfaq.sqlite3` と、あれば `-wal`・`-shm` を一緒に複写する)
   * 止めずに複写する: `docker compose exec -T api python -c "import sqlite3; s=sqlite3.connect('/data/dbfaq.sqlite3'); d=sqlite3.connect('/data/backup.sqlite3'); s.backup(d); d.close()" && docker compose cp api:/data/backup.sqlite3 ./backup.sqlite3`
   * 戻す: api を止め、ボリュームの `/data/dbfaq.sqlite3` をバックアップで置き換え(`-wal`・`-shm` は消す)、api を起動する。★ACCEPTED★ #83(バックアップを運用に任せる判断)

### 実運用に向けた推奨

* Oracle の接続ユーザーは読み取り専用ユーザー(`dbfaq_ro`。2 の手順)にする(※CR-006により推奨構成として手順に組み込んだ。以下は以前の記述)。**CR-004 で Query タブから利用者の SELECT を実行できるようになったため、特に重要**(副作用のある既存のストアドファンクションを SELECT から呼ぶことは、SQL の検査でも読み取り専用トランザクションでも防げない。ADR-015)(例: `CREATE USER dbfaq_ro ...; GRANT CREATE SESSION TO dbfaq_ro; GRANT SELECT ON <schema>.<table> TO dbfaq_ro;` と、辞書を読むための `SELECT_CATALOG_ROLE` 等は環境に合わせて付与)。アプリは読み取り専用トランザクションで防いでいるが、二重の防御になる。対象スキーマは `oracle.schema` で指定する。
* PDB 画面(CR-005)の「表領域の使用状況」と、PDB のひな型のうち DBA_* ・V$ を使うもの(01・04〜07・14〜17)は、接続ユーザーにそれらを読む権限(`SELECT_CATALOG_ROLE` など)が無いと ORA-00942 になる(画面には「権限が無いため取得できません」と出る)。権限を与えるかは運用側で判断する(読み取り専用ユーザーの原則とのかね合い)。
* 認証が無いため、ネットワーク(ファイアウォール・リバースプロキシ)でアクセス元を制限する。TLS が必要なら前段のリバースプロキシで終端する。

## 8. テスト実行手順

* テスト用データベースの前提(`docs/P006-test-plan.md` §3.1)。次の順に準備する。
  1. Oracle 配布の HR サンプルスキーマ(https://github.com/oracle/db-sample-schemas/releases/latest の human_resources)をインストールする。
  2. hr ユーザーで `server/scripts/sql/hr_employee_figure.sql` を実行し、LOB 列の表 `EMPLOYEE_FIGURE` を追加する。
  3. データを入れる場合: 画像ファイルを DB サーバに置き(`docker cp docs/P006-test-plan/ai_model_512_01.png oracle-db-free:/opt/oracle/oradata/ai_model_512_01.png`。詳細は P006 §3.1.1)、管理ユーザー(SYS・SYSTEM など)で PDB に接続して `server/scripts/sql/hr_photo_dir.sql`(`CREATE OR REPLACE DIRECTORY photo_dir AS '/opt/oracle/oradata'`、`GRANT READ ON DIRECTORY photo_dir TO hr`)を実行する。
  4. hr ユーザーで `server/scripts/sql/hr_employee_figure_data.sql` を実行する(EMPLOYEE_ID 100〜206 に同じ画像を 1 行ずつ。1 回の実行で 107 行。実行した回数だけ増える)。
  * `EMPLOYEE_FIGURE` の行のデータはテストの前提にしない(0 行でもよい)。前提の確認: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`。

| 種類 | コマンド | 合格条件 |
|---|---|---|
| Python 単体 | `cd server && uv run python -m pytest tests/unit -q`(この開発環境では `.venv` のシバン行の問題で `uv run pytest` が起動しない。`docs/ArchitectureHandbook.md` §9) | 286 passed |
| クライアント単体 | `cd client && npm ci && npm test` | 111 passed |
| クライアントのビルド | `cd client && npm run build` | 成功 |
| 結合 T01〜T04・T06〜T09・T13〜T15(実 Oracle。T15 は Oracle に接続しない) | `cd server && DBFAQ_CONFIG=../config.yaml uv run python -m pytest tests/integration -v` | 43 passed(接続ユーザーは `dbfaq_ro`。HR は 8 表のベースライン(P006 §3.2)。`config.yaml` の Oracle に接続できること。T09 は 127.0.0.1 の空きポートで TCP 中継を立てる) |
| 結合 T10・T11 | backend(`cd server && DBFAQ_CONFIG=../config.yaml uv run python -m uvicorn --factory dbfaq_api.main:create_app --port 8000`。この開発環境では `uv run uvicorn` が起動しない)と `cd client && npm run dev -- --port 5173 --strictPort` を起動し、`docs/P008-test-direction/T10-*.md`・`T11-*.md` の curl を実行 | 各手順が期待どおり |
| 結合 T12 | `docs/P008-test-direction/T12-compose-stack.md` の手順 | 各手順が期待どおり |
| 受け入れ結合 A01〜A10 | `cd e2e && npm ci && npx playwright install chromium` の後、`bash e2e/scripts/run-suite.sh`(A01〜A06・A08〜A10)を 2 回実行して出力を比較 | すべて PASS で 2 回の出力が同一 |

* テスト結果の格納先: `docs/test-records/`、Playwright の失敗時の証跡は `e2e/test-results/`・`e2e/playwright-report/`。
* 接続ユーザー(※CR-006): 開発・テストは `config.yaml` の `oracle.user` を `dbfaq_ro`(README の権限)、`oracle.schema` を `HR` にして実行する。テスト用 DB の準備(上の 1〜4)は `hr` や管理ユーザーで行う。
* 注意: `run-suite.sh` は `docker compose down -v` でボリュームを消してから始める(ベースライン復元)。運用中の環境では実行しない。

## 9. 最終確認結果

* 2026-09-23 03:30〜03:50 に P205 として全テストを実行: 単体 185 件合格、T01〜T09 を 2 回続けて 17 passed、T10〜T12 合格、A01〜A06 を 2 回続けて全 PASS・出力同一(A07 PASS)。
* compose でのビルド・起動・ヘルスチェック・画面表示を実際に確認済み(Docker は利用可能だった)。
* HR のデータはスイートの前後でチェックサムが一致(A06)。
* 2026-09-24 23:47〜23:52 に CR-001 として、A01(ドラッグの手順 8・9 を追加)〜A06・A08(同時 10 名、新規)を 2 回続けて実行し、すべて PASS・出力同一(A07 PASS)(docs/test-records/20260924-2352-test-record.md)。アプリケーションコードは変えていないため、単体・結合は B003 の結果を引き継ぐ(単体 Python 131 件は 2026-09-24 に再実行して合格)。
* 2026-09-27 に CR-002(MCP の廃止と backend への統合)として: P103 で T01〜T04・T06〜T12 PASS(docs/test-records/20260927-0233-test-record.md)。P201 1 回目で A03 FAIL(ホスト名を解決できないとき health が 500)と T08 の所見(Oracle に届かない間プールの close が約 2 分戻らない)を見つけ、F007・F008 で修正(docs/test-records/20260927-0238-test-record.md)。P205 で単体 + 結合の pytest を 2 回続けて 144 passed、A01〜A06・A08 を 2 回続けて全 PASS・出力同一(A07 PASS)(docs/test-records/20260927-0244-test-record.md)。版数を 0.2.0 に上げた後にも `run-suite.sh` を 1 回実行し全 PASS、`/api/health` の `backend.version` が 0.2.0(B007)。
* 2026-09-27〜28 に CR-003(`dbfaq_common` を `dbfaq_api` に統合)として: 単体 + 結合の pytest を 2 回続けて 144 passed、T10〜T12 PASS(docs/test-records/20260927-2358-test-record.md)、A01〜A06・A08 を 2 回続けて全 PASS・出力同一(A07 PASS)(docs/test-records/20260928-0001-test-record.md)。版数を 0.2.1 に上げた後にも単体 128 + 54 passed、`run-suite.sh` 1 回全 PASS、`backend.version` が 0.2.1(B009)。
* 2026-10-04 に CR-004(Query タブ)として: P103 で T02〜T04・T07・T09〜T11・T13 PASS、T01・T06・T08・T12 FAIL(docs/test-records/20261004-1430-test-record.md)。P201 1 回目で A01・A03・A05 FAIL、A06 は偽の PASS(docs/test-records/20261004-1440-test-record.md)。原因は開発用 Oracle の HR に 2026-09-29 に表 `EMPLOYEE_FIGURE` が追加されたことと、チェックサムのスクリプトが LOB の表に対応せず失敗を検出しなかったこと。F009(チェックサムの修正)・F010(依頼者の判断で 8 表を新しいベースラインに)の後、P205 で単体 + 結合の pytest を 2 回続けて 225 passed、A01〜A06・A08・A09 を 2 回続けて全 PASS・出力同一(A07 PASS)(docs/test-records/20261004-2110-test-record.md)。版数を 0.3.0 に上げた後にも単体 203 + 89 passed、クライアントのビルド成功、`run-suite.sh` 1 回全 PASS、`backend.version` が 0.3.0(B011)。
* 2026-10-09 に CR-006(読み取り専用ユーザー `dbfaq_ro`、対象スキーマ基準、README)として: 接続ユーザーを `dbfaq_ro` にして、P103 で単体 + 結合の pytest を 2 回続けて 329 passed、T10〜T12 PASS(docs/test-records/20261009-0047-test-record.md)。P201 で A01〜A06・A08〜A10 を 2 回続けて全 PASS・出力同一(A07 PASS)(docs/test-records/20261009-0051-test-record.md)。CR-005 のひな型が登録済みのボリュームで起動し、未変更のひな型 9 件が新しい版に更新されることを確認した。版数を 0.5.0 に上げた後の確認は B016。
* 2026-10-07 に CR-005(保存済み Query、PDB 画面、ひな型)として: P103 で単体 + 結合の pytest を 2 回続けて 320 passed、T10〜T12 PASS(docs/test-records/20261007-0100-test-record.md)。P201 1 回目で A10 FAIL(テストのロケータ `/実行/` がひな型名にも一致。docs/test-records/20261007-0115-test-record.md)。F011 の後、P205 で A01〜A06・A08〜A10 を 2 回続けて全 PASS・出力同一(A07 PASS)(docs/test-records/20261007-0130-test-record.md)。版数を 0.4.0 に上げた後、`run-suite.sh` 1 回全 PASS、`backend.version` が 0.4.0、単体 Python 278 passed、クライアントのビルド成功(B013)。このときクライアント単体の ER 図のテスト 1 件が並列実行の負荷で時々失敗する(10 回中 2 回)ことが分かり、テストの待ち時間を直して(F012)15 回続けて 111 passed(B014)。

## 10. 未整備事項・人間による確認事項

### 10.1 出荷影響「要対応」(0 件)

* なし。以前の 2 件(REQ-SCREEN-009-ドラッグ、REQ-NFR-005-同時10名)は CR-001 でテストを追加し、合格した(4 章)。

### 10.2 本番検証・代替検証・自明とした項目

* 本番検証: REQ-NFR-004-TLS(TLS 終端は前段のリバースプロキシ。稼働前に運用側で確認する)。
* 代替検証: REQ-SCREEN-013-LOB(第 1 リリース時点では HR に LOB が無く、単体テストで確認した。2026-09-29 以降の開発用 HR には BLOB 列の表 `EMPLOYEE_FIGURE` があるが、データタブの LOB 表示の受入テストは追加していない)。
* 自明: REQ-SCREEN-003-倍率範囲、REQ-SCREEN-004-操作、REQ-SCREEN-007-処理中、REQ-ARCH-008(理由は 4 章)。REQ-ARCH-001 は CR-002 でテストで確認する項目になった。

### 10.3 既知の制約(判断済み)

* ★ACCEPTED★ LOB を全体でメモリに読み込む(ADR-005)/★ACCEPTED★ OFFSET 方式のページ送り(ADR-006)。詳細は docs/ArchitectureHandbook.md §9。
* Oracle に接続できないとき、画面・API のメッセージは `DPY-4005: timed out waiting for the connection pool ...` となり、根本原因(接続拒否など)は直接は分からない(F006 の残課題)。ホスト名を解決できないときは「Oracle に接続できません: [Errno -2] Name or service not known」になる(F007)。ヘッダの Oracle 状態と `docker compose logs api` で判断する。
* 同時の Oracle 問い合わせが `pool_max`(既定 4)を超えると、超えた分は `connect_timeout_sec`(既定 10 秒)待って DPY-4005 で失敗する(F006 による変更。以前は無期限に待った)。
* uvicorn は 1 ワーカー固定(ADR-014。CR-002 で ADR-001 から引き継ぎ)。同時 10 名は A08 で確認済み。ただし api の起動直後など接続プールが広がる前は、データタブの応答が遅くなる(A08 の単独実行でオーバーヘッドの最大 0.916 秒。目標 1 秒に対して余裕が小さい)。気になる場合は `config.yaml` の `pool_min` を上げる。
* Oracle 障害は、接続拒否(T08)、ホスト名の解決失敗(A03)、通信の途中の切断と回復(T09、CR-002 で追加)を検証した。Oracle 側の応答が無くなる(パケットが捨てられる)状態は未検証。
* ★ACCEPTED★(2026-09-27 人間承認) Oracle のホストが応答しないとき、`/api/health` は接続の確立の待ち時間(`connect_timeout_sec`、既定 10 秒)まで返らない(CR-002 前は MCP の呼び出しを 5 秒で打ち切っていた)。詳細は P003 §3.8・ADR-014。
* ★ACCEPTED★(2026-09-27 人間承認) Oracle のリスナーに届かない間、python-oracledb のプールの close は約 2 分戻らないため、api の終了時は `connect_timeout_sec` で打ち切ってプールを捨てる(F008、P003 §3.1)。
* 既存の `config.yaml` に `app.mcp_call_timeout_sec` が残っていても無視される(CR-002。削除してよい)。
* Query タブ(CR-004、ADR-015): 列名・別名に `UPDATE` などの語を引用符なしで使った SELECT も「実行できない SQL」として拒否される(誤検知。引用符で囲めば通る)。`(SELECT ...)` のように括弧で始まる問い合わせも拒否される。CSV は全行を api コンテナの一時ファイルに書いてから返すため、行数に上限が無く、巨大な結果ではディスクと時間を消費する(★ACCEPTED★ #63)。Query の SQL・結果・入力内容は保存しない(画面を再読み込みすると初期のひな形に戻る)。
* 保存済み Query(CR-005、ADR-016): 保存先はスキーマ名とテーブル名の文字列で照合する。テーブルを改名すると保存済み Query は旧名に残る。無くなったテーブルの保存済み Query を画面で一覧・付け替えする機能は無い(★ACCEPTED★ #80)。登録済みのひな型は、後の版で SQL を直しても反映されない。
* PDB(CR-005・CR-006): 推奨の `dbfaq_ro`(`SELECT_CATALOG_ROLE`)では PDB 情報の全セクションとひな型 17 件が動く(CR-006 で確認。★ACCEPTED★ #82 は解消)。`SELECT_CATALOG_ROLE` の無い接続ユーザーでは、DBA_* ・V$ を使うセクション・ひな型が「権限が無いため取得できません」/ORA-00942 になる(ALL_* を使うひな型 09〜13 は動く)。`SELECT_CATALOG_ROLE` は PDB 内の全スキーマの辞書情報(表名・列名・セッションなど)を読める点に注意(データは `READ` を与えた表しか読めない。ADR-017)。全スキーマの LOB のひな型 04 は、接続ユーザーが読める表だけを対象にする。LOB の実データの合計(ひな型 03・04)は全行の LOB の長さを読むため、大きな表では `query_timeout_sec` を超えうる。
* 開発・テストで使った接続ユーザー hr は書き込み権限を持つ。本番は読み取り専用ユーザーを推奨(7 章)。
* フロントエンドのバージョンは画面に表示していない(backend のバージョンは `/api/health` で確認できる)。
* ヘッドレスのブラウザ環境によっては ER 図の 🔑・🔗 が絵文字フォントの不足で表示されない(Windows・macOS の通常のブラウザでは表示される)。

### 10.4 要求書に無い実装(P004 §2 の過剰実装)

* ヘッダの Oracle 状態表示(60 秒ごとの health 取得)、データタブのページ番号の URL 保持、関数索引の式の表示。CR-004: Query タブの入力内容をタブの切り替えで保持、[エラー位置へ移動]、Ctrl+Enter での実行、CSV 応答の `X-Row-Count` ヘッダ。CR-005: 保存済み Query の一覧のひな型の印・更新日時、[名前を付けて保存] の名前の初期値「 のコピー」。いずれも実装・テスト済み。要求書に追加するか、削るかを人間が判断する(CR の起票候補)。

### 10.5 ★FIXME★ 一覧(第 1 リリースの 58 件、CR-002・CR-003 の各 1 件、CR-004・CR-005 の各 12 件、CR-006 の 3 件はすべて解消済み。未解消 0 件)

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

#### CR-002 で付いた ★FIXME★(1 件。2026-09-27 に解消。未解消 0 件)

**未解消の★FIXME★: 0件。**

`docs/` 配下を `grep -rn "★FIXME★"` で検索し、印として残っているもの(本文中で印の説明として言及しているだけの箇所を除く)を列挙した。CR-002 の作業中に付けた暫定の ADR 番号(「ADR-014 見込み ★FIXME★」3 か所)は P021 で ADR-014 に確定して外した。

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 59 | `docs/P901-cr-direction/CR-002.md` 優先度の判断理由 | 依頼者から優先度の指定が無く、ルーブリック(影響度 高 × 緊急度 低)で「中」と仮置きした(`docs/CR.md` の優先度列も「中」) | -(2026-09-27 に依頼者が「中」でよいと確認。★ACCEPTED★ に書き換えた) |

#### CR-003 で付いた ★FIXME★(1 件。2026-09-28 に解消。未解消 0 件)

**未解消の★FIXME★: 0件。**

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 60 | `docs/P901-cr-direction/CR-003.md` 優先度の判断理由 | 依頼者から優先度の指定が無く、ルーブリック(影響度 低 × 緊急度 低)で「低」と仮置きした(`docs/CR.md` の優先度列も「低」) | -(2026-09-28 に依頼者が「低」でよいと確認。★ACCEPTED★ に書き換えた) |

#### CR-004 で付いた ★FIXME★(12 件。2026-10-09 に解消。未解消 0 件)

**未解消の★FIXME★: 0件。** 2026-10-09 に依頼者が下表の 12 件をすべて受け入れ(「全ての FIXME を受け入れます」)、各箇所の ★FIXME★ を ★ACCEPTED★(検討・承認理由・残存リスク付き)に書き換えた。以下は当時の一覧。`docs/` 配下を `grep -rn "★FIXME★"` で検索し、同じ論点が複数の文書にあるものは 1 件にまとめた。CR-004 の作業中に付けた暫定の ADR 番号(「ADR-015 見込み ★FIXME★」)は P021 で ADR-015 に確定して外した。

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 61 | `docs/P001-requirement.md` §6 Query タブ、`docs/P002-frontend-spec.md` §2.2.6 | JOIN の候補を両方向(このテーブルが参照するテーブル → と、このテーブルを参照するテーブル ←)にした(原文は「FK で連携するテーブル」) | 参照先だけにする場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 62 | `docs/P001-requirement.md` §8.3、`docs/P002-frontend-spec.md` §3.8、`docs/P003-backend-spec.md` §3.10、`docs/ArchitectureHandbook.md` §9 | SQL の検査方式(SELECT・WITH の 1 文だけ、禁止語の字句検査。OracleSearchMCP と同じ)と、その誤検知(`UPDATE` などの語を列名に引用符なしで使うと拒否)・見逃し(副作用のあるストアドファンクション) | 検査を緩める・強める場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 63 | `docs/P002-frontend-spec.md` §3.9、`docs/P003-backend-spec.md` §3.11、`docs/ArchitectureHandbook.md` §9 | CSV の全行に上限(行数・時間・サイズ)を設けない(依頼者の「全てのデータ」による)。一時ファイルのディスクと接続の占有 | 上限を設ける場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 64 | `docs/P001-requirement.md` §8.1 | Query の性能目標を「Oracle の処理時間 + 1 秒以内」とした(データタブと同じ) | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 65 | `docs/P002-frontend-spec.md` §2.2.1 | Query タブの入力・結果は、同じテーブルの画面にいる間だけ保持し、ブラウザには保存しない | 保存する場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 66 | `docs/P002-frontend-spec.md` §2.2.6 | 利用者が SQL を編集していたら、チェックボックスの切り替えで自動で置き換えない(内容を失わないため) | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 67 | `docs/P002-frontend-spec.md` §2.2.7 | JOIN は両方向とも LEFT JOIN(このテーブルの行が消えないように。← の JOIN は行が増えうる) | INNER JOIN にする場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 68 | `docs/P002-frontend-spec.md` §3.9 | CSV は UTF-8 の BOM 付き(Excel での文字化けを防ぐ) | BOM なし・Shift_JIS などにする場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 69 | `docs/P003-backend-spec.md` §3.11 | CSV の値が `=`・`+`・`-`・`@` で始まってもそのまま出す(CSV インジェクションの対策をしない。データを変えないため) | 対策する場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 70 | `docs/P003-backend-spec.md` §4.3 | ログに Query の SQL の本文を出さない(リテラルに業務データを含みうるため。監査が要るなら CR) | 監査ログが要る場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 71 | `docs/P003-backend-spec.md` §6 | nginx の `/api/query/csv` の待ち時間を 600 秒にした | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 72 | `docs/P901-cr-direction/CR-004.md` 優先度の判断理由 | 依頼者から優先度の指定が無く、ルーブリック(影響度 高 × 緊急度 低)で「中」と仮置きした(`docs/CR.md` の優先度列も「中」) | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |

* 補足: `docs/P001-requirement.md` §3.3 の「SQLAlchemy 2.x + SQLite / ORM で…」は、設計(P003 §1.2、ADR-008)で ORM を使わず SQLAlchemy Core にした。P001 の記述は更新していない(要件定義の確定後の変更のため)。

#### CR-005 で付いた ★FIXME★(12 件。2026-10-09 に解消。未解消 0 件)

**未解消の★FIXME★: 0件。** 2026-10-09 に依頼者が下表の 12 件をすべて受け入れ、各箇所の ★FIXME★ を ★ACCEPTED★(検討・承認理由・残存リスク付き)に書き換えた。以下は当時の一覧。`docs/` 配下を `grep -rn "★FIXME★"` で検索し、CR-005 で付けたものを同じ論点ごとに 1 件にまとめた。暫定の ADR 番号(「ADR-016 見込み ★FIXME★」)は P021 で ADR-016 に確定して外した。

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 73 | `docs/P001-requirement.md` §6 SC-03 | PDB 情報タブの表示項目(コンテナ名・DB 名・サービス名・バージョン・文字セット・接続ユーザー・表領域、表領域の割り当て、セグメントの使用量、表領域の使用状況) | 項目を変える場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 74 | `docs/P001-requirement.md` §6 SC-03 | 利用者が削除・改名したひな型を、次の起動で戻さない | 戻す場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 75 | `docs/P001-requirement.md` §6 SC-03、`server/src/dbfaq_api/pdb_templates.py` | 依頼者の指定 2 件以外のひな型の選定(表領域の使用率、データファイル、一時表領域、セグメントの大きい順、統計の鮮度、無効なオブジェクト、使用できない索引、無効な制約、オブジェクトの数、セッション、ロック待ち、長時間の処理、ユーザーごとの割り当て)と、USERS 表領域・LOB を「権限の要る版/要らない版」の 2 つずつにしたこと | 追加・削除は CR(または画面で保存・削除)(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 76 | `docs/P001-requirement.md` §8.1 | 保存済み Query の一覧・保存は 1 秒以内、PDB 情報タブは Oracle の処理時間 + 1 秒以内 | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 77 | `docs/P001-requirement.md` §8.3 | 保存時には SQL を検査しない(書きかけも保存できる。実行時に検査する) | 保存時に検査する場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 78 | `docs/P002-frontend-spec.md` §2.1.2 | ドラム缶のアイコンは ER 図のノードにせず、キャンバス領域の左上に固定で置く | 置き場所を変える場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 79 | `docs/P002-frontend-spec.md` §2.2.8 | [上書き保存] は確認ダイアログを出さない | 確認を出す場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 80 | `docs/P002-frontend-spec.md` §2.2.8 | 無くなったテーブルの保存済み Query を画面で一覧・付け替えする機能は作らない(要求は「残す」「同名で復活したら使える」まで) | 一覧・付け替えが要る場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 81 | `docs/P003-backend-spec.md` §4.7 | LOB の実データの合計を `DBMS_XMLGEN` による動的な問い合わせで求める(Query の検査は `DBMS_XMLGEN` を拒否しない)。単位は BLOB はバイト、CLOB・NCLOB は文字数 | 検査で `DBMS_XMLGEN` を拒否する場合は CR(ひな型 03・04 は使えなくなる)(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 82 | `docs/P003-backend-spec.md` §4.7、`docs/ArchitectureHandbook.md` §9 | DBA 権限のあるユーザーでの、権限の要るひな型 9 件と「表領域の使用状況」の実行結果は未確認(hr では ORA-00942 までを確認) | 権限のあるユーザーで確認できれば解消(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 83 | `docs/P003-backend-spec.md` §6、本書 7 章の 9 | 保存済み Query のバックアップは運用(SQLite ファイルの複写)に任せ、アプリに機能を持たせない | バックアップ・エクスポート機能が要る場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 84 | `docs/P901-cr-direction/CR-005.md` 優先度の判断理由 | 優先度の指定が無く、ルーブリック(影響度 高 × 緊急度 低)で「中」と仮置き | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |

#### CR-006 で付いた ★FIXME★(3 件。2026-10-09 に解消。未解消 0 件)

**未解消の★FIXME★: 0件。** 2026-10-09 に依頼者が下表の 3 件をすべて受け入れ(「保留事項はすべて受け入れます」)、各箇所の ★FIXME★ を ★ACCEPTED★(検討・承認理由・残存リスク付き)に書き換えた。以下は当時の一覧。`docs/` 配下を `grep -rn "★FIXME★"` で検索し、CR-006 で付けたものを列挙した。暫定の ADR 番号(「ADR-017 見込み ★FIXME★」)は P021 で ADR-017 に確定して外した。

| # | 所在(ファイル・章節) | 想定で補った内容 | CR起票候補か |
| --- | --- | --- | --- |
| 85 | `docs/P003-backend-spec.md` §3.1、ADR-017 | 対象スキーマを、接続ごとにカレントスキーマ(`conn.current_schema`)を `oracle.schema` にすることで示す。Query タブのスキーマ名の無い表名も対象スキーマの表になる | 別の方式にする場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 86 | `docs/P003-backend-spec.md` §4.7、ADR-016 | 登録済みのひな型は、SQL が以前の版と完全に一致する(利用者が変えていない)ときだけ新しい版に更新する。説明・名前も以前の版のままなら更新する | 常に上書きする・更新しない場合は CR(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |
| 87 | `docs/P901-cr-direction/CR-006.md` 優先度の判断理由 | 優先度の指定が無く、ルーブリック(影響度 高 × 緊急度 低)で「中」と仮置き | -(2026-10-09 に依頼者が受け入れ。★ACCEPTED★ に書き換えた) |

* 補足: CR-005 の ★ACCEPTED★ #82(DBA 権限のあるユーザーでの未確認)は、CR-006 で `dbfaq_ro` により全件を確認し、解消した(各箇所に注記)。

### 10.6 その他

* B001〜B003 は 9579d85 としてコミット済み。★FIXME★ の受け入れと CR-001 の変更はその次のコミット(a316427)に含まれる。CR-002・CR-003 の変更(B005〜B009)はコミット ac666af に含まれる。CR-004 の変更(B010・B011)はコミット 805fd6b に含まれる。CR-005 の変更(B012〜B014)はコミット 6767764 に含まれる。CR-006 の変更(B015・B016)は CR-006 のコミット(このファイルの次のコミット)に含まれる。コミットとリモートへのプッシュは人間の判断で行う。
* CR-002 で廃止した MCP サーバを Claude Desktop などから単体で使っていた場合、その使い方はできなくなった(P001 §3.1 の旧 ★ACCEPTED★。依頼者の指示「MCP の部分は廃止」による)。
* `e2e/scripts/run-suite.sh` はボリュームを消すため、運用環境では実行しない。
* 所見(F011 の関連): A09 は [実行] ボタンを正規表現 `/実行/` で探している。いまは HR.EMPLOYEES の保存済み Query に「実行」を含む名前が無いため合格するが、そのような名前で保存すると A09 が失敗しうる(A10 は F011 で完全一致に直した)。A09 は失敗していないため直していない。

## 11. リリース判定

**OK**(CR-006。2026-10-09 に ★FIXME★ 3 件の受け入れにより保留から変更)

根拠(CR-006 後):

* テスト: 接続ユーザーを読み取り専用ユーザー `dbfaq_ro` にして、単体・結合・受け入れ結合がすべて合格(9 章)。スイートの再実行性(A07)も確認した。P202〜P205 は不要だった。CR-005 のひな型が登録済みの環境で、未変更のひな型が新しい版に更新されることを実ファイルで確認した。
* 出荷影響「要対応」: **0 件**。REQ-SCREEN-025・027 の未確認だった正常系(★ACCEPTED★ #82)も確認できた。
* 未解消の ★FIXME★: **0 件**(10.5)。#85〜#87 は 2026-10-09 に依頼者が受け入れ、★ACCEPTED★ に書き換えた。
* 設計判断: ADR-017(推奨の接続ユーザー `dbfaq_ro`、カレントスキーマ)を追加し、ADR-016 に未変更のひな型の更新を加えた。2026-10-09 に依頼者が承認した(#85・#86 の受け入れ)。
* README に `dbfaq_ro` を作る理由・作り方・`config.yaml` への登録を載せた(依頼者の指示)。

以下は CR-005 時点の根拠(履歴):

**OK**(CR-005。2026-10-09 に ★FIXME★ 24 件の受け入れにより保留から変更)

根拠(CR-005 後):

* テスト: 単体・結合・受け入れ結合がすべて合格(9 章、P205)。スイートの再実行性(A07)も確認した。未解決の障害なし(P202-fix-unresolved.md。F011・F012 はテストコードの欠陥で解決済み)。マイグレーション 0002 は既存のデータベースへの適用と再起動での冪等性を確認した(P103、A04)。
* 出荷影響「要対応」: **0 件**(10.1)。CR-005 で追加した要求(REQ-SCREEN-020〜027、REQ-API-008〜012、REQ-ORA-006)はすべて OK(4 章)。
* 未解消の ★FIXME★: **0 件**(10.5)。CR-004 の #61〜#72 と CR-005 の #73〜#84 は、2026-10-09 に依頼者が全件を受け入れ、★ACCEPTED★ に書き換えた。
* 設計判断: ADR-016(保存済み Query をスナップショットと結ばない、ひな型を 1 回だけ登録)を追加した。ADR-015(CR-004)とあわせ、関連する ★FIXME★ の受け入れにより 2026-10-09 に依頼者が承認した。
* 運用上の注意: 保存済み Query は作り直せないデータになったため、SQLite のバックアップ手順(7 章の 9)を運用に組み込む必要がある。

以下は CR-004 時点の根拠(履歴):

根拠(CR-004 後):

* テスト: 単体・結合・受け入れ結合がすべて合格(9 章、P205)。スイートの再実行性(A07)も確認した。未解決の障害なし(P202-fix-unresolved.md)。HR のテストのベースラインは依頼者の判断で 8 表に改めた(P202 F010)。
* 出荷影響「要対応」: **0 件**(10.1)。CR-004 で追加した要求(REQ-SCREEN-016〜019、REQ-API-006・007、REQ-ORA-005)はすべて OK(4 章)。
* **未解消の ★FIXME★: 12 件**(10.5 の #61〜#72)。Query タブの設計で Agent が想定で補ったもの。依頼者が確認し、そのままでよいものは ★ACCEPTED★ に書き換え、変えたいものは CR を起票すれば OK にできる。
* 設計判断: ADR-011 を更新し(任意 SQL を作らない → ADR-015 の検査を通した SELECT を実行)、ADR-015 を追加した。依頼者の承認は未(★FIXME★ #62 と同じ論点)。

以下は CR-003 時点の根拠(履歴):

* テスト: 単体・結合・受け入れ結合がすべて合格(9 章)。CR-003 後も単体 + 結合を 2 回、A01〜A06・A08 を 2 回続けて合格した。CR-002 後に単体 + 結合を 2 回、A01〜A06・A08 を 2 回続けて合格し、スイートの再実行性(A07)も確認した。CR-002 で見つかった退行 2 件(F007・F008)は修正済みで、未解決の障害なし(P202-fix-unresolved.md)。配布資産は整備済みで、compose でのビルド・起動・停止を実際に確認した。
* 出荷影響「要対応」: **0 件**(10.1)。以前の 2 件は CR-001 で解消した。
* 設計判断: CR-002 の ADR-014(backend が Oracle に直接接続)と ADR-007 の変更(1 つの uv プロジェクトに 2 パッケージ)は 2026-09-27 に依頼者が承認し、確定の仕様とした。
* 本番検証・代替検証・自明: 理由を記載済み(10.2)。判定の根拠には数えない。本番検証の REQ-NFR-004-TLS は稼働前に運用側で確認する。
* 未解消の ★FIXME★: **0 件**(10.5)。CR-002 の #59 は 2026-09-27、CR-003 の #60 は 2026-09-28 に依頼者が優先度を確認し、★ACCEPTED★ にした。第 1 リリースの 58 件は 2026-09-24 に人間が全件受け入れ、★ACCEPTED★ にした。
* 4 章の対応表で状態が OK 以外の行は、NO_TEST_IMPL 3 件(自明)・NO_TEST_CASE 1 件(代替検証)・NO_TEST_PLAN 1 件(自明。REQ-ARCH-008。REQ-ARCH-001 は CR-002 でテスト対象になり OK)・BLOCKED 1 件(本番検証の REQ-NFR-004-TLS)で、いずれも理由を記載済み。
