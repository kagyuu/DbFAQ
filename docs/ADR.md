# ADR.md

本プロジェクトで現在有効な設計判断を管理する。
過去に廃止された設計判断は `ADR_master.md` に移動する(CR-002 で ADR-001 を廃止して移動した)。

## ADR 一覧

| ADR | タイトル | 状態 |
| --- | --- | --- |
| ADR-002 | SQLite のマイグレーションは管理テーブル付きの差分適用とする | 採用 |
| ADR-003 | スナップショットはスキーマごとに最新 1 件を 1 トランザクションで置き換える | 採用 |
| ADR-004 | ブラウザからは同一オリジンで API を呼び、CORS を使わない | 採用 |
| ADR-005 | テーブルデータのセル値は backend で表示用文字列にして返す | 採用 |
| ADR-006 | データタブは主キー順(無ければ ROWID 順)の OFFSET 方式で取得し、件数を数えない | 採用 |
| ADR-007 | Python は 1 つの uv プロジェクトに 1 パッケージを置く | 採用 |
| ADR-008 | SQLite へのアクセスには SQLAlchemy Core を使う | 採用 |
| ADR-009 | フロントエンドは React 19 + TypeScript + Vite + Mantine + TanStack Query + React Router | 採用 |
| ADR-010 | ER 図は React Flow(@xyflow/react)と elkjs で描く | 採用 |
| ADR-011 | Oracle へは python-oracledb(Thin)で読み取り専用トランザクション内でのみアクセスする | 採用 |
| ADR-012 | Docker Compose で web(nginx)と api の 2 サービス構成にし、api は公開しない | 採用 |
| ADR-013 | 設定は YAML ファイル + 一部の環境変数上書きとし、パスワードは SecretStr で扱う | 採用 |
| ADR-014 | backend のプロセス内で python-oracledb の非同期プールにより Oracle に直接接続する(MCP を使わない) | 採用 |

状態は `採用` / `検討中` / `廃止` のいずれか。

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

refresh は Oracle から全体を読み取ってから(※CR-002により「MCP から全体を受け取ってから」を変更)、1 トランザクションで同じ owner の旧スナップショットを削除(CASCADE)し新しいものを挿入する。履歴は持たない。

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

テーブルデータのセル値は backend で表示用文字列にして返す

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-SCREEN-013
* REQ-ORA-002

### 背景

NUMBER の精度、日付の形式、LOB・RAW を JSON で安全に運ぶ必要がある。

### 決定内容

python-oracledb を `fetch_decimals=True`、`fetch_lobs=False` で使い、backend(`dbfaq_api/oracle/values.py`)が P003 §3.7 の規則で文字列化(1,000 文字・32 バイトで切り詰め、truncated を記録)して返す。

### 理由

* JSON の数値で精度を落とさない
* 表示の規則を 1 か所にまとめられる

### 検討した代替案

#### DBMS_LOB.SUBSTR で SQL 側で切り詰める

却下。理由: `SELECT *` の列ごとに型を見て SQL を組み直す必要があり複雑。

### 残存リスク

★ACCEPTED★ LOB 全体をメモリに読み込む。1 ページ最大 500 行 × LOB の大きさがメモリ量の上限。巨大 LOB のテーブルでは limit を小さくして使う。

### 影響範囲

* Backend

### 関連成果物

* `docs/P003-backend-spec.md` §3.1、§3.7

### 備考

* 2026-09-27 CR-002 により、文字列化する場所を MCP サーバから backend に変更(規則は変えていない)。

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

* Backend(CR-002 で MCP サーバから変更)
* Frontend

### 関連成果物

* `docs/P003-backend-spec.md` §3.6

### 備考

なし

## ADR-007

### タイトル

Python は 1 つの uv プロジェクトに 1 パッケージを置く

### 状態

採用

### 日付

2026-09-23

### 関連要求

* REQ-ARCH-005

### 背景

backend(API、Oracle アクセス、設定読み込み、ログ)を 1 つのコンテナ・同じ依存で動かす。パッケージ管理は uv(人間の指示)。

### 決定内容

`server/` を 1 つの uv プロジェクト(hatchling、src レイアウト)とし、パッケージは `dbfaq_api` の 1 つだけにする(設定は `dbfaq_api/config.py`、ログは `dbfaq_api/log.py`)。Python 3.12。

### 理由

* 依存・ロックファイル・仮想環境が 1 つで済む
* 1 つのイメージにまとめやすい

### 検討した代替案

#### uv ワークスペース(複数プロジェクト)

却下。理由: 分離の利点が小さく、構成が増える。

### 残存リスク

なし(CR-003 で `dbfaq_common` を統合し、CR-002 で残した「`dbfaq_common` の利用者が 1 つだけ」という残存リスクは解消した)

### 影響範囲

* Backend
* Build

### 関連成果物

* `docs/P003-backend-spec.md` §1.2

### 備考

* 2026-09-27 CR-002 により `dbfaq_mcp` を削除し、3 パッケージから 2 パッケージに変更。
* 2026-09-27 人間承認: 依頼者が、MCP の廃止に伴う本 ADR の変更(1 つの uv プロジェクトに `dbfaq_common`・`dbfaq_api` の 2 パッケージ)を承認し、確定の仕様とした。
* 2026-09-27 CR-003 により `dbfaq_common` を `dbfaq_api` に統合し、2 パッケージから 1 パッケージに変更(依頼者の指示)。中心の決定「`server/` を 1 つの uv プロジェクトにする」は変わらないため、廃止せずに本 ADR を更新した。

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

* REQ-ORA-004
* REQ-NFR-004

### 背景

運用中の本番 DB を読むため、更新が起きてはならない。`../OracleSearchMCP` の方式を踏襲する。

### 決定内容

Thin モードの非同期プール。各処理は接続ごとに `call_timeout` を設定し、`SET TRANSACTION READ ONLY` の後に実行して必ず ROLLBACK する。任意 SQL を受け付ける機能は作らず、識別子は検証・実在確認・クォートしてから埋め込む。

### 理由

* Instant Client 不要でイメージが小さい
* DML は ORA-01456 で拒否される(実機確認済み)

### 検討した代替案

#### Thick モード

却下。理由: Instant Client が必要。

#### 任意 SQL の実行

却下。理由: 第 1 リリースの要求に無い(将来 CR)。

### 残存リスク

接続ユーザーに書き込み権限があっても読み取り専用トランザクションで防ぐが、実運用では読み取り専用ユーザーの利用を推奨する(手順書に記載)。

### 影響範囲

* Backend

### 関連成果物

* `docs/P003-backend-spec.md` §3.1〜§3.3

### 備考

* 2026-09-27 CR-002 により、実行する場所を MCP サーバから backend に変更(「ツール」を「処理」「機能」に言い換え。方式は変えていない)。

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

web(nginx、ホストの 8088→80)と api(uvicorn 1 ワーカー、ポート非公開)。api は `config.yaml` を読み取り専用でマウントし、SQLite は名前付きボリューム `/data`。Oracle は compose に含めず、コンテナからは `host.docker.internal`(host-gateway)で接続する。両サービス `restart: unless-stopped`。

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

* 2026-09-27 CR-002 により、api の構成から「MCP 子プロセス」を削除。

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
* Infra

### 関連成果物

* `docs/P003-backend-spec.md` §2

### 備考

* 2026-09-27 CR-002 により、影響範囲から MCP サーバを削除。設定項目 `app.mcp_call_timeout_sec` を廃止(残っていても無視する)。

## ADR-014

### タイトル

backend のプロセス内で python-oracledb の非同期プールにより Oracle に直接接続する(MCP を使わない)

### 状態

採用

### 日付

2026-09-27

### 関連要求

* REQ-ARCH-001
* REQ-ORA-001
* REQ-ORA-002
* REQ-ORA-003
* REQ-NFR-003

### 背景

第 1 リリースでは人間の指示により Oracle へのアクセスをすべて MCP サーバ(FastMCP、stdio、backend の子プロセス)経由にしていた(旧 ADR-001)。CR-002 で依頼者が MCP は不要と判断し、backend への統合を指示した。

### 決定内容

backend(`dbfaq_api`)が `dbfaq_api/oracle` パッケージの `OracleClient` を 1 つ持ち、その中の python-oracledb の非同期接続プール(最初のアクセスで作る。lifespan の終了時に閉じる)で Oracle に直接問い合わせる。SQL・読み取り専用トランザクション・値の文字列化は旧 MCP サーバの実装をそのまま移す(ADR-005・ADR-006・ADR-011)。Oracle のエラーは例外 `OracleFailure` で API 層に渡し、API のエラーに変換する。python-oracledb が `oracledb.Error` に包まずに送出する接続の失敗(`OSError`)も `OracleFailure` に変換する(P202 F007)。プールの close は `connect_timeout_sec` で打ち切る(P202 F008)。uvicorn は 1 ワーカーで動かす。

### 理由

* 子プロセスの管理(起動・再起動・stdio の標準出力の扱い)、MCP のエラーの JSON 化と解析、MCP 用の設定・テストが不要になる
* 1 回の呼び出しごとのプロセス間通信が無くなる
* 接続プールの切れた接続は python-oracledb が借りるときに捨てて作り直すため、Oracle が戻れば backend を再起動せずに回復する(T09 で確認)

### 検討した代替案

#### MCP サーバを残し、backend だけ直接接続にする(MCP を単体の外部向けとして残す)

却下。理由: 依頼者の指示は「MCP の部分は廃止」であり、単体利用を残す指示は無い。残すと同じ処理を 2 通りの入口で保守することになる。

#### Oracle アクセスを同期ドライバ(スレッドプール)で行う

却下。理由: 旧 MCP サーバの非同期実装をそのまま移せる。FastAPI の async と合う。

### 残存リスク

* uvicorn を複数ワーカーにすると refresh の排他(`asyncio.Lock`)が効かず、接続プールもワーカー数だけ増える。1 ワーカー前提(旧 ADR-001 から引き継ぎ。同時 10 名は A08 で確認)。
* ★ACCEPTED★(2026-09-27 人間承認) health の疎通確認は、Oracle のホストに届かない(応答が無い)とき接続の確立の待ち時間(`connect_timeout_sec`)まで返らない(P003 §3.8)。検討・不採用理由・残存リスクは P003 §3.8 に記載。
* ★ACCEPTED★(2026-09-27 人間承認) Oracle のリスナーに届かない間は python-oracledb のプールの close が約 2 分戻らないため、終了時は打ち切ってプールを捨てる。閉じ切らない接続はプロセスの終了で OS が片付ける(P003 §3.1)。
* 子プロセスという境界が無くなったため、ドライバが送出する例外の種類とプールの終了処理の挙動がそのまま API と lifespan に現れる(CR-002 の P201 で F007・F008 として顕在化し、対処済み)。python-oracledb の版を上げるときは、T08・T09・A03 で同じ挙動を確かめる。

### 影響範囲

* Backend
* Infra
* Test

### 関連成果物

* `docs/P003-backend-spec.md` §1.1、§3、§4.1、§4.2
* `docs/P007-impl-direction/U007-oracle-in-backend.md`

### 備考

* 旧 ADR-001 を置き換える(`docs/ADR_master.md`)。
* 2026-09-27 P905 で、P202 F007・F008 の決定を決定内容と残存リスクに追記した。
* 2026-09-27 人間承認: 依頼者が本 ADR の採用を承認し、確定の仕様とした(残存リスクの ★ACCEPTED★ 2 件を含む)。
