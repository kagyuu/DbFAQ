あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U013 — llm-exchange(※CR-008により追加)

LLM で SQL を作るときの、LLM へのリクエストと LLM のリプライを画面で表示できるようにする。変更要求: `docs/P901-cr-direction/CR-008.md`。**既存の振る舞いは変えない。**

## タスク一覧(OKF副目次)

- [x] U013-T1 [応答とエラーに exchange](#u013-t1-応答とエラーに-exchange) — `errors.py`、`services.py`、`schemas.py`
- [x] U013-T2 [LLM とのやりとりのボタンとダイアログ](#u013-t2-llm-とのやりとりのボタンとダイアログ) — `src/api/`、`LlmSqlPanel.tsx`
- [x] U013-T3 [結合・受入テストの追加分](#u013-t3-結合受入テストの追加分) — T16・T17・A11

## U013-T1: 応答とエラーに exchange

* 対象: `server/src/dbfaq_api/errors.py`(`ApiError(..., extra=None)`、`body()` で `error` に加える)、`services.py`(`LlmService.generate`)、`schemas.py`(`LlmExchange`、`LlmSqlResponse.exchange`、`ErrorBody` に任意の `exchange`)、`tests/unit/api/test_llm_api.py`
* 仕様: `docs/P002-frontend-spec.md` §3.1・§3.15、`docs/P003-backend-spec.md` §4.4・§4.8.4
* してはいけないこと: `exchange` をログに出すこと。LLM の設定が無いとき・検証エラー・404 に `exchange` を付けること。
* 単体テスト: P006 §2.1「LLM とのやりとりの表示」の backend の分。
* 実行: `cd server && uv run python -m pytest tests/unit -q`。完了条件: 全件合格。停止条件: 3 回自己修正しても合格しなければ停止して報告。

## U013-T2: LLM とのやりとりのボタンとダイアログ

* 対象: `client/src/api/types.ts`(`LlmExchange`、`LlmSqlResult.exchange`、`ApiErrorBody` の `exchange`)、`client.ts`(`ApiError.exchange`)、`src/components/LlmSqlPanel.tsx`、`LlmSqlPanel.test.tsx`
* 仕様: `docs/P002-frontend-spec.md` §2.2.9
* 単体テスト: P006 §2.1「LLM とのやりとりの表示」の frontend の分。
* 実行: `cd client && npm test`、`npm run build`。完了条件・停止条件は T1 と同じ。

## U013-T3: 結合・受入テストの追加分

* 対象: `server/tests/integration/test_t16_llm_sql.py`(手順 3b)、`test_t17_llm_unavailable.py`(手順 1b)、`e2e/tests/a11-llm-sql.spec.ts`(手順 3b)
* 仕様: `docs/P008-test-direction/T16-llm-sql.md`・`T17-llm-unavailable.md`、`docs/P009-acceptance-direction/A11-llm-sql-scenario.md`
* 完了条件: P103・P201 で実行する。
