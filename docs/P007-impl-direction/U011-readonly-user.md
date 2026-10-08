あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U011 — readonly-user(※CR-006により追加)

読み取り専用ユーザー `dbfaq_ro` を前提に、PDB 情報とひな型を対象スキーマ(`oracle.schema`)基準にし、登録済みのひな型を新しい版に更新できるようにする。README に `dbfaq_ro` の作成手順を載せる。変更要求: `docs/P901-cr-direction/CR-006.md`。**API の形・画面の構成・SQLite のテーブルは変えない。**

## タスク一覧(OKF副目次)

- [x] U011-T1 [接続のカレントスキーマ](#u011-t1-接続のカレントスキーマ) — `oracle/db.py`
- [x] U011-T2 [PDB 情報を対象スキーマ基準に](#u011-t2-pdb-情報を対象スキーマ基準に) — `oracle/pdb.py`
- [x] U011-T3 [ひな型を対象スキーマ基準にし、未変更のひな型を更新する](#u011-t3-ひな型を対象スキーマ基準にし未変更のひな型を更新する) — `pdb_templates.py`、`saved_query_repo.py`
- [x] U011-T4 [結合・受入テストの期待値](#u011-t4-結合受入テストの期待値) — T03・T14・A10
- [x] U011-T5 [README と設定のひな型](#u011-t5-readme-と設定のひな型) — `README.md`、`config.example.yaml`

---

## U011-T1: 接続のカレントスキーマ

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/db.py`、`server/tests/unit/oracle/fakes.py`(`current_schema` 属性)、`server/tests/unit/oracle/test_db.py`(新規、または既存の Database のテスト)

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.1

### 【実装内容】

* `run_readonly` で接続を借りたら、`SET TRANSACTION READ ONLY` の前に `conn.current_schema = cfg.target_schema` を設定する。

### 【Unit Test内容】

* 偽の接続で、`run_readonly` の中から見た `current_schema` が `target_schema`(`schema` 省略時は接続ユーザーの大文字)になる。

### 【実行コマンド】

* `cd server && uv run python -m pytest tests/unit/oracle -q`

### 【完了条件】・【停止条件】

* 単体テストが全件合格。3 回自己修正しても合格しなければ停止して報告する。

---

## U011-T2: PDB 情報を対象スキーマ基準に

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/oracle/pdb.py`、`server/tests/unit/oracle/test_pdb.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §3.12、`docs/P002-frontend-spec.md` §3.14

### 【実装内容】

* `overview` は 2 つの SQL(基本項目と、DBA_USERS の対象スキーマの表領域)。2 つ目の `ORACLE_ERROR` は 2 行の値を `(権限が無いため取得できません)` / `(取得できません: ORA-xxxxx)` にし、セクションのエラーにしない。`ORACLE_TIMEOUT` は全体の失敗。
* 項目名: 「カレントスキーマ」→「対象スキーマ」、「既定の表領域」→「対象スキーマの既定の表領域」、「一時表領域」→「対象スキーマの一時表領域」。
* `ts_quotas`・`segments` は DBA_* を `SYS_CONTEXT('USERENV','CURRENT_SCHEMA')` で絞る。

### 【Unit Test内容】

* overview の 10 行の項目名と値、DBA_USERS が ORA-00942 のときの 2 行の値(他のセクションに影響しない)、既存のセクションのエラー・タイムアウトのテスト。

### 【実行コマンド】・【完了条件】・【停止条件】

* `cd server && uv run python -m pytest tests/unit/oracle/test_pdb.py -q`。全件合格。3 回で停止。

---

## U011-T3: ひな型を対象スキーマ基準にし、未変更のひな型を更新する

### 【作成・編集対象ファイル】

* `server/src/dbfaq_api/pdb_templates.py`(02・03・04・08〜13 の SQL・名前・説明、`PdbTemplate.previous`)、`server/src/dbfaq_api/pdb_templates_v1.py`(新規。CR-005 の版の名前・説明・SQL を変更せずに残す)、`server/src/dbfaq_api/saved_query_repo.py`(`seed_templates` の更新)
* `server/tests/unit/oracle/test_pdb_templates.py`、`server/tests/unit/api/test_saved_query_repo.py`

### 【参照すべき仕様箇所】

* `docs/P003-backend-spec.md` §4.7、ADR-016

### 【実装内容】

* 02・03・08 は DBA_* 、09〜13 は ALL_* を、`owner`(または `username`)= `SYS_CONTEXT('USERENV','CURRENT_SCHEMA')` で絞る。04 は ALL_LOBS(読める表だけ)。
* `seed_templates` は登録済みのキーについて、行の SQL が `previous` の SQL のどれかと完全に一致するときだけ新しい版にする(説明・名前も以前の版のままなら更新。名前が重なるときは名前だけ残す)。戻り値で更新したキーも分かるようにする(ログに出す)。

### 【実装してはいけないこと】

* キーを変えること(既存の環境で別のひな型として二重に登録される)。利用者が SQL を変えた行の上書き。

### 【Unit Test内容】

* 全ひな型が検査を通る・権限の注記が DBA_* ・V$ の有無と一致する(既存)。以前の版で登録したデータベースで起動 → 未変更のひな型は新しい版、SQL を変えた行は残る、削除した行は復活しない、2 回目は何もしない。

### 【実行コマンド】・【完了条件】・【停止条件】

* `cd server && uv run python -m pytest tests/unit -q`。全件合格。3 回で停止。

---

## U011-T4: 結合・受入テストの期待値

### 【作成・編集対象ファイル】

* `server/tests/integration/test_t03_readonly.py`(手順 2 のエラーコード)、`test_t14_pdb.py`(手順 1〜5b)、`e2e/tests/a10-saved-queries-pdb.spec.ts`(手順 10・13)

### 【参照すべき仕様箇所】

* `docs/P008-test-direction/T03-oracle-readonly.md`・`T14-oracle-pdb.md`、`docs/P009-acceptance-direction/A10-saved-queries-pdb-scenario.md`

### 【完了条件】

* P103・P201 で実行する。

---

## U011-T5: README と設定のひな型

### 【作成・編集対象ファイル】

* `README.md`(依頼者の指示: `dbfaq_ro` を作る理由、作成の SQL、`config.yaml` への登録)、`config.example.yaml`(`oracle.user: dbfaq_ro`、`schema` の説明)

### 【実装内容】

* 理由: 読み取り専用で書き込みができない(Query タブの二重の防御を三重にする)、PDB 情報・運用ひな型に辞書ビュー(DBA_* ・V$)の参照が要る、`READ` は `SELECT ... FOR UPDATE`・`LOCK TABLE` もできない。
* SQL: PDB に管理ユーザーで接続して `CREATE USER`、`GRANT CREATE SESSION`、`GRANT SELECT_CATALOG_ROLE`、`GRANT READ ANY TABLE ON SCHEMA <対象スキーマ>`(23ai 以降)/ 19c 以前は表ごとの `GRANT READ`。
* `config.yaml`: `oracle.user: dbfaq_ro`、`password`、`schema: <対象スキーマ>`。パスワードは `config.yaml` にだけ書く。

### 【完了条件】

* README に 3 点(理由・作り方・config.yaml)がある。
