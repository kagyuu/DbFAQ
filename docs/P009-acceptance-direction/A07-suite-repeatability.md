あなたはReviewer Loop(実装横断レビュー担当)です。以下は1テストタスク分の作業範囲と完了条件を定義したものです。実施後は、結果(PASS/FAIL/BLOCKED/NOT RUNいずれであっても)を記録したうえで、Reviewer Loopの「停止条件」(`SKILL.md` 参照)に該当しない限り、`docs/P009-acceptance-direction.md` のWBSに従って自動的に次のテストタスクへ進んでください。人間の指示を待って停止しないでください。

# 【テストID】A07

## 【目的】

* 受入テストのスイート全体(A01〜A06、A08〜A10。※CR-001により A08 を追加。※CR-004により A09 を追加。※CR-005により A10 を追加)を 2 回続けて実行しても同じ結果になること(再実行可能であること)を確認する。

## 【参照テスト計画】

* `docs/P006-test-plan.md` §3.2「再実行性」、`SKILL.md` 共通指示(テストスイートの 2 回実行)

## 【対象モジュール】

* 受入テストのスイート全体とベースライン復元スクリプト

## 【前提条件】全モジュールビルドが成功していること

* ビルド対象: 全モジュール。ビルドコマンド: `cd server && uv sync && uv run pytest tests/unit -q`、`cd client && npm ci && npm test && npm run build`、`docker compose build`。成功条件: すべて終了コード 0。失敗時はテスト記録に BLOCKED として出力を残し、テストへ進まない。
* 開発用 Oracle(`localhost:1521/FREEPDB1`、hr)が起動していること(`cd server && DBFAQ_CONFIG=../config.yaml uv run python scripts/check_oracle.py` が `8`(※P202 F010(CR-004)により 7 から変更))。
* テスト実行環境の構成は P003 §7(ADR-004)に従い、compose の web(`http://localhost:8088`)の同一オリジンに対して実行する。

## 【使用するテストデータ】

* A01〜A06、A08〜A10 と同じ。

## 【事前準備】

* `e2e/scripts/run-suite.sh` を作る(新規): `reset-and-up.sh` → A01・A02(playwright)→ A03(api の作り直しを含む)→ A04(スクリプト)→ A05(スクリプト + playwright)→ A08(スクリプト)→ A06(スクリプト)を順に実行し(※CR-004により A02 の後に A09(playwright)を追加。※CR-005により A09 の後に A10(playwright)を追加。※CR-001により A08 を追加。A08 も読み取りのみであることを A06 のチェックサムで確かめるため A06 の前に置く)、各テストの PASS/FAIL を 1 行ずつ出力する。

## 【実行手順】

1. `OUT=$(mktemp -d)` で一時ディレクトリを作る。
2. `bash e2e/scripts/run-suite.sh > $OUT/run1.txt`
3. 続けて `bash e2e/scripts/run-suite.sh > $OUT/run2.txt`
4. `diff $OUT/run1.txt $OUT/run2.txt` で PASS/FAIL の行が一致する。

※P011矛盾点#4にもとづき出力先を統一

## 【実行コマンド】

* 上記 1〜4。

## 【期待結果】

* 2 回の結果が一致する(両方とも全 PASS であることが望ましいが、本テストの合否は「一致すること」で判定する)。

## 【合否判定基準】

* 一致すれば PASS。2 回目だけ失敗するテストがあれば FAIL(テスト側の欠陥として扱う。`SKILL.md` 共通指示)。

## 【失敗時に記録する内容】

* `docs/test-records/YYYYMMDD-HHMM-test-record.md`(`TEMPLATE-test-record.md` の共通形式)に、テスト ID、実行コマンド、失敗したテスト・手順、期待値と実際の値、エラーメッセージ、Playwright の失敗時スクリーンショット・トレースのパス(`e2e/test-results/`)を残す。
* 2 回の出力の差分。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`、`deploy/`、`compose.yaml`)を修正しない。
* 既存のテストコードを、失敗を回避する目的で書き換えない(本タスクの指示に従ってテストを新規作成することは改ざんに当たらない)。
* 失敗したテストをスキップしない。期待値を変更して成功扱いにしない。
* 同じ失敗に対して場当たり的な再テストを繰り返さない。
* 修正が必要な場合は P202(修正計画)以降に引き渡す。

## 【次タスクへ進む条件】

* 記録して A07 を `[x]` にしたら P201 の判定に進む。

## 重要:

* アプリケーションコードを修正しないでください。
* テスト失敗時に、その場で修正して再テストしないでください。
* テスト失敗時は、失敗内容をテスト記録に残してください。
* このテストタスクの結果を記録したら、Reviewer Loopの停止条件に該当しない限り、次のテストタスクに自動的に進んでください。1テストタスクごとに人間の指示を待つ必要はありません。
