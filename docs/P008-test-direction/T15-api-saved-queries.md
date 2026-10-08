あなたはExecutor(実装担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P008-test-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】T15(※CR-005により追加)

## 【目的】

* 保存済み Query の API が、実際の SQLite ファイル・マイグレーション・ひな型の登録・スナップショットの置き換え(refresh)と連携して仕様どおりに動くこと、特に**テーブルが無くなっても保存済み Query が残り、同じ名前のテーブルが戻ると再び使える**ことを確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「保存済み Query の API」「テーブルが無くなって戻ったとき」「マイグレーション 0002」

## 【対象モジュール】

* `routers/saved_queries.py`、`SavedQueryService`、`SavedQueryRepository`、`migrate.py`、`main.py` の lifespan、`SnapshotRepository.replace`(U010)

## 【前提条件】対象スプリントの全モジュールビルドが成功していること

* ビルド対象: `server/`(Python)。ビルドコマンド: `cd server && uv sync`。成功条件: 終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* Oracle は使わない(偽の Oracle アクセス `tests/fakes.py` の `FakeOracle` で refresh の結果を切り替える。HR を変更しない方針(P006 §3.2)のため、テーブルの消失と復活を実 Oracle では作らない)。

## 【使用するテストデータ】

* `FakeOracle` のスナップショット: (A) HR の EMPLOYEES・DEPARTMENTS を含む、(B) EMPLOYEES を含まない。SQLite は `tmp_path` の 1 つのファイルを、テストの中で 2 回の起動(lifespan)にまたがって使う。

## 【事前準備】

* `server/tests/integration/test_t15_saved_queries.py` を作る(`tests/integration/conftest.py` が `oracle` マーカーを付けるが、Oracle には接続しない)。`create_app(config(sqlite_path=tmp_path/...), oracle=FakeOracle)` を 既存の API の単体テスト(`tests/unit/api/test_api.py` の `client` フィクスチャ)と同じ形で lifespan を通して呼ぶ。

## 【実行手順】

1. 1 回目の起動: `GET /api/saved-queries?scope=pdb` → ひな型 17 件、すべて `is_template=true`。
2. (A) で refresh。`POST /api/saved-queries`(HR.EMPLOYEES、名前「部署50」)→ 201。同じ名前でもう一度 → 409 `QUERY_NAME_CONFLICT`。HR.DEPARTMENTS に同じ名前 → 201。
3. `GET ?scope=table&owner=HR&table=EMPLOYEES` → 「部署50」の 1 件だけ(DEPARTMENTS の分は出ない)。
4. (B) で refresh。`GET /api/schema/tables/HR/EMPLOYEES` → 404 `TABLE_NOT_FOUND`。`GET ?scope=table&owner=HR&table=EMPLOYEES` → 「部署50」が同じ id・SQL で残っている。
5. ひな型を 1 件削除し、別の 1 件を改名する。アプリを止めて同じ SQLite ファイルで 2 回目の起動 → マイグレーションの適用は 0 件で起動に成功し、`scope=pdb` は 16 件(削除したひな型は戻らず、改名はそのまま)。
6. (A) で refresh。`GET /api/schema/tables/HR/EMPLOYEES` → 200。`GET ?scope=table&owner=HR&table=EMPLOYEES` → 「部署50」(手順 2 と同じ id・SQL)。`PUT` で SQL を変える → 200、`DELETE` → 204、もう一度 `DELETE` → 404。
6b. ※CR-006により追加: ひな型の更新。(a) ひな型を以前の版の SQL で登録した状態(CR-005 の版を再現)で起動すると、利用者が変えていないひな型は新しい版の SQL・名前になり、SQL を変えたひな型はそのまま残る。(b) もう一度起動しても変わらない。この手順はリポジトリの単体テスト(`test_saved_query_repo.py`)で一時 SQLite を使って確かめる。
7. 2 回続けて実行して同じ結果になる。

## 【実行コマンド】

* `cd server && uv run python -m pytest tests/integration/test_t15_saved_queries.py -v`

## 【期待結果】

* 手順 1〜7 がすべて期待どおり。

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

* 記録して T15 を `[x]` にしたら、P008 の全項目の結果をまとめて P104 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
