# CR.md

変更要求(Change Request)の状態の台帳。CR 本文は `docs/P901-cr-direction/CR-NNN.md`(変更要求)と `docs/P903-cr-records/CR-NNN.md`(対処の記録)にある。完了した行も削除しない。

## CR 一覧

| CR | タイトル | 状態 | 優先度 | 変更要求 | 対処記録 |
| --- | --- | --- | --- | --- | --- |
| CR-001 | 出荷影響「要対応」2 件(ノードのドラッグ、同時 10 名)のテストを追加する | 完了 | 高 | [リンク](./P901-cr-direction/CR-001.md) | [リンク](./P903-cr-records/CR-001.md) |
| CR-002 | MCP サーバを廃止し、Oracle へのアクセスを backend(FastAPI)に統合する | 完了 | 中 | [リンク](./P901-cr-direction/CR-002.md) | [リンク](./P903-cr-records/CR-002.md) |
| CR-003 | 共通部品パッケージ dbfaq_common を dbfaq_api に統合する | 完了 | 低 | [リンク](./P901-cr-direction/CR-003.md) | [リンク](./P903-cr-records/CR-003.md) |
| CR-004 | テーブル詳細画面に Query タブを追加し、任意の SELECT 文を作成・実行できるようにする(画面は 500 行まで、CSV で全行) | 完了 | 中 | [リンク](./P901-cr-direction/CR-004.md) | [リンク](./P903-cr-records/CR-004.md) |
| CR-005 | Query の保存・復元(テーブルごと)と、PDB 画面(ドラム缶アイコン)・PDB の Query・運用 Query のひな型 | 完了 | 中 | [リンク](./P901-cr-direction/CR-005.md) | [リンク](./P903-cr-records/CR-005.md) |
| CR-006 | 読み取り専用ユーザー dbfaq_ro を前提に、PDB 情報・ひな型を対象スキーマ基準にする。README に dbfaq_ro の作成手順を載せる | 完了 | 中 | [リンク](./P901-cr-direction/CR-006.md) | [リンク](./P903-cr-records/CR-006.md) |
| CR-007 | 自然言語の要求から LLM(Ollama)で SELECT 文を作る。LLM の稼働状況をヘッダに表示する | 完了 | 中 | [リンク](./P901-cr-direction/CR-007.md) | [リンク](./P903-cr-records/CR-007.md) |
| CR-008 | LLM で SQL を作るときの、LLM へのリクエストと LLM のリプライを表示するボタンを追加する | 完了 | 低 | [リンク](./P901-cr-direction/CR-008.md) | [リンク](./P903-cr-records/CR-008.md) |
| CR-009 | LLM で SQL を作る機能には性能を求めない。時間がかかっても正しく SQL が作られることだけを検証する | 完了 | 低 | [リンク](./P901-cr-direction/CR-009.md) | [リンク](./P903-cr-records/CR-009.md) |
| CR-010 | Query タブにサブタブ(JOIN・保存済み Query・自然言語で SQL を作成)を設け、SQL の入力欄・実行・CSV・結果は共通領域として常に表示する | 完了 | 中 | [リンク](./P901-cr-direction/CR-010.md) | [リンク](./P903-cr-records/CR-010.md) |
| CR-011 | LLM で作成した Query を保存するとき、要求の先頭 20 文字を名前、要求の全文を説明の既定値にする | 完了 | 低 | [リンク](./P901-cr-direction/CR-011.md) | [リンク](./P903-cr-records/CR-011.md) |

状態: 未対応 / 対応中 / 反映確認中 / 完了 / 却下。優先度: 高 / 中 / 低 / N/A(却下のみ)。
