# DbFAQ
Save your routine SQL queries as FAQs (Frequent Asked Queries) and re-run them against your database at any time.

## 現在の機能(v0.4.0 / 第 1 リリース + CR-001〜CR-005)

Oracle のスキーマを backend(FastAPI)が直接読み取って SQLite に保存し、ブラウザで次の画面を提供します。CR-005 で、Query タブで作った SQL を名前と説明付きで保存し、いつでも復元・実行できるようになりました。

* **ER 図**: テーブルと外部キーの関係を表示。拡大・縮小、全体の略図(ミニマップ)、テーブル名検索。テーブルをクリックすると詳細へ
* **テーブル詳細**: 「スキーマ情報」(列・主キー・一意制約・外部キー・参照元・インデックス)、「データ」(50 行ずつのページ送り)、「Query」をタブで切り替え
* **Query タブ**(CR-004): スキーマ情報から SELECT 文のひな形を作り(外部キーでつながるテーブルをチェックすると JOIN を追加)、任意の SELECT 文を実行。結果は先頭 500 行を表で表示し、全行は CSV でダウンロード。Oracle のエラーは ORA コードと、SQL の何行目の何文字目かを表示。SELECT・WITH 以外の文は実行しない(読み取り専用トランザクションでも実行)
* **Query の保存・復元**(CR-005): Query タブの SQL を名前と説明を付けてテーブルごとに保存し、一覧から入力欄に復元。上書き保存・名前の変更・削除も可能。スキーマの変更でテーブルが無くなっても保存した Query は残り、同じ名前のテーブルが戻れば再び使える
* **PDB 画面**(CR-005): ER 図の左上のドラム缶のアイコンから開く。PDB の情報(コンテナ名・バージョン・文字セット・表領域の割り当て・セグメントの使用量など)の表示と、テーブルに属さない Query の実行・保存。USERS 表領域の大きさ、テーブル.カラムごとの LOB 領域と実データの合計など、運用でよく使う Query のひな型 17 件を最初から登録(DBA_* ・V$ を使うひな型は、それらを読む権限が必要)
* 保存した Query は SQLite(Docker ボリューム)にあり、Oracle からは作り直せないため、バックアップしてください(手順は docs/P302-deliver.md 7 章)

## 起動(Docker Compose)

```bash
cp config.example.yaml config.yaml   # Oracle の接続情報を記入(config.yaml は Git 管理外)
docker compose up -d --build
curl http://localhost:8088/api/health # "status":"ok" を確認
```

ブラウザで `http://localhost:8088/` を開き、[Oracle から読み込む] を押します。詳しい手順・前提・既知の制約は [docs/P302-deliver.md](./docs/P302-deliver.md) を参照してください。全体の目次は [INDEX.md](./INDEX.md) です。
