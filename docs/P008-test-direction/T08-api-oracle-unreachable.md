あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T08

## 【目的】

* Oracle に届かない設定でも backend が起動し、再読み込みの失敗で前回のスナップショットが残り、health が degraded になることを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「POST /api/schema/refresh」「GET /api/health」の異常系

## 【対象モジュール】

* `dbfaq_api`(U003、CR-002 で U007 により変更)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7` を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* 一時的な設定ファイル: 元の config.yaml の `port` を `1`(何も待ち受けていないポート)、`connect_timeout_sec: 3` にしたもの。SQLite は `tmp_path`。

## 【事前準備】

* `server/tests/integration/test_t08_oracle_unreachable.py` を作る。
* 同じ SQLite ファイルに対して、まず正しい設定の app で refresh してスナップショットを作り(1 回目の app を閉じる)、次に Oracle に届かない設定の app を作る。

## 【実行手順】

1. 届かない設定の app が lifespan を完了する(起動に成功する)。
2. `GET /api/schema` → `loaded=true`、tables 7(前回のスナップショット)。
3. `POST /api/schema/refresh` → 502 `ORACLE_ERROR` または 504 `ORACLE_TIMEOUT`。
4. `GET /api/schema` → 変わらず tables 7、fetched_at が 1 回目と同じ。
5. `GET /api/health` → 200、status=degraded、oracle.status=error、message が空でない、`mcp` が無い(※CR-002により「mcp.status=ok」を変更)。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t08_oracle_unreachable.py -v`

## 【期待結果】

* 1〜5 がすべて成り立つ。

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

* 記録して T08 を `[x]` にしたら T09 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
