# P006 テスト計画書 — DbFAQ(第1リリース)

入力: `docs/P001-requirement.md`、`docs/P002-frontend-spec.md`、`docs/P003-backend-spec.md`、`docs/P005-impl-plan.md`。
個々のテストケースの実装指示は P007(単体)・P008(スプリント内結合)・P009(スプリント横断・システム・受入)で作る。

## 1. テストレベルと目的

| テストレベル | 目的 | 定義する文書 | ツール |
|---|---|---|---|
| 単体テスト | P002・P003 で定義した画面・API・Oracle アクセスの処理・内部モジュールが(※CR-002により「MCP ツール」を変更)単体で仕様どおりに動くか | P007(各スプリントの実装指示の中) | pytest(+pytest-asyncio)、Vitest + Testing Library |
| 結合テスト | 画面・API・Oracle・SQLite が連携して仕様どおりか(スプリント内/モジュール間) | P008 | pytest(実 Oracle HR)、Vitest(※CR-002により MCP・実 MCP 子プロセスを削除) |
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
| Oracle: スキーマの読み取り(※CR-002により「MCP get_schema_snapshot」から変更) | HR: 8 表、列 38、PK 8、UK 1、FK 11、インデックス 20(※P202 F010(CR-004)により変更。人間の指示 2026-10-04) | 存在しないスキーマ → NOT_FOUND | 結合(実 Oracle) |
| Oracle: テーブルデータ(※CR-002により「MCP get_table_rows」から変更) | HR.EMPLOYEES の 1〜50 行目・51〜100 行目・101〜107 行目、複合 PK(JOB_HISTORY)の並び | 存在しない表 → NOT_FOUND、offset/limit 範囲外 → INVALID_ARGUMENT、`"` を含む名前 | 結合(実 Oracle) |
| Oracle: 読み取り専用(※CR-002により「MCP」を変更) | 各処理の実行後に HR のデータが変わっていない | 読み取り専用トランザクション内で DML → ORA-01456。※CR-006により、接続ユーザーが `dbfaq_ro` のときは権限エラー ORA-41900(または ORA-01031)で先に拒否される。どちらかで拒否され、データが変わらないことを確かめる | 結合(実 Oracle) |
| Oracle: 疎通確認(※CR-002により「MCP ping」から変更) | バージョン・ユーザー | 誤ったパスワード → ORACLE_ERROR(ORA-01017)、到達不能ホスト → ORACLE_ERROR/TIMEOUT | 結合 |
| マイグレーション | 空ファイルに適用、同じファイルに 2 回適用しても失敗しない | 不正 SQL でロールバックして例外 | 単体 |
| スナップショット保存 | 置き換え、別 owner は消さない | 挿入途中の失敗で前回が残る | 単体(一時 SQLite) |
| GET /api/schema | 未取得、取得済み(is_pk/is_fk、relations) | - | 単体(偽の Oracle アクセス)、結合 |
| POST /api/schema/refresh | 成功で置き換わる | 409(実行中)、502/504、失敗時に前回が残る | 単体(偽の Oracle アクセス)、結合(実 Oracle)(※CR-002により 503・MCP を削除) |
| GET /api/schema/tables/... | 詳細、referenced_by、ref_in_snapshot | 404(未取得/無い表/owner 違い)、422(129 文字) | 単体、結合 |
| GET .../rows | ページ、has_next | 422(offset/limit)、404、502(Oracle アクセスの NOT_FOUND → ORA-00942)、504 | 単体(偽の Oracle アクセス)、結合(※CR-002により 503・MCP を変更) |
| GET /api/health | ok(`mcp` を含まない) | Oracle エラー時 degraded、パスワードを含まない | 単体、結合(※CR-002により「MCP 停止時 degraded」を削除) |
| Oracle アクセスの入口(`OracleClient`) | 3 つの処理が読み取り専用トランザクションで実行される、疎通確認の問い合わせ上限が 5 秒 | - | 単体(偽のプール)※CR-002により「MCP ゲートウェイ」(子プロセスの再起動、エラー JSON の解析)から置き換え |
| frontend buildGraph | ノード・エッジ(自己参照、別スキーマ参照は線なし、30 列超の省略) | 0 件 | 単体(Vitest) |
| frontend layout | 全ノードに座標が付く、重ならない | - | 単体(Vitest、elkjs を実際に使う) |
| SC-01 | 描画、検索候補、再読み込みの成功・失敗通知、未取得表示 | API エラー | 単体(Vitest、API を偽物に) |
| SC-02 | タブ切替と URL、スキーマ情報の各表、データのページ送り、(null) 表示 | 404 表示、データタブのエラー表示と再試行 | 単体(Vitest) |
| SQL の検査(※CR-004により追加) | SELECT・WITH、末尾のセミコロン 1 個、コメント・文字列・引用符付き識別子の中の禁止語(`'DELETE'`、`"UPDATE"`、`-- drop`)、ヒント句 | INSERT/UPDATE/DELETE/MERGE/DDL/GRANT/COMMIT 等、BEGIN/DECLARE、EXECUTE IMMEDIATE・DBMS_SQL、FOR UPDATE、LOCK TABLE、複数の文、WITH の中の DML、空 | 単体 |
| エラー位置の変換(※CR-004により追加) | ASCII の 1 行・複数行、日本語(マルチバイト)を含む SQL、タブ | offset 0・文字の途中・長さ超過 → 位置なし | 単体 |
| SELECT の実行(※CR-004により追加) | 結果の列・行・値の文字列化、500 行で打ち切り(has_more)、0 行、WITH、末尾のセミコロン | ORA-00904 で position(行・文字)、ORA-00942、タイムアウト、SQL_REJECTED は Oracle に送らない | 単体(偽のカーソル)、結合(実 Oracle) |
| CSV(※CR-004により追加) | 見出し行、BOM、CRLF、カンマ・`"`・改行を含む値の囲み、NULL は空、切り詰めない(1,000 文字超・32 バイト超)、500 行を超える全行(`X-Row-Count`) | 取得途中のエラーは JSON、SQL_REJECTED | 単体、結合(実 Oracle) |
| POST /api/query・/api/query/csv(※CR-004により追加) | 200 の形 | 422(空・100,000 文字超・SQL_REJECTED)、502(position 付き)、504 | 単体(偽の Oracle アクセス)、結合 |
| frontend のひな形(※CR-004により追加) | 外部キーなし、→ の JOIN、← の JOIN、自己参照、複数選択、複合 FK、同じ列名の別名、引用符が要る識別子、主キーなしで ORDER BY なし | 相手の列情報が無い制約は選べない | 単体(Vitest) |
| SC-02 Query タブ(※CR-004により追加) | `tab=query`、初期のひな形、チェックボックスでの置き換え(未編集なら自動・編集済みなら置き換えない)、実行結果の表、打ち切りの表示、0 行、CSV の保存 | エラー表示(ORA コード、エラー位置と ^、エラー位置へ移動)、SQL_REJECTED の表示 | 単体(Vitest) |
| マイグレーション 0002(※CR-005により追加) | 0001 だけ適用済みのファイルに 0002 が適用される、起動処理(マイグレーション + ひな型の登録)を 2 回続けても成功しひな型が重複しない | - | 単体(一時 SQLite)、受入(A04 の再起動) |
| 保存済み Query のリポジトリ(※CR-005により追加) | 作成・一覧(名前順、保存先ごとに分離。table と pdb、別のテーブル、大文字小文字の違うテーブル名は別)・更新(updated_at)・削除、スナップショットの置き換え(テーブルが無くなる/戻る)の前後で行が残り同じ一覧が返る | 同じ保存先の同じ名前 → 重複エラー、別の保存先なら同じ名前で可、無い id の更新・削除 | 単体(一時 SQLite) |
| ひな型の登録(※CR-005により追加) | 初回に全件登録、2 回目は何もしない、削除・改名したひな型を戻さない、新しいキーだけ追加、利用者の同名の Query があれば「 (ひな型)」を付ける、全ひな型が SQL の検査を通る | - | 単体 |
| 保存済み Query の API(※CR-005により追加) | 一覧・201・200・204 の形、pdb の owner/table が null、is_template | 422(scope 不正、table で owner 欠落、pdb で owner 指定、名前の空白だけ・101 文字、説明 1,001 文字、SQL 空白だけ)、409、404 | 単体(偽の Oracle アクセス)、結合(T15) |
| PDB 情報(※CR-005により追加) | 4 セクションの形、overview の 10 行、バージョンは conn.version | セクションの ORA-00942 はそのセクションだけのエラー、タイムアウトは全体の 504、接続の失敗は全体の 502 | 単体(偽のカーソル)、結合(実 Oracle、T14) |
| PDB のひな型の実行(※CR-005により追加) | 権限の要らないひな型は HR で成功する(03 で EMPLOYEE_FIGURE.FIGURE の行) | 権限の要るひな型は ORA-00942/ORA-01031 だけ(構文エラーにならない) | 結合(実 Oracle、T14) |
| 読み取り専用ユーザーと対象スキーマ(※CR-006により追加) | `dbfaq_ro` で接続して、カレントスキーマが対象スキーマ(HR)、PDB 情報の全セクションが成功し HR の分を返す、ひな型 17 件がすべて成功(03・04 に EMPLOYEE_FIGURE.FIGURE、04 は読めない APPOWNER の表があっても成功)、スキーマ名なしの表名が HR の表になる。登録済みのひな型の更新(SQL が以前の版なら新しい版に、利用者が変えたものは残す、2 回目は何もしない) | DBA_USERS を読めないとき概要の表領域だけ「権限が無いため取得できません」 | 単体、結合(T14・T15) |
| テーブルが無くなって戻ったとき(※CR-005により追加) | 保存 → スナップショットからテーブルが無くなる refresh → SQLite に残る(SC-02 は TABLE_NOT_FOUND)→ 同名のテーブルが戻る refresh → 一覧に出て SQL が同じ | - | 結合(T15。偽の Oracle アクセスで refresh の結果を切り替え、実際の SQLite ファイルと API を通す) ★ACCEPTED★ 検討: 実 Oracle の HR で表を消して戻す/不採用理由: テストは HR を変更しない方針(§3.2)/残存リスク: 実 Oracle の辞書の変化からの一連は A10 で確かめない(スナップショットの置き換えの処理は既存のテストで実 Oracle 由来のデータで確かめ済み) |
| frontend の保存済み Query(※CR-005により追加) | 一覧(0 件・ひな型の印・復元中の ●)、名前を付けて保存(201 で一覧更新・復元中)、復元(未編集なら即時、編集済みなら確認)、上書き保存、編集、削除(確認、復元中の解除) | 409 をダイアログ内に表示、名前の空白だけ・101 文字で保存できない | 単体(Vitest) |
| SC-01 の PDB のアイコン・SC-03(※CR-005により追加) | アイコンの表示(未取得・0 件でも)・PDB 名・クリックで /pdb、PDB 情報タブのセクション・権限エラーの表示・再読み込み、Query タブ(JOIN なし・初期値は空・ひな型の復元と実行)、`tab=query` | 全体のエラーと再試行 | 単体(Vitest) |
| 画面遷移全体 | ER 図 → クリック → 詳細 → FK 先 → 戻る | - | 受入(Playwright) |
| 保存・復元と PDB 画面の操作全体(※CR-005により追加) | HR.EMPLOYEES の Query タブで保存 → 別のテーブルには出ない → 再読み込み後に復元して実行 → 上書き・変更・削除。SC-01 のドラム缶 → SC-03 → PDB 情報 → ひな型 03 を復元・実行して EMPLOYEE_FIGURE.FIGURE → 保存 | 同じ名前の保存で 409 の表示 | 受入(Playwright、A10) |
| Query タブの操作全体(※CR-004により追加) | HR.EMPLOYEES でひな形 → FK を ON → 実行して表 → 500 行を超える SELECT で打ち切り表示 → CSV ダウンロードで全行 | 存在しない列でエラー位置の表示、DELETE が拒否される | 受入(Playwright、A09) |
| ノードのドラッグ | ドラッグしたノードだけが動く、ドラッグ後に SC-02 へ遷移しない、再読み込みで自動レイアウトの位置に戻る | - | 受入(Playwright、A01 手順 8・9)※CR-001により追加 |

### 2.2 非機能観点

| 観点 | 内容 | レベル |
|---|---|---|
| 性能 | HR で `GET /api/schema` < 1 秒、refresh < 10 秒、rows 1 ページ < Oracle 処理時間 + 1 秒、`POST /api/query`(EMPLOYEES の全列・全行)< Oracle 処理時間(`elapsed_ms`)+ 1 秒(※CR-004により追加) | システム(P009) |
| 性能(規模) | 300 表・5,000 列の偽スナップショットを SQLite に入れ、`GET /api/schema` < 3 秒、ブラウザでの ER 図表示 < 3 秒 | システム(P009) ★ACCEPTED★(2026-09-24 人間承認)大規模な実 Oracle スキーマは用意できないため偽データで代替。検討: 実スキーマでの測定/承認理由: 表示性能は SQLite 側のデータで決まる/残存リスク: 大規模スキーマの Oracle からの再読み込み時間は未測定 |
| タイムアウト | `query_timeout_sec` を 1 秒にして、backend の読み取り専用トランザクション内で(※CR-002により「MCP の」を変更) `DBMS_SESSION.SLEEP(3)` を呼ぶと ORACLE_TIMEOUT になり、その後の呼び出しは正常に動く | 結合(P008) |
| セキュリティ | API 応答・ログにパスワードが出ない、backend は CORS ヘッダを返さない、compose で api のポートが公開されていない、`config.yaml` がイメージに含まれない | システム(P009) |
| 読み取りのみ | テストスイートの前後で HR の各表の行数とチェックサム(`ORA_HASH` の合計)が同じ。※CR-004により追加: `POST /api/query`・`/api/query/csv` に DML・DDL・PL/SQL・FOR UPDATE を送ると 422 `SQL_REJECTED` になり、HR が変わらない | システム(P009)、結合(P008 T13) |
| ログ | backend のログが JSON で出る(※CR-002により「MCP のログが stderr に出る(stdout を汚さない)」を削除) | 単体 |
| 同時利用 | 10 名の仮想利用者が同時に ER 図の取得・テーブル詳細・データタブの 1・2 ページ目を各 10 回繰り返す。応答はすべて 200、ER 図の取得・テーブル詳細は各 1 秒以内、データ 1 ページは Oracle の処理時間(`elapsed_ms`)+ 1 秒以内(P001 §8.4)。API に対して測る(ER 図の描画はブラウザ内の処理で、同時利用者数の影響を受けないため) | システム(P009、A08)※CR-001により追加 |

### 2.3 運用観点(再起動耐性)

* **アプリケーションを停止・再起動しても正常に起動すること**を独立した観点とする。P003 §5.2 のマイグレーションは管理テーブルによる差分適用で冪等だが、これは永続化された SQLite ファイルに対して 2 回以上起動して初めて確認できる。単体テスト・結合テストは一時ファイルを使うため常に初回になり検出できない。
* 確認内容: compose で起動 → refresh → `docker compose restart api` → 起動に成功し、`GET /api/schema` が再起動前と同じスナップショットを返す。さらに `docker compose down` → `up`(ボリュームは残す)でも同じ。
* Oracle が停止している状態で api を起動しても起動に成功し、ER 図(保存済み)が表示できる。
* ※CR-002により「MCP 子プロセスを強制終了しても、次の API 呼び出しで回復する」を削除(子プロセスが無くなった)。代わりに、Oracle との通信が切れて戻ったときに api を再起動せずに回復することを **T09(結合)** で確認する(テスト内の TCP 中継を止めて再開する。共有の Oracle 本体は止めない)。A03 の回復確認は api を作り直して行うため、この観点の代わりにはならない。
* 担当: 受け入れ結合テスト(P009)。

## 3. テスト遂行上の決め事

### 3.1 テスト環境

| 項目 | 内容 |
|---|---|
| Oracle | 人間が指定した既存の Oracle(`localhost:1521/FREEPDB1`、ユーザー hr)。スキーマの前提は次の 2 つ(人間の指示 2026-10-04): ① Oracle 配布の HR サンプルスキーマ(https://github.com/oracle/db-sample-schemas/releases/latest の human_resources)、② ①に LOB 列が無いため追加する表 `EMPLOYEE_FIGURE`(DDL は `server/scripts/sql/hr_employee_figure.sql`。IDENTITY の主キー `FIGURE_ID`、`EMPLOYEE_ID` → EMPLOYEES の外部キー、BLOB 列 `FIGURE`)。`EMPLOYEE_FIGURE` の行のデータは前提にしない(テストは構造だけを確かめ、チェックサムはスイートごとに取り直す)。データの投入方法(手順は §3.1.1): 画像ファイル `docs/P006-test-plan/ai_model_512_01.png` を DB サーバの `/opt/oracle/oradata` に置き、管理ユーザーで `server/scripts/sql/hr_photo_dir.sql`(DIRECTORY `PHOTO_DIR` と hr への READ 権限)、hr ユーザーで `server/scripts/sql/hr_employee_figure_data.sql`(EMPLOYEE_ID 100〜206 に同じ画像を 1 行ずつ。1 回の実行で 107 行)を実行する。2026-10-04 の開発用 Oracle は 2 回実行した 214 行。接続情報は `config.yaml`(Git 管理外)から読む。テストは環境変数 `DBFAQ_CONFIG` で設定ファイルを指定できる |
| Oracle が使えない場合 | 実 Oracle を使うテスト(pytest マーカー `oracle`)は、`ping` に失敗したら **失敗として扱う**(スキップしない。黙って 0 件にならないようにする)。単体テストだけを回すときは `-m "not oracle"` を明示する |
| Oracle アクセス | 結合テストは実際の `OracleClient`(実 Oracle)を使う。backend の単体テストは偽物(`FakeOracle`: 処理ごとに応答・例外を登録できる)を使う。※CR-002により「MCP(実際の子プロセス、偽ゲートウェイ)」から変更 |
| frontend の API | Vitest では `fetch` を偽物(`vi.fn` で差し替える)にする。MSW は使わない ★ACCEPTED★(2026-09-24 人間承認)検討: MSW/承認理由: 依存を増やさない/残存リスク: 特になし |
| ブラウザ | Playwright の Chromium |

#### 3.1.1 テスト用データベースの準備(2026-10-05 追記。依頼者の指示)

§3.1 の ①・② を次の順に準備する。スクリプトは `server/scripts/sql/`、画像は本書の付属ファイル `docs/P006-test-plan/ai_model_512_01.png`(420,605 バイト。SHA-256 `31c89ca2a00c5036f510f38bedb89bb93fb4f3b869412a492bb94681f578238c`。開発用 Oracle の `/opt/oracle/oradata/ai_model_512_01.png` からコピーしたもの)にある。

1. Oracle 配布の HR サンプルスキーマ(https://github.com/oracle/db-sample-schemas/releases/latest の human_resources)をインストールする。
2. hr ユーザーで `server/scripts/sql/hr_employee_figure.sql` を実行し、表 `EMPLOYEE_FIGURE` を作る。
3. 画像を Oracle のコンテナにコピーする(リポジトリのルートで実行。コンテナ名は開発環境の `oracle-db-free`):

   ```bash
   docker cp docs/P006-test-plan/ai_model_512_01.png oracle-db-free:/opt/oracle/oradata/ai_model_512_01.png
   docker exec oracle-db-free ls -l /opt/oracle/oradata/ai_model_512_01.png   # 420605 バイトであることを確認
   ```

   * `docker cp` でコピーしたファイルの所有者は、コピー元の uid のままになる。Oracle のプロセス(ユーザー oracle)が読めない場合は `docker exec -u root oracle-db-free chmod 644 /opt/oracle/oradata/ai_model_512_01.png` で読み取りを許可する。
4. 管理ユーザー(SYS・SYSTEM など)で PDB(例: FREEPDB1)に接続し、`server/scripts/sql/hr_photo_dir.sql` を実行する(`CREATE OR REPLACE DIRECTORY photo_dir AS '/opt/oracle/oradata'`、`GRANT READ ON DIRECTORY photo_dir TO hr`)。
5. hr ユーザーで `server/scripts/sql/hr_employee_figure_data.sql` を実行する(EMPLOYEE_ID 100〜206 に同じ画像を 1 行ずつ。1 回の実行で 107 行。実行した回数だけ増える)。
6. 確認: `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`。

* 手順 3〜5(データの投入)は省略してよい。`EMPLOYEE_FIGURE` の行のデータはテストの前提にしない(0 行でもよい)。

* ※CR-006により: 開発・テストの接続ユーザーは `dbfaq_ro`(2026-10-09 に依頼者が FREEPDB1 に作成。`CREATE SESSION`、`SELECT_CATALOG_ROLE`、`READ ANY TABLE ON SCHEMA hr`)。`config.yaml` の `oracle.user` に設定し、`oracle.schema` は `HR`。テスト用 DB の準備(§3.1.1 の HR・`EMPLOYEE_FIGURE` の投入)は従来どおり `hr` や管理ユーザーで行う。

### 3.2 テストデータとライフサイクル

| 項目 | 方針 |
|---|---|
| Oracle(HR) | **読み取りのみ。テストは HR のデータを一切変更しない**。ベースラインは「§3.1 の ①(HR サンプルスキーマのインストール直後)に ②(`server/scripts/sql/hr_employee_figure.sql`)を実行した状態」(`EMPLOYEE_FIGURE` の行数は問わない。2026-10-04 の開発用 Oracle では 214 行)であり、テスト側で復元はしない(変更しないので不要)。期待値は 2026-10-04 に実測した値(8 表、38 列、PK 8、UK 1、FK 11、インデックス 20、EMPLOYEES 107 行、JOB_HISTORY 10 行)を使う(※P202 F010(CR-004)により、2026-09-23 の実測値(7 表、35 列、PK 7、UK 1、FK 10、インデックス 19)から変更。開発用 Oracle の HR に 2026-09-29 に表が追加されたため、人間の指示で新しいベースラインにした。2026-10-04)。チェックサム(`hr_checksum.py`)は LOB 列の表を SHA-256 で計算する(P202 F009) |
| 読み取り専用の確認で DML を試すテスト | 必ず `SET TRANSACTION READ ONLY` の中で行い、ORA-01456 で失敗することを確認する(成功してしまった場合に備え、テストは最後に必ず ROLLBACK する) |
| SQLite(単体・結合) | **テスト 1 件ごとに新しい一時ファイル**(pytest の `tmp_path`)を使う。共有しないので累積しない |
| SQLite(受入・compose) | ベースライン = 「マイグレーション適用直後、スナップショット無し」。**テストスイートの実行ごと**に、開始時に `docker compose down -v`(ボリューム削除)→ `up` で復元する。スイート内のテストは順に実行し、先行テストが作ったスナップショット(refresh の結果)を後続テストが使うことを許容する |
| Query の行数の多い結果(※CR-004により追加) | HR には 500 行を超える表が無いため、HR を変えずに行を作る問い合わせを使う: `SELECT a.EMPLOYEE_ID, b.EMPLOYEE_ID FROM HR.EMPLOYEES a CROSS JOIN HR.EMPLOYEES b`(107 × 107 = 11,449 行)、または `SELECT LEVEL FROM DUAL CONNECT BY LEVEL <= 1200` |
| 保存済み Query(受入)(※CR-005により追加) | A10 が作る保存済み Query は名前に `A10-` を付け、テストの最初と最後に `A10-` で始まるものを API で削除する(スイートの開始時の `down -v` でも消える)。ひな型は変更・削除しない(変更したら最後に元に戻す) |
| CSV のダウンロード(受入)(※CR-004により追加) | Playwright のダウンロードは一時ディレクトリに保存し、テストの終わりに消す(累積しない) |
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
