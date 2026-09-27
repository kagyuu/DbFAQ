あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A05

## 【目的】

* P001 §8.1 の性能目標(HR での ER 図表示・再読み込み・データ 1 ページ、300 表規模での ER 図表示)を確認する(REQ-NFR-001)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.2「性能」「性能(規模)」

## 【対象モジュール】

* web、api、Oracle(CR-002 で MCP を削除)、ブラウザでのレイアウト(elkjs)

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `7`)。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* HR(compose、A01 のスナップショット)。
* 大規模: 300 表・合計 5,000 列・外部キー 400 本の偽スナップショット。**owner は `HR`**(backend は設定の schema=HR のスナップショットを読むため)。`server/scripts/gen_large_snapshot.py <出力先 SQLite>` で生成する(本タスクで新規作成する。マイグレーションを適用したうえで、`SnapshotRepository.replace` に P003 §3.5 の形の dict を渡して保存する)。実 Oracle の大規模スキーマが無いための代替(`docs/P006-test-plan.md` §2.2)。

## 【事前準備】

* `e2e/tests/a05-performance.spec.ts`、`e2e/scripts/a05-perf-api.sh`、`e2e/scripts/a05-load-large.sh`、`e2e/scripts/a05-restore-hr.sh` を作る(新規)。
* 大規模データの投入(`a05-load-large.sh`。手順 5 の前に実行): `D=$(mktemp -d)` → `cd server && uv run python scripts/gen_large_snapshot.py $D/large.sqlite3` → `docker compose stop api` → `docker compose cp $D/large.sqlite3 api:/data/dbfaq.sqlite3`(停止中のコンテナにもコピーできる)→ `docker compose run --rm --no-deps --user root --entrypoint sh api -c 'chown 10001:10001 /data/dbfaq.sqlite3 && rm -f /data/dbfaq.sqlite3-wal /data/dbfaq.sqlite3-shm'`(コピーしたファイルはホストの所有者のままで、非 root(uid 10001)で動く api が書き込めないため所有者を変える。※P202 F004 にもとづき訂正)→ `docker compose start api` → `/api/health` が 200 になるまで待つ。
* HR への復帰(`a05-restore-hr.sh`。手順 7): `curl -s -X POST localhost:8088/api/schema/refresh` → `/api/schema` の `table_count` が 7 に戻ったことを確認する。
* 測定はすべて compose の web(`http://localhost:8088`)に対して行う。別ポートの backend や開発サーバは立てない(アプリの設定を変えないため)。
* ※P011矛盾点#3にもとづき、事前準備を 1 通りの手順に整理

## 【実行手順】

1. HR: `curl -s -o /dev/null -w '%{time_total}' localhost:8088/api/schema` を 5 回 → 中央値 < 1 秒。
2. HR: `POST /api/schema/refresh` の `time_total` → < 10 秒。
3. HR: `GET /api/schema/tables/HR/EMPLOYEES/rows?offset=0&limit=50` の `time_total` − 応答の `elapsed_ms`/1000 → < 1 秒。
4. HR(ブラウザ): `/` を開いてから 7 ノードが表示されるまで < 1 秒(`performance.now()` の差。Playwright で測る)。
5. 大規模(api): `GET /api/schema` の `time_total` の中央値(5 回)< 3 秒。
6. 大規模(ブラウザ): `/` を開いてから 300 ノードが表示されるまで < 3 秒。表示後、ホイールでの拡大縮小が操作できる(1 回の操作後 1 秒以内に transform が変わる)。
7. 後片付け: `a05-restore-hr.sh` で HR に戻す。

## 【実行コマンド】

* `bash e2e/scripts/a05-perf-api.sh hr`(手順 1〜3)
* `cd e2e && npx playwright test tests/a05-performance.spec.ts -g "hr:"`(手順 4)
* `bash e2e/scripts/a05-load-large.sh && bash e2e/scripts/a05-perf-api.sh large`(手順 5)
* `cd e2e && npx playwright test tests/a05-performance.spec.ts -g "large:"`(手順 6)
* `bash e2e/scripts/a05-restore-hr.sh`(手順 7)
* ※P202 F004 にもとづき `-g` のパターンを `"hr:"`・`"large:"` に訂正(`hr` だけだと project 名 `chromium` にも一致するため)

## 【期待結果】

* すべての測定値が目標内。

## 【合否判定基準】

* すべて目標内なら PASS。1 つでも超えたら FAIL(測定値を記録)。大規模データの投入に失敗した場合はその項目を BLOCKED。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。
* 各測定の生の値(5 回分)を記録する。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* HR に戻したことを確認し、記録して A05 を `[x]` にしたら A06 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
