あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T03

## 【目的】

* backend の読み取り専用トランザクションが実 Oracle で有効であり、Oracle アクセスの各処理の実行で HR のデータが変わらないことを確認する。※CR-002により「MCP サーバ」「ツール」から変更

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「Oracle: 読み取り専用」、§3.2

## 【対象モジュール】

* `dbfaq_api.oracle.db.Database.run_readonly`、`OracleClient` の各処理と Oracle(U002、CR-002 で U007 に移設)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR.EMPLOYEES。チェックサム: `SELECT COUNT(*), SUM(ORA_HASH(EMPLOYEE_ID||'|'||SALARY||'|'||EMAIL)) FROM HR.EMPLOYEES`。

## 【事前準備】

* `server/tests/integration/test_t03_readonly.py` を作る。`Database(load_config(<config.yaml>).oracle)` を直接使う(`OracleClient` を通さない。3 層目の防御を直接確かめるため。`../OracleSearchMCP` の ADR-009 と同じ考え方)。

## 【実行手順】

1. チェックサムを取る(`run_readonly` の中で)。
2. `run_readonly` の中で `UPDATE HR.EMPLOYEES SET SALARY = SALARY + 1 WHERE EMPLOYEE_ID = 100` を実行 → `OracleFailure` で ora_code が `ORA-01456`。
3. `OracleClient` で `get_schema_snapshot`、`get_table_rows`(EMPLOYEES 全 3 ページ)、`ping` を呼ぶ(※CR-002により「MCP クライアント経由で」を変更)。
4. 再度チェックサムを取り、1 と一致する。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t03_readonly.py -v`

## 【期待結果】

* UPDATE が ORA-01456 で拒否され、チェックサムが前後で一致する。

## 【合否判定基準】

* 全件 PASS なら PASS。UPDATE が成功した場合は FAIL(重大。記録に明記する)。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。
* UPDATE が成功してしまった場合は、テストの最後の ROLLBACK が行われたか、チェックサムの前後の値を必ず記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T03 を `[x]` にしたら T04 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
