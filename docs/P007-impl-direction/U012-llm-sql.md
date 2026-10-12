あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U012 — llm-sql(※CR-007により追加)

自然言語の要求から LLM(Ollama)で SELECT 文を作り、Query タブの入力欄に入れる。LLM の状態をヘッダに表示し、LLM が使えないときは作成のボタンを押せなくする。変更要求: `docs/P901-cr-direction/CR-007.md`。**作った SQL は自動で実行しない。既存の API・画面の振る舞いは変えない。**

## タスク一覧(OKF副目次)

- [x] U012-T1 [LLM の設定](#u012-t1-llm-の設定) — `config.py`、`config.example.yaml`
- [x] U012-T2 [LLM アクセス](#u012-t2-llm-アクセス) — `llm/client.py`
- [x] U012-T3 [LLM に渡す情報・プロンプト・SQL の取り出し](#u012-t3-llm-に渡す情報プロンプトsql-の取り出し) — `llm/context.py`、`llm/prompt.py`
- [x] U012-T4 [サービス・API・health](#u012-t4-サービスapihealth) — `services.py`、`routers/llm.py`、`schemas.py`、`errors.py`、`main.py`、`tests/fakes.py`
- [x] U012-T5 [ヘッダの LLM の丸と LlmSqlPanel](#u012-t5-ヘッダの-llm-の丸と-llmsqlpanel) — `LlmStatus.tsx`、`LlmSqlPanel.tsx`、`AppShell.tsx`、`QueryTab.tsx`、`src/api/`
- [x] U012-T6 [nginx・compose・受入テスト](#u012-t6-nginxcompose受入テスト) — `deploy/nginx.conf`、`compose.yaml`、`e2e/tests/a11-llm-sql.spec.ts`、`run-suite.sh`

---

## U012-T1: LLM の設定

* 対象: `server/src/dbfaq_api/config.py`(`LlmConfig`、`AppConfig.llm: LlmConfig | None = None`、`DBFAQ_LLM_BASE_URL`)、`config.example.yaml`(`llm` 節)、`server/tests/unit/test_config.py`
* 仕様: `docs/P003-backend-spec.md` §2.1・§2.2
* 単体テスト: 既定値、節が無いとき None、範囲外・provider の誤りで `ConfigError`、`DBFAQ_LLM_BASE_URL` は節があるときだけ上書き。
* 実行: `cd server && uv run python -m pytest tests/unit/test_config.py -q`。完了条件: 全件合格。停止条件: 3 回自己修正しても合格しなければ停止して報告。

## U012-T2: LLM アクセス

* 対象: `server/src/dbfaq_api/llm/__init__.py`・`client.py`(新規)、`server/pyproject.toml`(httpx を実行時の依存に)、`server/tests/unit/llm/test_client.py`(新規。`httpx.MockTransport`)
* 仕様: `docs/P003-backend-spec.md` §4.8.1
* 単体テスト: P006 §2.1「LLM アクセス」の正常系・異常系をすべて。
* 実行: `cd server && uv run python -m pytest tests/unit/llm -q`。完了条件・停止条件は T1 と同じ。

## U012-T3: LLM に渡す情報・プロンプト・SQL の取り出し

* 対象: `server/src/dbfaq_api/llm/context.py`・`prompt.py`(新規)、`server/tests/unit/llm/test_context.py`・`test_prompt.py`(新規)
* 仕様: `docs/P003-backend-spec.md` §4.8.2・§4.8.3
* 実装: 構造は `SnapshotRepository.get_table_detail`(SC-02 のテーブルと関連するテーブル)・`get_er_view`(SC-03)から作る。データの例は `OracleAccess.get_table_rows(owner, table, 0, n)` の `rows`・`columns`。
* してはいけないこと: 要求の文・データの例をログに出すこと。SQL を実行すること。
* 単体テスト: P006 §2.1「LLM に渡す情報とプロンプト」「SQL の取り出しと検査」をすべて。
* 完了条件・停止条件は T1 と同じ。

## U012-T4: サービス・API・health

* 対象: `services.py`(`LlmService`、`SchemaService.health` に `llm`)、`routers/llm.py`(新規)、`schemas.py`(`LlmSqlRequest`・`LlmSqlResponse`・`LlmHealth`)、`errors.py`(3 つのコード)、`main.py`(`create_app(llm_access=...)`、lifespan で `OllamaClient` を作り閉じる)、`tests/fakes.py`(`FakeLlm`)、`tests/unit/api/test_llm_api.py`(新規)、既存の health のテスト
* 仕様: `docs/P002-frontend-spec.md` §3.1・§3.7・§3.15、`docs/P003-backend-spec.md` §4.3・§4.8.4
* 単体テスト: P006 §2.1「POST /api/llm/sql・health の llm」をすべて。既存の health のテストは `llm` の追加以外を変えずに合格させる。
* 実行: `cd server && uv run python -m pytest tests/unit -q`。完了条件・停止条件は T1 と同じ。
* 結合テスト: `tests/integration/test_t16_llm_sql.py`・`test_t17_llm_unavailable.py`(P008 T16・T17。P103 で実行)

## U012-T5: ヘッダの LLM の丸と LlmSqlPanel

* 対象: `client/src/components/LlmStatus.tsx`・`LlmSqlPanel.tsx`(新規)、`AppShell.tsx`(Oracle の丸の右)、`QueryTab.tsx`(保存済み Query と入力欄の間、`QueryState` に要求の文・結果・エラー)、`src/api/types.ts`・`client.ts`(`generateSql`)、テスト(`LlmStatus.test.tsx`・`LlmSqlPanel.test.tsx`(新規)、`QueryTab.test.tsx`・`PdbPage.test.tsx` の追加)、`src/test/fetchMock.ts`(`HEALTH_OK` に `llm`)
* 仕様: `docs/P002-frontend-spec.md` §1.1・§2.2.9・§2.3.3
* してはいけないこと: 作った SQL を自動で実行すること。既存のテストの期待値を変えること(`HEALTH_OK` への `llm` の追加を除く)。
* 単体テスト: P006 §2.1「frontend の LLM」をすべて。
* 実行: `cd client && npm test`、`npm run build`。完了条件・停止条件は T1 と同じ。

## U012-T6: nginx・compose・受入テスト

* 対象: `deploy/dev/llm-relay.sh`(新規。`start`・`stop`・`status`。WSL の socat で docker0 の IP(既定 `172.17.0.1`)の 11435 番 → `127.0.0.1:11434`。開発環境だけ。※当初は `0.0.0.0:11435`。LAN から届かないよう 2026-10-13 に変更)、`deploy/nginx.conf`(`location /api/llm/`、`proxy_read_timeout 300s`)、`compose.yaml`(api の `DBFAQ_LLM_BASE_URL: ${DBFAQ_LLM_BASE_URL:-http://host.docker.internal:11434}`)、`e2e/tests/a11-llm-sql.spec.ts`(新規)、`e2e/scripts/run-suite.sh`(A11。A11 の後半は api を作り直して LLM に届かない設定にする)
* 仕様: `docs/P003-backend-spec.md` §6、`docs/P009-acceptance-direction/A11-llm-sql-scenario.md`
* 完了条件: P201 で実行する。
