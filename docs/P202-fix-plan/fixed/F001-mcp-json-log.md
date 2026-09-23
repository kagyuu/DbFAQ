あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F001

## 【対応する失敗テスト】T05

* T05(MCP: stdio の標準出力)

## 【障害記録】

* 記録: `docs/test-records/20260923-0315-test-record.md` の T05。stdout は JSON-RPC のみで合格。stderr に dbfaq_mcp 自身の JSON ログが 1 行も無い(FastMCP の非 JSON の起動行のみ)。
* 原因区分: アプリケーションコードの欠陥(P003 §4.5「MCP サーバは標準エラー出力へ JSON のログを出す」を満たしていない。起動・終了時にログを出していない)

## 【参照ファイル】

* `server/src/dbfaq_mcp/__main__.py`、`server/src/dbfaq_common/logging.py`、`docs/P003-backend-spec.md` §4.5

## 【調査方針】

* `__main__.py` の起動処理で logger を使っていないことを確認する。

## 【修正方針】

* `__main__.py` で `setup_logging` の後に INFO で「MCP server starting」(対象スキーマ、DSN のホスト:ポート/サービス名。パスワードは出さない)を出し、`run()` の終了後に「MCP server stopped」を出す。
* FastMCP 自身の非 JSON 出力は変更しない(T05 は非 JSON 行を許容している)。

## 【試行錯誤してよい範囲】

* `server/src/dbfaq_mcp/__main__.py` のみ。

## 【修正成功時に更新するdocs】

* なし(仕様どおりに実装を直す)。

## 【ロールバック条件】

* T05 が合格しない、または T01〜T04 が失敗するようになった場合は変更を戻す。

## 【検証コマンド】

* `cd server && uv run pytest tests/unit -q && uv run pytest tests/integration/test_t05_stdio.py tests/integration/test_t01_mcp_snapshot.py -v`

## 【完了条件】

* 上記がすべて合格。

## 重要:

* 作業開始前に現在の変更状態を確認してください(本リポジトリは作業ツリーが未コミットのため、P203 の開始時にリポジトリ外へ zip で退避済みのバックアップを使う)。
* 必要な範囲でソースコード変更を試して構いません。
* 修正に成功した場合は、関連する docs/* も必要に応じて更新してください。
* 修正しきれなかった場合は、試行錯誤で変更した未完了のソースコードを元の状態に戻してください。
* 原因が仕様矛盾の場合は、コードで無理に解決せず、人間に判断を促す内容を `docs/P202-fix-plan/P202-fix-unresolved.md` に記録してください。

## 完了条件:

* 全モジュールビルド成功
* すべての Unit Test 成功
* すべての結合テスト成功(P008・P009)
* `docs/P202-fix-plan/P202-fix-resolved.md` に全修正結果が記録されている
* 未解決障害がない、または `docs/P202-fix-plan/P202-fix-unresolved.md` に未解決なしと明記されている

## 未解決時の記録方法:

* 修正しきれなかった障害が1件でもある場合、`TEMPLATE-P202-fix-unresolved.md` の構成に従って `docs/P202-fix-plan/P202-fix-unresolved.md` を作成または更新する。

## 修正内容の詳細(P203、2026-09-23)

* 変更: `server/src/dbfaq_mcp/__main__.py` — `setup_logging` の後に INFO「MCP server starting」(schema、host、port、service_name。パスワードは出さない)、`run()` の終了時に「MCP server stopped」を JSON で stderr に出す。
* 作業前の状態: 作業ツリーは未コミット。バックアップは zip コマンドが無かったため F001 の変更直後に tar で取得した(`scratchpad/DbFAQ-20260923032547.tar.gz`、リポジトリ外)。F001 の変更は上記 2 か所の追加のみで、差分から元に戻せる。
* 実行したテスト: `uv run pytest tests/unit -q`(131 passed)、`uv run pytest tests/integration/test_t05_stdio.py tests/integration/test_t01_mcp_snapshot.py -q`(3 passed)。
