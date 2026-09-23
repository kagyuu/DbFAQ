# P004 要求トレーサビリティマトリクス — DbFAQ(第1リリース)

入力: `docs/P001-requirement.md`、`docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`。
P001 には要求 ID が無いため、本書で一時 ID を付ける。

## 1. マトリクス

| 要求ID | 要求内容(要約) | 対応するP002の箇所 | 対応するP003の箇所 | 状態 | 差し戻し先 | 判断理由 |
|---|---|---|---|---|---|---|
| REQ-SCREEN-001 | SC-01 ER 図(テーブルのノード・列・PK/FK/NOT NULL の印) | §2.1.1、§2.1.2 | §4.3 GET /api/schema | OK | - | - |
| REQ-SCREEN-002 | SC-01 リレーションの線(複合 FK も 1 本、制約名ラベル、自己参照) | §2.1.2 | §3.5 Q-03、§4.3 | OK | - | - |
| REQ-SCREEN-003 | SC-01 拡大・縮小・パン(10〜200%) | §2.1.3 | - | OK | - | フロントエンドのみで完結 |
| REQ-SCREEN-004 | SC-01 全体の略図(ミニマップ) | §2.1.3 | - | OK | - | フロントエンドのみで完結 |
| REQ-SCREEN-005 | SC-01 テーブルのクリックで SC-02 へ遷移 | §2.1.3、§1.2 | - | OK | - | - |
| REQ-SCREEN-006 | SC-01 テーブル名検索 | §2.1.3、§2.1.4 | - | OK | - | - |
| REQ-SCREEN-007 | SC-01 Oracle から再読み込み(失敗時は前回を残す、処理中表示) | §2.1.3、§2.1.5、§5.1 | §4.3 refresh、§4.2 | OK | - | - |
| REQ-SCREEN-008 | SC-01 未取得時・0 件時の表示 | §2.1.5 | §4.3 | OK | - | - |
| REQ-SCREEN-009 | SC-01 ノードのドラッグ(位置は保存しない)、取得日時の表示 | §2.1.3、§1.1 | - | OK | - | - |
| REQ-SCREEN-010 | SC-02 タブ切替(スキーマ情報/データ、URL に保持) | §2.2.1、§1.2 | - | OK | - | - |
| REQ-SCREEN-011 | SC-02 スキーマ情報タブ(列・PK・UK・FK 参照先/参照元・インデックス・統計) | §2.2.2 | §4.3 詳細、§3.5 | OK | - | - |
| REQ-SCREEN-012 | SC-02 FK 先・参照元テーブルへの遷移 | §2.2.2 | §4.3(ref_in_snapshot) | OK | - | - |
| REQ-SCREEN-013 | SC-02 データタブ(50 行ページ、主キー順/ROWID 順、NULL 表示、LOB 切り詰め、取得時間、再読み込み) | §2.2.3、§3.6 | §3.6、§3.7 | OK | - | - |
| REQ-SCREEN-014 | SC-02 異常時の表示(テーブル無し、Oracle エラー時もスキーマ情報タブは使える、0 行) | §2.2.4、§2.2.5 | §4.1 エラー対応表 | OK | - | - |
| REQ-SCREEN-015 | 共通ヘッダ(アプリ名、スキーマ名、取得日時、ER 図リンク) | §1.1 | - | OK | - | - |
| REQ-API-001 | GET /api/schema | §3.2 | §4.3 | OK | - | - |
| REQ-API-002 | POST /api/schema/refresh | §3.3 | §4.3、§3.5 | OK | - | - |
| REQ-API-003 | GET /api/schema/tables/{owner}/{table} | §3.4 | §4.3 | OK | - | - |
| REQ-API-004 | GET /api/schema/tables/{owner}/{table}/rows(limit 最大 500) | §3.5 | §4.3、§3.6 | OK | - | - |
| REQ-API-005 | GET /api/health | §3.7 | §4.3、§3.8 | OK | - | - |
| REQ-MCP-001 | MCP ツール get_schema_snapshot | §5.1 | §3.5 | OK | - | - |
| REQ-MCP-002 | MCP ツール get_table_rows(実在確認+クォート、バインド変数) | §5.2 | §3.6、§3.3 | OK | - | - |
| REQ-MCP-003 | MCP ツール ping | §3.7 | §3.8 | OK | - | - |
| REQ-MCP-004 | 全ツールを読み取り専用トランザクションで実行し必ずロールバック | - | §3.1 | OK | - | - |
| REQ-ARCH-001 | Oracle へのアクセスはすべて MCP 経由(backend は直接接続しない) | §5 | §1.1、§4.1 | OK | - | - |
| REQ-ARCH-002 | MCP は stdio、backend の子プロセス | - | §1.1、§4.1 | OK | - | - |
| REQ-ARCH-003 | スキーマ情報を SQLite に保存し、再起動後も保持 | §4 | §5 | OK | - | - |
| REQ-ARCH-004 | 接続パラメータを設定ファイル(config.yaml、Git 管理外)に保持 | §3.7(config 表示) | §2 | OK | - | - |
| REQ-ARCH-005 | Python は uv で管理 | - | §1.2 | OK | - | - |
| REQ-ARCH-006 | React / FastAPI / FastMCP / python-oracledb | §6 | §1.2、§3.1 | OK | - | - |
| REQ-ARCH-007 | Docker Compose で起動、コンテナから Oracle へは host.docker.internal | - | §1.1、§2.2(環境変数上書き)、§6 | OK | - | インフラ構成は P005・P302 に委譲と明記済み |
| REQ-ARCH-008 | MCP の設計は ../OracleSearchMCP を参考にする | - | §3.1、§3.5 | OK | - | - |
| REQ-NFR-001 | 性能(ER 図 1 秒/300 テーブル 3 秒、再読み込み 10 秒、データ 1 ページ) | - | §6 | OK | - | 測定は P006/P009 |
| REQ-NFR-002 | タイムアウト 30 秒(設定で変更可) | - | §2.1、§3.1 | OK | - | - |
| REQ-NFR-003 | 可用性(単一ホスト、restart、Oracle 無しでも起動、MCP 子プロセスの再起動) | - | §4.1、§6(P005・P302 へ委譲) | OK | - | - |
| REQ-NFR-004 | セキュリティ(認証なし、公開は frontend のみ、読み取りのみ、パスワード非表示、TLS は外部) | §3.1、§3.7 | §3.1〜3.3、§6、§7 | OK | - | - |
| REQ-NFR-005 | スケーラビリティ(10 名、WAL、refresh の排他) | §3.3(409) | §4.2、§5.1 | OK | - | - |
| REQ-NFR-006 | ログ(JSON、backend は stdout、MCP は stderr)と /api/health | - | §4.5、§6 | OK | - | - |
| REQ-TEST-001 | テスト方針(pytest / Vitest / 結合(HR)/ Playwright、HR を変更しない、2 回実行) | - | §5.2(再起動耐性を P009 で) | OK | - | 詳細は P006 |

## 2. 過剰実装の確認(P001 に無い項目)

| 項目 | 箇所 | 判断 |
|---|---|---|
| ヘッダの Oracle 状態表示(60 秒ごとの health 取得) | P002 §1.1 | 対応する要求なし(P001 は `/api/health` の API のみ定義し、画面での使い道を定めていない)。実装側に残すことを推奨(運用者が接続状態を一目で確認できる)。要求書側への追加は人間の判断事項として P302 に引き継ぐ |
| データタブのページ番号を URL に保持 | P002 §1.2 | P001 のタブ状態の URL 保持の延長。対応する要求なし。実装側に残すことを推奨 |
| 関数索引の式の表示(Q-05) | P003 §3.5 | インデックス表示の詳細化。対応する要求なし。実装側に残すことを推奨 |

いずれも非ブロッキング(記録して P010・P302 に引き継ぐ)。

## 3. 結論

すべての要求 ID が `OK`。`PARTIAL`・`MISSING`・`DEVIATED` は無い。P005 に進む。
