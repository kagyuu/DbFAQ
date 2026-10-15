あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U015 — query-subtabs(※CR-010により追加)

Query タブ(SC-02・SC-03)の部品をサブタブ(JOIN・保存済み Query・自然言語で SQL を作成)と共通領域(入力欄・実行・CSV・結果)に分ける。変更要求: `docs/P901-cr-direction/CR-010.md`。**frontend だけの変更。部品の振る舞いは変えない。**

## タスク一覧(OKF副目次)

- [x] U015-T1 [サブタブと共通領域](#u015-t1-サブタブと共通領域) — `QueryTab.tsx`、`LlmSqlPanel.tsx`
- [x] U015-T2 [受入テストの手順の追加分](#u015-t2-受入テストの手順の追加分) — A09・A10・A11

## U015-T1: サブタブと共通領域

* 対象: `client/src/pages/QueryTab.tsx`(Mantine の `Tabs`(`keepMounted` の既定 true のまま)で 3 つの `Tabs.Panel` に JOIN・`SavedQueries`・`LlmSqlPanel` を入れ、その下に入力欄・ボタン・結果を置く。`QueryState` に `subTab?: 'join' | 'saved' | 'llm'` を加え、未設定のときは SC-02 で `join`・SC-03 で `saved`)、`client/src/components/LlmSqlPanel.tsx`(見出し「自然言語で SQL を作成(LLM)」を外す)、単体テスト(`QueryTab.test.tsx`・`LlmSqlPanel.test.tsx`・`PdbPage.test.tsx`・`TableDetailPage` のテストなど、非表示の部品を操作するテストはサブタブを押してから操作する)
* 仕様: `docs/P002-frontend-spec.md` §2.2.6・§2.2.1・§2.2.8・§2.2.9・§2.3.3
* してはいけないこと: サブタブの切り替えで部品をアンマウントすること(入力・ダイアログの状態が消える)。API・保存の振る舞いを変えること。
* 単体テスト: P006 §2.1「Query タブのサブタブ」。
* 実行: `cd client && npm test`、`npm run build`。完了条件: 全件合格・ビルド成功。停止条件: 3 回自己修正しても合格しなければ停止して報告。

## U015-T2: 受入テストの手順の追加分

* 対象: `e2e/tests/a09-query-tab.spec.ts`(手順 1b・10。画面のタブ「Query」はサブタブ「保存済み Query」と名前が部分一致するため `exact: true` で指す)、`a10-saved-queries-pdb.spec.ts`(サブタブ「保存済み Query」を押す)、`a11-llm-sql.spec.ts`(手順 2・5 でサブタブ「自然言語で SQL を作成」を押す)
* 仕様: `docs/P009-acceptance-direction/A09-query-tab-scenario.md`・`A10-saved-queries-pdb-scenario.md`・`A11-llm-sql-scenario.md`
* 完了条件: P201 で実行する。
