あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U014 — llm-no-perf(※CR-009により追加)

LLM で SQL を作る機能の性能を求めないことにあわせ、待ち時間の既定を延ばし、テストを時間で判定しないようにする。変更要求: `docs/P901-cr-direction/CR-009.md`。

## タスク一覧(OKF副目次)

- [x] U014-T1 [待ち時間の既定と作成中の表示](#u014-t1-待ち時間の既定と作成中の表示) — `config.py`、`config.example.yaml`、`deploy/nginx.conf`、`LlmSqlPanel.tsx`、README
- [x] U014-T2 [T16・A11 の待ち時間](#u014-t2-t16a11-の待ち時間) — `test_t16_llm_sql.py`、`a11-llm-sql.spec.ts`

## U014-T1: 待ち時間の既定と作成中の表示

* 対象: `server/src/dbfaq_api/config.py`(`LlmConfig.timeout_sec` の既定 600)、`server/tests/unit/test_config.py`、`config.example.yaml`・README の設定例(600)、`deploy/nginx.conf`(`/api/llm/` の `proxy_read_timeout 660s`)、`client/src/components/LlmSqlPanel.tsx`(作成中の文言)
* 仕様: `docs/P003-backend-spec.md` §2.1・§6、`docs/P002-frontend-spec.md` §2.2.9
* 実行: `cd server && uv run python -m pytest tests/unit -q`、`cd client && npm test && npm run build`。完了条件: 全件合格。停止条件: 3 回自己修正しても合格しなければ停止して報告。
* 開発環境の `config.yaml`(Git 管理外)の `llm.timeout_sec` も 600 にする(パスワードの行には触れない)。

## U014-T2: T16・A11 の待ち時間

* 対象: `server/tests/integration/test_t16_llm_sql.py`(httpx の待ち時間 660 秒)、`e2e/tests/a11-llm-sql.spec.ts`(作成の待ち時間 660 秒、テスト全体 900 秒)
* 仕様: `docs/P008-test-direction/T16-llm-sql.md`、`docs/P009-acceptance-direction/A11-llm-sql-scenario.md`
* 完了条件: P103・P201 で実行する。
