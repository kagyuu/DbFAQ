# ADR.md

本プロジェクトで現在有効な設計判断を管理する。
過去に廃止された設計判断は `ADR_master.md` に移動する(現時点で廃止された ADR は無い)。

## ADR 一覧

| ADR | タイトル | 状態 |
| --- | --- | --- |
| ADR-001 | MCP サーバを backend の子プロセス(stdio)として常駐させる | 採用 |
| ADR-002 | SQLite のマイグレーションは管理テーブル付きの差分適用とする | 採用 |
| ADR-003 | スナップショットはスキーマごとに最新 1 件を 1 トランザクションで置き換える | 採用 |
| ADR-004 | ブラウザからは同一オリジンで API を呼び、CORS を使わない | 採用 |
| ADR-005 | テーブルデータのセル値は MCP サーバで表示用文字列にして返す | 採用 |
| ADR-006 | データタブは主キー順(無ければ ROWID 順)の OFFSET 方式で取得し、件数を数えない | 採用 |
| ADR-007 | Python は 1 つの uv プロジェクトに 3 パッケージを置く | 採用 |
| ADR-008 | SQLite へのアクセスには SQLAlchemy Core を使う | 採用 |
| ADR-009 | フロントエンドは React 19 + TypeScript + Vite + Mantine + TanStack Query + React Router | 採用 |
| ADR-010 | ER 図は React Flow(@xyflow/react)と elkjs で描く | 採用 |
| ADR-011 | Oracle へは python-oracledb(Thin)で読み取り専用トランザクション内でのみアクセスする | 採用 |
| ADR-012 | Docker Compose で web(nginx)と api の 2 サービス構成にし、api は公開しない | 採用 |
| ADR-013 | 設定は YAML ファイル + 一部の環境変数上書きとし、パスワードは SecretStr で扱う | 採用 |

状態は `採用` / `検討中` / `廃止` のいずれか。

## ADR-001

### タイトル

MCP サーバを backend の子プロセス(stdio)として常駐させる

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-001
* REQ-ARCH-002

### 背景

Oracle へのアクセスはすべて MCP(FastMCP)経由にするよう人間から指示があり、トランスポートは当面 stdio でよいとされた。

### 決定内容

backend(FastAPI)が起動時に `python -m dbfaq_mcp` を子プロセスとして 1 つ起動し、fastmcp の Client で stdio セッションを維持する。通信不能を検出したらセッションを捨て、次の呼び出しで起動し直す。backend は Oracle に直接接続しない。

### 理由

* リクエストごとの子プロセス起動は Python の起動と Oracle 接続で 1〜2 秒かかる
* 1 セッション上で JSON-RPC の要求 ID により並行呼び出しができる
* MCP サーバを単体でも stdio 対応クライアントから使える

### 検討した代替案

#### リクエストごとに子プロセスを起動

却下。理由: 応答が遅く、接続プールが効かない。

#### MCP の HTTP トランスポート

却下。理由: 人間の指示で第 1 リリースは stdio。将来 CR で追加。

### 残存リスク

uvicorn を複数ワーカーにすると子プロセスもワーカー数だけ増え、refresh の排他も効かない。1 ワーカー前提(ADR-012)。

### 影響範囲

* Backend
* MCP サーバ

### 関連成果物

* `docs/P003-backend-spec.md` §1.1、§4.1

### 備考

なし

## ADR-002

### タイトル

SQLite のマイグレーションは管理テーブル付きの差分適用とする

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-003

### 背景

スキーマ情報を SQLite に保存し、再起動後も保持する。将来 FAQ 機能を CR で追加する際に列追加が発生する。

### 決定内容

`dbfaq_api/migrations/NNNN_*.sql` を起動時にファイル名順に読み、`schema_migrations` に無いものだけを 1 ファイル 1 トランザクションで適用・記録する。

### 理由

* 冪等であり、`ALTER TABLE ADD COLUMN` のような条件付き構文の無い DDL を後から追加しても 2 回目の起動で失敗しない

### 検討した代替案

#### 全件再実行(`CREATE TABLE IF NOT EXISTS`)

却下。理由: 列追加の時点で破綻する。

#### Alembic

却下。理由: 依存と設定が増える。SQL ファイルで十分。

### 残存リスク

なし

### 影響範囲

* Backend
* Database

### 関連成果物

* `docs/P003-backend-spec.md` §5.2

### 備考

なし

## ADR-003

### タイトル

スナップショットはスキーマごとに最新 1 件を 1 トランザクションで置き換える

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-SCREEN-007
* REQ-API-002

### 背景

再読み込みに失敗したときは前回の情報を残す必要がある。

### 決定内容

refresh は MCP から全体を受け取ってから、1 トランザクションで同じ owner の旧スナップショットを削除(CASCADE)し新しいものを挿入する。履歴は持たない。

### 理由

* 失敗時は ROLLBACK で前回がそのまま残る
* 読み出し側は常に 1 件だけを見ればよい

### 検討した代替案

#### 差分更新

却下。理由: 辞書の変更検出が複雑。スキーマ全体でも数千行で置き換えが安い。

#### 履歴を持つ

却下。理由: 第 1 リリースの要求に無い。

### 残存リスク

なし

### 影響範囲

* Backend
* Database

### 関連成果物

* `docs/P003-backend-spec.md` §4.3

### 備考

なし

## ADR-004

### タイトル

ブラウザからは同一オリジンで API を呼び、CORS を使わない

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-NFR-004

### 背景

フロントエンドと backend は別プロセス。開発時は別ポートで動く。

### 決定内容

開発時は Vite 開発サーバの proxy で `/api` を backend(8000)へ中継、本番は nginx が静的配信と `/api` 中継を同じオリジンで行う。backend は CORS ヘッダを返さない。受入テストは compose の web のオリジンに対して行う。

### 理由

* 不要な許可を持たない
* 開発・本番で同じ相対パス `/api` を使える

### 検討した代替案

#### CORS を許可

却下。理由: 認証が無いので必須ではなく、許可範囲の管理が増える。

### 残存リスク

なし

### 影響範囲

* Frontend
* Backend
* Infra

### 関連成果物

* `docs/P003-backend-spec.md` §7

### 備考

なし

## ADR-005

### タイトル

テーブルデータのセル値は MCP サーバで表示用文字列にして返す

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-SCREEN-013
* REQ-MCP-002

### 背景

NUMBER の精度、日付の形式、LOB・RAW を JSON で安全に運ぶ必要がある。

### 決定内容

python-oracledb を `fetch_decimals=True`、`fetch_lobs=False` で使い、MCP サーバが P003 §3.7 の規則で文字列化(1,000 文字・32 バイトで切り詰め、truncated を記録)して返す。

### 理由

* JSON の数値で精度を落とさない
* 表示の規則を 1 か所にまとめられる

### 検討した代替案

#### DBMS_LOB.SUBSTR で SQL 側で切り詰める

却下。理由: `SELECT *` の列ごとに型を見て SQL を組み直す必要があり複雑。

### 残存リスク

★ACCEPTED★ LOB 全体をメモリに読み込む。1 ページ最大 500 行 × LOB の大きさがメモリ量の上限。巨大 LOB のテーブルでは limit を小さくして使う。

### 影響範囲

* MCP サーバ

### 関連成果物

* `docs/P003-backend-spec.md` §3.1、§3.7

### 備考

なし

## ADR-006

### タイトル

データタブは主キー順(無ければ ROWID 順)の OFFSET 方式で取得し、件数を数えない

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-SCREEN-013
* REQ-API-004

### 背景

運用中のテーブルを安全に 50 行ずつ閲覧したい。大きなテーブルでの COUNT(*) は重い。

### 決定内容

`ORDER BY 主キー列 OFFSET :off ROWS FETCH NEXT :limit+1 ROWS ONLY`。limit+1 行目の有無で has_next を決める。offset 上限 100,000、limit 上限 500。

### 理由

* URL のページ番号で直接移動できる
* 主キーの無い表・複合主キーでも同じ形

### 検討した代替案

#### キーセット方式

却下。理由: 主キーの無い表・複合主キーで条件式が複雑になり、ページ番号での直接移動ができない。

#### COUNT(*) で総件数表示

却下。理由: 大きなテーブルで遅い。

### 残存リスク

★ACCEPTED★ ページを進めるほど Oracle 側で読み飛ばしが増えて遅くなる(offset 上限で抑える)。ページ間に他セッションが行を増減すると重複・欠落して見えることがある(参照用途として許容)。

### 影響範囲

* MCP サーバ
* Frontend

### 関連成果物

* `docs/P003-backend-spec.md` §3.6

### 備考

なし

## ADR-007

### タイトル

Python は 1 つの uv プロジェクトに 3 パッケージを置く

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-005

### 背景

backend と MCP サーバは同じコンテナ・同じ依存で動き、設定読み込みとログを共有する。パッケージ管理は uv(人間の指示)。

### 決定内容

`server/` を 1 つの uv プロジェクト(hatchling、src レイアウト)とし、`dbfaq_common`・`dbfaq_mcp`・`dbfaq_api` を置く。Python 3.12。

### 理由

* 依存・ロックファイル・仮想環境が 1 つで済む
* 1 つのイメージにまとめやすい

### 検討した代替案

#### uv ワークスペース(複数プロジェクト)

却下。理由: 分離の利点が小さく、構成が増える。

### 残存リスク

なし

### 影響範囲

* Backend
* MCP サーバ
* Build

### 関連成果物

* `docs/P003-backend-spec.md` §1.2

### 備考

なし

## ADR-008

### タイトル

SQLite へのアクセスには SQLAlchemy Core を使う

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-003

### 背景

スナップショットの一括削除・一括挿入と、組み立て用の少数の SELECT が中心。

### 決定内容

SQLAlchemy 2.x の Core(`text()`/`Table`)を使い、ORM は使わない。接続ごとに `foreign_keys=ON`、WAL、`busy_timeout=5000`。

### 理由

* ORM の変更追跡が不要
* SQL が明示的で N+1 を避けやすい

### 検討した代替案

#### ORM

却下。理由: 変更追跡が不要でオーバーヘッドだけ増える。

#### 標準 sqlite3 モジュール直書き

却下。理由: 接続設定・トランザクション管理を自前で持つことになる。

### 残存リスク

なし

### 影響範囲

* Backend
* Database

### 関連成果物

* `docs/P003-backend-spec.md` §1.2、§5.1

### 備考

なし

## ADR-009

### タイトル

フロントエンドは React 19 + TypeScript + Vite + Mantine + TanStack Query + React Router

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-006

### 背景

人間の指示は React。その他はおまかせ。

### 決定内容

React 19 + TypeScript、ビルドは Vite(npm)、UI 部品は Mantine、API の取得は TanStack Query、ルーティングは React Router。テストは Vitest + Testing Library。

### 理由

* タブ・表・通知など必要な部品が揃う
* API のキャッシュ・再取得・読み込み状態を宣言的に扱える

### 検討した代替案

#### 状態管理ライブラリ(Redux 等)

却下。理由: サーバ状態は TanStack Query で足り、クライアント状態は小さい。

### 残存リスク

なし

### 影響範囲

* Frontend

### 関連成果物

* `docs/P002-frontend-spec.md` §6、docs/P001-requirement.md §3.2

### 備考

なし

## ADR-010

### タイトル

ER 図は React Flow(@xyflow/react)と elkjs で描く

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-SCREEN-001〜005

### 背景

拡大縮小・全体の略図・クリックでの遷移が要求されている。

### 決定内容

描画・拡大縮小・パン・ミニマップは React Flow の `ReactFlow`・`Controls`・`MiniMap`、配置は elkjs の layered(左→右)でブラウザ側で計算する。自己参照は独自エッジで描く。ノード位置は保存しない。

### 理由

* 要求がそのまま標準部品で満たせる
* サーバ側にレイアウト計算を持たなくてよい

### 検討した代替案

#### Mermaid の erDiagram

却下。理由: 拡大縮小・クリック・ミニマップを自前で作る必要がある。

#### dagre

却下。理由: elkjs の方が大規模で線の重なりが少ない。

### 残存リスク

なし

### 影響範囲

* Frontend

### 関連成果物

* `docs/P002-frontend-spec.md` §2.1

### 備考

なし

## ADR-011

### タイトル

Oracle へは python-oracledb(Thin)で読み取り専用トランザクション内でのみアクセスする

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-MCP-004
* REQ-NFR-004

### 背景

運用中の本番 DB を読むため、更新が起きてはならない。`../OracleSearchMCP` の方式を踏襲する。

### 決定内容

Thin モードの非同期プール。各ツールは接続ごとに `call_timeout` を設定し、`SET TRANSACTION READ ONLY` の後に実行して必ず ROLLBACK する。任意 SQL を受け付けるツールは作らず、識別子は検証・実在確認・クォートしてから埋め込む。

### 理由

* Instant Client 不要でイメージが小さい
* DML は ORA-01456 で拒否される(実機確認済み)

### 検討した代替案

#### Thick モード

却下。理由: Instant Client が必要。

#### 任意 SQL ツール

却下。理由: 第 1 リリースの要求に無い(将来 CR)。

### 残存リスク

接続ユーザーに書き込み権限があっても読み取り専用トランザクションで防ぐが、実運用では読み取り専用ユーザーの利用を推奨する(手順書に記載)。

### 影響範囲

* MCP サーバ

### 関連成果物

* `docs/P003-backend-spec.md` §3.1〜§3.3

### 備考

なし

## ADR-012

### タイトル

Docker Compose で web(nginx)と api の 2 サービス構成にし、api は公開しない

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-007
* REQ-NFR-003
* REQ-NFR-004

### 背景

実運用環境で Docker Compose で動かす(人間の指示)。認証が無いので公開範囲を絞る。Oracle は既存のもの。

### 決定内容

web(nginx、ホストの 8088→80)と api(uvicorn 1 ワーカー + MCP 子プロセス、ポート非公開)。api は `config.yaml` を読み取り専用でマウントし、SQLite は名前付きボリューム `/data`。Oracle は compose に含めず、コンテナからは `host.docker.internal`(host-gateway)で接続する。両サービス `restart: unless-stopped`。

### 理由

* 公開面が web だけ
* パスワードがイメージに入らない

### 検討した代替案

#### 1 コンテナにまとめる

却下。理由: nginx と Python のプロセス管理が必要になる。

### 残存リスク

なし

### 影響範囲

* Infra

### 関連成果物

* `docs/P005-impl-plan.md` U006、docs/P003-backend-spec.md §6

### 備考

なし

## ADR-013

### タイトル

設定は YAML ファイル + 一部の環境変数上書きとし、パスワードは SecretStr で扱う

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-004

### 背景

Oracle の接続パラメータを設定ファイルに保持する(人間の指示)。コンテナでは接続先だけ差し替えたい。

### 決定内容

`config.yaml`(Git 管理外。ひな型は `config.example.yaml`)を pydantic で検証して読む。`DBFAQ_CONFIG`、`DBFAQ_ORACLE_HOST`・`_PORT`・`_PASSWORD`、`DBFAQ_SQLITE_PATH` で上書きできる。パスワードは `SecretStr` で、ログ・API・例外メッセージに出さない。

### 理由

* compose で接続先だけ差し替えられる
* 設定ミスを起動時に検出できる

### 検討した代替案

#### .env のみ

却下。理由: 入れ子の設定が書きにくい。

### 残存リスク

なし

### 影響範囲

* Backend
* MCP サーバ
* Infra

### 関連成果物

* `docs/P003-backend-spec.md` §2

### 備考

なし
