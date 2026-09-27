あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F008(CR-002)

## 【対応する失敗テスト】T08(PASS だが所見あり)

## 【障害記録】

* T08 が 132 秒かかる。最小再現で、Oracle のリスナーに届かない(接続拒否)間は python-oracledb 26.0.0 の非同期プールの `close(force=True)` が約 2 分戻らないことを確認した(`docs/test-records/20260927-0233-test-record.md`、`docs/ArchitectureHandbook.md` §9)。
* 影響: backend の lifespan の終了(`OracleClient.close()`)が止まり、Oracle に届かない間の api の停止・再起動が遅れる(docker の停止猶予 10 秒を使い切って強制終了になる)。CR-002 前は MCP の子プロセスごと終了していたため表に出なかった(CR-002 による退行)。
* 原因区分: アプリケーションコードの欠陥(ドライバの挙動への対処が無い)

## 【参照ファイル】

* `server/src/dbfaq_api/oracle/db.py`(`Database.close`)、`docs/P003-backend-spec.md` §3.1

## 【調査方針】

* 最小再現は記録済み。close を待つ時間に上限を設ける。

## 【修正方針】

* `Database.close` で `asyncio.wait_for(pool.close(force=True), timeout=connect_timeout_sec)` とし、時間切れ(`TimeoutError`)なら警告ログを出してプールの参照を捨てる(プロセスの終了時なので、閉じ切らない接続は OS が片付ける)。
* `docs/P003-backend-spec.md` §3.1 に、close の待ち時間の上限と理由を ★ACCEPTED★ で追記する(取り消しは P003 §3.8 で避けた方法だが、ここはプールを捨てる場面なので接続の状態が壊れても影響しない)。

## 【試行錯誤してよい範囲】

* `server/src/dbfaq_api/oracle/db.py`、`server/tests/unit/oracle/test_db.py`

## 【修正成功時に更新するdocs】

* `docs/P003-backend-spec.md` §3.1、`docs/ArchitectureHandbook.md` §9(対処を追記)、`docs/P202-fix-plan/P202-fix-resolved.md`

## 【ロールバック条件】

* 単体テストを 3 回自己修正しても合格しない場合、変更を元に戻して `P202-fix-unresolved.md` に記録する。

## 【検証コマンド】

* `cd server && uv run pytest tests/unit/oracle/test_db.py -q`
* `cd server && DBFAQ_CONFIG=../config.yaml uv run pytest tests/integration/test_t08_oracle_unreachable.py -q --durations=1`(132 秒 → 15 秒程度になる)

## 【完了条件】

* 単体テストが合格し、T08 の所要時間が短くなる。

## 【対応結果】(P203、2026-09-27)

* `Database.close` を `asyncio.wait_for(pool.close(force=True), connect_timeout_sec)` にし、時間切れなら警告ログを出してプールを捨てる。単体テスト `test_close_gives_up_after_connect_timeout` を追加(unit 128 passed)。
* 最小再現(port 1 の `OracleClient`)で close が 123.87 秒 → 3.0 秒。T08 は 131.97 秒 → 9.22 秒。compose で接続拒否の設定(`DBFAQ_ORACLE_PORT=1`)の api の `docker compose stop` が 1 秒で終わり、lifespan の終了ログ(`Application shutdown complete.`)が出ることを確認。初回で解決。
