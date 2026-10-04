あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A06

## 【目的】

* 受入テストのスイート全体を通して Oracle のデータが変わっていないこと(読み取りのみ)、パスワードが応答・ログ・イメージに出ないこと、公開範囲が web だけであることを確認する(REQ-NFR-004、REQ-ORA-004(旧 REQ-MCP-004))。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2「セキュリティ」「読み取りのみ」

## 【対象モジュール】

* api、web、compose(CR-002 で MCP を削除)

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更))。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* HR の全表(8 表。※P202 F010(CR-004))のチェックサム。取得に失敗したとき・ベースラインが無いときは FAIL(P202 F009)。基準値は A01 の事前準備(`reset-and-up.sh`)がスイート開始前に `server/scripts/hr_checksum.py` で取得した `e2e/.baseline-checksum.json` を使う。※P011(2回目)矛盾点#1にもとづき修正

## 【事前準備】

* `e2e/scripts/a06-security.sh` を作る(新規)。※CR-004により手順 6 を追加する。`server/scripts/hr_checksum.py` は A01 で作成済みのものを使う。

## 【実行手順】

1. 現在の HR のチェックサムを取り、`e2e/.baseline-checksum.json` と完全一致する。
2. パスワード文字列(`config.yaml` の oracle.password)が、次のいずれにも含まれない: `/api/health` の本文/`/api/schema` の本文/`docker compose logs api web` の全文/`docker image inspect` と `docker run --rm dbfaq-api ... sh -c 'grep -r <pw> /app || true'` の出力(イメージ名は `docker compose images -q api` で得る)。
3. `docker compose ps --format json` で公開ポート(Publishers の PublishedPort が 0 でないもの)を持つのは web だけで、ポートは 8088。
4. `curl -s -i -H 'Origin: http://evil.example' localhost:8088/api/schema` のヘッダに `access-control-allow-origin` が無い。
5. `git ls-files | grep -x config.yaml` が何も出さない(リポジトリに入っていない)。
6. ※CR-004により追加: `POST /api/query` と `POST /api/query/csv` に次の SQL を送ると、どれも 422 で `error.code` が `SQL_REJECTED` になる: `UPDATE HR.EMPLOYEES SET SALARY = SALARY + 1`、`DELETE FROM HR.EMPLOYEES`、`DROP TABLE HR.EMPLOYEES`、`BEGIN NULL; END;`、`SELECT * FROM HR.EMPLOYEES FOR UPDATE`、`SELECT 1 FROM DUAL; DELETE FROM HR.EMPLOYEES`。手順 1 のチェックサムはこれらを送った後に取る(スクリプト内で手順 6 を手順 1 より先に実行する)。

## 【実行コマンド】

* `bash e2e/scripts/a06-security.sh`

## 【期待結果】

* 1〜6 がすべて成り立つ。

## 【合否判定基準】

* すべて成り立てば PASS。1 でチェックサムが違えば FAIL(重大。どの表かを記録)。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。
* パスワードが見つかった場合は、**パスワード自体は記録せず**、見つかった場所(ファイル・行番号・ログの行)だけを記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A06 を `[x]` にしたら A07 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
