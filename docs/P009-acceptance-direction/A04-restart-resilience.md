あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A04

## 【目的】

* 永続化された SQLite に対して api を停止・再起動しても正常に起動し(マイグレーションが冪等)、スナップショットが保持されることを確認する(REQ-ARCH-003、P003 §5.2、運用観点)。あわせて、api コンテナで MCP の子プロセスが動いていないことを確認する(CR-002)。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §2.3

## 【対象モジュール】

* api(migrate.py、snapshot_repo)、compose のボリューム

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更))。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* A01 が作ったスナップショット(ボリュームを消さない)。**このテストはデータが永続していること自体を確認するため、途中でベースライン復元(`down -v`)を挟まない。**

## 【事前準備】

* `e2e/scripts/a04-restart.sh` を作る(下記の手順をコマンドで実行し、各確認の結果を echo する)。

## 【実行手順】

1. `curl -s localhost:8088/api/schema` の `snapshot.fetched_at` を記録(F0)。
2. `docker compose restart api` → `/api/health` が 200 になるまで待つ(最大 60 秒)。起動に成功する。
3. `fetched_at` が F0 と同じ。tables 7。
4. `docker compose down`(**`-v` を付けない**)→ `docker compose up -d` → 待つ。起動に成功し、`fetched_at` が F0 と同じ。
5. `docker compose exec api python -c "import sqlite3; print(sqlite3.connect('/data/dbfaq.sqlite3').execute('select count(*) from schema_migrations').fetchone()[0])"` → `1`(0001_init が 1 回だけ記録されている)。
6. `docker compose logs api` に起動時の例外(`Traceback`、`MigrationError`)が無い。
7. api コンテナに MCP の子プロセスが無い: api イメージには `ps` が無いため、Python で `/proc` を走査して数える: `docker compose exec -T api python -c "import os; print(sum(1 for p in os.listdir('/proc') if p.isdigit() and int(p)!=os.getpid() and b'dbfaq_mcp' in open(f'/proc/{p}/cmdline','rb').read()))"` → `0`。続けて `/api/health` の status が `ok`。※CR-002により「MCP 子プロセスの強制終了からの回復」(※P011(2回目)矛盾点#2)から置き換え。子プロセスが無くなったため

## 【実行コマンド】

* `bash e2e/scripts/a04-restart.sh`

## 【期待結果】

* 1〜7 がすべて成り立つ。

## 【合否判定基準】

* 全ステップ成立で PASS。起動に失敗、またはスナップショットが消えたら FAIL。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。
* `docker compose logs --tail 100 api`。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A04 を `[x]` にしたら A05 へ進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
