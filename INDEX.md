# DbFAQ INDEX

Oracle のスキーマを MCP 経由で読み取って SQLite に保存し、ブラウザで ER 図とテーブル詳細を見る運用者向けツール(第 1 リリース)。

## ソースツリー

- [server/INDEX.md](./server/INDEX.md) — Python(uv)。MCP サーバ `dbfaq_mcp`、backend `dbfaq_api`、共通部品 `dbfaq_common`、単体・結合テスト
- [client/INDEX.md](./client/INDEX.md) — フロントエンド(React + Vite)。SC-01 ER 図、SC-02 テーブル詳細、単体テスト
- [deploy/](./deploy/) — `api.Dockerfile`、`web.Dockerfile`、`nginx.conf`
- [e2e/](./e2e/) — 受入テスト(Playwright の `tests/`、手順スクリプトの `scripts/`)
- [compose.yaml](./compose.yaml) — web(nginx、8088)と api(非公開)
- [config.example.yaml](./config.example.yaml) — 設定ファイルのひな型(実物の `config.yaml` は Git 管理外)
- [README.md](./README.md) — 概要と最短の起動手順
- [.dockerignore](./.dockerignore) — イメージに入れないもの(config.yaml など)

## ドキュメント

- [docs/P001-requirement.md](./docs/P001-requirement.md) — システム要件定義(第 1 リリースの範囲と将来スコープ)
- [docs/P002-frontend-spec.md](./docs/P002-frontend-spec.md) — ユーザインタフェース設計(画面、API の外部仕様、SQLite のデータモデル)
- [docs/P003-backend-spec.md](./docs/P003-backend-spec.md) — システム詳細設計(MCP サーバ、backend の内部処理、マイグレーション、設定)
- [docs/P004-traceability-matrix.md](./docs/P004-traceability-matrix.md) — 要求トレーサビリティマトリクス
- [docs/P005-impl-plan.md](./docs/P005-impl-plan.md) — 実装計画(スプリント U001〜U006)
- [docs/P006-test-plan.md](./docs/P006-test-plan.md) — テスト計画
- [docs/P007-impl-direction.md](./docs/P007-impl-direction.md) — プログラム実装定義(目次)
- [docs/P008-test-direction.md](./docs/P008-test-direction.md) — 結合テスト定義 T01〜T12(目次)
- [docs/P009-acceptance-direction.md](./docs/P009-acceptance-direction.md) — 受け入れ結合テスト定義 A01〜A07(目次)
- [docs/P010-design-review.md](./docs/P010-design-review.md) — 設計書横断レビュー(3 回目で矛盾 0 件)
- [docs/P011-impact-analysis.md](./docs/P011-impact-analysis.md) — 設計の矛盾点の影響分析
- [docs/ADR.md](./docs/ADR.md) — 設計判断(ADR-001〜013)
- [docs/ArchitectureHandbook.md](./docs/ArchitectureHandbook.md) — 技術的な要点のハンドブック
- [docs/P101-impl-context.md](./docs/P101-impl-context.md) — 実装コンテキスト(確定したコマンド一覧を含む)
- [docs/P201-review-report.md](./docs/P201-review-report.md) — 実装横断レビュー(2 回目で全件 PASS)
- [docs/P202-fix-plan.md](./docs/P202-fix-plan.md) — 修正計画 F001〜F006(すべて解決)
- [docs/P204-impact-analysis.md](./docs/P204-impact-analysis.md) — 修正の影響分析
- [docs/test-records/](./docs/test-records/) — テスト実行記録
- [docs/P302-deliver.md](./docs/P302-deliver.md) — 納品物まとめ・起動手順・リリース判定
- [docs/BUILD_HISTORY.md](./docs/BUILD_HISTORY.md) — ビルド履歴
