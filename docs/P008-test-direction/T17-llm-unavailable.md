あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T17(※CR-007により追加)

## 【目的】

* LLM に届かない設定・モデルが無い設定・LLM の節が無い設定で、`GET /api/health` の `llm` と `POST /api/llm/sql` のエラーが仕様どおりで、他の機能(Oracle の health・Query)に影響しないことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「LLM アクセス」「POST /api/llm/sql・health の llm」

## 【対象モジュール】

* `OllamaClient`、`LlmService`、`SchemaService.health`(U012)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド: `cd server && uv sync`。開発用 Oracle が使えること(Ollama は手順 2 だけで使う)。

## 【使用するテストデータ】

* 設定を書き換えた一時の `config.yaml`(T08 と同じ `write_config` の形で `llm` 節を変える): (A) `base_url: http://127.0.0.1:9`(待ち受けの無いポート)、(B) 開発用の Ollama で `model: no-such-model:latest`、(C) `llm` 節なし。

## 【事前準備】

* `server/tests/integration/test_t17_llm_unavailable.py` を作る。

## 【実行手順】

1. (A): `GET /api/health` → 200、`llm.status=error`、`message` に「LLM に接続できません」、最上位の `status` は `ok`(Oracle は使える)。`POST /api/llm/sql` → 503 `LLM_UNAVAILABLE`。`POST /api/query` は 200。
2. (B): `llm.status=error`、`message` に「モデル no-such-model:latest が LLM にありません」。`POST /api/llm/sql` → 503 `LLM_UNAVAILABLE`。
3. (C): `llm.status=disabled`、`model`・`base_url` が null。`POST /api/llm/sql` → 503 `LLM_UNAVAILABLE`(「LLM は設定されていません」)。
4. `GET /api/health` の所要時間が、(A) で `health_timeout_sec`(3 秒)+ 1 秒以内。
5. 2 回続けて実行して同じ結果になる。

## 【実行コマンド】

* `cd server && DBFAQ_CONFIG=../config.yaml uv run python -m pytest tests/integration/test_t17_llm_unavailable.py -v`

## 【期待結果】

* 手順 1〜5 がすべて期待どおり。

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

* 記録して T17 を `[x]` にしたら、P008 の全項目の結果をまとめて P104 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
