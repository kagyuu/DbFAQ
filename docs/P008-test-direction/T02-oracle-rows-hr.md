あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T02

## 【目的】

* backend の Oracle アクセス(`OracleClient.get_table_rows`)が(※CR-002により「MCP の `get_table_rows`」から変更)実 Oracle で主キー順にページ取得でき、存在しない表・不正な引数を正しく扱うことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「Oracle: テーブルデータ」

## 【対象モジュール】

* `dbfaq_api.oracle`(client.py、rows.py、values.py、identifiers.py)と Oracle(U002、CR-002 で U007 に移設)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更) を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR.EMPLOYEES(107 行、主キー EMPLOYEE_ID。最小 100、最大 206)、HR.JOB_HISTORY(10 行、複合主キー EMPLOYEE_ID, START_DATE)。

## 【事前準備】

* `server/tests/integration/test_t02_oracle_rows.py` を作る(T01 の `oracle_client` フィクスチャを使う。CR-002 で `test_t02_mcp_rows.py` から改名)。

## 【実行手順】

1. EMPLOYEES を offset 0/limit 50 → 50 行、has_next=true、先頭行の EMPLOYEE_ID が `"100"`、order_basis=PRIMARY_KEY、order_by=["EMPLOYEE_ID"]。
2. offset 50/limit 50 → 50 行、has_next=true。offset 100/limit 50 → 7 行、has_next=false、最終行の EMPLOYEE_ID が `"206"`。3 ページの EMPLOYEE_ID に重複が無く合計 107。
3. HIRE_DATE 列の値が `YYYY-MM-DD HH:MM:SS` 形式、COMMISSION_PCT に null(JSON null)が含まれる。columns の data_type に `NUMBER`・`VARCHAR`・`DATE` がある。
4. JOB_HISTORY を offset 0/limit 10 → 10 行、(EMPLOYEE_ID, START_DATE) の昇順に並ぶ。order_by=["EMPLOYEE_ID","START_DATE"]。
5. 異常系(`OracleFailure` の code を検証): table="NO_SUCH_TABLE" → NOT_FOUND/limit=501 → INVALID_ARGUMENT/table='A"B' → INVALID_ARGUMENT/owner="hr"(小文字。辞書には HR で入っている)→ NOT_FOUND。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t02_oracle_rows.py -v`

## 【期待結果】

* 手順の検証がすべて成り立つ。

## 【合否判定基準】

* 全件 PASS なら PASS。失敗があれば FAIL。接続できなければ BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T02 を `[x]` にしたら T03 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
