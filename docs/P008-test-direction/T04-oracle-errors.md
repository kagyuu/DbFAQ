あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T04

## 【目的】

* Oracle 側のエラー(認証失敗、タイムアウト)が `OracleFailure` のエラーコードに正しく変換され(※CR-002により「MCP の」を変更)、タイムアウトの後も次の呼び出しが動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「Oracle: 疎通確認」の異常系、§2.2「タイムアウト」

## 【対象モジュール】

* `dbfaq_api.oracle`(db.py、errors.py、client.py)と Oracle(U002、CR-002 で U007 に移設)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* 一時的な設定ファイル(`tmp_path` に作る): (a) パスワードだけを `wrong-password` にしたもの、(b) `query_timeout_sec: 1` にしたもの。どちらも元の config.yaml を読み込んで値を変えて書き出す。

## 【事前準備】

* `server/tests/integration/test_t04_oracle_errors.py` を作る(CR-002 で `test_t04_mcp_errors.py` から改名)。(a) は (a) の設定で作った `OracleClient` を使う(※CR-002により「MCP の子プロセスを起動するフィクスチャ」から変更)。(b) は `Database` を直接使う。

## 【実行手順】

1. (a) で `ping` → `OracleFailure` の code=ORACLE_ERROR、ora_code=ORA-01017。message に `wrong-password` が含まれない。
2. (b) の `Database.run_readonly` の中で `BEGIN DBMS_SESSION.SLEEP(3); END;` → `OracleFailure` の code=ORACLE_TIMEOUT。
3. 同じ (b) の `Database` で続けて `SELECT 1 FROM DUAL` → 成功(壊れた接続がプールに残っていない)。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t04_oracle_errors.py -v`

## 【期待結果】

* 1〜3 がすべて成り立つ。

## 【合否判定基準】

* 全件 PASS なら PASS。失敗があれば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。
* 2 で得られた実際の `full_code` とメッセージを必ず記録する(P003 §3.1 の実機確認の補強になる)。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T04 を `[x]` にしたら T05 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
