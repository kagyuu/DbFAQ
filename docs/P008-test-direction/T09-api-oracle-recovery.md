あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T09

※CR-002により内容を置き換えた(旧: 「API: MCP 子プロセスの回復」。MCP の子プロセスが無くなったため)。

## 【目的】

* Oracle との通信が切れても、backend が Oracle のエラー(502/504)を返したのち、通信が戻れば **backend を再起動せずに** 次の呼び出しから回復することを確認する(CR-002「期待する振る舞い」、P001 §8.2)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.3

## 【対象モジュール】

* `dbfaq_api`(services、oracle の接続プール)+ Oracle(U007)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更) を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR。SQLite は `tmp_path`。
* 共有の Oracle 本体は止めない(他の利用者がいるため)。代わりに、テスト内で **TCP 中継**(`127.0.0.1` の空きポート → config.yaml の `host:port`)を立て、backend の接続先をその中継にする。中継を止める(待ち受けを閉じ、中継中の接続もすべて切る)ことで「Oracle との通信が切れた」状態を作り、同じポートで中継を再開することで「戻った」状態を作る。

## 【事前準備】

* `server/tests/integration/test_t09_oracle_recovery.py` を作る(旧 `test_t09_mcp_recovery.py` を削除)。
* 中継は `asyncio.start_server` で作り、接続ごとに Oracle へ `asyncio.open_connection` して双方向にコピーする。止めるときは待ち受けを `close()` し、中継中の全ソケットを `transport.abort()` で切る。
* app の設定は config.yaml の `oracle.host` を `127.0.0.1`、`port` を中継のポート、`connect_timeout_sec` を 3 にしたもの(`write_config` と `make_app` を使う)。

## 【実行手順】

1. 中継を開始し、app を起動する。`POST /api/schema/refresh` → 200。`GET /api/health` → status=ok。
2. 中継を止める。
3. `GET /api/health` → status=degraded、oracle.status=error。`GET /api/schema/tables/HR/EMPLOYEES/rows` → 502 `ORACLE_ERROR` または 504 `ORACLE_TIMEOUT`。`GET /api/schema` は 200(保存済み)。
4. 同じポートで中継を再開する。app は再起動しない。
5. `GET /api/health` を最大 3 回(1 秒間隔)→ status=ok になる。
6. `GET /api/schema/tables/HR/EMPLOYEES/rows` → 200、50 行。`POST /api/schema/refresh` → 200。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t09_oracle_recovery.py -v`

## 【期待結果】

* 通信が切れている間は Oracle のエラーになり、戻った後は app を再起動せずに 3 回以内の呼び出しで回復する。

## 【合否判定基準】

* 全件 PASS なら PASS。回復しなければ FAIL。中継のポートへ Oracle がリダイレクト(別ポートへの接続指示)を返して中継が使えない場合は、環境要因として最小再現で切り分け、BLOCKED として記録する。

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
