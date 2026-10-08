# P007 プログラム実装定義(目次)

入力: `docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`、`docs/P006-test-plan.md`。
コードの格納先: `server/`(Python。backend。※CR-002により MCP サーバを削除)、`client/`(フロントエンド)、`deploy/`・`compose.yaml`・`e2e/`(配布・受入テスト)。
技術スタックは `docs/ADR.md` を参照(フロントエンド: ADR-009・ADR-010、Python の構成: ADR-007、Oracle アクセス: ADR-014・ADR-011(※CR-002により ADR-001 から変更)、配布: ADR-012)。

- [x] U001 [foundation](./P007-impl-direction/U001-foundation.md) — Python プロジェクトの初期化、設定ファイル読み込み、JSON ログ、開発用 Oracle の疎通確認
- [x] U002 [mcp-server](./P007-impl-direction/U002-mcp-server.md) — MCP サーバ(ツール 3 本、識別子、型表記、値の文字列化、読み取り専用トランザクション)※CR-002 で廃止し U007 で backend に移設(第 1 リリース時点の記録として残す)
- [x] U003 [backend-api](./P007-impl-direction/U003-backend-api.md) — SQLite マイグレーションとスナップショット、MCP ゲートウェイ、API 5 本 ※MCP ゲートウェイは CR-002 で廃止(U007)
- [x] U004 [frontend-er](./P007-impl-direction/U004-frontend-er.md) — クライアントの土台、共通ヘッダ、SC-01 ER 図
- [x] U005 [frontend-detail](./P007-impl-direction/U005-frontend-detail.md) — SC-02 テーブル詳細(スキーマ情報タブ・データタブ)
- [x] U006 [deploy](./P007-impl-direction/U006-deploy.md) — コンテナイメージ、nginx、compose、受入テストの実行環境
- [x] U007 [oracle-in-backend](./P007-impl-direction/U007-oracle-in-backend.md) — MCP を廃止し Oracle アクセスを `dbfaq_api/oracle` に移す、health から mcp を除く ※CR-002により追加
- [x] U008 [merge-common](./P007-impl-direction/U008-merge-common.md) — `dbfaq_common` を `dbfaq_api` に統合(`config.py`・`log.py`)※CR-003により追加
- [x] U009 [query-tab](./P007-impl-direction/U009-query-tab.md) — SC-02 の Query タブ(SQL の検査、SELECT の実行・エラー位置・CSV、API 2 本、ひな形、nginx、受入テスト A09)※CR-004により追加
- [x] U010 [saved-queries-pdb](./P007-impl-direction/U010-saved-queries-pdb.md) — 保存済み Query(テーブルごと・PDB)、SC-01 のドラム缶のアイコン、SC-03 PDB 画面、PDB のひな型、API 5 本、受入テスト A10 ※CR-005により追加
- [ ] U011 [readonly-user](./P007-impl-direction/U011-readonly-user.md) — 読み取り専用ユーザー dbfaq_ro を前提に PDB 情報・ひな型を対象スキーマ基準に、未変更のひな型の更新、README ※CR-006により追加

## 未解決事項

* なし(P010 のレビューで見つかったものはここに追記する)
