# P008 結合テスト定義(スプリント内/モジュール間)— 目次

入力: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`、`docs/P007-impl-direction.md`。
実行は P103(Executor)。結果は `docs/test-records/YYYYMMDD-HHMM-test-record.md` に記録する。失敗してもその場で修正せず、Reviewer Loop(P201〜)に引き渡す。
テストデータの方針は `docs/P006-test-plan.md` §3.2(Oracle HR は読み取りのみ、SQLite はテストごとに一時ファイル、compose はスイート実行ごとにボリュームを消してから起動)。

| スプリント | テスト |
|---|---|
| U002 mcp-server(CR-002 で U007 に移設) | T01〜T04(T05 は CR-002 で廃止) |
| U003 backend-api | T06〜T08 |
| U004 frontend-er | T10 |
| U005 frontend-detail | T11 |
| U006 deploy | T12 |
| U007 oracle-in-backend(CR-002) | T01〜T04・T06・T08・T12 の再実行、T09(置き換え) |
| U009 query-tab(CR-004) | T13(新規)、T03(Query の経路を追加)。T01〜T12 は回帰として再実行 |
| U010 saved-queries-pdb(CR-005) | T14・T15(新規)。T01〜T13 は回帰として再実行 |

- [x] T01 [Oracle: HR のスナップショット](./P008-test-direction/T01-oracle-snapshot-hr.md) — OracleClient.get_schema_snapshot が HR の表・列・制約・インデックスを正しく返す ※CR-002で再実行
- [x] T02 [Oracle: HR のページ取得](./P008-test-direction/T02-oracle-rows-hr.md) — OracleClient.get_table_rows の主キー順ページ送りと異常系 ※CR-002で再実行
- [x] T03 [Oracle: 読み取り専用の確認](./P008-test-direction/T03-oracle-readonly.md) — DML が ORA-01456 で拒否され、データが変わらない ※CR-002で再実行 ※CR-004で Query の経路を追加して再実行
- [x] T04 [Oracle: エラー変換](./P008-test-direction/T04-oracle-errors.md) — 認証失敗・タイムアウトのコードとタイムアウト後の回復 ※CR-002で再実行
- [x] T05 [MCP: stdio の標準出力](./P008-test-direction/T05-mcp-stdio-hygiene.md) — **CR-002 で廃止**(MCP サーバが無くなり対象が無い。テストコードも削除)
- [x] T06 [API: スキーマの再読み込み](./P008-test-direction/T06-api-refresh-schema.md) — backend→Oracle→SQLite の連携 ※CR-002で再実行
- [x] T07 [API: テーブルデータ](./P008-test-direction/T07-api-rows.md) — rows API のページ取得とエラー変換
- [x] T08 [API: Oracle に届かないとき](./P008-test-direction/T08-api-oracle-unreachable.md) — 起動でき、前回のスナップショットが残り、health が degraded ※CR-002で再実行
- [x] T09 [API: Oracle との通信断からの回復](./P008-test-direction/T09-api-oracle-recovery.md) — TCP 中継を止めて再開し、再起動なしで回復する ※CR-002で「MCP 子プロセスの回復」から置き換え
- [x] T10 [クライアント: ER 図の API(開発構成)](./P008-test-direction/T10-client-proxy-schema.md) — Vite proxy 越しの schema/refresh/health
- [x] T11 [クライアント: 詳細の API(開発構成)](./P008-test-direction/T11-client-proxy-detail.md) — Vite proxy 越しの詳細・rows・404
- [x] T12 [compose の連携と公開範囲](./P008-test-direction/T12-compose-stack.md) — web→api→Oracle、api 非公開、イメージに設定なし ※CR-002で再実行
- [x] T13 [Oracle: SELECT の実行・エラー位置・CSV](./P008-test-direction/T13-oracle-query.md) — run_query・export_csv・Query API を実 Oracle で ※CR-004により追加
- [x] T14 [Oracle: PDB の情報とひな型](./P008-test-direction/T14-oracle-pdb.md) — get_pdb_info・GET /api/pdb・ひな型 17 件を実 Oracle で ※CR-005により追加
- [x] T15 [API: 保存済み Query とスナップショットの置き換え](./P008-test-direction/T15-api-saved-queries.md) — 保存・重複・テーブルごとの分離、テーブルが無くなっても残り戻ると使える、再起動でひな型が重複しない ※CR-005により追加

FAIL/BLOCKED が残った場合は、Reviewer Loop(P201〜P205)への引き渡しが必要。

**P103 の結果(2026-09-23、`docs/test-records/20260923-0315-test-record.md`)**: T05 が FAIL(MCP サーバが stderr に JSON ログを出していない)。T08 は PASS だが所要時間に懸念あり。Reviewer Loop(P201〜)へ引き渡す。

**P103(CR-002、2026-09-27、`docs/test-records/20260927-0233-test-record.md`)**: T01〜T04・T06〜T12 PASS(T05 は廃止)。pytest の結合テストは 2 回続けて同じ結果。T08 の所要時間(132 秒)の原因は、Oracle に届かない間の接続プールの close が長く待つこと(python-oracledb の挙動)。Reviewer Loop(P201〜)へ引き渡す。

**P103(CR-003、2026-09-27、`docs/test-records/20260927-2358-test-record.md`)**: 単体 + T01〜T04・T06〜T09 を 2 回続けて 144 passed、T10〜T12 PASS(T05 は廃止)。テストコードは import 先だけを変えた。

**P103(CR-004、2026-10-04、`docs/test-records/20261004-1430-test-record.md`)**: T02〜T04・T07・T09・T10・T11・T13 PASS(pytest は 2 回とも同じ結果)。T01・T06・T08・T12 は FAIL。原因は開発用 Oracle の HR に 2026-09-29 に表 `EMPLOYEE_FIGURE` が追加され、ベースラインの 7 表・外部キー 10 本と一致しないこと(アプリケーションの欠陥ではない)。Reviewer Loop(P201〜)へ引き渡す。

**P205(CR-004、2026-10-04、`docs/test-records/20261004-2110-test-record.md`)**: F009・F010 の後、T01〜T04・T06〜T13 PASS(pytest は 2 回とも 225 passed)。HR のベースラインは 8 表(P006 §3.2)。

**P103(CR-005、2026-10-07、`docs/test-records/20261007-0100-test-record.md`)**: T01〜T04・T06〜T15 PASS(T05 は廃止)。pytest は 2 回とも 320 passed。T10 の期待値の直し漏れ(F010)を P006 §3.2 に合わせて直した。
