# P009 受け入れ結合テスト定義(スプリント横断/システム/受入)— 目次

入力: `docs/P001-requirement.md`、`docs/P006-test-plan.md`。
実行は P201(Reviewer Loop)。compose で起動した web(`http://localhost:8088`)の同一オリジンに対して実行する(P003 §7)。
テストデータの方針(`docs/P006-test-plan.md` §3.2): スイートの開始前(アプリ起動前)に 1 回だけ `docker compose down -v` でベースラインに戻し、以降のテストは A01 が作ったスナップショットを順に使う。A04(再起動耐性)は途中で復元を挟まない。HR は読み取りのみ。

- [x] A01 [ER 図のシナリオ](./P009-acceptance-direction/A01-er-diagram-scenario.md) — 初回読み込み → ER 図 → 拡大縮小・ミニマップ・検索 → クリックで詳細へ
- [x] A02 [テーブル詳細のシナリオ](./P009-acceptance-direction/A02-table-detail-scenario.md) — スキーマ情報 → 外部キーで移動 → データタブのページ送り
- [x] A03 [Oracle に届かないときのシナリオ](./P009-acceptance-direction/A03-oracle-down-scenario.md) — 保存済みで閲覧でき、エラーが正しく表示され、回復する
- [x] A04 [再起動耐性](./P009-acceptance-direction/A04-restart-resilience.md) — 再起動・down/up でスナップショットが残り、マイグレーションが冪等
- [x] A05 [性能](./P009-acceptance-direction/A05-performance.md) — HR と 300 表規模での表示時間
- [x] A06 [読み取りのみ・秘密情報・公開範囲](./P009-acceptance-direction/A06-security-readonly.md) — HR のチェックサム不変、パスワード非露出、web のみ公開
- [x] A07 [スイートの再実行性](./P009-acceptance-direction/A07-suite-repeatability.md) — A01〜A06 を 2 回続けて同じ結果

FAIL/BLOCKED が残った場合は、P202(修正計画)への引き渡しが必要。

**P201 1 回目(2026-09-23、`docs/test-records/20260923-0320-test-record.md`)**: A03・A04 PASS。A01・A02・A05・A06 FAIL(いずれもテストコード/手順側の欠陥)。A07 は修正後に実行(未実行のため `[ ]` のまま)。P202 へ引き渡す。

**P205(2026-09-23、`docs/test-records/20260923-0350-test-record.md`)**: A01〜A07 すべて PASS。
