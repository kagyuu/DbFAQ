# DbFAQ
Save your routine SQL queries as FAQs (Frequent Asked Queries) and re-run them against your database at any time.

## 現在の機能(v0.1.0 / 第 1 リリース)

Oracle のスキーマを MCP サーバ経由で読み取って SQLite に保存し、ブラウザで次の画面を提供します。FAQ(クエリの保存・実行)は今後のリリースで追加予定です。

* **ER 図**: テーブルと外部キーの関係を表示。拡大・縮小、全体の略図(ミニマップ)、テーブル名検索。テーブルをクリックすると詳細へ
* **テーブル詳細**: 「スキーマ情報」(列・主キー・一意制約・外部キー・参照元・インデックス)と「データ」(50 行ずつのページ送り)をタブで切り替え

## 起動(Docker Compose)

```bash
cp config.example.yaml config.yaml   # Oracle の接続情報を記入(config.yaml は Git 管理外)
docker compose up -d --build
curl http://localhost:8088/api/health # "status":"ok" を確認
```

ブラウザで `http://localhost:8088/` を開き、[Oracle から読み込む] を押します。詳しい手順・前提・既知の制約は [docs/P302-deliver.md](./docs/P302-deliver.md) を参照してください。全体の目次は [INDEX.md](./INDEX.md) です。
