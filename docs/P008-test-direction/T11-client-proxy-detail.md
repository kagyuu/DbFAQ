あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T11

## 【目的】

* 開発時の構成で、テーブル詳細画面が使う API(詳細・rows)が proxy 越しに正しく呼べ、URL エンコードされた名前と 404 がそのまま届くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「SC-02」

## 【対象モジュール】

* `client`(proxy)+ `dbfaq_api`(U005)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(`cd server && uv sync`)と `client/`(`cd client && npm ci && npm run build`)。成功条件: 両方とも終了コード 0。失敗時は BLOCKED として出力を記録し、テストへ進まない。
* 開発用 Oracle が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7`)。

## 【使用するテストデータ】

* HR。SQLite は新しい一時ファイル(T10 と同じ方法)。

## 【事前準備】

* T10 の事前準備と同じ手順で backend と Vite を起動し、`curl -s -X POST localhost:5173/api/schema/refresh` を 1 回実行する。

## 【実行手順】

1. `curl -s localhost:5173/api/schema/tables/HR/EMPLOYEES` → 200、`"name":"EMPLOYEES"`、primary_key が EMP_EMP_ID_PK。
2. `curl -s 'localhost:5173/api/schema/tables/HR/EMPLOYEES/rows?offset=0&limit=50'` → 200、rows 50、has_next true。
3. `curl -s -o /dev/null -w '%{http_code}' localhost:5173/api/schema/tables/HR/NO%20SUCH` → 404。本文の code が `TABLE_NOT_FOUND`。
4. `curl -s -o /dev/null -w '%{http_code}' 'localhost:5173/api/schema/tables/HR/EMPLOYEES/rows?limit=0'` → 422。
5. `curl -s -o /dev/null -w '%{http_code}' localhost:5173/tables/HR/EMPLOYEES` → 200(Vite が SPA の index.html を返す)。
6. 終了後にプロセスを止める。

## 【実行コマンド】

* 上記の `curl` を順に実行する。

## 【期待結果】

* 1〜5 がすべて成り立つ。

## 【合否判定基準】

* すべて成り立てば PASS。違えば FAIL。起動できなければ BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T11 を `[x]` にしたら T12 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
