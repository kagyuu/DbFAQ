あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U016 — llm-save-defaults(※CR-011により追加)

LLM で作成した SQL を [名前を付けて保存] するとき、名前の初期値を要求の先頭 20 文字、説明の初期値を要求の全文(1,000 文字で切る)にする。変更要求: `docs/P901-cr-direction/CR-011.md`。**frontend だけの変更。**

## タスク一覧(OKF副目次)

- [x] U016-T1 [LLM の要求を覚えて保存の初期値にする](#u016-t1-llm-の要求を覚えて保存の初期値にする) — `QueryTab.tsx`、`LlmSqlPanel.tsx`、`SavedQueries.tsx`
- [x] U016-T2 [受入テストの手順の追加分](#u016-t2-受入テストの手順の追加分) — A11 手順 3c

## U016-T1: LLM の要求を覚えて保存の初期値にする

* 対象: `client/src/components/LlmSqlPanel.tsx`(`onApply(sql, request)`。確認待ちの結果にも要求を持たせる)、`client/src/pages/QueryTab.tsx`(`QueryState.llmRequest`。`applyLlmSql` で覚え、ひな形の作成・チェックボックスの自動の置き換え・復元・保存(`onSaved`)で消す)、`client/src/components/SavedQueries.tsx`(`llmRequest` を受け取り、[名前を付けて保存] の初期値を決める純粋関数 `saveDefaults` を export する。名前は空白・改行の並びを 1 つの空白にまとめて先頭 20 文字、説明は先頭 1,000 文字。文字数は `MAX_NAME_CHARS`・`MAX_DESCRIPTION_CHARS` と同じ数え方(JS の文字列の長さ)で上限を超えないようにし、サロゲートペアを途中で切らない)、単体テスト
* 仕様: `docs/P002-frontend-spec.md` §2.2.8・§2.2.9
* してはいけないこと: API・保存の上限(名前 100 文字・説明 1,000 文字)を変えること。初期値を書き換えられなくすること。
* 単体テスト: P006 §2.1「LLM で作成した Query の保存の初期値」。
* 実行: `cd client && npm test`、`npm run build`。完了条件: 全件合格・ビルド成功。停止条件: 3 回自己修正しても合格しなければ停止して報告。

## U016-T2: 受入テストの手順の追加分

* 対象: `e2e/tests/a11-llm-sql.spec.ts`(手順 3c)
* 仕様: `docs/P009-acceptance-direction/A11-llm-sql-scenario.md`
* 完了条件: P201 で実行する。
