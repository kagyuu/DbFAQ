あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T01

## 【目的】

* backend の Oracle アクセス(`OracleClient.get_schema_snapshot`)が、実 Oracle の HR スキーマを正しく読み取ることを確認する。※CR-002により「MCP サーバ(実際の stdio 子プロセス)の `get_schema_snapshot`」から変更

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「Oracle: スキーマの読み取り」、§3.2

## 【対象モジュール】

* `dbfaq_api.oracle`(client.py、snapshot.py、dictionary.py、db.py)と Oracle(U002、CR-002 で U007 に移設)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR サンプルスキーマ(読み取りのみ)。期待値(2026-09-23 実測): テーブル 7(COUNTRIES, DEPARTMENTS, EMPLOYEES, JOBS, JOB_HISTORY, LOCATIONS, REGIONS)、列の合計 35、主キー 7、一意制約 1(EMP_EMAIL_UK)、外部キー 10、インデックス 19。

## 【事前準備】

* `server/tests/integration/conftest.py` のフィクスチャ `oracle_client` — `OracleClient(load_config(<リポジトリルートの config.yaml の絶対パス>).oracle)` を作って渡し、終わったら `close()` する。すべての結合テストに `oracle` マーカーを付ける(conftest で付与)。※CR-002により `mcp_client`(MCP の子プロセス)から変更
* テストファイル `server/tests/integration/test_t01_oracle_snapshot.py` を作る(CR-002 で `test_t01_mcp_snapshot.py` から改名)。
* SQLite は使わないので復元は不要。

## 【実行手順】

1. `get_schema_snapshot(None)` を呼ぶ。
2. 戻り値の owner、テーブル名の一覧、列数の合計、制約の種類別の数、インデックス数を検証する。
3. EMPLOYEES の EMPLOYEE_ID が `NUMBER(6)`・NOT NULL、SALARY が `NUMBER(8,2)`、EMP_MANAGER_FK が EMPLOYEES→EMPLOYEES(MANAGER_ID→EMPLOYEE_ID)、JHIST_EMP_ID_ST_DATE_PK が 2 列(EMPLOYEE_ID, START_DATE の順)、COUNTRIES の iot が true であることを検証する。
4. `get_schema_snapshot("NO_SUCH_SCHEMA")` が `OracleFailure`(code=NOT_FOUND)を送出することを検証する。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t01_oracle_snapshot.py -v`

## 【期待結果】

* 上記の期待値がすべて一致し、存在しないスキーマは NOT_FOUND。

## 【合否判定基準】

* pytest が全件 PASS なら PASS。1 件でも失敗なら FAIL。Oracle に接続できず実行できなければ BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 結果をテスト記録に残し、`docs/P008-test-direction.md` の T01 を `[x]` にしたら T02 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
