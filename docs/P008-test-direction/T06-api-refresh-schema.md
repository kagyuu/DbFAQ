あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T06

## 【目的】

* backend → Oracle → SQLite の連携で(※CR-002により MCP(実子プロセス)を削除)、スキーマの再読み込みと ER 図用・詳細用の読み出しが動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「POST /api/schema/refresh」「GET /api/schema」「GET /api/schema/tables/...」

## 【対象モジュール】

* `dbfaq_api`(services、snapshot_repo、oracle、routers)+ Oracle + SQLite(U003、CR-002 で U007 により変更)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更) を出す。出なければ BLOCKED として記録する。

## 【使用するテストデータ】

* HR(T01 と同じ期待値)。SQLite はテストごとに `tmp_path` の新しいファイル(`docs/P006-test-plan.md` §3.2)。

## 【事前準備】

* `server/tests/integration/conftest.py` にフィクスチャ `api_client` を追加: `load_config(<config.yaml>)` の `app.sqlite_path` を `tmp_path/"t.sqlite3"` に差し替えた設定で `create_app(config)`(oracle は省略=実際の `OracleClient`。※CR-002により「gateway は省略=実際の `StdioMcpGateway`」から変更)を作り、lifespan を動かして `httpx.AsyncClient(transport=ASGITransport(app), base_url="http://t")` を渡す。
* `server/tests/integration/test_t06_api_refresh.py` を作る。

## 【実行手順】

1. `GET /api/schema` → `loaded=false`。
2. `POST /api/schema/refresh` → 200、`table_count=8`、`relation_count=11`(※P202 F010(CR-004)により 7・10 から変更)、`owner=HR`。
3. `GET /api/schema` → tables 8(名前の昇順)、relations 11、EMPLOYEES の EMPLOYEE_ID が `is_pk=true`、DEPARTMENT_ID が `is_fk=true`。
4. `GET /api/schema/tables/HR/EMPLOYEES` → primary_key `EMP_EMP_ID_PK`、unique_keys に `EMP_EMAIL_UK`、foreign_keys 3 本(EMP_DEPT_FK、EMP_JOB_FK、EMP_MANAGER_FK)、referenced_by に DEPT_MGR_FK・JHIST_EMP_FK・EMP_MANAGER_FK・FK_EMPLOYEE_FIGURE_EMP(※P202 F010(CR-004)により追加)、indexes 6、num_rows=107。
5. もう一度 `POST /api/schema/refresh` → 200。SQLite の `snapshots` が 1 行のまま(直接 SELECT して確認)。

## 【実行コマンド】

* `cd server && uv run pytest tests/integration/test_t06_api_refresh.py -v`

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

* 記録して T06 を `[x]` にしたら T07 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Executor Stepの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
