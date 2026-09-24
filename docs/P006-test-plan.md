# P006 テスト計画書 — DbFAQ(第1リリース)

入力: `docs/P001-requirement.md`、`docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`。
個々のテストケースの実装指示は P007(単体)・P008(スプリント内結合)・P009(スプリント横断・システム・受入)で作る。

## 1. テストレベルと目的

| テストレベル | 目的 | 定義する文書 | ツール |
|---|---|---|---|
| 単体テスト | P002・P003 で定義した画面・API・MCP ツール・内部モジュールが単体で仕様どおりに動くか | P007(各スプリントの実装指示の中) | pytest(+pytest-asyncio)、Vitest + Testing Library |
| 結合テスト | 画面・API・MCP・Oracle・SQLite が連携して仕様どおりか(スプリント内/モジュール間) | P008 | pytest(実 Oracle HR、実 MCP 子プロセス)、Vitest |
| システムテスト | P001 の要件・非機能要件(性能、再起動耐性、Oracle 停止時の振る舞い、秘密情報)を満たしているか | P009 | pytest、Playwright、docker compose |
| 受け入れテスト | 運用担当者の視点で、compose で起動した本番相当環境で一連の操作ができるか | P009 | Playwright(compose の web に対して) |

## 2. 観点とテストレベルの割り当て

### 2.1 機能観点

| 対象 | 正常系 | 主要な異常系 | レベル |
|---|---|---|---|
| config 読み込み | 必須項目、既定値、環境変数上書き | 必須欠落・範囲外 → 起動時例外、パスワードが repr に出ない | 単体 |
| 識別子の検証 | 通常名、小文字・空白入りの引用識別子 | 空、129 文字、`"`・NUL を含む | 単体 |
| 型表記 | P003 §3.4 の全分岐 | - | 単体 |
| 値の文字列化 | P003 §3.7 の全分岐(Decimal、DATE、TIMESTAMP、TZ 付き、bytes、長文) | - | 単体 |
| スナップショット組み立て | 複合 PK/FK、自己参照 FK、別スキーマ参照、関数索引、主キー無し表、ビューの列を捨てる | 空スキーマ | 単体(辞書の結果を偽データで与える) |
| MCP get_schema_snapshot | HR: 7 表、列 35、PK 7、UK 1、FK 10、インデックス 19 | 存在しないスキーマ → NOT_FOUND | 結合(実 Oracle) |
| MCP get_table_rows | HR.EMPLOYEES の 1〜50 行目・51〜100 行目・101〜107 行目、複合 PK(JOB_HISTORY)の並び | 存在しない表 → NOT_FOUND、offset/limit 範囲外 → INVALID_ARGUMENT、`"` を含む名前 | 結合(実 Oracle) |
| MCP 読み取り専用 | ツール実行後に HR のデータが変わっていない | 読み取り専用トランザクション内で DML → ORA-01456 | 結合(実 Oracle) |
| MCP ping | バージョン・ユーザー | 誤ったパスワード → ORACLE_ERROR(ORA-01017)、到達不能ホスト → ORACLE_ERROR/TIMEOUT | 結合 |
| マイグレーション | 空ファイルに適用、同じファイルに 2 回適用しても失敗しない | 不正 SQL でロールバックして例外 | 単体 |
| スナップショット保存 | 置き換え、別 owner は消さない | 挿入途中の失敗で前回が残る | 単体(一時 SQLite) |
| GET /api/schema | 未取得、取得済み(is_pk/is_fk、relations) | - | 単体(偽ゲートウェイ)、結合 |
| POST /api/schema/refresh | 成功で置き換わる | 409(実行中)、502/503/504、失敗時に前回が残る | 単体(偽ゲートウェイ)、結合(実 MCP + Oracle) |
| GET /api/schema/tables/... | 詳細、referenced_by、ref_in_snapshot | 404(未取得/無い表/owner 違い)、422(129 文字) | 単体、結合 |
| GET .../rows | ページ、has_next | 422(offset/limit)、404、502(MCP の NOT_FOUND → ORA-00942)、503、504 | 単体(偽ゲートウェイ)、結合 |
| GET /api/health | ok | MCP 停止時 degraded、Oracle エラー時 degraded、パスワードを含まない | 単体、結合 |
| MCP ゲートウェイ | 呼び出し、エラー JSON の解析 | 子プロセスの強制終了後の再起動、解析不能なエラー | 結合(実子プロセス) |
| frontend buildGraph | ノード・エッジ(自己参照、別スキーマ参照は線なし、30 列超の省略) | 0 件 | 単体(Vitest) |
| frontend layout | 全ノードに座標が付く、重ならない | - | 単体(Vitest、elkjs を実際に使う) |
| SC-01 | 描画、検索候補、再読み込みの成功・失敗通知、未取得表示 | API エラー | 単体(Vitest、API を偽物に) |
| SC-02 | タブ切替と URL、スキーマ情報の各表、データのページ送り、(null) 表示 | 404 表示、データタブのエラー表示と再試行 | 単体(Vitest) |
| 画面遷移全体 | ER 図 → クリック → 詳細 → FK 先 → 戻る | - | 受入(Playwright) |
| ノードのドラッグ | ドラッグしたノードだけが動く、ドラッグ後に SC-02 へ遷移しない、再読み込みで自動レイアウトの位置に戻る | - | 受入(Playwright、A01 手順 8・9)※CR-001により追加 |

### 2.2 非機能観点

| 観点 | 内容 | レベル |
|---|---|---|
| 性能 | HR で `GET /api/schema` < 1 秒、refresh < 10 秒、rows 1 ページ < Oracle 処理時間 + 1 秒 | システム(P009) |
| 性能(規模) | 300 表・5,000 列の偽スナップショットを SQLite に入れ、`GET /api/schema` < 3 秒、ブラウザでの ER 図表示 < 3 秒 | システム(P009) ★ACCEPTED★(2026-09-24 人間承認)大規模な実 Oracle スキーマは用意できないため偽データで代替。検討: 実スキーマでの測定/承認理由: 表示性能は SQLite 側のデータで決まる/残存リスク: 大規模スキーマの Oracle からの再読み込み時間は未測定 |
| タイムアウト | `query_timeout_sec` を 1 秒にして、MCP の読み取り専用トランザクション内で `DBMS_SESSION.SLEEP(3)` を呼ぶと ORACLE_TIMEOUT になり、その後の呼び出しは正常に動く | 結合(P008) |
| セキュリティ | API 応答・ログにパスワードが出ない、backend は CORS ヘッダを返さない、compose で api のポートが公開されていない、`config.yaml` がイメージに含まれない | システム(P009) |
| 読み取りのみ | テストスイートの前後で HR の各表の行数とチェックサム(`ORA_HASH` の合計)が同じ | システム(P009) |
| ログ | backend のログが JSON で出る、MCP のログが stderr に出る(stdout を汚さない) | 結合(P008) |
| 同時利用 | 10 名の仮想利用者が同時に ER 図の取得・テーブル詳細・データタブの 1・2 ページ目を各 10 回繰り返す。応答はすべて 200、ER 図の取得・テーブル詳細は各 1 秒以内、データ 1 ページは Oracle の処理時間(`elapsed_ms`)+ 1 秒以内(P001 §8.4)。API に対して測る(ER 図の描画はブラウザ内の処理で、同時利用者数の影響を受けないため) | システム(P009、A08)※CR-001により追加 |

### 2.3 運用観点(再起動耐性)

* **アプリケーションを停止・再起動しても正常に起動すること**を独立した観点とする。P003 §5.2 のマイグレーションは管理テーブルによる差分適用で冪等だが、これは永続化された SQLite ファイルに対して 2 回以上起動して初めて確認できる。単体テスト・結合テストは一時ファイルを使うため常に初回になり検出できない。
* 確認内容: compose で起動 → refresh → `docker compose restart api` → 起動に成功し、`GET /api/schema` が再起動前と同じスナップショットを返す。さらに `docker compose down` → `up`(ボリュームは残す)でも同じ。
* Oracle が停止している状態で api を起動しても起動に成功し、ER 図(保存済み)が表示できる。
* MCP 子プロセスを強制終了しても、次の API 呼び出しで回復する。
* 担当: 受け入れ結合テスト(P009)。

## 3. テスト遂行上の決め事

### 3.1 テスト環境

| 項目 | 内容 |
|---|---|
| Oracle | 人間が指定した既存の Oracle(`localhost:1521/FREEPDB1`、ユーザー hr、HR サンプルスキーマ)。接続情報は `config.yaml`(Git 管理外)から読む。テストは環境変数 `DBFAQ_CONFIG` で設定ファイルを指定できる |
| Oracle が使えない場合 | 実 Oracle を使うテスト(pytest マーカー `oracle`)は、`ping` に失敗したら **失敗として扱う**(スキップしない。黙って 0 件にならないようにする)。単体テストだけを回すときは `-m "not oracle"` を明示する |
| MCP | 結合テストは実際の子プロセス(`python -m dbfaq_mcp`)を使う。backend の単体テストは偽ゲートウェイ(`FakeGateway`: ツール名ごとに応答・例外を登録できる)を使う |
| frontend の API | Vitest では `fetch` を偽物(`vi.fn` で差し替える)にする。MSW は使わない ★ACCEPTED★(2026-09-24 人間承認)検討: MSW/承認理由: 依存を増やさない/残存リスク: 特になし |
| ブラウザ | Playwright の Chromium |

### 3.2 テストデータとライフサイクル

| 項目 | 方針 |
|---|---|
| Oracle(HR) | **読み取りのみ。テストは HR のデータを一切変更しない**。ベースラインは「HR サンプルスキーマのインストール直後の状態」であり、テスト側で復元はしない(変更しないので不要)。期待値は 2026-09-23 に実測した値(7 表、35 列、PK 7、UK 1、FK 10、インデックス 19、EMPLOYEES 107 行、JOB_HISTORY 10 行)を使う |
| 読み取り専用の確認で DML を試すテスト | 必ず `SET TRANSACTION READ ONLY` の中で行い、ORA-01456 で失敗することを確認する(成功してしまった場合に備え、テストは最後に必ず ROLLBACK する) |
| SQLite(単体・結合) | **テスト 1 件ごとに新しい一時ファイル**(pytest の `tmp_path`)を使う。共有しないので累積しない |
| SQLite(受入・compose) | ベースライン = 「マイグレーション適用直後、スナップショット無し」。**テストスイートの実行ごと**に、開始時に `docker compose down -v`(ボリューム削除)→ `up` で復元する。スイート内のテストは順に実行し、先行テストが作ったスナップショット(refresh の結果)を後続テストが使うことを許容する |
| 再実行性 | テストスイート全体を 2 回続けて実行して同じ結果になることを、テストを作成・変更したフェーズ(P103・P201・P203・P205)が確認する |

### 3.3 実行コマンド(予定)

以下は予定であり、P102/P103 で実際に実行して確認した後に P007/P008 の各文書・P101 に確定版を記載する ★ACCEPTED★(2026-09-24 人間承認)作成時点では未実行だった。確定版は P101 §5 と本書 8 章に記載済み

| 対象 | コマンド |
|---|---|
| Python 単体 | `cd server && uv run pytest tests/unit` |
| Python 結合(実 Oracle) | `cd server && uv run pytest tests/integration` |
| Python 1 件だけ | `cd server && uv run pytest tests/unit/test_type_format.py::test_number_precision_scale` |
| frontend 単体 | `cd client && npm test` |
| 受入(Playwright) | `docker compose up -d --build && cd e2e && npx playwright test` |
