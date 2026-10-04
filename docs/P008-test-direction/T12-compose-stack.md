あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T12

## 【目的】

* compose で起動した web(nginx)→ api(FastAPI)→ Oracle(ホスト上)(※CR-002により MCP 子プロセスを削除)の連携と、公開範囲の構成を確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2「セキュリティ」、`docs/P005-impl-plan.md` U006

## 【対象モジュール】

* `compose.yaml`、`deploy/`(U006)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: 両イメージ。ビルドコマンド: `docker compose build`。成功条件: 終了コード 0。失敗時は BLOCKED として出力を記録し、テストへ進まない。
* 開発用 Oracle が起動していること。

## 【使用するテストデータ】

* HR。SQLite はボリューム `dbfaq_dbfaq-data`。ベースラインは「ボリューム無し」。

## 【事前準備】

* `docker compose down -v`(ボリュームを消してベースラインに戻す。**アプリを起動する前に**行う)→ `docker compose up -d` → `curl -sf localhost:8088/api/health` が応答するまで最大 60 秒待つ。

## 【実行手順】

1. `curl -s localhost:8088/api/health` → status=ok、oracle.version が空でない。本文に config.yaml のパスワードの文字列が含まれない(`grep -c` で 0)。
2. `curl -s -X POST localhost:8088/api/schema/refresh` → `"table_count":8`。(※P202 F010(CR-004)により変更。人間の指示 2026-10-04)
3. `curl -s -o /dev/null -w '%{http_code}' localhost:8088/tables/HR/EMPLOYEES` → 200、本文が index.html(`<div id="root">` を含む)。
4. `docker compose port api 8000` が何も出さない(公開されていない)。`curl -s -m 3 localhost:8000/api/health` が接続できない(8000 番を他に使っていないことを先に `ss -ltn | grep :8000` で確認)。
5. `docker compose exec api sh -c 'ls /app /app/server'` の結果に `config.yaml` が無い(マウントは /config のみ)。
6. `docker compose ps --format json` で api・web とも running。

## 【実行コマンド】

* 上記のコマンドを順に実行する。

## 【期待結果】

* 1〜6 がすべて成り立つ。

## 【合否判定基準】

* すべて成り立てば PASS。違えば FAIL。コンテナから Oracle に届かず 1 が error の場合は、U006-T3 の停止条件の切り分けを行い、環境要因なら BLOCKED として記録する。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、エラーメッセージ(ORA コードを含む)、pytest の出力の該当部分を残す。
* `docker compose logs --tail 50 api web` を記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示でテストファイルを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップ(`skip`/`xfail`)しない。期待値を変えて成功扱いにしない。
* 同じ失敗に対して場当たり的な再実行を繰り返さない(環境要因の切り分けのための再実行は 1 回まで)。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。
* `compose.yaml`・`deploy/` も修正しない。

## 【次タスクへ進む条件】

* 記録して T12 を `[x]` にしたら、P008 の全テストの結果を確認して P104 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
