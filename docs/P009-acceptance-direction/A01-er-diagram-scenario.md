あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A01

## 【目的】

* 運用担当者の視点で、初回起動から ER 図の表示・拡大縮小・ミニマップ・検索・クリックでの遷移までを通しで確認する(REQ-SCREEN-001〜009、REQ-API-001・002・005)。
* ノードのドラッグ(REQ-SCREEN-009。ドラッグしたノードだけが動く、クリック扱いにならない、位置を保存しない)を確認する。※CR-001により追加

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.1「画面遷移全体」「SC-01」「ノードのドラッグ」(※CR-001により追加)、§1 受け入れテスト

## 【対象モジュール】

* web(nginx + client)、api(dbfaq_api。CR-002 で dbfaq_mcp を削除)、Oracle(U002〜U006 をまたぐ)

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7`)。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* HR(7 表、外部キー 10)。SQLite はベースライン(スナップショット無し)から開始。

## 【事前準備】

* スイートのベースライン復元(`docs/P006-test-plan.md` §3.2): **A01 の開始前に 1 回だけ**、アプリを起動する前に `e2e/scripts/reset-and-up.sh` を実行する(中身: `docker compose down -v` → `docker compose up -d --build` → `/api/health` が 200 になるまで最大 60 秒待つ → `cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/hr_checksum.py > ../e2e/.baseline-checksum.json` で HR の全 7 表のチェックサム(各表の `COUNT(*)` と全列を `||` で連結した `ORA_HASH` の合計。読み取り専用トランザクションで実行)を保存する)。このスクリプトと `server/scripts/hr_checksum.py` が無ければ本タスクで新規作成する。※P011(2回目)矛盾点#1にもとづきチェックサム取得を追加A02 以降は A01 が作ったスナップショットを使う(テスト間のデータ依存を許容する方針)。
* `e2e/tests/a01-er-diagram.spec.ts` を作る。

## 【実行手順】

1. `/` を開く → 「スキーマ情報がありません」と [Oracle から読み込む] が表示される。ヘッダの `[data-testid=oracle-status]` の `data-status` が `ok`。
2. [Oracle から読み込む] を押す → 通知「スキーマ情報を更新しました(テーブル 7 / 関連 10)」→ `[data-testid^=er-node-]` が 7 個。ツールバーに「テーブル 7 / 関連 10」。ヘッダに「スキーマ: HR」と取得日時。
3. ミニマップ(`.react-flow__minimap`)とコントロール(`.react-flow__controls`)が見える。エッジ(`.react-flow__edge`)が 10 本。
4. ビューポート(`.react-flow__viewport` の `transform` の scale)を記録 → コントロールの拡大ボタンを 2 回 → scale が大きくなる → 縮小ボタンを 4 回 → 小さくなる → 全体表示ボタン → 7 ノードすべてが画面内(`boundingBox` がキャンバス内)。
5. 検索欄に `job_h` を入力 → 候補に JOB_HISTORY → 選ぶ → `er-node-JOB_HISTORY` が画面中央付近(キャンバス中心から 100px 以内)に来る。
6. `er-node-EMPLOYEES` をクリック → URL が `/tables/HR/EMPLOYEES`、見出し `HR.EMPLOYEES`。
7. ブラウザの戻る → ER 図に戻り、7 ノードが表示される。
8. (別のテストケースとして実行。1〜7 が作ったスナップショットを使う)`/` を開き、`er-node-DEPARTMENTS` と `er-node-LOCATIONS` の位置、および DEPARTMENTS の LOCATIONS からの相対位置を scale で割った値を記録する → DEPARTMENTS の見出し付近をマウスで押し、右へ 120px・下へ 80px(10 段階)動かして離す → URL が `/` のまま(SC-02 へ遷移しない)、DEPARTMENTS が右へ 90〜125px・下へ 55〜85px 動いている(ドラッグ判定のしきい値 5px を超えるまでの最初の移動分は動かないため範囲で見る)、LOCATIONS は動いていない(1px 未満)。※CR-001により追加
9. ページを再読み込みする → 7 ノードが表示され、DEPARTMENTS の LOCATIONS からの相対位置(scale で割った値)が手順 8 の記録と 2px 未満の差で一致する(位置を保存せず、自動レイアウトに戻る)。※CR-001により追加

## 【実行コマンド】

* `bash e2e/scripts/reset-and-up.sh && cd e2e && npx playwright test tests/a01-er-diagram.spec.ts`

## 【期待結果】

* 1〜9 がすべて成り立つ。

## 【合否判定基準】

* 全ステップ成立で PASS。失敗があれば FAIL。compose が起動しなければ BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A01 を `[x]` にしたら A02 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
