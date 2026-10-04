あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T07

## 【目的】

* `GET /api/schema/tables/{owner}/{table}/rows` が実 Oracle を通してページ取得でき(※P011(CR-002 2回目)矛盾点#1にもとづき「実 MCP・」を削除)、エラーを API の形式に変換することを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「GET .../rows」

## 【対象モジュール】

* `dbfaq_api` + Oracle(U003。※P011(CR-002)矛盾点#2にもとづき `dbfaq_mcp` を削除)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更) を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR.EMPLOYEES(107 行)。SQLite は `tmp_path`。

## 【事前準備】

* T06 の `api_client` を使う。テストの最初に `POST /api/schema/refresh` を 1 回呼んでスナップショットを作る(同じテストファイル内の前提)。
* `server/tests/integration/test_t07_api_rows.py` を作る。

## 【実行手順】

1. `GET /api/schema/tables/HR/EMPLOYEES/rows?offset=100&limit=50` → 200、rows 7、has_next=false、owner=HR、table=EMPLOYEES、elapsed_ms が 0 以上の整数。
2. `?limit=501` → 422 `VALIDATION_ERROR`。
3. `GET /api/schema/tables/HR/NO_SUCH/rows` → 404 `TABLE_NOT_FOUND`(Oracle にアクセスしない。※P011(CR-002 2回目)矛盾点#1にもとづき「MCP を呼ばない」から変更)。
4. スナップショットの db_tables に存在しない表名 `GHOST` を SQLite に直接 1 行挿入し(Oracle には無い表 = 削除済みの再現)、`GET /api/schema/tables/HR/GHOST/rows` → 502 `ORACLE_ERROR`、ora_code=`ORA-00942`。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t07_api_rows.py -v`

## 【期待結果】

* 1〜4 がすべて成り立つ。

## 【合否判定基準】

* 全件 PASS なら PASS。失敗があれば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T07 を `[x]` にしたら T08 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
