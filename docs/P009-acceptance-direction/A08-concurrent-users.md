あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

※CR-001により新規作成

# 【テストID】A08

## 【目的】

* 同時利用者 10 名で、エラーが出ず、各操作が性能目標内に収まることを確認する(REQ-NFR-005、P001 §8.4 の合格基準)。uvicorn 1 ワーカー(ADR-001)・MCP 子プロセス 1 つ・Oracle 接続プール(既定 `pool_max` 4)の構成で捌けることを確かめる。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2「同時利用」

## 【対象モジュール】

* web(nginx)、api(dbfaq_api + dbfaq_mcp)、SQLite、Oracle

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象・コマンド・成功条件は A01 と同じ。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* HR のスナップショット(A01 が作り、A05 の後片付けで HR に戻したもの)。`/api/schema` の `table_count` が 7 であること。

## 【事前準備】

* `server/scripts/a08_concurrent_load.py`(httpx の非同期クライアント。server の dev 依存にある)と `e2e/scripts/a08-concurrency.sh`(`cd server && uv run python scripts/a08_concurrent_load.py`)を作る(新規)。
* 暖機(事前の空打ち)はしない。接続プールが広がるまでの待ちも含めて測る。

## 【実行手順】

1. 10 名の仮想利用者を同時に動かす。各利用者は次の 1 巡を 10 回繰り返す(テーブルは HR の 7 表から利用者ごとに固定の乱数の種で選ぶ)。
   1. `GET /api/schema`(ER 図の取得)
   2. `GET /api/schema/tables/HR/{table}`(テーブル詳細)
   3. `GET /api/schema/tables/HR/{table}/rows?offset=0&limit=50`(データタブの 1 ページ目)
   4. `GET /api/schema/tables/HR/{table}/rows?offset=50&limit=50`(2 ページ目)
2. 各応答の状態コードと所要時間(クライアントから見た時間)を記録する。rows は所要時間から応答の `elapsed_ms`/1000 を引いたもの(Oracle の処理時間を除いたオーバーヘッド)を記録する。
3. 種類ごとに中央値・95 パーセンタイル・最大値を出力する。

## 【実行コマンド】

* `bash e2e/scripts/a08-concurrency.sh`

## 【期待結果】

* 400 件の応答がすべて 200(エラー 0 件)。
* `GET /api/schema`・テーブル詳細の最大値が 1 秒未満。rows のオーバーヘッドの最大値が 1 秒未満。

## 【合否判定基準】

* 期待結果をすべて満たせば PASS(スクリプトの終了コード 0)。1 件でもエラー、または最大値が目標以上なら FAIL(測定値を記録)。HR のスナップショットが無い、または compose が起動していない場合は BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、スクリプトの出力全体(種類ごとの中央値・95 パーセンタイル・最大値、エラーの一覧)、`docker compose logs api` の該当時刻の抜粋を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)と `config.yaml` の設定(`pool_max` など)を修正しない。
* 失敗を避ける目的で、同時利用者数・繰り返し回数・目標値を変えない。暖機を足さない。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A08 を `[x]` にしたら、`docs/P009-acceptance-direction.md` の WBS の次のタスクへ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
