あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F006

## 【対応する失敗テスト】T08(所見)

* T08 は PASS。`docs/P201-review-report.md` §5 の所見(Oracle に届かないとき refresh が約 90 秒待つ)への対応。

## 【障害記録】

* 記録: `docs/test-records/20260923-0315-test-record.md` の T08(97.57 秒)。
* 原因区分: アプリケーションコードの欠陥(の疑い)。python-oracledb の非同期プールの既定 `getmode` は WAIT で、接続を作れない間 `acquire` が戻らない。P001 §8.2 は「Oracle に接続できなくても…再読み込みだけがエラーになる」ことを求めており、90 秒待たせるのは意図に反する。

## 【参照ファイル】

* `server/src/dbfaq_mcp/db.py`、`docs/P003-backend-spec.md` §3.1

## 【調査方針】

* 最小再現: port=1 の設定で `Database.run_readonly` を呼び、戻るまでの時間を測る(修正前)。
* python-oracledb の `create_pool_async` の `getmode`・`wait_timeout` の挙動を確認する。

## 【修正方針】

* `create_pool_async` に `getmode=oracledb.POOL_GETMODE_TIMEDWAIT`、`wait_timeout=connect_timeout_sec * 1000` を渡す。取得できなかった場合のエラー(`DPY-4005` 等)は ORACLE_ERROR として返る(既存の変換で扱える)。可能なら、接続できない原因(接続拒否など)がメッセージに出るとよい。
* 単体テスト(`tests/unit/mcp/test_db.py`)に、プール作成時の引数(getmode・wait_timeout)の確認を追加する。
* `docs/P003-backend-spec.md` §3.1 のプール作成の記述に getmode・wait_timeout を追記する(実装の明確化)。

## 【試行錯誤してよい範囲】

* `server/src/dbfaq_mcp/db.py`、`server/tests/unit/mcp/test_db.py`。

## 【修正成功時に更新するdocs】

* `docs/P003-backend-spec.md` §3.1

## 【ロールバック条件】

* T01〜T09 のいずれかが失敗するようになった場合、または待ち時間が改善しない場合は変更を戻し、未解決に記録する。

## 【検証コマンド】

* `cd server && uv run pytest tests/unit -q && uv run pytest tests/integration -v`

## 【完了条件】

* 単体・結合テストがすべて合格し、T08 の所要時間が connect_timeout_sec(3 秒)の数倍程度(目安 30 秒以内)に短縮される。

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

* 最小再現(修正前): port=1(待ち受けなし)に対して `create_pool_async(...).acquire()` → 20 秒待っても戻らない。`getmode=POOL_GETMODE_TIMEDWAIT, wait_timeout=3000` にすると 3.0 秒で `DPY-4005: timed out waiting for the connection pool to return a connection`。
* 変更: `server/src/dbfaq_mcp/db.py`(プール作成に getmode・wait_timeout を追加)、`server/tests/unit/mcp/test_db.py`(プール作成時の引数を確認)、`docs/P003-backend-spec.md` §3.1(明確化の注記)。
* 実行したテスト: 単体 131 passed。T08 は 97.57 秒 → 8.73 秒で PASS。
* 残課題: 接続拒否のとき利用者に見えるメッセージは `DPY-4005: timed out waiting for the connection pool ...` で、根本原因(接続拒否)が直接は分からない。運用上は health の赤表示とログで判断できるため許容する(P302 の既知の制約に記載する)。
