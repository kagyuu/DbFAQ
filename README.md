# DbFAQ
Save your routine SQL queries as FAQs (Frequent Asked Queries) and re-run them against your database at any time.

## 現在の機能(v0.5.0 / 第 1 リリース + CR-001〜CR-006)

Oracle のスキーマを backend(FastAPI)が直接読み取って SQLite に保存し、ブラウザで次の画面を提供します。CR-005 で、Query タブで作った SQL を名前と説明付きで保存し、いつでも復元・実行できるようになりました。

* **ER 図**: テーブルと外部キーの関係を表示。拡大・縮小、全体の略図(ミニマップ)、テーブル名検索。テーブルをクリックすると詳細へ
* **テーブル詳細**: 「スキーマ情報」(列・主キー・一意制約・外部キー・参照元・インデックス)、「データ」(50 行ずつのページ送り)、「Query」をタブで切り替え
* **Query タブ**(CR-004): スキーマ情報から SELECT 文のひな形を作り(外部キーでつながるテーブルをチェックすると JOIN を追加)、任意の SELECT 文を実行。結果は先頭 500 行を表で表示し、全行は CSV でダウンロード。Oracle のエラーは ORA コードと、SQL の何行目の何文字目かを表示。SELECT・WITH 以外の文は実行しない(読み取り専用トランザクションでも実行)
* **Query の保存・復元**(CR-005): Query タブの SQL を名前と説明を付けてテーブルごとに保存し、一覧から入力欄に復元。上書き保存・名前の変更・削除も可能。スキーマの変更でテーブルが無くなっても保存した Query は残り、同じ名前のテーブルが戻れば再び使える
* **PDB 画面**(CR-005): ER 図の左上のドラム缶のアイコンから開く。PDB の情報(コンテナ名・バージョン・文字セット・表領域の割り当て・セグメントの使用量など)の表示と、テーブルに属さない Query の実行・保存。USERS 表領域の大きさ、テーブル.カラムごとの LOB 領域と実データの合計など、運用でよく使う Query のひな型 17 件を最初から登録(DBA_* ・V$ を使うひな型は、それらを読む権限が必要)
* PDB 画面とひな型は、接続ユーザーではなく `config.yaml` の `oracle.schema`(対象スキーマ)の情報を表示します(CR-006)
* 保存した Query は SQLite(Docker ボリューム)にあり、Oracle からは作り直せないため、バックアップしてください(手順は docs/P302-deliver.md 7 章)

## Oracle に読み取り専用ユーザー dbfaq_ro を作る

DbFAQ は、Oracle に**読み取り専用ユーザー `dbfaq_ro`** で接続して使います(ユーザー名は任意。以下では `dbfaq_ro`)。

### なぜ作るのか

* **書き込みを権限で防ぐため**: DbFAQ の Query タブ・PDB 画面では、利用者が書いた SELECT 文を実行します。DbFAQ は SQL の検査(SELECT・WITH の 1 文だけを通す)と読み取り専用トランザクションで更新を防いでいますが、接続ユーザーに書き込み権限が無ければ、Oracle の権限でも DML・DDL が止まります(三重の防御)。表の所有者(例 `hr`)で接続すると、この最後の防御がありません。
* **`SELECT` ではなく `READ` を与えるため**: `READ` 権限では、`SELECT ... FOR UPDATE`(行ロック)や `LOCK TABLE` もできません。参照だけの用途に合っています。
* **PDB の情報を読むため**: PDB 画面の「表領域の割り当て」「セグメントの使用量」「表領域の使用状況」と、運用 Query のひな型(USERS 表領域の大きさ、LOB 領域の大きさ、セッションの一覧など)は、辞書ビュー `DBA_*` ・動的パフォーマンスビュー `V$*` を読みます。これには `SELECT_CATALOG_ROLE` が要ります。このロールは辞書を参照できるだけで、データの変更はできません。

### 作り方

PDB(例 `FREEPDB1`)に管理ユーザー(SYS・SYSTEM など)で接続して実行します。CDB$ROOT ではなく PDB のローカルユーザーとして作ってください。`HR` は DbFAQ で見る対象スキーマに置き換えます。

```sql
CREATE USER dbfaq_ro IDENTIFIED BY "<パスワード>";

GRANT CREATE SESSION TO dbfaq_ro;             -- ログインだけ
GRANT SELECT_CATALOG_ROLE TO dbfaq_ro;        -- DBA_* ・V$ ビューの参照(読み取りのみ)

-- 対象スキーマの表を読む権限(どちらか)
GRANT READ ANY TABLE ON SCHEMA hr TO dbfaq_ro;   -- Oracle 23ai 以降: スキーマ単位
-- GRANT READ ON hr.employees TO dbfaq_ro;       -- 19c 以前: 表ごとに付与(表の数だけ)
```

* 表の作成・表領域の割り当て(quota)・プロシージャの `EXECUTE` などは与えません。
* 全スキーマの LOB のひな型は、`dbfaq_ro` が読める表だけを対象にします。他のスキーマの表も見たい場合は、そのスキーマにも `READ` を与えます。

### config.yaml に登録する

`config.example.yaml` を `config.yaml` にコピーし、`oracle` の `user`・`password`・`schema` を書きます。

```yaml
oracle:
  host: localhost            # コンテナからは compose が host.docker.internal に置き換える(docs/P302-deliver.md 7 章)
  port: 1521
  service_name: FREEPDB1     # PDB のサービス名
  user: dbfaq_ro             # 上で作った読み取り専用ユーザー
  password: "<パスワード>"    # パスワードはこのファイルにだけ書く(Git 管理外)
  schema: HR                 # 対象スキーマ(ER 図・PDB 情報・ひな型の対象)
```

* `schema` は、ER 図に表示し、PDB 画面・ひな型の対象にするスキーマです。DbFAQ は Oracle に接続するたびにカレントスキーマをこのスキーマにするので、Query タブではスキーマ名を付けずに表名だけで書けます(例 `SELECT * FROM EMPLOYEES`)。
* `config.yaml` は Git の管理対象外です。ファイルの権限は、サーバの運用者だけが読めるようにしてください。
* 権限を絞ったユーザー(`SELECT_CATALOG_ROLE` なし)でも動きます。その場合、読めない項目は画面に「権限が無いため取得できません」と表示されます。

## 起動(Docker Compose)

```bash
cp config.example.yaml config.yaml   # Oracle の接続情報(dbfaq_ro)を記入(config.yaml は Git 管理外)
docker compose up -d --build
curl http://localhost:8088/api/health # "status":"ok" を確認
```

ブラウザで `http://localhost:8088/` を開き、[Oracle から読み込む] を押します。詳しい手順・前提・既知の制約は [docs/P302-deliver.md](./docs/P302-deliver.md) を参照してください。全体の目次は [INDEX.md](./INDEX.md) です。
