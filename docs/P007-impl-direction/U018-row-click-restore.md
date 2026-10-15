あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U018 — row-click-restore(※CR-013により追加)

保存済み Query の一覧の行をクリックすると、その行の [復元] を押したときと同じことをする。変更要求: `docs/P901-cr-direction/CR-013.md`。**frontend だけの変更。**

## タスク一覧(OKF副目次)

- [x] U018-T1 [行のクリックで復元する](#u018-t1-行のクリックで復元する) — `SavedQueries.tsx`
- [x] U018-T2 [受入テストの手順の追加分](#u018-t2-受入テストの手順の追加分) — A10 手順 7b

## U018-T1: 行のクリックで復元する

* 対象: `client/src/components/SavedQueries.tsx`(`Table.Tr` の `onClick` で `restore(q)`、`style` に `cursor: 'pointer'`。行の中の [復元]・[名前変更]・[削除] の `onClick` では `e.stopPropagation()` を呼び、行のクリックにしない)、`client/src/components/SavedQueries.test.tsx`
* 仕様: `docs/P002-frontend-spec.md` §2.2.8(行のクリック)
* してはいけないこと: [復元] の確認の条件(`dirty`)を変えること。ダイアログ(Mantine の `Modal` はポータルで描かれる)の中のクリックが行に伝わって復元が起きないかを確かめずに済ませること。
* 単体テスト: P006 §2.1「frontend の保存済み Query」の行のクリック(未編集ならすぐ復元、編集中なら確認、[名前変更]・[削除] のクリックでは復元しない)。
* 実行: `cd client && npm test`、`npm run build`。完了条件: 全件合格・ビルド成功。停止条件: 3 回自己修正しても合格しなければ停止して報告。

## U018-T2: 受入テストの手順の追加分

* 対象: `e2e/tests/a10-saved-queries-pdb.spec.ts`(手順 7b)
* 仕様: `docs/P009-acceptance-direction/A10-saved-queries-pdb-scenario.md`
* 完了条件: P201 で実行する。
