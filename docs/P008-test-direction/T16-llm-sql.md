あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T16(※CR-007により追加)

## 【目的】

* 開発用の Ollama と実 Oracle(HR)をつないで、`POST /api/llm/sql` が自然言語の要求から実行できる SELECT 文を作ること、`GET /api/health` の `llm` が `ok` になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「LLM アクセス」「POST /api/llm/sql・health の llm」、§3.1(開発用の LLM、判定の基準)

## 【対象モジュール】

* `dbfaq_api.llm`(`OllamaClient`、`context`、`prompt`)、`LlmService`、`routers/llm.py`(U012)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド: `cd server && uv sync`(終了コード 0。失敗は BLOCKED)。
* 開発用 Oracle(`check_oracle.py` が `8`)と、開発用の Ollama(`curl -s http://localhost:11434/api/tags` に `gemma4:e2b-it-qat` がある)が使えること。どちらかが使えなければ BLOCKED。
* `config.yaml` に `llm` 節(`base_url: http://localhost:11434`、`model: gemma4:e2b-it-qat`、`temperature: 0`、`seed: 42`)。

## 【使用するテストデータ】

* HR(読み取りのみ)。要求: (a)「給与の高い社員を上位5人、姓と部署名と給与を表示」(SC-02、HR.EMPLOYEES)、(b)「部署ごとの社員数を多い順に」(SC-02、HR.EMPLOYEES)、(c)「USERS 表領域の合計サイズ(MB)」(SC-03)。

## 【事前準備】

* `server/tests/integration/test_t16_llm_sql.py` を作る。`create_app(config)`(実 `OracleClient` と実 `OllamaClient`)を lifespan 付きの `httpx.AsyncClient` で呼ぶ(T14 と同じ形。LLM の応答に時間がかかるため、クライアントの上限は 300 秒)。

## 【実行手順】

1. `GET /api/health` → `llm.status` が `ok`、`llm.model` が `gemma4:e2b-it-qat`。最上位の `status` は `ok`。
2. `POST /api/schema/refresh` → 200。
3. 要求 (a) で `POST /api/llm/sql`(`scope=table`、`HR`・`EMPLOYEES`)→ 200。`guard.ok=true`、`sql` が SELECT または WITH で始まる、`context.tables` の先頭が `HR.EMPLOYEES` で `HR.DEPARTMENTS` を含む、`context.sample_rows` が 3、`elapsed_ms` > 0。
4. 手順 3 の `sql` を `POST /api/query` で実行 → 200、`row_count` が 1〜5。
5. 要求 (b) で同じく作成 → `guard.ok=true`。実行 → 200、`row_count` ≥ 1。
6. 要求 (c) で `scope=pdb` → 200、`guard.ok=true`、`context.sample_rows` が 0。実行 → 200(`dbfaq_ro` は DBA_* を読める)。
7. 2 回続けて実行して、同じ判定(PASS/FAIL)になる。

## 【実行コマンド】

* `cd server && DBFAQ_CONFIG=../config.yaml uv run python -m pytest tests/integration/test_t16_llm_sql.py -v`

## 【期待結果】

* 手順 1〜7 がすべて期待どおり。LLM の応答の SQL の文字列そのものは比べない(P006 §3.1)。

## 【合否判定基準】

* 全件 PASS なら PASS。1 件でも違えば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md` に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、ORA コード、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない。
* 失敗したテストをスキップしない。期待値を変えて成功扱いにしない。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T16 を `[x]` にしたら T17 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
