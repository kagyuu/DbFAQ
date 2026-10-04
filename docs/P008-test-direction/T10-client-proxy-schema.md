あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T10

## 【目的】

* 開発時の構成(Vite 開発サーバの proxy → backend)で、ER 図画面が使う API(`/api/schema`、`/api/schema/refresh`、`/api/health`)が同一オリジンで呼べ、エラーの形式もそのまま届くことを確認する(ADR-004の方針の確認)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「SC-01」、`docs/P003-backend-spec.md` §7

## 【対象モジュール】

* `client`(vite.config.ts の proxy)+ `dbfaq_api`(U004)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(`cd server && uv sync`)と `client/`(`cd client && npm ci && npm run build`)。成功条件: 両方とも終了コード 0。失敗時は BLOCKED として出力を記録し、テストへ進まない。
* 開発用 Oracle が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更))。

## 【使用するテストデータ】

* HR。SQLite は `/tmp` ではなくスクラッチの一時ディレクトリ(`mktemp -d`)のファイルを `DBFAQ_SQLITE_PATH` で指定する(毎回新しい=ベースライン)。

## 【事前準備】

* 端末 1: `cd server && DBFAQ_CONFIG=../config.yaml DBFAQ_SQLITE_PATH=$(mktemp -d)/t10.sqlite3 uv run uvicorn --factory dbfaq_api.main:create_app --port 8000`
* 端末 2: `cd client && npm run dev -- --port 5173 --strictPort`
* 両方が応答するまで待つ(`curl -sf localhost:8000/api/health`、`curl -sf localhost:5173/`)。

## 【実行手順】

1. `curl -s -o /dev/null -w '%{http_code}' localhost:5173/api/health` → 200。本文に `"status"`。
2. `curl -s localhost:5173/api/schema` → `"loaded":false`。
3. `curl -s -X POST localhost:5173/api/schema/refresh` → 200、`"table_count":7`。
4. `curl -s localhost:5173/api/schema | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d["tables"]), len(d["relations"]))'` → `7 10`。
5. `curl -s -i localhost:5173/api/schema` のヘッダに `access-control-allow-origin` が無い。
6. 終了後、端末 1・2 のプロセスを止める。

## 【実行コマンド】

* 上記の `curl` を順に実行する(結果を記録にそのまま貼る)。

## 【期待結果】

* 1〜5 がすべて成り立つ。

## 【合否判定基準】

* すべて成り立てば PASS。1 つでも違えば FAIL。いずれかのサーバが起動しなければ BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。
* uvicorn と Vite の端末出力の末尾 30 行を記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T10 を `[x]` にしたら T11 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
