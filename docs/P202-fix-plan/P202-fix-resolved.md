# 解決済み修正障害一覧

## 概要

* 修正完了した障害数: 6(うち F002〜F005 の結果の確定は P205 の再実行による)
* 未解決の障害数: 0
* 全体状態: ALL_RESOLVED

## 解決済障害一覧

| 修正タスク | 対応障害 | 結果 | テスト日付 | 修正日付 |
|---|---|---|---|---|
| F001 | T05 | RESOLVED | 2026/09/23 | 2026/09/23 |
| F002 | A01 | RESOLVED | 2026/09/23 | 2026/09/23 |
| F003 | A02 | RESOLVED | 2026/09/23 | 2026/09/23 |
| F004 | A05 | RESOLVED | 2026/09/23 | 2026/09/23 |
| F005 | A06 | RESOLVED | 2026/09/23 | 2026/09/23 |
| F006 | T08(所見) | RESOLVED | 2026/09/23 | 2026/09/23 |

## 解決済障害

### F001: MCP サーバの JSON ログ

* 対応するテストID: T05
* 対応するテスト記録: docs/test-records/20260923-0315-test-record.md
* 失敗していたテストコマンド: `cd server && uv run pytest tests/integration/test_t05_stdio.py -v`
* 修正内容: 起動・終了時に stderr へ JSON ログを出す
* 変更したソースコード: server/src/dbfaq_mcp/__main__.py
* 更新したdocs: なし
* 実行したテスト: 単体 131、T05・T01
* テスト結果: すべて合格
* 残課題: なし
* 修正経緯: 初回で解決(詳細は fixed/F001-mcp-json-log.md)

### F002: A01 のロケータ

* 対応するテストID: A01
* 対応するテスト記録: docs/test-records/20260923-0320-test-record.md
* 失敗していたテストコマンド: `cd e2e && npx playwright test tests/a01-er-diagram.spec.ts`
* 修正内容: ツールバーの件数表示を完全一致で確認する
* 変更したソースコード: なし(テストコードの欠陥のため、e2e/tests/a01-er-diagram.spec.ts を修正)
* 更新したdocs: なし
* 実行したテスト: P205 で A01
* テスト結果: P205 の記録を参照
* 残課題: なし
* 修正経緯: 初回で修正

### F003: A02 の行の特定

* 対応するテストID: A02
* 対応するテスト記録: docs/test-records/20260923-0320-test-record.md
* 失敗していたテストコマンド: `cd e2e && npx playwright test tests/a02-table-detail.spec.ts`
* 修正内容: 列名セルの完全一致で行を特定する
* 変更したソースコード: なし(テストコードの欠陥のため、e2e/tests/a02-table-detail.spec.ts を修正)
* 更新したdocs: なし
* 実行したテスト: P205 で A02
* テスト結果: P205 の記録を参照
* 残課題: なし
* 修正経緯: 初回で修正

### F004: A05 の手順

* 対応するテストID: A05
* 対応するテスト記録: docs/test-records/20260923-0320-test-record.md
* 失敗していたテストコマンド: `bash e2e/scripts/run-suite.sh` の A05 部分
* 修正内容: `-g` のパターンを `"hr:"`・`"large:"` に、コピーした SQLite の所有者を uid 10001 に
* 変更したソースコード: なし(テスト指示側の誤りのため、e2e/scripts/run-suite.sh・a05-load-large.sh と docs/P009-acceptance-direction/A05-performance.md を訂正)
* 更新したdocs: docs/P009-acceptance-direction/A05-performance.md
* 実行したテスト: P205 で A05
* テスト結果: P205 の記録を参照
* 残課題: なし
* 修正経緯: 初回で修正

### F005: A06 のスクリプト

* 対応するテストID: A06
* 対応するテスト記録: docs/test-records/20260923-0320-test-record.md
* 失敗していたテストコマンド: `bash e2e/scripts/a06-security.sh`
* 修正内容: Python 3.10 で動く書き方に変更
* 変更したソースコード: なし(テストスクリプトの欠陥のため、e2e/scripts/a06-security.sh を修正)
* 更新したdocs: なし
* 実行したテスト: P205 で A06
* テスト結果: P205 の記録を参照
* 残課題: なし
* 修正経緯: 初回で修正

### F006: 接続プールの待ち時間

* 対応するテストID: T08(所見)
* 対応するテスト記録: docs/test-records/20260923-0315-test-record.md
* 失敗していたテストコマンド: (PASS だが 97.57 秒)`cd server && uv run pytest tests/integration/test_t08_oracle_unreachable.py`
* 修正内容: プールを TIMEDWAIT(wait_timeout=connect_timeout_sec)にして早く失敗させる
* 変更したソースコード: server/src/dbfaq_mcp/db.py、server/tests/unit/mcp/test_db.py
* 更新したdocs: docs/P003-backend-spec.md §3.1
* 実行したテスト: 単体 131、T08
* テスト結果: 合格、T08 は 8.73 秒
* 残課題: 接続拒否時のメッセージが DPY-4005(プール取得のタイムアウト)になる(P302 に記載)
* 修正経緯: 初回で解決

## CR-002(2026-09-27)

### F007: ネットワークの OSError の変換

* 対応するテストID: A03
* 対応するテスト記録: docs/test-records/20260927-0238-test-record.md
* 失敗していたテストコマンド: `bash e2e/scripts/run-suite.sh`(A03 手順 1)
* 修正内容: python-oracledb がそのまま送出する `OSError`(`socket.gaierror` など)を `OracleFailure` に変換。health は想定外の例外でも 200・degraded を返す
* 変更したソースコード: server/src/dbfaq_api/oracle/errors.py、server/src/dbfaq_api/oracle/db.py、server/src/dbfaq_api/services.py、server/tests/unit/oracle/test_errors.py、server/tests/unit/oracle/test_db.py、server/tests/unit/api/test_api.py
* 更新したdocs: docs/P003-backend-spec.md §3.2・§4.3
* 実行したテスト: 単体 128、compose での手動確認(health 200・degraded、refresh 502)
* テスト結果: 合格。A03 は P205 で再実行
* 残課題: なし
* 修正経緯: 初回で解決

### F008: 接続プールの close の上限

* 対応するテストID: T08(所見)
* 対応するテスト記録: docs/test-records/20260927-0233-test-record.md
* 失敗していたテストコマンド: (PASS だが 131.97 秒)`cd server && DBFAQ_CONFIG=../config.yaml uv run pytest tests/integration/test_t08_oracle_unreachable.py`
* 修正内容: `Database.close` の待ち時間を `connect_timeout_sec` で打ち切る
* 変更したソースコード: server/src/dbfaq_api/oracle/db.py、server/tests/unit/oracle/test_db.py
* 更新したdocs: docs/P003-backend-spec.md §3.1、docs/ArchitectureHandbook.md §9
* 実行したテスト: 単体 128、T08
* テスト結果: 合格、T08 は 9.22 秒
* 残課題: なし
* 修正経緯: 初回で解決

* F009(CR-004、2026-10-04): `hr_checksum.py` を LOB 列の表に対応させ、`reset-and-up.sh`・`a06-security.sh` がチェックサムの取得失敗を FAIL にするようにした。記録: `fixed/F009-hr-checksum-lob.md`
* F010(CR-004、2026-10-04): 依頼者の判断(案 B)で、HR のベースラインを 8 表(`EMPLOYEE_FIGURE` を含む)に改め、テストの期待値と P006 §3.2 などを更新した。記録: `fixed/F010-hr-extra-table.md`
