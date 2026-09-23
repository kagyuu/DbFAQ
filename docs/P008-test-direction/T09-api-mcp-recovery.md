あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T09

## 【目的】

* MCP の子プロセスが異常終了しても、backend が 503 を返したのち次の呼び出しで起動し直して回復することを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「MCP ゲートウェイ」、§2.3

## 【対象モジュール】

* `dbfaq_api.mcp_gateway.StdioMcpGateway` + `dbfaq_mcp`(U003)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR。SQLite は `tmp_path`。

## 【事前準備】

* `server/tests/integration/test_t09_mcp_recovery.py` を作る。T06 の `api_client` を使い、`app.state.gateway` から子プロセスの PID を得る方法がなければ、`psutil` を使わずに `/proc` を走査して親 PID が自プロセスで コマンドラインに `dbfaq_mcp` を含むプロセスを探す(Linux 前提)。

## 【実行手順】

1. `GET /api/health` → status=ok。
2. MCP 子プロセスに SIGKILL を送り、終了を待つ(最大 5 秒)。
3. `GET /api/health` → mcp.status=error(1 回目)。または内部で再起動が間に合って ok の場合もある。
4. `GET /api/health` をもう一度(最大 3 回、1 秒間隔)→ status=ok になる。新しい子プロセスの PID が 2 の PID と異なる。
5. `GET /api/schema/tables/HR/EMPLOYEES/rows` が呼べる(事前に refresh しておく)。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t09_mcp_recovery.py -v`

## 【期待結果】

* 子プロセスの強制終了後、3 回以内の呼び出しで回復する。

## 【合否判定基準】

* 全件 PASS なら PASS。回復しなければ FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T09 を `[x]` にしたら T10 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
