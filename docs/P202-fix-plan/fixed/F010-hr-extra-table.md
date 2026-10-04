あなたはReviewer Loop(修正担当)です。以下の1修正タスクを実施してください。

# 【修正タスクID】F010(※CR-004 の P201 1 回目)

## 【対応する失敗テスト】T01・T06・T08・T12(P008)、A01・A03・A05(P009)

## 【障害記録】

* 記録: `docs/test-records/20261004-1430-test-record.md`(T01・T06・T08・T12)、`docs/test-records/20261004-1440-test-record.md`(A01・A03・A05)。
* 現象: 開発用 Oracle の HR に、2026-09-29 15:11:52 に表 `EMPLOYEE_FIGURE`(BLOB 列、外部キー `FK_EMPLOYEE_FIGURE_EMP` → EMPLOYEES、214 行)が追加され、HR が 8 表・外部キー 11 本になった。これらのテストは P006 §3.2 のベースライン(HR サンプルスキーマのインストール直後: 7 表・外部キー 10 本)を期待値にしているため失敗する。
* 原因区分: テストデータ(HR)の状態の変化。アプリケーション(CR-004 を含む)の欠陥ではない。refresh・ER 図・詳細は 8 表目も正しく扱っている。

## 【修正の選択肢】(人間が選ぶ。`docs/.stop-report.md` と同じ)

| 案 | 内容 | 利点 | 欠点 |
|---|---|---|---|
| A | 人間が `EMPLOYEE_FIGURE` を HR から外す(別のスキーマへ移す・削除する) | テスト・期待値を変えずに元のベースラインに戻る | 表を HR で使い続けたい場合は不可。テストは HR を変更しない方針なので、Agent は実施しない |
| B | 8 表(外部キー 11 本)を新しいベースラインとし、P006 §3.2 と T01・T06・T08・T12・A01・A03・A05 の期待値を改める | 現状の HR のままで全件 PASS になる | HR がまた変わると同じ失敗になる。期待値の変更なので人間の承認が要る |
| C | テストを「HR サンプルの 7 表と 10 本の外部キーが含まれていること」の確認に変え、表の総数は API が返す値と画面の表示が一致することで確かめる | HR に表が増えても壊れない | 予期しない表の増加はテストで検出しなくなる。テスト定義(P006・P008・P009)の変更が要る |

## 【人間の判断】(2026-10-04)

* 依頼者が **案 B(8 表を新しいベースラインにする)** を選んだ。

## 【修正内容】(P203)

* テストの期待値を 2026-10-04 の実測値に改めた: 8 表(`EMPLOYEE_FIGURE` を含む)、列 38、主キー 8、一意制約 1、外部キー 11、インデックス 20。`check_oracle.py` の出力は `8`。
  * `server/tests/integration/test_t01_oracle_snapshot.py`(表の一覧と各件数)、`test_t06_api_refresh.py`(`table_count`・`relation_count`・表の数・関連の数・EMPLOYEES の `referenced_by` に `FK_EMPLOYEE_FIGURE_EMP`)、`test_t08_oracle_unreachable.py`(表の数)
  * `e2e/tests/a01-er-diagram.spec.ts`(通知とツールバーの「テーブル 8 / 関連 11」、ノード 8、エッジ 11)、`a03-oracle-down.spec.ts`・`a05-performance.spec.ts`(ノード 8)、`e2e/scripts/a05-restore-hr.sh`(`table_count` 8)
* 文書: `docs/P006-test-plan.md` §2.1・§3.2(ベースラインの定義と期待値)、P008 の T01・T06・T08・T12 と各テストの前提(`check_oracle.py` が `8`)、P009 の A01・A03・A05・A06 と各テストの前提、`docs/P101-impl-context.md` §5、`docs/ArchitectureHandbook.md` §7・§9。各箇所に「※P202 F010(CR-004)」の注記を付けた。
* 変えていないもの: アプリケーションコード。T02・T07(行数 7 は EMPLOYEES の 3 ページ目の行数)、A02(EMPLOYEES のインデックス 6)、A08(サンプルの 7 表から選ぶ。8 表目を選ばなくても負荷の観点は同じ)。`docs/P001-requirement.md` §2 の「HR には 7 テーブル…確認済み(2026-09-23、Oracle 23.26)」は日付付きの事実の記録であり要件ではないため、変えていない(テストのベースラインの正は P006 §3.2)。

## 【追記】テスト用データベースの前提の明文化(2026-10-04、依頼者の指示)

* 依頼者が前提を次のとおり示した: ① Oracle 配布の HR サンプルスキーマ(https://github.com/oracle/db-sample-schemas/releases/latest)、② HR に LOB 列が無いため `EMPLOYEE_FIGURE` を追加する(DDL を依頼者が提示)。
* DDL を `server/scripts/sql/hr_employee_figure.sql` に置き、`docs/P006-test-plan.md` §3.1・§3.2、`docs/P302-deliver.md` 8 章、`docs/ArchitectureHandbook.md` §7 に前提として書いた。
* 開発用 Oracle の `EMPLOYEE_FIGURE` は DDL と一致することを確認した(列 3・型・NOT NULL、`FIGURE_ID` が GENERATED ALWAYS の IDENTITY、主キー・外部キーの名前)。行は 214 行(各社員 2 行、BLOB はいずれも 420,605 バイト)だが、テストは行のデータに依存しない(`grep` で確認。T01・T06 は表・制約の名前と数だけを見る)ため、行のデータは前提に含めない。
* データの投入方法も依頼者が示した(DIRECTORY `PHOTO_DIR` を `/opt/oracle/oradata` に作り hr に READ を付与、`ai_model_512_01.png` を EMPLOYEE_ID 100〜206 に 1 行ずつ入れる PL/SQL)。`server/scripts/sql/hr_photo_dir.sql`・`hr_employee_figure_data.sql` に置いた。DB サーバの `/opt/oracle/oradata/ai_model_512_01.png` は 420,605 バイトで、開発用 Oracle の BLOB と同じ大きさ。214 行はこの PL/SQL を 2 回実行した結果と見られる。
* 投入の PL/SQL は、COMMIT を除いて実行し件数を確かめてからロールバックする方法で動作を確認した(107 行が増え、BLOB は 420,605 バイト、ロールバック後は 214 行のまま)。この確認で IDENTITY(`FIGURE_ID`)の値が 214 個(2 回分)進んだが、テストは `FIGURE_ID` の値に依存しない。
* アプリケーションコード・テストコードは変えていない。

## 【状態】

* 解決(P203、2026-10-04。P205 で確認)
