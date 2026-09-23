あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A03

## 【目的】

* Oracle に届かない状態で、保存済みのスキーマ情報による ER 図・スキーマ情報タブは使え、再読み込み・データタブ・ヘッダの状態表示がエラーを正しく示すことを確認する(REQ-SCREEN-007・014、REQ-NFR-003)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.3(Oracle 停止時の起動)、§2.1 各画面の異常系

## 【対象モジュール】

* web、api、MCP(Oracle は届かない設定)

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7`)。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* A01 が作ったスナップショット(ボリュームを消さない)。

## 【事前準備】

* `e2e/tests/a03-oracle-down.spec.ts` を作る。
* Oracle 本体は止めない(他の利用者がいるため)。代わりに api コンテナだけを届かない接続先で作り直す: `DBFAQ_ORACLE_HOST=oracle-unreachable.invalid docker compose up -d --no-deps --force-recreate api` → `/api/health` が 200 になるまで待つ。
* テスト後の後片付け(必ず実行): `docker compose up -d --no-deps --force-recreate api`(既定の接続先に戻す)→ `/api/health` の status が ok になるまで待つ。

## 【実行手順】

1. api が起動している(`/api/health` が 200、status=degraded、oracle.status=error)。
2. `/` を開く → ER 図のノードが 7 個表示される(保存済み)。ヘッダの `data-status` が `error`。
3. [Oracle から再読み込み] → 赤い通知(エラーメッセージを含む)。ノードは 7 個のまま。取得日時が変わらない。
4. `/tables/HR/EMPLOYEES` → スキーマ情報タブが表示される。
5. [データ] タブ → 表の代わりにエラー表示と [再試行]。
6. 後片付けを実行し、`/tables/HR/EMPLOYEES?tab=data` で 50 行が表示される(回復)。

## 【実行コマンド】

* `DBFAQ_ORACLE_HOST=oracle-unreachable.invalid docker compose up -d --no-deps --force-recreate api && cd e2e && npx playwright test tests/a03-oracle-down.spec.ts; cd .. && docker compose up -d --no-deps --force-recreate api`(手順 6 の回復確認はスペックの最後のテストとして、後片付けの後に別コマンド `npx playwright test tests/a03-oracle-down.spec.ts -g recovered` で行ってよい)

## 【期待結果】

* 1〜6 がすべて成り立つ。

## 【合否判定基準】

* 全ステップ成立で PASS。失敗があれば FAIL。後片付けが失敗した場合は、後続テストの前に必ず手動で既定の構成に戻し、その旨を記録する。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。
* `docker compose logs --tail 50 api`。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 後片付けが済み、`/api/health` が ok であることを確認し、記録して A03 を `[x]` にしたら A04 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
