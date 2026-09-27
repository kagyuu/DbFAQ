あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F007(CR-002)

## 【対応する失敗テスト】A03

## 【障害記録】

* A03 手順 1: Oracle の接続先のホスト名を解決できないとき(`DBFAQ_ORACLE_HOST=oracle-unreachable.invalid`)、`/api/health` が 500 `INTERNAL_ERROR` を返す(期待: 200、status=degraded)。記録: `docs/test-records/20260927-0238-test-record.md`。
* 原因: python-oracledb 26.0.0 は、ホスト名の解決に失敗すると `oracledb.Error` ではなく `socket.gaierror`(`OSError` のサブクラス)をそのまま送出する。`dbfaq_api/oracle/db.py` の `run_readonly` は `oracledb.Error` だけを `OracleFailure` に変換するため、例外が API まで抜けて 500 になる。`/api/health` も `OracleFailure` だけを捕まえている。refresh・rows も同じ原因で 502 ではなく 500 になる(P002 §3.1「Oracle に届かない → ORACLE_ERROR」に反する)。
* CR-002 前は MCP サーバがあらゆる例外をツールエラーに包んでいたため表に出なかった(CR-002 による退行)。
* 原因区分: アプリケーションコードの欠陥

## 【参照ファイル】

* `server/src/dbfaq_api/oracle/db.py`、`server/src/dbfaq_api/oracle/errors.py`、`server/src/dbfaq_api/services.py`
* `docs/P003-backend-spec.md` §3.2、§4.3(health は常に 200)、`docs/P002-frontend-spec.md` §3.1・§3.7

## 【調査方針】

* python-oracledb が `oracledb.Error` 以外で送出しうる接続関係の例外は `OSError` 系(`socket.gaierror` など)。`TimeoutError` も `OSError` のサブクラスなので区別する。

## 【修正方針】

* `errors.py` に `from_os_error(exc: OSError, secret) -> OracleFailure` を加える。`TimeoutError` → `ORACLE_TIMEOUT`、それ以外 → `ORACLE_ERROR`(ora_code なし、message は「Oracle に接続できません: {例外の文字列}」をパスワードでマスクしたもの)。
* `db.py` の `run_readonly` で `OSError` も捕まえて `from_oracle_error` と同じ位置で変換する。
* `services.py` の health は、`OracleFailure` 以外の想定外の例外も捕まえてログに出し、oracle.status=error・message「内部エラーが発生しました」として 200 を返す(P003 §4.3「常に 200」を守る)。
* `docs/P003-backend-spec.md` §3.2 の表に `OSError` の変換を、§4.3 の health に想定外の例外の扱いを追記する。

## 【試行錯誤してよい範囲】

* 上記 3 ファイルと、その単体テスト(`tests/unit/oracle/test_db.py`・`test_errors.py`、`tests/unit/api/test_api.py`)。

## 【修正成功時に更新するdocs】

* `docs/P003-backend-spec.md` §3.2・§4.3、`docs/P202-fix-plan/P202-fix-resolved.md`

## 【ロールバック条件】

* 単体テストを 3 回自己修正しても合格しない場合、変更を元に戻して `P202-fix-unresolved.md` に記録する。

## 【検証コマンド】

* `cd server && uv run pytest tests/unit -q`
* `DBFAQ_ORACLE_HOST=oracle-unreachable.invalid docker compose up -d --build --no-deps --force-recreate api` → `curl -s localhost:8088/api/health`(200、degraded)、`curl -s -X POST localhost:8088/api/schema/refresh`(502 `ORACLE_ERROR`)→ `docker compose up -d --no-deps --force-recreate api`

## 【完了条件】

* 単体テストが合格し、上記の手動確認で health が 200・degraded、refresh が 502 になる。A03 は P205 で再実行する。

## 【対応結果】(P203、2026-09-27)

* `errors.py` に `from_os_error` を追加(`TimeoutError` → `ORACLE_TIMEOUT`、その他の `OSError` → `ORACLE_ERROR`、ora_code なし、パスワードをマスク)。`db.py` の `run_readonly` で `OSError` を変換。`services.py` の health で想定外の例外も捕まえて 200・degraded を返す。
* 単体テスト 4 件追加(`test_os_error`・`test_os_error_masks_secret`・`test_os_timeout`・`test_os_error_is_converted`・`test_health_unexpected_error_is_still_200`)。unit 128 passed。
* 手動確認: `DBFAQ_ORACLE_HOST=oracle-unreachable.invalid` の api で `/api/health` → 200・degraded・message「Oracle に接続できません: [Errno -2] Name or service not known」、refresh → 502 `ORACLE_ERROR`。初回で解決。
