あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T13(※CR-004により追加)

## 【目的】

* 利用者の SELECT の実行(`run_query`)・CSV(`export_csv`)・エラー位置と、`POST /api/query`・`POST /api/query/csv` が実 Oracle(HR)で仕様どおりに動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「SELECT の実行」「CSV」「POST /api/query・/api/query/csv」、§3.2「Query の行数の多い結果」

## 【対象モジュール】

* `dbfaq_api.oracle.query`、`OracleClient.run_query`・`export_csv`、`routers/query.py`(U009)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更) を出す。出なければ BLOCKED。

## 【使用するテストデータ】

* HR(読み取りのみ)。EMPLOYEES 107 行。11,449 行の結果: `SELECT a.EMPLOYEE_ID A_ID, b.EMPLOYEE_ID B_ID FROM HR.EMPLOYEES a CROSS JOIN HR.EMPLOYEES b ORDER BY 1, 2`。

## 【事前準備】

* `server/tests/integration/test_t13_query.py` を作る(pytest マーカー `oracle`)。`OracleClient` と、`create_app(config, oracle=実 OracleClient)` を `httpx.AsyncClient(transport=ASGITransport(app))` で呼ぶ(T07 と同じ形)。

## 【実行手順】

1. `run_query("SELECT EMPLOYEE_ID, LAST_NAME, HIRE_DATE, COMMISSION_PCT FROM HR.EMPLOYEES WHERE EMPLOYEE_ID = 100;")` → 1 行、`["100", "King", "2013-06-17 00:00:00", None]`、`has_more=false`。
2. `run_query(11,449 行の SQL)` → `row_count=500`、`has_more=true`、`max_rows=500`。
3. `run_query("SELECT 1 FROM HR.EMPLOYEES WHERE 1 = 0")` → 0 行、`columns` は 1 列。
4. `run_query("SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1")` → `ORACLE_ERROR`、`ORA-00904`、position `{offset: 33, line: 3, column: 7}`。
5. `run_query("-- 日本語コメント\nSELECT ほげ FROM HR.EMPLOYEES")` → `ORA-00904`、position `{offset: 18, line: 2, column: 8}`。
6. `run_query("SELECT * FROM HR.NO_SUCH_TABLE")` → `ORA-00942`、position の line 1。
7. `export_csv(11,449 行の SQL)` → 行数 11,449。ファイルの先頭が BOM、1 行目が `A_ID,B_ID`、改行が CRLF、データ行が 11,449 行。
8. API: `POST /api/query` に手順 1 の SQL → 200、手順 4 の SQL → 502 で `error.position.line=3`、`DELETE FROM HR.EMPLOYEES` → 422 `SQL_REJECTED`。`POST /api/query/csv` に手順 7 の SQL → 200、`text/csv`、`X-Row-Count: 11449`。
9. 2 回続けて実行して同じ結果になる。

## 【実行コマンド】

* `cd server && DBFAQ_CONFIG=../config.yaml uv run pytest tests/integration/test_t13_query.py -v`

## 【期待結果】

* 手順 1〜9 がすべて期待どおり。

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

* 記録して T13 を `[x]` にしたら、P008 の全項目の結果をまとめて P104 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
