あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A10(※CR-005により追加)

## 【目的】

* 運用担当者が、SC-02 の Query タブで SQL を名前と説明付きで保存し、再読み込みの後に復元して実行し、上書き・変更・削除できること、保存がテーブルごとであること、SC-01 のドラム缶のアイコンから SC-03 を開いて PDB の情報を見て、ひな型を復元・実行・保存できることを、compose の本番相当環境で確認する(REQ-SCREEN-020〜027、REQ-API-008〜012、`docs/P901-cr-direction/CR-005.md` の「期待する振る舞い」)。
* テーブルが無くなって戻ったときの振る舞いは、HR を変更しない方針(P006 §3.2)のため T15 で確かめる(本テストの対象外)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「保存・復元と PDB 画面の操作全体」、§3.2「保存済み Query(受入)」

## 【対象モジュール】

* web(ErDiagramPage の PdbIcon、QueryTab、SavedQueries、PdbPage、PdbInfoTab)、nginx、api(保存済み Query・PDB の API)、SQLite(ボリューム)、Oracle

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run python -m pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle が起動していること(`check_oracle.py` が `8`)。
* compose の web(`http://localhost:8088`)の同一オリジンに対して実行する(P003 §7)。A01 が HR のスナップショットを作っていること(スイートでは A09 の後に実行する)。

## 【使用するテストデータ】

* HR(読み取りのみ)。保存済み Query は名前に `A10-` を付け、テストの最初と最後に `GET /api/saved-queries` で `A10-` で始まるものを探して `DELETE` する(P006 §3.2)。ひな型は変更しない。

## 【事前準備】

* `e2e/tests/a10-saved-queries-pdb.spec.ts` を作る(新規)。

## 【実行手順】

1. `/tables/HR/EMPLOYEES?tab=query` を開く → 「保存済み Query (0)」と「保存済みの Query はありません」。
2. 入力欄を `SELECT EMPLOYEE_ID, LAST_NAME FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50 ORDER BY LAST_NAME` にし、[名前を付けて保存] → 名前 `A10-部署50`、説明 `部署 50 の社員` → [保存] → 通知「保存しました: A10-部署50」、一覧に 1 件、「復元中: A10-部署50」。
3. もう一度 [名前を付けて保存] で名前 `A10-部署50` → ダイアログに「同じ名前の Query が既にあります」。[キャンセル]。
4. `/tables/HR/DEPARTMENTS?tab=query` を開く → 「保存済み Query (0)」(EMPLOYEES の Query は出ない)。
5. `/tables/HR/EMPLOYEES?tab=query` を開き直す(ページの再読み込み)→ 入力欄はひな形、一覧に `A10-部署50`。[復元] → 入力欄が手順 2 の SQL になる。[実行] → 「45 行」。
6. 入力欄の `50` を `60` に変え、[上書き保存] → 通知「上書き保存しました」。ページを再読み込みして [復元] → 入力欄に `DEPARTMENT_ID = 60` を含む。
7. 入力欄を編集してから [復元] → 確認ダイアログ「入力欄の SQL を「A10-部署50」で置き換えますか」→ [キャンセル] で入力欄は編集後のまま。
8. [編集] で名前を `A10-部署60` に変える → 一覧の名前が変わる。[削除] → 確認 → [削除] → 「保存済みの Query はありません」。
9. `/` を開く → ドラム缶のアイコン(「PDB」と `FREEPDB1`)が表示されている。クリック → URL が `/pdb`、見出しに `PDB: FREEPDB1`。
10. PDB 情報タブに「概要」(コンテナ名(PDB) `FREEPDB1`、接続ユーザー `DBFAQ_RO`、対象スキーマ `HR`)、「表領域の割り当て(対象スキーマ)」(`USERS`)、「セグメントの使用量(対象スキーマ)」(`LOBSEGMENT`)、「表領域の使用状況」(`USERS` の行。権限エラーにならない)が表示される(※CR-006により変更)。
11. [Query] タブ → URL に `tab=query`。JOIN の一覧が無く、入力欄は空。「保存済み Query (17)」にひな型の印付きで `01. USERS 表領域の大きさ`・`03. LOB 領域の大きさと実データの合計(テーブル.カラムごと)` がある。
12. `03. ...` を [復元] → [実行] → 結果の表に `EMPLOYEE_FIGURE.FIGURE` と `BLOB` がある。
13. `01. ...` を [復元] → [実行] → 結果の表に `USERS` の行がある(※CR-006により変更。`dbfaq_ro` は DBA_* を読める。以前は hr に権限が無く `[ORA-00942]`)。
14. 入力欄を `SELECT SYS_CONTEXT('USERENV','CON_NAME') AS CON FROM DUAL` にして [名前を付けて保存](名前 `A10-PDB名`)→ 一覧が 18 件。ページを再読み込みして [Query] タブ → `A10-PDB名` を復元・実行 → `FREEPDB1`。
15. 後始末として `A10-` の Query を削除する → PDB の一覧が 17 件に戻る。

## 【実行コマンド】

* `cd e2e && npx playwright test tests/a10-saved-queries-pdb.spec.ts`

## 【期待結果】

* 1〜15 がすべて成り立つ。

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

* 記録して A10 を `[x]` にしたら次へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
