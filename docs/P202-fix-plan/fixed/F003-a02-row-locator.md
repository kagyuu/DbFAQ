あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F003

## 【対応する失敗テスト】A02

* A02(テーブル詳細のシナリオ)

## 【障害記録】

* 記録: `docs/test-records/20260923-0320-test-record.md` の A02。`filter({ hasText: 'EMPLOYEE_ID' })` が、コメントに employee_id を含む MANAGER_ID の行にも一致して 2 行になり strict mode 違反。
* 原因区分: テスト側の欠陥(指示 A02 手順 1 は「EMPLOYEE_ID の行」を確認するもので、テストコードの行の特定方法が不正確)。アプリの表示は P002 §2.2.2 どおり。カバレッジは失われない。

## 【参照ファイル】

* `e2e/tests/a02-table-detail.spec.ts`

## 【調査方針】

* 同じ問題が SALARY など他の行の特定にも無いか確認する。

## 【修正方針】

* 列名のセル(2 列目)が完全一致する行で特定する(例: `cols.getByRole('row').filter({ has: page.getByRole('cell', { name: 'EMPLOYEE_ID', exact: true }) })`)。確認する値(`NUMBER(6)`、「不可」、`🔑 1`)は変えない。「1」の確認は「🔑 1」の確認に置き換えて明確にする(弱めない)。

## 【試行錯誤してよい範囲】

* `e2e/tests/a02-table-detail.spec.ts` のみ。

## 【修正成功時に更新するdocs】

* なし。

## 【ロールバック条件】

* 該当なし(ソースコード変更を伴わない)。

## 【検証コマンド】

* `cd e2e && npx playwright test tests/a02-table-detail.spec.ts`(A01 の後)

## 【完了条件】

* A02 が合格する。

## 重要:

* 作業開始前に現在の変更状態を確認してください(本リポジトリは作業ツリーが未コミットのため、P203 の開始時にリポジトリ外へ zip で退避済みのバックアップを使う)。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新する。

## 修正内容の詳細(P203、2026-09-23)

* 変更: `e2e/tests/a02-table-detail.spec.ts` — 列名セルの完全一致(`getByRole('cell', { name, exact: true })`)で行を特定する `rowOf` を使う。主キーの確認を「1」から「🔑 1」に明確化(弱めていない)。
* 結果の確認は P205 で行う。
