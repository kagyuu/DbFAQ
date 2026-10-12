# DbFAQ
Save your routine SQL queries as FAQs (Frequent Asked Queries) and re-run them against your database at any time.

## 現在の機能(v0.6.0 / 第 1 リリース + CR-001〜CR-007)

Oracle のスキーマを backend(FastAPI)が直接読み取って SQLite に保存し、ブラウザで次の画面を提供します。CR-005 で、Query タブで作った SQL を名前と説明付きで保存し、いつでも復元・実行できるようになりました。

* **ER 図**: テーブルと外部キーの関係を表示。拡大・縮小、全体の略図(ミニマップ)、テーブル名検索。テーブルをクリックすると詳細へ
* **テーブル詳細**: 「スキーマ情報」(列・主キー・一意制約・外部キー・参照元・インデックス)、「データ」(50 行ずつのページ送り)、「Query」をタブで切り替え
* **Query タブ**(CR-004): スキーマ情報から SELECT 文のひな形を作り(外部キーでつながるテーブルをチェックすると JOIN を追加)、任意の SELECT 文を実行。結果は先頭 500 行を表で表示し、全行は CSV でダウンロード。Oracle のエラーは ORA コードと、SQL の何行目の何文字目かを表示。SELECT・WITH 以外の文は実行しない(読み取り専用トランザクションでも実行)
* **Query の保存・復元**(CR-005): Query タブの SQL を名前と説明を付けてテーブルごとに保存し、一覧から入力欄に復元。上書き保存・名前の変更・削除も可能。スキーマの変更でテーブルが無くなっても保存した Query は残り、同じ名前のテーブルが戻れば再び使える
* **PDB 画面**(CR-005): ER 図の左上のドラム缶のアイコンから開く。PDB の情報(コンテナ名・バージョン・文字セット・表領域の割り当て・セグメントの使用量など)の表示と、テーブルに属さない Query の実行・保存。USERS 表領域の大きさ、テーブル.カラムごとの LOB 領域と実データの合計など、運用でよく使う Query のひな型 17 件を最初から登録(DBA_* ・V$ を使うひな型は、それらを読む権限が必要)
* **LLM で SQL を作成**(CR-007): Query タブ(テーブル・PDB)で、作りたい SQL を文章で書くと、LLM(Ollama)がスキーマの構造をもとに SELECT 文を作って入力欄に入れます。作った SQL は自動では実行しません(内容を確かめてから [実行])。ヘッダの「Oracle」の丸の並びに「LLM」の丸(緑 = 使える、赤 = 使えない、灰 = 設定なし)を表示し、LLM が使えないときは作成のボタンを押せません
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

## LLM(Ollama)を設定する

LLM で SQL を作る機能は、`config.yaml` の `llm` 節で設定します(節を消すと LLM は使わず、ヘッダの丸は灰色になります)。いまは Ollama の API に対応しています。

```yaml
llm:
  enabled: true
  provider: ollama
  base_url: http://localhost:11434   # Ollama の接続先
  model: gemma4:e2b-it-qat           # Ollama に入っているモデル(ollama pull で入れる)
  timeout_sec: 180                   # 1 回の作成で待つ上限(CPU だと数十秒〜かかる)
  sample_rows: 3                     # LLM に渡すデータの例の行数(0 で送らない)
```

* **LLM に送る情報**: データベースの種類(Oracle とバージョン)、スキーマの構造(テーブル・列の名前・型・コメント、主キー・外部キー)、テーブルの Query タブではそのテーブルの先頭 `sample_rows` 行、あなたが書いた要求。**業務データの一部が LLM に渡る**ので、LLM の接続先は社内の信頼できるもの(ローカルの Ollama など)にしてください。データの例を送りたくなければ `sample_rows: 0` にします。
* **Docker Compose で動かすとき**: コンテナからは `localhost` で Ollama に届かないため、環境変数 `DBFAQ_LLM_BASE_URL` で接続先を指定します(既定 `http://host.docker.internal:11434` = Docker ホスト)。Ollama がホストのすべてのアドレスで待ち受けている(`OLLAMA_HOST=0.0.0.0:11434`)必要があります。`.env` ファイル(Git 管理外)に `DBFAQ_LLM_BASE_URL=http://<Ollama のホスト>:11434` と書くこともできます。
* **WSL2 上の Docker で、ホスト Windows の Ollama を使う場合**: コンテナから Windows の Ollama には直接届かないため、WSL2 で socat による中継が要ります。手順は下の「起動(Docker Compose)」の「WSL2 上の Docker でホスト Windows の Ollama を使う場合」を参照してください。
* 作られた SQL は、Query タブで実行するときに、手で書いた SQL と同じ検査(SELECT・WITH の 1 文だけ)と読み取り専用トランザクション・読み取り専用ユーザーで守られます。

## 起動(Docker Compose)

```bash
cp config.example.yaml config.yaml   # Oracle の接続情報(dbfaq_ro)を記入(config.yaml は Git 管理外)
docker compose up -d --build
curl http://localhost:8088/api/health # "status":"ok" を確認
```

ブラウザで `http://localhost:8088/` を開き、[Oracle から読み込む] を押します。

### WSL2 上の Docker でホスト Windows の Ollama を使う場合

DbFAQ を WSL2 上の Docker(docker compose)で動かし、LLM にホストの Windows で動いている Ollama を使う場合は、**WSL2 に socat を入れて中継を立てる**必要があります。

**なぜ要るのか**: WSL2 の mirrored モード(`.wslconfig` の `networkingMode=mirrored`)では、WSL2 からは `localhost:11434` で Windows の Ollama に届きますが、Docker のコンテナからは届きません(コンテナの `localhost` はコンテナ自身で、`host.docker.internal`・`172.17.0.1`・ホストの IP で接続しても WSL2 自身に届くため)。Windows で `OLLAMA_HOST=0.0.0.0:11434` にしても変わりません。そこで WSL2 側で socat を動かし、コンテナから届くアドレス(Docker のホスト側アドレス `172.17.0.1` の 11435 番)で受けて、`127.0.0.1:11434`(Windows の Ollama)へ転送します。11434 番は Windows と WSL2 で共有されるため、WSL2 側では別の番号(11435)を使います。

1. **Windows で Ollama を動かす**: モデルを入れておきます(`ollama pull gemma4:e2b-it-qat`)。WSL2 から届くことを確かめます。

   ```bash
   curl http://localhost:11434/api/version     # {"version":"..."} が返る
   ```

2. **WSL2 に socat を入れる**:

   ```bash
   sudo apt install socat
   ```

3. **中継を起動する**(リポジトリのルートで。WSL2 を再起動したら、もう一度実行します):

   ```bash
   deploy/dev/llm-relay.sh start     # 172.17.0.1:11435 → 127.0.0.1:11434
   deploy/dev/llm-relay.sh status    # 動いているか
   deploy/dev/llm-relay.sh stop      # 止める
   ```

   スクリプトを使わない場合は、次のコマンドを動かしたままにしても同じです。

   ```bash
   socat TCP-LISTEN:11435,bind=172.17.0.1,fork,reuseaddr TCP:127.0.0.1:11434
   ```

   中継は Docker のホスト側アドレス(`docker0` の IP。通常 `172.17.0.1`)だけで待ち受けるので、LAN の他の端末からは届きません。アドレスやポートは環境変数 `LLM_RELAY_BIND`・`LLM_RELAY_PORT` で変えられます。

4. **接続先を `.env` に書く**: リポジトリのルートに `.env`(Git 管理外)を作り、次の 1 行を書きます。docker compose が読み込み、api コンテナの LLM の接続先になります(`config.yaml` の `llm.base_url` より優先)。

   ```bash
   echo 'DBFAQ_LLM_BASE_URL=http://host.docker.internal:11435' > .env
   ```

5. **起動する**: `docker compose up -d --build`(既に起動している場合は `docker compose up -d --force-recreate api`)。

6. **確かめる**: `curl -s http://localhost:8088/api/health` の `"llm"` が `"status":"ok"` になり、画面のヘッダの「LLM」の丸が緑になります。赤のときはマウスを乗せて理由を見て、`deploy/dev/llm-relay.sh status` で中継が動いているかを確かめてください。

詳しい手順・前提・既知の制約は [docs/P302-deliver.md](./docs/P302-deliver.md) を参照してください。全体の目次は [INDEX.md](./INDEX.md) です。
