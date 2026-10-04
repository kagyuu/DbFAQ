あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U009 — query-tab(※CR-004により追加)

SC-02 テーブル詳細に Query タブを追加し、利用者が書いた SELECT 文を実行できるようにする。変更要求: `docs/P901-cr-direction/CR-004.md`。**既存の API・スキーマ情報タブ・データタブ・ER 図の振る舞いは変えない。**

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U009-T1 [SQL の検査](#u009-t1-sql-の検査) — `oracle/sql_guard.py`(正規化 N1〜N6、拒否規則 G1〜G5)
- [x] U009-T2 [SELECT の実行・エラー位置・CSV](#u009-t2-select-の実行エラー位置csv) — `oracle/query.py`、`values.py` の切り詰めない文字列化、`errors.py` の `SQL_REJECTED`・位置、`OracleClient`
- [x] U009-T3 [Query の API](#u009-t3-query-の-api) — `routers/query.py`、`services.py`、`schemas.py`、`errors.py`、`main.py`、`tests/fakes.py`
- [x] U009-T4 [ひな形の組み立て](#u009-t4-ひな形の組み立て) — `client/src/query/template.ts`
- [x] U009-T5 [Query タブの画面](#u009-t5-query-タブの画面) — `QueryTab.tsx`、`TableDetailPage.tsx`、`urlState.ts`、`src/api/`
- [x] U009-T6 [nginx と受入テスト](#u009-t6-nginx-と受入テスト) — `deploy/nginx.conf`、`e2e/tests/a09-query-tab.spec.ts`、`e2e/scripts/a06-security.sh`・`run-suite.sh`

---

## U009-T1: SQL の検査

### 【目的】

* 利用者の SQL を Oracle に送る前に字句で検査する(多層防御の 1 層目)。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/sql_guard.py`(新規)、`server/src/dbfaq_api/oracle/errors.py`(`SQL_REJECTED` を追加)
* `server/tests/unit/oracle/test_sql_guard.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.10、`docs/P002-frontend-spec.md` §3.8
* 参考実装: `../OracleSearchMCP/app/src/guard/sql-lexer.ts`・`sql-guard.ts`

### 【実装内容】

* `normalize_sql(sql) -> tuple[str, list[tuple[int, int]]]`(判定用の文字列と、引用符付き識別子の範囲)。
* `check_select(sql) -> str`: 拒否なら `OracleFailure(SQL_REJECTED, 理由)`、通れば実行用の SQL(末尾の空白とセミコロン 1 個を取り除く。先頭は変えない)。
* メッセージは P003 §3.10 の例のとおり日本語。

### 【実装してはいけないこと】

* 判定用の文字列を実行に使わない。先頭の空白・コメントを取り除いた SQL を実行しない(エラー位置がずれる)。

### 【Unit Test内容】

* P006 §2.1「SQL の検査」の正常系・異常系をすべて。少なくとも: `SELECT 1 FROM DUAL;` は通り末尾の `;` が取れる、`with a as (select 1 x from dual) select x from a` が通る、`SELECT 'DELETE' FROM DUAL`・`SELECT "UPDATE" FROM T`・`SELECT 1 FROM DUAL -- drop table x` が通る、`SELECT q'[;DROP]' FROM DUAL` が通る、`/*+ FULL(t) */` を含む SELECT が通る、`UPDATE`・`delete from t`・`BEGIN NULL; END;`・`DECLARE`・`SELECT 1 FROM DUAL; SELECT 2 FROM DUAL`・`SELECT * FROM T FOR UPDATE`・`WITH x AS (DELETE ...)`・`SELECT ... EXECUTE IMMEDIATE`・`DBMS_SQL`・`LOCK TABLE`・`GRANT`・`COMMIT`・空白だけ、が拒否される。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit/oracle/test_sql_guard.py -q`

### 【完了条件】

* 単体テストが全件合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U009-T2: SELECT の実行・エラー位置・CSV

### 【目的】

* 検査を通った SELECT を読み取り専用トランザクションで実行し、先頭 500 行または全行の CSV を作る。Oracle のエラー位置を行・文字に変換する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/query.py`(新規)、`oracle/values.py`(`format_cell(..., full=False)` の引数を追加)、`oracle/errors.py`(`OracleFailure.position`、バイト位置 → 位置の変換)、`oracle/client.py`(`run_query`・`export_csv`、`OracleAccess` プロトコル)
* `server/tests/unit/oracle/test_query.py`(新規。偽のカーソル・プールは `tests/unit/oracle/fakes.py` を拡張)、`test_values.py`(`full=True` を追加)、`test_errors.py`(位置の変換)
* `server/tests/integration/test_t13_query.py`(新規。P008 T13)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.1、§3.2、§3.7、§3.11、`docs/P002-frontend-spec.md` §3.1・§3.8・§3.9

### 【実装内容】

* `run_query(db, sql, max_rows=500, clock=time.perf_counter) -> dict`: P002 §3.8 の本文(`columns`、`rows`、`truncated`、`row_count`、`has_more`、`max_rows`、`elapsed_ms`)。
* `export_csv(db, sql) -> tuple[BinaryIO, int]`: P003 §3.11 のとおり `SpooledTemporaryFile` に BOM 付き UTF-8・CRLF で書き、先頭に戻したファイルと行数を返す。失敗時はファイルを閉じて例外。
* 実行・取得の `oracledb.Error` は、`from_oracle_error` に実行用の SQL を渡して `position`(`offset`・`line`・`column`)を付ける。`err.offset` は UTF-8 のバイト位置。0 以下・文字の途中・長さ超過なら位置なし。
* `SET TRANSACTION READ ONLY` や接続の失敗には位置を付けない(従来どおり `Database.run_readonly` が変換する)。

### 【実装してはいけないこと】

* 利用者の SQL をサブクエリで包まない。`run_readonly` を経ずに実行しない。既存の `get_table_rows`・`format_cell` の既定の振る舞いを変えない。

### 【Unit Test内容】

* 位置の変換: `SELECT FOO FROM T`(offset 7 → 1 行 8 文字目)、`SELECT 1\nFROM T\nWHERE BAR = 1`(30 → 3 行 7 文字目)、`-- 日本語コメント\nSELECT ほげ FROM EMPLOYEES`(バイト 32 → 文字 18、2 行 8 文字目)、0・長さ超過・文字の途中 → None。
* `run_query`: 501 行目があれば `has_more=True` で 500 行、0 行、値の文字列化と切り詰め、`SQL_REJECTED` のときカーソルを使わない(Oracle に送らない)、実行時の `oracledb.Error` に位置が付く。
* `export_csv`: BOM、CRLF、見出し、`"`・カンマ・改行の囲み、NULL は空、1,000 文字超・32 バイト超を切り詰めない、行数。
* `format_cell(full=True)`: 切り詰めない。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit -q`
* `cd server && DBFAQ_CONFIG=../config.yaml uv run pytest tests/integration/test_t13_query.py -q`

### 【完了条件】

* 単体テストが全件合格(既存を含む)。T13 は P103 で実行する(ここでは書くだけでよいが、実行できるなら実行して記録する)。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U009-T3: Query の API

### 【目的】

* `POST /api/query`・`POST /api/query/csv` を提供する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/routers/query.py`(新規)、`services.py`(`QueryService` または `SchemaService` へのメソッド追加、`_to_api_error` の `SQL_REJECTED`・`position`)、`errors.py`(`SQL_REJECTED` 422、`ApiError.position`)、`schemas.py`(`QueryRequest`、`QueryResponse`、`ErrorBody.position`)、`main.py`(ルータの登録)
* `server/tests/fakes.py`(`FakeOracle` に `run_query`・`export_csv`)、`server/tests/unit/api/test_query_api.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3.1・§3.8・§3.9、`docs/P003-backend-spec.md` §4.1・§4.3・§4.4・§4.5

### 【実装内容】

* 本文の検証: `sql` は 1〜100,000 文字、空白だけは 422 `VALIDATION_ERROR`。
* CSV は `StreamingResponse`(64 KiB ずつ、送り終えたら・切断されたらファイルを閉じる)。ヘッダ `Content-Disposition: attachment; filename="query.csv"`、`X-Row-Count`。
* ログ: `sql_chars`・`row_count`・`has_more`・`elapsed_ms`・(エラー時)`ora_code`。SQL の本文と結果は出さない。

### 【実装してはいけないこと】

* 既存の API の応答の形を変えない(エラーの `position` は Query のときだけ付く任意の項目)。

### 【Unit Test内容】

* 200 の形、CSV のヘッダと本文、422(空・空白・100,001 文字・SQL_REJECTED)、502(`ora_code` と `position`)、504、ログに SQL の本文が出ない。

### 【実行コマンド】

* `cd server && uv run pytest tests/unit -q && uv run ruff check src tests scripts`

### 【完了条件】

* 単体テストが全件合格し、ruff の指摘が CR-004 前(10 件)より増えていない。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U009-T4: ひな形の組み立て

### 【目的】

* スキーマ情報から SELECT 文のひな形を作る純粋関数を作る。

### 【作成・編集対象ファイル】

* `client/src/query/template.ts`(新規)、`client/src/query/template.test.ts`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §2.2.6(JOIN するテーブルの一覧)、§2.2.7

### 【実装内容】

* `listJoinCandidates(detail: TableDetail, schema: ErView): JoinCandidate[]` — → と ← の制約を P002 §2.2.6 の順に。相手の列が分からないものは `available=false`。
* `buildSelectTemplate(detail, schema, selected: JoinCandidate[]): string` — P002 §2.2.7。
* `quoteIdent(name)` — 予約語の一覧(`ACCESS`、`ADD`、`ALL`、`ALTER`、`AND`、`ANY`、`AS`、`ASC`、`AUDIT`、`BETWEEN`、`BY`、`CHAR`、`CHECK`、`CLUSTER`、`COLUMN`、`COMMENT`、`COMPRESS`、`CONNECT`、`CREATE`、`CURRENT`、`DATE`、`DECIMAL`、`DEFAULT`、`DELETE`、`DESC`、`DISTINCT`、`DROP`、`ELSE`、`EXCLUSIVE`、`EXISTS`、`FILE`、`FLOAT`、`FOR`、`FROM`、`GRANT`、`GROUP`、`HAVING`、`IDENTIFIED`、`IMMEDIATE`、`IN`、`INCREMENT`、`INDEX`、`INITIAL`、`INSERT`、`INTEGER`、`INTERSECT`、`INTO`、`IS`、`LEVEL`、`LIKE`、`LOCK`、`LONG`、`MAXEXTENTS`、`MINUS`、`MLSLABEL`、`MODE`、`MODIFY`、`NOAUDIT`、`NOCOMPRESS`、`NOT`、`NOWAIT`、`NULL`、`NUMBER`、`OF`、`OFFLINE`、`ON`、`ONLINE`、`OPTION`、`OR`、`ORDER`、`PCTFREE`、`PRIOR`、`PUBLIC`、`RAW`、`RENAME`、`RESOURCE`、`REVOKE`、`ROW`、`ROWID`、`ROWNUM`、`ROWS`、`SELECT`、`SESSION`、`SET`、`SHARE`、`SIZE`、`SMALLINT`、`START`、`SUCCESSFUL`、`SYNONYM`、`SYSDATE`、`TABLE`、`THEN`、`TO`、`TRIGGER`、`UID`、`UNION`、`UNIQUE`、`UPDATE`、`USER`、`VALIDATE`、`VALUES`、`VARCHAR`、`VARCHAR2`、`VIEW`、`WHENEVER`、`WHERE`、`WITH`。Oracle の V$RESERVED_WORDS の RESERVED='Y' 相当)に当たる名前と、規則に合わない名前を `"` で囲む。

### 【Unit Test内容】

* P006 §2.1「frontend のひな形」のすべて。HR 相当のデータ(`client/src/test/hr.ts`・`detail.ts`)で EMPLOYEES の EMP_DEPT_FK を選んだ結果が P002 §2.2.7 の例と一致する。

### 【実行コマンド】

* `cd client && npx vitest run src/query/template.test.ts`

### 【完了条件】

* 単体テストが全件合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U009-T5: Query タブの画面

### 【目的】

* SC-02 に Query タブを追加する。

### 【作成・編集対象ファイル】

* `client/src/pages/QueryTab.tsx`(新規)、`client/src/pages/QueryTab.test.tsx`(新規)、`TableDetailPage.tsx`(タブの追加、Query の状態の保持)、`urlState.ts`(`query`)、`urlState.test.ts`、`TableDetailPage.test.tsx`(タブの切り替え)
* `client/src/api/types.ts`(`QueryResult`、`ApiErrorBody.position`)、`client.ts`(`runQuery`、`downloadQueryCsv`、`ApiError.position`)、`hooks.ts`(必要なら)、`client.test.ts`
* `client/src/test/fetchMock.ts`(必要なら POST と CSV の応答)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1.2、§1.3、§2.2.1、§2.2.4〜§2.2.6、§3.1、§3.8、§3.9

### 【実装内容】

* Query タブの状態(入力欄、最後に作ったひな形、チェックボックス、結果・エラー)は `TableDetailPage` の `Detail` に持ち、タブを切り替えても保つ(`Detail` はテーブルごとに `key` で作り直されるので、別のテーブルでは初期化される)。
* 結果の表はデータタブと同じ部品の見た目にする(重複するならデータタブの表を共通の部品に切り出してよい。その場合もデータタブの振る舞いは変えない)。
* CSV は `fetch` で受け取り、`Blob` → `URL.createObjectURL` → `<a download>` で保存する。エラー時は JSON を `ApiError` にする。
* エラー位置: 「エラー位置: N 行目 M 文字目」、その行と `^`、[エラー位置へ移動](入力欄にフォーカスし、その文字を選択)。`column` はコードポイント単位なので、JS の文字列の位置(UTF-16)に直してから選択する。

### 【実装してはいけないこと】

* スキーマ情報タブ・データタブの振る舞いを変えない。SQL を URL・ブラウザの保存領域に保存しない。

### 【Unit Test内容】

* P006 §2.1「SC-02 Query タブ」のすべて。

### 【実行コマンド】

* `cd client && npm test && npm run build`

### 【完了条件】

* 単体テスト全件合格、ビルド成功。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U009-T6: nginx と受入テスト

### 【目的】

* CSV の長い応答を nginx で切らないようにし、受入テストを用意する。

### 【作成・編集対象ファイル】

* `deploy/nginx.conf`(`location = /api/query/csv` に `proxy_read_timeout 600s`、`proxy_buffering off`)
* `e2e/tests/a09-query-tab.spec.ts`(新規。P009 A09)、`e2e/scripts/a06-security.sh`(Query API の拒否を追加)、`e2e/scripts/a05-perf-api.sh`(Query の性能を追加)、`e2e/scripts/run-suite.sh`(A09 を A02 の後に追加)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §6、`docs/P009-acceptance-direction/A09-query-tab-scenario.md`、`A05-performance.md`、`A06-security-readonly.md`

### 【実装内容】

* P009 の各手順をそのままテストにする。

### 【実行コマンド】

* `docker compose up -d --build` → `cd e2e && npx playwright test tests/a09-query-tab.spec.ts`

### 【完了条件】

* テストが書け、compose で起動して 1 回は実行できた(合否は P201 で判定する)。

### 【次タスクに進む前の停止条件】

* なし(受入テストの合否は P201 が扱う)。

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件(`SKILL.md` 参照。例: 単体テストが3回自己修正しても合格しない)に該当しない限り、次のタスクに自動的に進んでください。1タスクごとに人間の指示を待つ必要はありません。
