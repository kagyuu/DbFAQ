あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U005 — frontend-detail

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U005-T1 [テーブル詳細画面の枠とタブ](#u005-t1-テーブル詳細画面の枠とタブ) — `TableDetailPage`、URL の `tab`・`page`
- [x] U005-T2 [スキーマ情報タブ](#u005-t2-スキーマ情報タブ) — `SchemaTab`
- [x] U005-T3 [データタブ](#u005-t3-データタブ) — `DataTab`

---

## U005-T1: テーブル詳細画面の枠とタブ

### 【目的】

* SC-02 の見出し・タブ切替・URL との同期・存在しないテーブルの表示を作る。

### 【作成・編集対象ファイル】

* `client/src/pages/TableDetailPage.tsx`(U004-T1 のプレースホルダを置き換える)、`client/src/pages/urlState.ts`
* `client/src/pages/TableDetailPage.test.tsx`、`client/src/pages/urlState.test.ts`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1.2、§2.2.1、§2.2.4、§2.2.5

### 【実装内容】

* `urlState.ts`(純粋関数): `parseTab(v: string | null): "schema" | "data"`(不正・null は `schema`)、`parsePage(v: string | null): number`(整数でない・1 未満・`(page-1)*50 > 100000` は 1)。定数 `PAGE_SIZE = 50`。
* `TableDetailPage`: `useParams` の owner・table(React Router がデコード済み)。`useTableDetail(owner, table)`。
  * 見出し: 「← ER 図へ」(`/` へのリンク)、`{owner}.{table}`、コメント。
  * Mantine `Tabs`(値 `schema`/`data`、ラベル「スキーマ情報」「データ」)。タブ変更で `setSearchParams({tab, page?}, { replace: true })`。
  * `tab=schema` → `<SchemaTab detail=… />`(T2)、`tab=data` → `<DataTab owner table page onPageChange />`(T3)。**データタブを開いていない間は DataTab をマウントしない**(`Tabs.Panel` の `keepMounted={false}`)。
  * エラー: `SCHEMA_NOT_LOADED` → 「スキーマ情報がありません」+ [ER 図へ]/`TABLE_NOT_FOUND` → 「テーブルが見つかりません: {owner}.{table}」+ [ER 図へ]/その他 → `displayMessage`。
  * T1 の時点では `SchemaTab`・`DataTab` は中身が見出しだけの仮コンポーネント(`client/src/pages/SchemaTab.tsx`、`DataTab.tsx`)を作っておき、T2・T3 で置き換える。

### 【実装してはいけないこと】

* タブ以外の画面(編集など)を追加しない。

### 【Unit Test内容】

* urlState: `parseTab("data")`/`parseTab("x")`→schema/`parsePage("3")`→3/`"0"`・`"-1"`・`"abc"`・`"2.5"`・`"2002"`(offset 100,050 > 100,000)→1/`"2001"`→2001。
* TableDetailPage(`fetch` を偽物に):
  * 正常系: `/tables/HR/EMPLOYEES` で見出し `HR.EMPLOYEES` とコメント、スキーマ情報タブが選択/`?tab=data` でデータタブが選択/タブをクリックすると URL の `tab` が変わる(テスト用に `useLocation` を表示する小さな部品で確認)/スキーマ情報タブだけのとき rows の API が呼ばれない。
  * 異常系: 404 `TABLE_NOT_FOUND` で「テーブルが見つかりません: HR.NOPE」と ER 図へのリンク/404 `SCHEMA_NOT_LOADED` で「スキーマ情報がありません」。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npx vitest run src/pages`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U005-T2: スキーマ情報タブ

### 【目的】

* テーブル詳細のスキーマ情報(概要・列・主キー・一意制約・外部キー・参照元・インデックス)を表示する。

### 【作成・編集対象ファイル】

* `client/src/pages/SchemaTab.tsx`
* `client/src/pages/SchemaTab.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §2.2.2、§3.4

### 【実装内容】

* セクションごとに見出し + Mantine `Table`。
  * 概要: テーブル名、コメント、行数の目安(`num_rows` を 3 桁区切り。null は「統計なし」)、統計取得日(`formatLocalDateTime`。null は空欄)。
  * 列: `#`、列名、データ型、NULL(「可」/「不可」)、デフォルト、主キー(`🔑 {pk_position}`)、コメント。
  * 主キー: 制約名と列(`, ` 区切り)。null は「主キーなし」。
  * 一意制約: 名前と列。空は「なし」。
  * 外部キー(参照先): 制約名、`列 → 参照先スキーマ.参照先テーブル(列)`、削除時の動作。`ref_in_snapshot` なら参照先テーブル名を `/tables/{ref_owner}/{ref_table}` へのリンク(`Link`、`encodeURIComponent`)にする。空は「なし」。
  * 外部キー(参照元): 制約名、`参照元テーブル(列) → 列`。参照元テーブル名はリンク。空は「なし」。
  * インデックス: 名前、一意(「一意」/空欄)、種類、列(`descending` なら ` DESC`)。空は「なし」。

### 【実装してはいけないこと】

* API 呼び出しをこの部品の中で行わない(`detail` を props で受け取る)。

### 【Unit Test内容】

* 正常系(EMPLOYEES 相当の detail): 列が column_id 順に並ぶ/`NUMBER(6)` と「不可」/主キー `EMP_EMP_ID_PK`/一意制約 `EMP_EMAIL_UK`/外部キーの参照先リンク `/tables/HR/DEPARTMENTS`/自己参照 `EMP_MANAGER_FK` のリンク `/tables/HR/EMPLOYEES`/参照元 `DEPT_MGR_FK` のリンク `/tables/HR/DEPARTMENTS`/インデックスの DESC 表示/`num_rows=107`。
* 異常系・境界: 主キーなし → 「主キーなし」/`ref_in_snapshot=false` の外部キーはリンクでない/`num_rows=null` → 「統計なし」/インデックス 0 件 → 「なし」。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npx vitest run src/pages/SchemaTab.test.tsx`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U005-T3: データタブ

### 【目的】

* テーブルのデータを 50 行ずつページ送りで表示する。

### 【作成・編集対象ファイル】

* `client/src/pages/DataTab.tsx`
* `client/src/pages/DataTab.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §2.2.3、§3.5、§3.6

### 【実装内容】

* props: `owner`、`table`、`page`、`onPageChange(page)`。`offset = (page-1) * PAGE_SIZE`。`useTableRows(owner, table, offset, PAGE_SIZE, true)`。
* 上部のバー: 並び順(`PRIMARY_KEY` → 「並び順: {order_by を , で連結}(主キー)」、`ROWID` → 「並び順: ROWID(主キーなし)」)、「取得 {elapsed_ms} ms」、[再読み込み](`refetch()`。キャッシュを使わず取り直す)、[< 前へ](page>1 で有効)、「{page} ページ目 ({offset+1}〜{offset+rows.length} 行)」、[次へ >](`has_next` で有効)。
* 表: Mantine `Table` を `Table.ScrollContainer`(横スクロール)に入れ、`stickyHeader`。見出しは列名(`title` 属性に data_type)。セル: `null` は `<span className="null-cell">(null)</span>`(灰色・斜体。`data-null="true"`)、`truncated[i]` に含まれる列は `title="先頭 1,000 文字のみ表示"`。
* 0 行: 「データがありません」。
* 取得中: `LoadingOverlay` を表の上に重ね、ボタンを無効化。前のページのデータは取得中も表示したままにする(`placeholderData: keepPreviousData`)。
* エラー: 表の代わりに赤枠の `Alert` に `displayMessage` と [再試行] ボタン(`refetch()`)。

### 【実装してはいけないこと】

* 件数(総行数)を表示しない。データを SQLite やブラウザに保存しない。

### 【Unit Test内容】

* 正常系(`fetch` を偽物に): 50 行と見出し/「並び順: EMPLOYEE_ID(主キー)」/「取得 38 ms」/`has_next=true` で [次へ] が有効、クリックで `onPageChange(2)`/page=2 で offset=50 の URL を呼ぶ/page=1 で [前へ] が無効/`null` セルが `(null)` で `data-null="true"`、文字列 `"(null)"` のセルは `data-null` を持たない/truncated の列に title/[再読み込み] で同じ URL をもう一度呼ぶ/`ROWID` の並び順表示。
* 異常系: 502 `ORA-00942` で `[ORA-00942] ...` と [再試行]、[再試行] で再度呼ぶ/0 行で「データがありません」。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npm test`
* `cd client && npm run build`

### 【完了条件】

* テストがすべて合格し、ビルドが成功する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
