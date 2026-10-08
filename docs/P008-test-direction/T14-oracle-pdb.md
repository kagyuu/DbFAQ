あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T14(※CR-005により追加)

## 【目的】

* PDB の情報の読み取り(`get_pdb_info`)・`GET /api/pdb` と、PDB の Query のひな型が実 Oracle(HR)で仕様どおりに動くことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「PDB 情報」「PDB のひな型の実行」

## 【対象モジュール】

* `dbfaq_api.oracle.pdb`、`OracleClient.get_pdb_info`、`routers/pdb.py`、`pdb_templates.PDB_TEMPLATES`(U010)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle が起動していること: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8` を出す。出なければ BLOCKED。
* 接続ユーザー `hr` は DBA_* ・V$SESSION を読めない(2026-10-07 確認)。

## 【使用するテストデータ】

* HR(読み取りのみ)。LOB 列は `EMPLOYEE_FIGURE.FIGURE`(BLOB、SECUREFILE)。

## 【事前準備】

* `server/tests/integration/test_t14_pdb.py` を作る(pytest マーカー `oracle`)。`OracleClient` と、`create_app(config, oracle=実 OracleClient)` を `httpx.AsyncClient(transport=ASGITransport(app))` で呼ぶ(T13 と同じ形)。

## 【実行手順】

1. `get_pdb_info()` → セクションの `key` が `overview`・`ts_quotas`・`segments`・`tablespaces` の順。`overview` は 10 行で、コンテナ名(PDB)が `FREEPDB1`、接続ユーザーが `HR`、既定の表領域が `USERS`。
2. `ts_quotas` に `USERS` の行があり、`segments` に `TABLE`・`INDEX`・`LOBSEGMENT` の行がある(いずれも `error` が null)。
3. `tablespaces` は `error.ora_code` が `ORA-00942`(hr に権限が無いため)で、`rows` が空。他のセクションには影響しない。
4. `GET /api/pdb` → 200、`sections` が 4 件、`fetched_at`(`Z` 付き)・`elapsed_ms`。
5. ひな型を全件 `run_query` で実行する: 権限の要らないもの(02・03・08〜13)は成功する。03 は `TABLE_COLUMN=EMPLOYEE_FIGURE.FIGURE`、`DATA_TYPE=BLOB`、`SEGMENT_MB` > 0、`DATA_LENGTH` > 0 の行を含む。権限の要るもの(01・04〜07・14〜17。16 は開発用 Oracle の hr でも読めたが、一般には権限が要る)は成功するか、`ORACLE_ERROR` の `ORA-00942`・`ORA-01031` のどちらかで失敗する(構文エラー(ORA-009xx の 942 以外)にならない)。※P011(CR-005)矛盾点#1にもとづき修正
6. 2 回続けて実行して同じ結果になる。

## 【実行コマンド】

* `cd server && DBFAQ_CONFIG=../config.yaml uv run python -m pytest tests/integration/test_t14_pdb.py -v`

## 【期待結果】

* 手順 1〜6 がすべて期待どおり。

## 【合否判定基準】

* 全件 PASS なら PASS。1 件でも違えば FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md` に、テスト ID、実行コマンド、失敗したテスト名、期待値と実際の値、ORA コード、pytest の出力の該当部分を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない。
* 失敗したテストをスキップしない。期待値を変えて成功扱いにしない。
* 失敗は記録して Reviewer Loop(P202 以降)に引き渡す。

## 【次タスクへ進む条件】

* 記録して T14 を `[x]` にしたら T15 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
