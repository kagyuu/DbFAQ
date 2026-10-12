あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A11(※CR-007により追加)

## 【目的】

* compose の本番相当環境で、ヘッダに LLM の状態が表示され、SC-02 の Query タブで自然言語の要求から LLM が作った SELECT 文を実行できること、LLM に届かないときは丸が赤になり作成のボタンを押せないことを確認する(REQ-SCREEN-028〜031、REQ-API-013、`docs/P901-cr-direction/CR-007.md` の「期待する振る舞い」)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「LLM の操作全体」、§3.1(開発用の LLM、判定の基準)

## 【対象モジュール】

* web(`LlmStatus`、`LlmSqlPanel`、`QueryTab`)、nginx(`/api/llm/` の中継)、api(LLM の API・health)、LLM(Ollama)、Oracle

## 【前提条件】全モジュールビルドが成功していること

* ビルド: `cd server && uv sync && uv run python -m pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。失敗は BLOCKED。
* 開発用 Oracle と、**compose の api コンテナから LLM に届くこと**(`docker compose exec -T api python -c "import urllib.request;urllib.request.urlopen('<DBFAQ_LLM_BASE_URL>/api/tags',timeout=5)"` が成功)。届かなければ手順 1〜4 は BLOCKED(手順 5 は実行する)。開発環境では `deploy/dev/llm-relay.sh start` で中継を起動し、`.env` に `DBFAQ_LLM_BASE_URL=http://host.docker.internal:11435` を書いておく(CR-007 の備考)。
* A01 が HR のスナップショットを作っていること(スイートでは A10 の後に実行する)。

## 【使用するテストデータ】

* HR(読み取りのみ)。要求「給与の高い社員を上位5人、姓と部署名と給与を表示」。

## 【事前準備】

* `e2e/tests/a11-llm-sql.spec.ts` を作る(手順 1〜4 は `-g available`、手順 5 は `-g unreachable`)。LLM の作成の待ち時間は 300 秒。

## 【実行手順】

1. `/` を開く → ヘッダの「Oracle」の丸の右に「LLM」と丸があり、丸が緑(`data-status="ok"`)。マウスを乗せると `gemma4:e2b-it-qat` が表示される。
2. `/tables/HR/EMPLOYEES?tab=query` を開く → 「自然言語で SQL を作成(LLM)」があり、要求が空の間は [LLM で SQL を作成] が押せない。
3. 要求を入力して [LLM で SQL を作成] → 作成中の表示 → 入力欄が SELECT または WITH で始まる SQL になり、「LLM(gemma4:e2b-it-qat)が作成しました」が表示され、「実行できない SQL です」は表示されない。結果の表は表示されていない(自動で実行しない)。
4. [実行] → 結果の行数が 1〜5 行。
5. api を `DBFAQ_LLM_BASE_URL=http://llm-unreachable.invalid:11434` で作り直す(`run-suite.sh` が行う)→ ヘッダの LLM の丸が赤(`data-status="error"`)、`/tables/HR/EMPLOYEES?tab=query` で要求を入力しても [LLM で SQL を作成] が押せず、「LLM が使えないため作成できません」が表示される。Oracle の丸は緑のまま。その後 api を元の設定で作り直す。

## 【実行コマンド】

* `cd e2e && npx playwright test tests/a11-llm-sql.spec.ts -g available`(手順 1〜4)、手順 5 は `run-suite.sh` の中で api を作り直して `-g unreachable`

## 【期待結果】

* 1〜5 がすべて成り立つ。LLM の SQL の文字列そのものは比べない。

## 【合否判定基準】

* すべて成り立てば PASS。1 つでも違えば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md` に、テスト ID、実行コマンド、失敗した手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A11 を `[x]` にしたら次へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
