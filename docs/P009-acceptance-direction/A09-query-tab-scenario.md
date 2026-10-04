あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A09(※CR-004により追加)

## 【目的】

* 運用担当者が SC-02 の Query タブで、ひな形の作成 → 外部キーで JOIN → 実行 → 表で確認 → 500 行の打ち切り → 全行の CSV ダウンロード → エラー位置の確認、を compose の本番相当環境で行えることを確認する(REQ-SCREEN-010・016〜019、REQ-API-006・007、`docs/P901-cr-direction/CR-004.md` の「期待する振る舞い」)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「Query タブの操作全体」、§3.2「Query の行数の多い結果」「CSV のダウンロード(受入)」

## 【対象モジュール】

* web(QueryTab)、nginx(`/api/query/csv` の中継)、api(Query API)、Oracle

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle が起動していること(`check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更))。
* compose の web(`http://localhost:8088`)の同一オリジンに対して実行する(P003 §7)。A01 が HR のスナップショットを作っていること(スイートでは A02 の後に実行する)。

## 【使用するテストデータ】

* HR(読み取りのみ)。500 行を超える結果: `SELECT a.EMPLOYEE_ID A_ID, b.EMPLOYEE_ID B_ID FROM HR.EMPLOYEES a CROSS JOIN HR.EMPLOYEES b ORDER BY 1, 2`(11,449 行)。

## 【事前準備】

* `e2e/tests/a09-query-tab.spec.ts` を作る(新規)。ダウンロードは Playwright の `page.waitForEvent('download')` で受け、一時ディレクトリに保存してテストの終わりに消す。

## 【実行手順】

1. `/tables/HR/EMPLOYEES` を開き [Query] タブを押す → URL に `tab=query`。入力欄が `SELECT` で始まり、`t0.EMPLOYEE_ID` と `FROM HR.EMPLOYEES t0`、`ORDER BY t0.EMPLOYEE_ID` を含む。
2. ページを再読み込み → Query タブが選ばれたまま。
3. チェックボックス「→ DEPARTMENTS EMP_DEPT_FK」を ON → 入力欄が `LEFT JOIN HR.DEPARTMENTS t1 ON t1.DEPARTMENT_ID = t0.DEPARTMENT_ID` と `t1.DEPARTMENT_NAME` を含む。
4. [実行] → 結果の表が表示され、「107 行」と取得時間が表示される。1 行目の 1 列目が `100`、`DEPARTMENT_NAME` の列に `Executive` がある。`(null)` のセルがある(COMMISSION_PCT)。
5. 入力欄を 500 行を超える SQL に書き換えて Ctrl+Enter → 表の行数が 500、「500 行で打ち切り」の表示がある。
6. [CSV ダウンロード] → ファイル名が `EMPLOYEES_query_` で始まり `.csv` で終わる。中身: 先頭が BOM、1 行目が `A_ID,B_ID`、データ行が 11,449 行。
7. 入力欄を `SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1` にして [実行] → `[ORA-00904]` を含むエラーと「エラー位置: 3 行目 7 文字目」が表示される。[エラー位置へ移動] を押すと、入力欄の選択範囲の開始位置が 33 になる。
8. 入力欄を `DELETE FROM HR.EMPLOYEES` にして [実行] → 「実行できない SQL です」を含むエラーが表示される。
9. スキーマ情報タブ・データタブに切り替えると従来どおり表示され、Query タブに戻ると手順 8 の入力が残っている。

## 【実行コマンド】

* `cd e2e && npx playwright test tests/a09-query-tab.spec.ts`

## 【期待結果】

* 1〜9 がすべて成り立つ。

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

* 記録して A09 を `[x]` にしたら次へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
