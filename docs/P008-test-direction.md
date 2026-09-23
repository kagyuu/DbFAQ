# P008 結合テスト定義(スプリント内/モジュール間)— 目次

入力: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`、`docs/P007-impl-direction.md`。
実行は P103(Executor)。結果は `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録する。失敗してもその場で修正せず、Reviewer Loop(P201〜)に引き渡す。
テストデータの方針は `docs/P006-test-plan.md` §3.2(Oracle HR は読み取りのみ、SQLite はテストごとに一時ファイル、compose はスイート実行ごとにボリュームを消してから起動)。

| スプリント | テスト |
|---|---|
| U002 mcp-server | T01〜T05 |
| U003 backend-api | T06〜T09 |
| U004 frontend-er | T10 |
| U005 frontend-detail | T11 |
| U006 deploy | T12 |

- [x] T01 [MCP: HR のスナップショット](./P008-test-direction/T01-mcp-snapshot-hr.md) — get_schema_snapshot が HR の表・列・制約・インデックスを正しく返す
- [x] T02 [MCP: HR のページ取得](./P008-test-direction/T02-mcp-rows-hr.md) — get_table_rows の主キー順ページ送りと異常系
- [x] T03 [MCP: 読み取り専用の確認](./P008-test-direction/T03-mcp-readonly.md) — DML が ORA-01456 で拒否され、データが変わらない
- [x] T04 [MCP: Oracle のエラー変換](./P008-test-direction/T04-mcp-oracle-errors.md) — 認証失敗・タイムアウトのコードとタイムアウト後の回復
- [x] T05 [MCP: stdio の標準出力](./P008-test-direction/T05-mcp-stdio-hygiene.md) — stdout は JSON-RPC のみ、ログは stderr
- [x] T06 [API: スキーマの再読み込み](./P008-test-direction/T06-api-refresh-schema.md) — backend→MCP→Oracle→SQLite の連携
- [x] T07 [API: テーブルデータ](./P008-test-direction/T07-api-rows.md) — rows API のページ取得とエラー変換
- [x] T08 [API: Oracle に届かないとき](./P008-test-direction/T08-api-oracle-unreachable.md) — 起動でき、前回のスナップショットが残り、health が degraded
- [x] T09 [API: MCP 子プロセスの回復](./P008-test-direction/T09-api-mcp-recovery.md) — 強制終了後に起動し直す
- [x] T10 [クライアント: ER 図の API(開発構成)](./P008-test-direction/T10-client-proxy-schema.md) — Vite proxy 越しの schema/refresh/health
- [x] T11 [クライアント: 詳細の API(開発構成)](./P008-test-direction/T11-client-proxy-detail.md) — Vite proxy 越しの詳細・rows・404
- [x] T12 [compose の連携と公開範囲](./P008-test-direction/T12-compose-stack.md) — web→api→MCP→Oracle、api 非公開、イメージに設定なし

FAIL/BLOCKED が残った場合は、Reviewer Loop(P201〜P205)への引き渡しが必要。

**P103 の結果(2026-09-23、`docs/test-records/20260923-0315-test-record.md`)**: T05 が FAIL(MCP サーバが stderr に JSON ログを出していない)。T08 は PASS だが所要時間に懸念あり。Reviewer Loop(P201〜)へ引き渡す。
