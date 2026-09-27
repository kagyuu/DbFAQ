# P202 修正計画(目次)

入力: `docs/P201-review-report.md`(1 回目)、`docs/test-records/20260923-0315-test-record.md`、`docs/test-records/20260923-0320-test-record.md`。
修正は P203 で 1 件ずつ行う。A07(NOT RUN)は修正ではなく、全修正後に P205 で実行する。

- [x] F001 [MCP サーバの JSON ログ](./P202-fix-plan/fixed/F001-mcp-json-log.md) — T05: 起動・終了時に stderr へ JSON ログを出す
- [x] F002 [A01 のロケータ](./P202-fix-plan/fixed/F002-a01-locator.md) — A01: ツールバーの件数表示を完全一致で確認する
- [x] F003 [A02 の行の特定](./P202-fix-plan/fixed/F003-a02-row-locator.md) — A02: 列名セルの完全一致で行を特定する
- [x] F004 [A05 の手順](./P202-fix-plan/fixed/F004-a05-procedure.md) — A05: -g のパターンとコピーした SQLite の所有者
- [x] F005 [A06 のスクリプト](./P202-fix-plan/fixed/F005-a06-python310.md) — A06: Python 3.10 で動く書き方に
- [x] F006 [接続プールの待ち時間](./P202-fix-plan/fixed/F006-pool-wait-timeout.md) — T08 所見: Oracle に届かないとき早く失敗させる

## CR-002(2026-09-27)

入力: `docs/P201-review-report.md`(CR-002 の 1 回目)、`docs/test-records/20260927-0233-test-record.md`、`docs/test-records/20260927-0238-test-record.md`。A07 は全修正後に P205 で実行する。

- [x] F007 [ネットワークの OSError の変換](./P202-fix-plan/fixed/F007-oserror-conversion.md) — A03: ホスト名を解決できないとき health が 500 になる。`OSError` を `OracleFailure` に変換し、health は常に 200
- [x] F008 [接続プールの close の上限](./P202-fix-plan/fixed/F008-pool-close-timeout.md) — T08 所見: Oracle に届かない間 close が約 2 分戻らない。待ち時間に上限を設ける
