# P201 実装横断レビュー

## 最新の判定(CR-004 の 2 回目。P205 の再実施による)

* 実行回数: CR-004 の 2 回目(1 回目の差し戻し → P202〜P205(F009・F010)の後)
* P008: T01〜T04・T06〜T13 PASS(T05 は廃止)。単体 + 結合の pytest は 2 回続けて 225 passed
* P009: A01〜A06・A08・A09 PASS(スイートを 2 回続けて実行し出力が同一。A07 PASS)
* 記録: `docs/test-records/20261004-2110-test-record.md`

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T01〜T04・T06〜T13 | 結合(P008) | PASS | docs/test-records/20261004-2110-test-record.md |
| A01〜A09 | 受け入れ結合(P009) | PASS | 同上 |

**判定: 全件 PASS。Closing(P301〜)へ進む。**

---

## CR-004 の 1 回目の判定

* 実行回数: CR-004 の 1 回目
* P008: T02〜T04・T07・T09〜T11・T13 PASS、**T01・T06・T08・T12 FAIL**(`docs/test-records/20261004-1430-test-record.md`。pytest は 2 回とも 222 passed / 3 failed)
* P009: A02・A04・A08・A09 PASS、A07 PASS(2 回の結果が一致)、**A01・A03・A05 FAIL、A06 FAIL(偽の PASS)、RESET FAIL**(`docs/test-records/20261004-1440-test-record.md`)

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T01 | 結合(P008) | FAIL(環境) | docs/test-records/20261004-1430-test-record.md |
| T02・T03・T04・T07・T09・T10・T11 | 結合(P008) | PASS | 同上 |
| T06・T08 | 結合(P008) | FAIL(環境) | 同上 |
| T12 | 結合(P008) | FAIL(環境。table_count の 1 項目) | 同上 |
| T13 | 結合(P008) | PASS | 同上 |
| A01・A03・A05 | 受け入れ結合(P009) | FAIL(環境) | docs/test-records/20261004-1440-test-record.md |
| A02・A04・A08・A09 | 受け入れ結合(P009) | PASS | 同上 |
| A06 | 受け入れ結合(P009) | FAIL(テストの欠陥。チェックサムを比べられていない) | 同上 |
| A07 | 受け入れ結合(P009) | PASS(2 回一致) | 同上 |

| # | 種別 | 内容 | 対応 |
|---|---|---|---|
| 1 | FAIL(テストの欠陥) | `hr_checksum.py` が LOB 列を持つ表で ORA-22835 になり、`reset-and-up.sh`・`a06-security.sh` はその失敗を検出せず、空のベースラインと空の現在値を「一致」と判定する(A06 手順 1 の偽の PASS) | P202 へ(F009) |
| 2 | FAIL(テストデータの変化) | 開発用 Oracle の HR に 2026-09-29 に表 `EMPLOYEE_FIGURE` が追加され、7 表・外部キー 10 本を期待する T01・T06・T08・T12・A01・A03・A05 が失敗する。アプリケーション(CR-004 を含む)の欠陥ではない | P202 へ(F010。直し方は人間の判断を要する) |

* CR-004 の変更点(Query タブ・API・SQL の検査・CSV・エラー位置・nginx)に関わるテスト(T03 の追加分、T13、A05 手順 3b、A06 手順 6、A09)はすべて PASS。

**判定: 失敗あり。P202(修正計画)へ差し戻す。**

---

## CR-003 の 1 回目の判定

* 実行回数: CR-003 の 1 回目
* P008: 単体 + T01〜T04・T06〜T09 を 2 回続けて 144 passed、T10〜T12 PASS(`docs/test-records/20260927-2358-test-record.md`)
* P009: A01〜A08 PASS(スイートを 2 回続けて実行し結果が同一。`docs/test-records/20260928-0001-test-record.md`)

**判定: 全件 PASS。Closing(P301〜)へ進む(P202〜P205 は不要)。**

---

## CR-002 の 2 回目の判定(P205 の再実施による)

* 実行回数: CR-002 の 2 回目(1 回目の差し戻し → P202〜P205(F007・F008)の後)
* P008: T01〜T04・T06〜T12 PASS(T05 は廃止)。単体 + 結合の pytest は 2 回続けて 144 passed
* P009: A01〜A08 PASS(スイートを 2 回続けて実行し結果が同一)
* 記録: `docs/test-records/20260927-0244-test-record.md`

**判定: 全件 PASS。Closing(P301〜)へ進む。**

---

## CR-002 の 1 回目の判定

* 実行回数: CR-002 の 1 回目(Refactor 経由のため CR ごとに数える)
* P008: T01〜T04・T06〜T12 PASS(T05 は CR-002 で廃止)。pytest の結合テストは 2 回続けて同じ結果(`docs/test-records/20260927-0233-test-record.md`)
* P009: A01・A02・A04〜A06・A08 PASS、**A03 FAIL**、A07 未実施(`docs/test-records/20260927-0238-test-record.md`)

| # | 種別 | 内容 | 対応 |
|---|---|---|---|
| 1 | FAIL(A03 手順 1) | ホスト名を解決できないとき `/api/health` が 500。python-oracledb が `socket.gaierror`(`OSError`)をそのまま送出し、`run_readonly` が `OracleFailure` に変換しない。refresh・rows も同じ原因で 502 でなく 500 になる。health は P002 §3.7 の「常に 200」を満たさない | P202 へ(F007) |
| 2 | 所見(T08) | Oracle のリスナーに届かない間、接続プールの `close` が約 2 分戻らず、api の停止・再起動が止まる(python-oracledb の挙動。`docs/ArchitectureHandbook.md` §9) | P202 へ(F008) |

**判定: 失敗あり。P202(修正計画)へ差し戻す。**

---

# CR-002 より前の判定(履歴)

## 2 回目の判定(P205 の再実施による)

* 実行回数: 2 回目(1 回目の差し戻し → P202〜P205 の後)
* P008: T01〜T12 すべて PASS(T01〜T09 は 2 回続けて 17 passed)
* P009: A01〜A07 すべて PASS(スイートを 2 回続けて実行し結果が同一)
* 所見だった T08 の待ち時間は F006 で解消(97.6 秒 → 約 9 秒)

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T01〜T04 | 結合(P008) | PASS | docs/test-records/20260923-0350-test-record.md |
| T05 | 結合(P008) | PASS | 同上 |
| T06〜T12 | 結合(P008) | PASS | 同上 |
| A01〜A06 | 受け入れ結合(P009) | PASS | 同上 |
| A07 | 受け入れ結合(P009) | PASS | 同上 |

**判定: 全件 PASS。Closing(P301〜)へ進む。**

---

# 1 回目の判定(履歴)

## 1. 実行回数

* 1 回目(通常フロー)

## 2. 前提の確認

* `docs/P008-test-direction.md` の T01〜T12 はすべて `[x]`(P103 で実行済み)。
* `docs/P009-acceptance-direction.md` の A01〜A06 を本フェーズで新規作成・実行した。A07 は未実行(下記)。
* テスト実行環境は ADR-004(同一オリジン)に従い、compose の web(`http://localhost:8088`)に対して実行した。

## 3. 集計

| テストID | 種別 | 結果 | 記録 |
|---|---|---|---|
| T01 | 結合(P008) | PASS | docs/test-records/20260923-0315-test-record.md |
| T02 | 結合(P008) | PASS | 同上 |
| T03 | 結合(P008) | PASS | 同上 |
| T04 | 結合(P008) | PASS | 同上 |
| T05 | 結合(P008) | FAIL | 同上 |
| T06 | 結合(P008) | PASS | 同上 |
| T07 | 結合(P008) | PASS | 同上 |
| T08 | 結合(P008) | PASS(所見あり) | 同上 |
| T09 | 結合(P008) | PASS | 同上 |
| T10 | 結合(P008) | PASS | 同上 |
| T11 | 結合(P008) | PASS | 同上 |
| T12 | 結合(P008) | PASS | 同上 |
| A01 | 受け入れ結合(P009) | FAIL | docs/test-records/20260923-0320-test-record.md |
| A02 | 受け入れ結合(P009) | FAIL | 同上 |
| A03 | 受け入れ結合(P009) | PASS | 同上 |
| A04 | 受け入れ結合(P009) | PASS | 同上 |
| A05 | 受け入れ結合(P009) | FAIL | 同上 |
| A06 | 受け入れ結合(P009) | FAIL | 同上 |
| A07 | 受け入れ結合(P009) | NOT RUN | 同上 |

## 4. PASS 以外の一覧

| テストID | 結果 | 原因の見立て |
|---|---|---|
| T05 | FAIL | アプリの不足: MCP サーバ(`dbfaq_mcp`)が stderr に JSON のログを 1 行も出していない(P003 §4.5) |
| A01 | FAIL | テストコードの欠陥: 「テーブル 7 / 関連 10」のロケータが通知文言にも部分一致 |
| A02 | FAIL | テストコードの欠陥: 行の特定が大文字小文字を区別しない部分一致で、コメントに一致した別の行も拾う |
| A05 | FAIL | テスト手順の欠陥: `-g hr` が project 名 `chromium` に一致/コピーした SQLite の所有者が api の実行ユーザーと異なり書き込めない。測定値自体はすべて目標内 |
| A06 | FAIL | テストスクリプトの欠陥: ホストの Python 3.10 で f-string 内のバックスラッシュが構文エラー。その他の確認項目はすべて OK |
| A07 | NOT RUN | A01〜A06 の修正後に実行する |

## 5. 所見(PASS だが対応を推奨するもの)

* T08: Oracle が待ち受けていないポートを設定した場合、refresh が即座に失敗せず約 90 秒(`mcp_call_timeout_sec`)待ってから 504 になった。python-oracledb の接続プールが接続を作れないまま `acquire` で待ち続けている疑いがある。P001 §8.2(Oracle に接続できないときは再読み込みがエラーになる)は満たすが、利用者を 90 秒待たせ、その間ほかの呼び出しも滞る。P202 で改善を計画する。

## 6. 判定

PASS 以外が 6 件(FAIL 5、NOT RUN 1)。P202(修正計画)へ進む。

## 実行履歴

| 回 | 日時 | 結果 |
|---|---|---|
| 1 | 2026-09-23 03:24 | FAIL 5(T05、A01、A02、A05、A06)、NOT RUN 1(A07)、所見 1(T08) |
| 2 | 2026-09-23 03:50 | 全件 PASS(P205 の再実施) |
| 3 | 2026-09-24 23:52 | CR-001: A01(ドラッグの手順 8・9 を追加)〜A06・A08(新規)を 2 回実行し全件 PASS、A07 PASS。T01〜T12 はアプリケーションコードを変えていないため B003 の結果を引き継ぐ。P202 へ引き渡す失敗なし(`docs/test-records/20260924-2352-test-record.md`) |
