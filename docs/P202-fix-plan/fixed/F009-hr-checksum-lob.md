あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F009(※CR-004 の P201 1 回目)

## 【対応する失敗テスト】A06(手順 1)、RESET(`reset-and-up.sh`)

## 【障害記録】

* 記録: `docs/test-records/20261004-1440-test-record.md` の RESET・A06。
* 現象: `server/scripts/hr_checksum.py` が、LOB 列を持つ表(HR に追加された `EMPLOYEE_FIGURE` の BLOB)で全列を `||` で連結して `ORA_HASH` にかけ、`ORA-22835` で失敗する。`reset-and-up.sh` は空の `e2e/.baseline-checksum.json` を残し、`a06-security.sh` は失敗した現在値(空)と空のベースラインを「一致」と判定した(偽の PASS)。
* 原因区分: テスト側の欠陥(テストスクリプト)。アプリケーションの欠陥ではない。カバレッジは失われない(修正で回復する)。

## 【修正内容】

* `server/scripts/hr_checksum.py`: LOB 列(BLOB・CLOB・NCLOB)を持つ表は、全行を ROWID 順に取得して Python の SHA-256 で計算する(`"checksum": "sha256:..."`)。LOB の無い表は従来どおり `SUM(ORA_HASH(...))`。
* `e2e/scripts/reset-and-up.sh`: 一時ファイルに書いて成功したときだけ `e2e/.baseline-checksum.json` に移す(失敗したら古い・空のベースラインを残さない)。
* `e2e/scripts/a06-security.sh`: 現在値の取得に失敗した・空のとき、ベースラインが無い・空のときは FAIL にする。

## 【修正禁止事項】

* アプリケーションコード(`server/src/`、`client/src/`)を変えない。期待値を変えない。

## 【確認】(2026-10-04 実施)

* `hr_checksum.py` を 2 回続けて実行し、8 表すべての値が出て一致した(`EMPLOYEE_FIGURE` は 214 行、`sha256:...`)。
* `reset-and-up.sh` が終了コード 0 で 620 バイトのベースラインを作り、続く `a06-security.sh` が「HR のチェックサムがベースラインと一致」「A06 PASS」。
* ベースラインを退避して `a06-security.sh` を実行すると「FAIL ベースラインのチェックサム(e2e/.baseline-checksum.json)が無い」「A06 FAIL」になる(失敗を検出する)。

## 【状態】

* 解決(P203、2026-10-04)
