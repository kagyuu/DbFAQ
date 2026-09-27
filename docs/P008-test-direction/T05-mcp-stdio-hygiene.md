> **※CR-002 により廃止。** MCP サーバ(stdio)を廃止したため、確かめる対象が無くなった。テストコード `server/tests/integration/test_t05_stdio.py` も削除した。backend のログが 1 行 1 JSON で標準出力に出ることは単体テスト(`tests/unit/test_logging.py`)で確かめている。本書は第 1 リリース時点の記録として残す。

あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T05

## 【目的】

* MCP サーバの標準出力が MCP の通信だけに使われ、ログは標準エラー出力に JSON で出ることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2「ログ」

## 【対象モジュール】

* `dbfaq_mcp.__main__`、`dbfaq_common.logging`(U001・U002)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* MCP の initialize 要求(JSON-RPC 1 行): `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t05","version":"0"}}}`

## 【事前準備】

* `server/tests/integration/test_t05_stdio.py` を作る。`subprocess.Popen([sys.executable, "-m", "dbfaq_mcp"], stdin=PIPE, stdout=PIPE, stderr=PIPE, env={..., "DBFAQ_CONFIG": ...})`。

## 【実行手順】

1. initialize 要求を stdin に書いて改行し、stdout から 1 行読む(タイムアウト 10 秒)。
2. stdin を閉じてプロセスの終了を待つ(10 秒)。
3. stdout の全行が JSON として読め、すべて `"jsonrpc": "2.0"` を持つ。
4. stderr の空でない行のうち、JSON として読める行があり、それらは `level`・`msg` を持つ(FastMCP 自体が出す JSON でない行が混じってもよいが、stdout には混じらないこと)。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t05_stdio.py -v`

## 【期待結果】

* stdout は JSON-RPC の応答のみ。

## 【合否判定基準】

* 全件 PASS なら PASS。stdout に JSON-RPC 以外の行があれば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。
* stdout・stderr の先頭 20 行を記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T05 を `[x]` にしたら T06 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
