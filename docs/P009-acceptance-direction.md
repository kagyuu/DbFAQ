# P009 受け入れ結合テスト定義(スプリント横断/システム/受入)— 目次

入力: `docs/P001-requirement.md`、`docs/P006-test-plan.md`。
実行は P201(Reviewer Loop)。compose で起動した web(`http://localhost:8088`)の同一オリジンに対して実行する(P003 §7)。
テストデータの方針(`docs/P006-test-plan.md` §3.2): スイートの開始前(アプリ起動前)に 1 回だけ `docker compose down -v` でベースラインに戻し、以降のテストは A01 が作ったスナップショットを順に使う。A04(再起動耐性)は途中で復元を挟まない。HR は読み取りのみ。

- [x] A01 [ER 図のシナリオ](./P009-acceptance-direction/A01-er-diagram-scenario.md) — 初回読み込み → ER 図 → 拡大縮小・ミニマップ・検索 → クリックで詳細へ → ノードのドラッグ(手順 8・9 は CR-001 で追加) ※CR-002で再実行
- [x] A02 [テーブル詳細のシナリオ](./P009-acceptance-direction/A02-table-detail-scenario.md) — スキーマ情報 → 外部キーで移動 → データタブのページ送り ※CR-002で再実行
- [x] A03 [Oracle に届かないときのシナリオ](./P009-acceptance-direction/A03-oracle-down-scenario.md) — 保存済みで閲覧でき、エラーが正しく表示され、回復する ※CR-002で再実行
- [x] A04 [再起動耐性](./P009-acceptance-direction/A04-restart-resilience.md) — 再起動・down/up でスナップショットが残り、マイグレーションが冪等、MCP の子プロセスが無い ※CR-002で再実行 ※CR-005で手順 8(保存済み Query が残り、ひな型が重複しない)を追加して再実行
- [x] A05 [性能](./P009-acceptance-direction/A05-performance.md) — HR と 300 表規模での表示時間 ※CR-002で再実行 ※CR-004で Query の性能を追加
- [x] A06 [読み取りのみ・秘密情報・公開範囲](./P009-acceptance-direction/A06-security-readonly.md) — HR のチェックサム不変、パスワード非露出、web のみ公開 ※CR-002で再実行 ※CR-004で Query API の拒否を追加
- [x] A08 [同時利用者 10 名](./P009-acceptance-direction/A08-concurrent-users.md) — 10 名同時でエラー 0、性能目標内 ※CR-001により追加(A07 の前に単独で実行し、A07 のスイートにも含める) ※CR-002で再実行
- [x] A09 [Query タブのシナリオ](./P009-acceptance-direction/A09-query-tab-scenario.md) — ひな形 → JOIN → 実行 → 500 行の打ち切り → CSV で全行 → エラー位置 → DELETE の拒否 ※CR-004により追加(スイートでは A02 の後に実行)
- [x] A10 [保存済み Query と PDB 画面のシナリオ](./P009-acceptance-direction/A10-saved-queries-pdb-scenario.md) — 保存 → テーブルごとの分離 → 復元・実行 → 上書き・変更・削除 → ドラム缶 → PDB 情報 → ひな型の実行・保存 ※CR-005により追加(スイートでは A09 の後に実行) ※CR-006で手順 10・13 の期待値を変えて再実行
- [x] A07 [スイートの再実行性](./P009-acceptance-direction/A07-suite-repeatability.md) — A01〜A06・A08〜A10 を 2 回続けて同じ結果(A08 は CR-001 で追加) ※CR-002で再実行 ※CR-004で A09 を追加 ※CR-005で A10 を追加して再実行 ※CR-006で再実行

FAIL/BLOCKED が残った場合は、P202(修正計画)への引き渡しが必要。

**P201 1 回目(2026-09-23、`docs/test-records/20260923-0320-test-record.md`)**: A03・A04 PASS。A01・A02・A05・A06 FAIL(いずれもテストコード/手順側の欠陥)。A07 は修正後に実行(未実行のため `[ ]` のまま)。P202 へ引き渡す。

**P205(2026-09-23、`docs/test-records/20260923-0350-test-record.md`)**: A01〜A07 すべて PASS。

**P201(CR-001、2026-09-24、`docs/test-records/20260924-2352-test-record.md`)**: A01(手順 8・9 を含む)〜A06・A08 を 2 回続けて実行し、すべて PASS・出力同一(A07 PASS)。

**P201(CR-002 の 1 回目、2026-09-27、`docs/test-records/20260927-0238-test-record.md`)**: A03 FAIL(ホスト名を解決できないとき health が 500)。P202 へ(F007・F008)。

**P205(CR-002、2026-09-27、`docs/test-records/20260927-0244-test-record.md`)**: A01〜A08 すべて PASS(スイートを 2 回続けて実行し、出力が同一)。

**P201(CR-003、2026-09-28、`docs/test-records/20260928-0001-test-record.md`)**: A01〜A08 すべて PASS(スイートを 2 回続けて実行し、出力が同一)。

**P201(CR-004 の 1 回目、2026-10-04、`docs/test-records/20261004-1440-test-record.md`)**: A02・A04・A08・A09 PASS。A01・A03・A05 FAIL(HR に表 `EMPLOYEE_FIGURE` が追加され 7 表の期待値と合わない)、A06 は偽の PASS(チェックサムを取得できず空同士を比較)。P202 へ(F009・F010)。

**P205(CR-004、2026-10-04、`docs/test-records/20261004-2110-test-record.md`)**: A01〜A09 すべて PASS(スイートを 2 回続けて実行し、出力が同一)。HR のベースラインは 8 表(依頼者の判断。P202 F010)。

**P201(CR-005 の 1 回目、2026-10-07、`docs/test-records/20261007-0115-test-record.md`)**: A10 FAIL(テストのロケータ)。P202 へ(F011)。

**P205(CR-005、2026-10-07、`docs/test-records/20261007-0130-test-record.md`)**: A01〜A10 すべて PASS(スイートを 2 回続けて実行し、出力が同一)。

**P201(CR-006、2026-10-09、`docs/test-records/20261009-0051-test-record.md`)**: 接続ユーザー `dbfaq_ro` で A01〜A10 すべて PASS(スイートを 2 回続けて実行し、出力が同一)。
