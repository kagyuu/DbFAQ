あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A02

## 【目的】

* テーブル詳細画面で、スキーマ情報の確認・外部キーをたどった移動・データタブのページ送りまでを通しで確認する(REQ-SCREEN-010〜014、REQ-API-003・004)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「SC-02」「画面遷移全体」

## 【対象モジュール】

* web、api、Oracle(CR-002 で MCP を削除)

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7`)。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* HR。A01 が作ったスナップショット(ベースライン復元はしない)。

## 【事前準備】

* A01 が完了していること(スナップショットがある)。`e2e/tests/a02-table-detail.spec.ts` を作る。

## 【実行手順】

1. `/tables/HR/EMPLOYEES` を開く → スキーマ情報タブが選択。列の表に EMPLOYEE_ID(`NUMBER(6)`、不可、🔑 1)、SALARY(`NUMBER(8,2)`)。主キー EMP_EMP_ID_PK、一意制約 EMP_EMAIL_UK、インデックス 6 行、行数の目安 107。
2. 外部キーの表の DEPARTMENTS のリンクをクリック → URL `/tables/HR/DEPARTMENTS`、見出し `HR.DEPARTMENTS`。参照元の表に EMPLOYEES(EMP_DEPT_FK)と JOB_HISTORY(JHIST_DEPT_FK)。
3. ブラウザの戻る → `HR.EMPLOYEES`。
4. [データ] タブ → URL に `tab=data`。「並び順: EMPLOYEE_ID(主キー)」、「1 ページ目 (1〜50 行)」、表の行が 50、先頭行の EMPLOYEE_ID が 100。COMMISSION_PCT の列に `(null)`(`data-null=true`)がある。
5. [次へ] → 「2 ページ目 (51〜100 行)」、URL に `page=2`。[次へ] → 「3 ページ目 (101〜107 行)」、[次へ] が無効。[前へ] → 2 ページ目。
6. ページを再読み込み(`page.reload()`)→ データタブの 2 ページ目のまま。
7. `/tables/HR/JOB_HISTORY?tab=data` → 「並び順: EMPLOYEE_ID, START_DATE(主キー)」、10 行。
8. `/tables/HR/NO_SUCH` → 「テーブルが見つかりません: HR.NO_SUCH」と ER 図へのリンク。
9. ヘッダの [ER 図] → `/`。

## 【実行コマンド】

* `cd e2e && npx playwright test tests/a02-table-detail.spec.ts`

## 【期待結果】

* 1〜9 がすべて成り立つ。

## 【合否判定基準】

* 全ステップ成立で PASS。失敗があれば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A02 を `[x]` にしたら A03 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
