あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U010 — saved-queries-pdb(※CR-005により追加)

Query の SQL をテーブルごと・PDB に名前と説明付きで保存・復元できるようにし、SC-01 のドラム缶のアイコンから開く SC-03 PDB 画面(PDB 情報・Query)を作る。PDB の Query のひな型を起動時に登録する。変更要求: `docs/P901-cr-direction/CR-005.md`。**既存の API・ER 図・スキーマ情報タブ・データタブ・Query タブ(ひな形・実行・CSV・エラー位置)の振る舞いは変えない。**

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U010-T1 [マイグレーション・保存済み Query のリポジトリ・ひな型の登録](#u010-t1-マイグレーション保存済み-query-のリポジトリひな型の登録) — `0002_saved_queries.sql`、`saved_query_repo.py`、`pdb_templates.py`
- [x] U010-T2 [PDB の情報の読み取り](#u010-t2-pdb-の情報の読み取り) — `oracle/pdb.py`、`OracleClient.get_pdb_info`
- [x] U010-T3 [保存済み Query と PDB の API](#u010-t3-保存済み-query-と-pdb-の-api) — `routers/saved_queries.py`・`routers/pdb.py`、`services.py`、`schemas.py`、`errors.py`、`main.py`、`tests/fakes.py`
- [x] U010-T4 [API クライアントと保存済み Query の部品](#u010-t4-api-クライアントと保存済み-query-の部品) — `src/api/`、`src/components/SavedQueries.tsx`
- [x] U010-T5 [Query タブの共用化・ドラム缶のアイコン・SC-03](#u010-t5-query-タブの共用化ドラム缶のアイコンsc-03) — `QueryTab.tsx`、`TableDetailPage.tsx`、`PdbIcon.tsx`、`ErDiagramPage.tsx`、`PdbPage.tsx`、`PdbInfoTab.tsx`、`App.tsx`、`urlState.ts`
- [x] U010-T6 [受入テスト](#u010-t6-受入テスト) — `e2e/tests/a10-saved-queries-pdb.spec.ts`、`e2e/scripts/run-suite.sh`

---

## U010-T1: マイグレーション・保存済み Query のリポジトリ・ひな型の登録

### 【目的】

* 保存済み Query を SQLite に置き、スナップショットの置き換えで消えないようにする。PDB のひな型を 1 回だけ登録する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/migrations/0002_saved_queries.sql`(新規)、`server/src/dbfaq_api/saved_query_repo.py`(新規)、`server/src/dbfaq_api/pdb_templates.py`(新規。CR-005 の設計時に作成済みの SQL を使う)
* `server/tests/unit/api/test_saved_query_repo.py`(新規)、`server/tests/unit/api/test_migrate.py`(0002 を追加)、`server/tests/unit/oracle/test_pdb_templates.py`(新規)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §4.2(`saved_queries`・`query_template_seeds`)、`docs/P003-backend-spec.md` §4.6・§4.7・§5.2・§5.4

### 【実装内容】

* 0002 は `CREATE TABLE` 2 つだけ(UNIQUE はテーブル定義の制約で)。`--` の行はコメントだけ、`;` は文の区切りだけ。
* `SavedQueryRepository(engine, now: Callable[[], str])`: `list(scope, owner, table)`、`get(id)`、`create(...)`、`update(id, name, description, sql)`、`delete(id)`、`seed_templates(templates) -> list[str]`(登録したキー)。重複は `NameConflict` 例外(`sqlalchemy.exc.IntegrityError` の UNIQUE 違反から変換)。`scope=pdb` は owner・table_name を空文字列で保存し、返す辞書では `None`。
* `seed_templates` は 1 トランザクション。`query_template_seeds` にあるキーは飛ばす。名前が既にあれば「 (ひな型)」を付ける。

### 【実装してはいけないこと】

* `db_tables`・`snapshots` への外部キー、スナップショットとの JOIN。`snapshot_repo.replace` の変更。
* ひな型をマイグレーションの SQL ファイルで入れること(`;`・`--` の分割規則に合わない)。

### 【Unit Test内容】

* P006 §2.1「マイグレーション 0002」「保存済み Query のリポジトリ」「ひな型の登録」の正常系・異常系をすべて。少なくとも: 0001 だけ適用済みのファイルに `apply_all` → 0002 が適用される。同じファイルにマイグレーション + `seed_templates` を 2 回 → 2 回目は登録 0 件で件数が変わらない。HR.EMPLOYEES に保存 → `SnapshotRepository.replace` で EMPLOYEES の無いスナップショット → 行が残る → EMPLOYEES のあるスナップショット → `list` が同じ行を返す。同じ保存先の同じ名前は `NameConflict`、`HR.EMPLOYEES` と `HR.employees`・PDB では同じ名前で可。全ひな型が `check_select` を通り、キーと名前が一意。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/unit/api/test_saved_query_repo.py tests/unit/api/test_migrate.py tests/unit/oracle/test_pdb_templates.py -q`

### 【完了条件】

* 単体テストが全件合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U010-T2: PDB の情報の読み取り

### 【目的】

* `GET /api/pdb` のための決まった SELECT を、セクションごとのエラーを許して実行する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/pdb.py`(新規)、`server/src/dbfaq_api/oracle/client.py`(`get_pdb_info`、`OracleAccess` プロトコル)
* `server/tests/unit/oracle/test_pdb.py`(新規。偽のカーソルは `tests/unit/oracle/fakes.py` を使う・拡張する)
* `server/tests/integration/test_t14_pdb.py`(新規。P008 T14)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.12、`docs/P002-frontend-spec.md` §3.14

### 【実装内容】

* `get_pdb_info(db) -> {"sections": [...]}`。各セクションは `{"key","title","columns","rows","truncated","error"}`。`run_readonly` の中でセクションを順に実行する。`query.py` の `_columns` と `values.format_row` を使う。
* セクションの `oracledb.Error` → `from_oracle_error(e, db.secret)`。`ORACLE_TIMEOUT` は送出、それ以外はセクションの `error`。

### 【実装してはいけないこと】

* 利用者の入力を SQL に埋め込むこと。セクションごとに別のトランザクション・接続を使うこと。

### 【Unit Test内容】

* overview の 10 行(バージョンは `conn.version`)、tablespaces の ORA-00942 が error になり他のセクションは行を持つ、タイムアウト(DPY-4024)で `OracleFailure(ORACLE_TIMEOUT)`。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/unit/oracle/test_pdb.py -q`
* 結合: `cd server && uv run python -m pytest tests/integration/test_t14_pdb.py -q`

### 【完了条件】

* 単体テストが全件合格(結合テストは P103 で実行する)。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U010-T3: 保存済み Query と PDB の API

### 【目的】

* P002 §3.10〜§3.14 の API 5 本を作る。起動時にひな型を登録する。

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/routers/saved_queries.py`・`routers/pdb.py`(新規)、`services.py`(`SavedQueryService`・`PdbService`)、`schemas.py`、`errors.py`(`SAVED_QUERY_NOT_FOUND`・`QUERY_NAME_CONFLICT`)、`main.py`(lifespan でひな型の登録、ルータの追加)
* `server/tests/fakes.py`(`FakeOracle.get_pdb_info`)
* `server/tests/unit/api/test_saved_queries_api.py`・`test_pdb_api.py`(新規)
* `server/tests/integration/test_t15_saved_queries.py`(新規。P008 T15)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3.1・§3.10〜§3.14、`docs/P003-backend-spec.md` §4.3〜§4.7

### 【実装内容】

* 名前・説明は pydantic の `field_validator` で前後の空白を除いてから長さを検査する。`scope` は `Literal["table","pdb"]`。`scope` と `owner`・`table` の組み合わせの検査は 422 `VALIDATION_ERROR`(メッセージは「owner: scope=table のときは必須です」など)。
* `DELETE` は `Response(status_code=204)`。
* ログは P003 §4.3・§4.5(名前・SQL を出さない)。

### 【実装してはいけないこと】

* 保存時に SQL の検査(`check_select`)を行うこと。保存済み Query の API でスナップショットや Oracle にアクセスすること。

### 【Unit Test内容】

* P006 §2.1「保存済み Query の API」「PDB 情報」の API の分をすべて(偽の Oracle アクセスと一時 SQLite)。起動直後の `GET /api/saved-queries?scope=pdb` にひな型 17 件(`is_template=true`)があること。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/unit -q`

### 【完了条件】

* 単体テスト(既存を含む)が全件合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U010-T4: API クライアントと保存済み Query の部品

### 【目的】

* 保存済み Query の一覧・保存・復元・上書き保存・変更・削除の画面部品を作る(SC-02・SC-03 で共用)。

### 【作成・編集対象ファイル】

* `client/src/api/types.ts`・`client.ts`・`hooks.ts`(保存済み Query・PDB の型と関数、`useSavedQueries`・`usePdbInfo`)
* `client/src/components/SavedQueries.tsx`(新規)、`client/src/components/SavedQueries.test.tsx`(新規)、`client/src/api/client.test.ts`(追加)

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §2.2.8、§3.10〜§3.13

### 【実装内容】

* `SavedQueries` の props: 保存先(`{scope:'table', owner, table}` / `{scope:'pdb'}`)、現在の SQL、復元中の項目(`{id, name, description}` か null)、編集中かどうか、`onRestore(item)`、`onSaved(item)`、`onLoadedChange(item | null)`。ダイアログは Mantine の `Modal`。
* 一覧のキーは `['saved-queries', scope, owner, table]`。保存・変更・削除の成功時に無効化する。

### 【Unit Test内容】

* P006 §2.1「frontend の保存済み Query」をすべて(`fetchMock` で API を偽物に)。

### 【実行コマンド】

* `cd client && npx vitest run src/components/SavedQueries.test.tsx src/api/client.test.ts`

### 【完了条件】

* 単体テストが全件合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U010-T5: Query タブの共用化・ドラム缶のアイコン・SC-03

### 【目的】

* Query タブをテーブル・PDB の両方で使えるようにし、保存済み Query を組み込む。SC-01 にアイコン、SC-03 を作る。

### 【作成・編集対象ファイル】

* `client/src/pages/QueryTab.tsx`(`detail` を省略可能にし、省略時は PDB として扱う(既存の呼び出しとテストをそのまま使うため。P102 で決定)。保存済み Query の組み込み、[名前を付けて保存]・[上書き保存]、復元中の表示)、`TableDetailPage.tsx`
* `client/src/components/PdbIcon.tsx`(新規。円柱の SVG)、`client/src/pages/ErDiagramPage.tsx`(キャンバス領域の左上にアイコン)
* `client/src/pages/PdbPage.tsx`・`PdbInfoTab.tsx`(新規)、`client/src/App.tsx`(`/pdb`)、`client/src/pages/urlState.ts`(`parsePdbTab`)
* テスト: `QueryTab.test.tsx`(保存・復元の追加、既存はそのまま合格すること)、`PdbPage.test.tsx`(新規)、`ErDiagramPage.test.tsx`(アイコン)、`urlState.test.ts`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1.2、§2.1、§2.2.1、§2.2.6、§2.2.8、§2.3

### 【実装内容】

* `QueryState` に `loaded`(復元中の項目)と `baseline`(最後にひな形・復元・保存した SQL)を加える。編集中 = `sql.trim() !== '' && sql !== baseline`。
* PDB では JOIN の一覧と [ひな形を作成] を出さず、初期値は空、CSV のファイル名は `PDB_query_...csv`。
* `PdbPage` の Query タブの状態は `PdbPage` が持つ(タブを切り替えても保つ)。

### 【実装してはいけないこと】

* CR-004 のひな形・チェックボックスの自動置き換え・エラー表示の振る舞いを変えること(既存の `QueryTab.test.tsx` のテストを変えずに合格させる)。

### 【Unit Test内容】

* P006 §2.1「SC-01 の PDB のアイコン・SC-03」をすべてと、Query タブの保存・復元の組み込み(復元すると入力欄が変わり実行できる、チェックボックスで復元した SQL が置き換わらない)。

### 【実行コマンド】

* `cd client && npm test`、`cd client && npm run build`

### 【完了条件】

* 単体テスト(既存を含む)が全件合格し、ビルドが成功する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても単体テストが合格しない場合は停止して報告する。

---

## U010-T6: 受入テスト

### 【目的】

* compose で起動した環境で、保存・復元と PDB 画面の一連の操作を確かめる(P009 A10)。

### 【作成・編集対象ファイル】

* `e2e/tests/a10-saved-queries-pdb.spec.ts`(新規)、`e2e/scripts/run-suite.sh`(A10 を追加)

### 【参照すべき仕様箇所】

* `docs/P009-acceptance-direction/A10-saved-queries-pdb-scenario.md`、`docs/P006-test-plan.md` §3.2

### 【実装内容】

* 名前に `A10-` を付け、テストの最初と最後に API で `A10-` で始まる保存済み Query を削除する。

### 【実行コマンド】

* `docker compose up -d --build && cd e2e && npx playwright test tests/a10-saved-queries-pdb.spec.ts`

### 【完了条件】

* A10 が合格する(P201 で実行・記録する)。

### 【次タスクに進む前の停止条件】

* なし(失敗は P201 → P202 で扱う)。
