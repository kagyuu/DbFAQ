# P007 プログラム実装定義(目次)

入力: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`。
コードの格納先: `server/`(Python。MCP サーバと backend)、`client/`(フロントエンド)、`deploy/`・`compose.yaml`・`e2e/`(配布・受入テスト)。
技術スタックは `docs/ADR.md` を参照(フロントエンド: ADR-009・ADR-010、Python の構成: ADR-007、Oracle アクセス: ADR-001・ADR-011、配布: ADR-012)。

- [x] U001 [foundation](./P007-impl-direction/U001-foundation.md) — Python プロジェクトの初期化、設定ファイル読み込み、JSON ログ、開発用 Oracle の疎通確認
- [x] U002 [mcp-server](./P007-impl-direction/U002-mcp-server.md) — MCP サーバ(ツール 3 本、識別子、型表記、値の文字列化、読み取り専用トランザクション)
- [x] U003 [backend-api](./P007-impl-direction/U003-backend-api.md) — SQLite マイグレーションとスナップショット、MCP ゲートウェイ、API 5 本
- [x] U004 [frontend-er](./P007-impl-direction/U004-frontend-er.md) — クライアントの土台、共通ヘッダ、SC-01 ER 図
- [x] U005 [frontend-detail](./P007-impl-direction/U005-frontend-detail.md) — SC-02 テーブル詳細(スキーマ情報タブ・データタブ)
- [x] U006 [deploy](./P007-impl-direction/U006-deploy.md) — コンテナイメージ、nginx、compose、受入テストの実行環境

## 未解決事項

* なし(P010 のレビューで見つかったものはここに追記する)
