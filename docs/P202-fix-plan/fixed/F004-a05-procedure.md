あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F004

## 【対応する失敗テスト】A05

* A05(性能)

## 【障害記録】

* 記録: `docs/test-records/20260923-0320-test-record.md` の A05。測定値はすべて目標内。失敗は 2 つの手順の欠陥による: (1) `-g hr` が project 名 `chromium` にも一致し、大規模データ投入前に large のテストが実行された。(2) `docker compose cp` で入れた SQLite ファイルの所有者がホストの uid 1000 のままで、api(uid 10001)が書き込めず、HR への復帰(refresh)が 500 になった。
* 1 つの失敗テスト(A05)に 2 つの原因があるが、どちらもテスト手順(スクリプト)の欠陥なので 1 件の修正タスクにまとめる。
* 原因区分: テスト指示側の誤り(一部)。A05 の【事前準備】の `docker compose cp` 手順は、api イメージを非 root(uid 10001)で動かす決定(`docs/P007-impl-direction/U006-deploy.md` U006-T1、ADR-012)と整合しておらず、コピー後に所有者を変える手順が欠けている。カバレッジは失われない(測定内容は変えない)。

## 【参照ファイル】

* `e2e/scripts/run-suite.sh`、`e2e/scripts/a05-load-large.sh`、`docs/P009-acceptance-direction/A05-performance.md`

## 【調査方針】

* `docker compose exec api ls -ln /data` で所有者を確認する(確認済み: 1000:1000)。

## 【修正方針】

* `run-suite.sh` と A05 の【実行コマンド】の `-g hr`・`-g large` を `-g "hr:"`・`-g "large:"` にする(テスト名の接頭辞に一致させる)。
* `a05-load-large.sh` のコピー後の処理を `docker compose run --rm --no-deps --user root --entrypoint sh api -c 'chown 10001:10001 /data/dbfaq.sqlite3 && rm -f /data/dbfaq.sqlite3-wal /data/dbfaq.sqlite3-shm'` にする。
* `docs/P009-acceptance-direction/A05-performance.md` の【事前準備】【実行コマンド】を同じ内容に訂正する(訂正箇所に注記)。

## 【試行錯誤してよい範囲】

* `e2e/scripts/` と `docs/P009-acceptance-direction/A05-performance.md`。

## 【修正成功時に更新するdocs】

* `docs/P009-acceptance-direction/A05-performance.md`

## 【ロールバック条件】

* 該当なし(アプリのソースコード変更を伴わない)。

## 【検証コマンド】

* A05 の【実行コマンド】を順に実行する。

## 【完了条件】

* A05 が合格し、最後に HR(7 表)に戻っている。

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

* 変更: `e2e/scripts/run-suite.sh`(`-g "hr:"`・`-g "large:"`)、`e2e/scripts/a05-load-large.sh`(コピー後に root で `chown 10001:10001` と WAL/SHM の削除)、`docs/P009-acceptance-direction/A05-performance.md`(【事前準備】【実行コマンド】を訂正。注記あり)。
* 訂正の根拠: api イメージは非 root(uid 10001)で動く(U006-T1、ADR-012)。測定内容・目標値は変えていない。
* 結果の確認は P205 で行う。
