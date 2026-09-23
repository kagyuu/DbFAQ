あなたはExecutor(実装担当)です。以下は1スプリント分の作業範囲と完了条件を定義したものです。スプリントは複数のタスクから成り、各タスクに個別の完了条件とチェックボックスを持ちます。実施後は、そのタスクの完了条件を満たしたことを確認したうえで、Executor Stepの「停止条件」(`SKILL.md` 参照)に該当しない限り、自動的に次のタスクへ進んでください。人間の指示を待って停止しないでください。

# 【スプリントID】U004 — frontend-er

## タスク一覧(OKF副目次)

* 状態は `[ ]` / `[~]` / `[x]`。運用は U001 と同じ(中断からの再開・先行実装の禁止を含む)。

- [x] U004-T1 [クライアントの初期化](#u004-t1-クライアントの初期化) — `client/` の初期化、依存、テスト環境、ルーティングの骨組み
- [x] U004-T2 [API クライアント](#u004-t2-api-クライアント) — API の型、`ApiError`、取得関数とフック
- [x] U004-T3 [ER 図の組み立てとレイアウト](#u004-t3-er-図の組み立てとレイアウト) — `buildGraph.ts`・`layout.ts`
- [x] U004-T4 [共通ヘッダと SC-01 ER 図画面](#u004-t4-共通ヘッダと-sc-01-er-図画面) — `AppShell`・`ErDiagramPage`・`TableNode`・`TableSearch`

---

## U004-T1: クライアントの初期化

### 【目的】

* フロントエンドのプロジェクトを用意し、テストとルーティングの骨組みを作る。

### 【作成・編集対象ファイル】

* `client/` 一式(`package.json`、`package-lock.json`、`vite.config.ts`、`tsconfig*.json`、`index.html`、`src/main.tsx`、`src/App.tsx`、`src/pages/NotFoundPage.tsx`、`src/test/setup.ts`)
* `client/src/App.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1.2、§6、`docs/P003-backend-spec.md` §7

### 【実装内容】

* `client/` を `npm create vite@latest`(テンプレート `react-ts`)相当の構成で初期化する(`client/INDEX.md` がある場合は消さない。スキャフォールドが既存ディレクトリで実行できなければ、一時ディレクトリで生成してファイルをコピーする)。
* 依存: `react@19`、`react-dom@19`、`react-router-dom@7`、`@tanstack/react-query@5`、`@mantine/core@9`、`@mantine/hooks@9`、`@mantine/notifications@9`、`@xyflow/react@12`、`elkjs`。開発依存: `vitest`、`@testing-library/react`、`@testing-library/user-event`、`@testing-library/jest-dom`、`jsdom`。バージョンは導入時点の最新の安定版でよい(メジャーは上記)。
* `vite.config.ts`: `server.proxy = { "/api": "http://localhost:8000" }`、`test: { environment: "jsdom", setupFiles: "./src/test/setup.ts", globals: true }`。
* `src/test/setup.ts`: `@testing-library/jest-dom/vitest` を読み込む。jsdom に無い `ResizeObserver`・`window.matchMedia`・`DOMMatrixReadOnly` の最小限の代替を定義する(Mantine と React Flow が使うため)。
* `package.json` の scripts: `"dev": "vite"`、`"build": "tsc -b && vite build"`、`"test": "vitest run"`。
* `src/main.tsx`: `MantineProvider`(`@mantine/core/styles.css`、`@mantine/notifications/styles.css`、`@xyflow/react/dist/style.css` を import)、`Notifications`、`QueryClientProvider`(`retry: false`、`refetchOnWindowFocus: false`)、`BrowserRouter` で `App` を包む。
* `src/App.tsx`: ルート `/` → 仮の `ErDiagramPage`(T4 で置き換える。ここでは見出し「ER 図」だけのプレースホルダを `src/pages/ErDiagramPage.tsx` に置く)、`/tables/:owner/:table` → 仮の `TableDetailPage`(見出しだけ。U005 で置き換える)、`*` → `NotFoundPage`(「ページが見つかりません」と `/` へのリンク「ER 図へ」)。
* テスト用のラッパ `src/test/render.tsx`: `renderWithProviders(ui, { route })` — MantineProvider・QueryClientProvider(テストごとに新しい QueryClient)・`MemoryRouter(initialEntries=[route])` で包む。

### 【実装してはいけないこと】

* 状態管理ライブラリ(Redux 等)や CSS フレームワークを追加しない。

### 【Unit Test内容】

* テスト対象: `App` のルーティング
* 正常系: `/` でプレースホルダの「ER 図」が表示される。
* 異常系: `/nope` で「ページが見つかりません」とリンク「ER 図へ」(href `/`)が表示される。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npm install && npm test`
* `cd client && npm run build`

### 【完了条件】

* テストがすべて合格し、ビルドが成功する。

### 【次タスクに進む前の停止条件】

* `npm install` が失敗し 3 回試しても解消しない場合は停止して報告する。

---

## U004-T2: API クライアント

### 【目的】

* backend の API を型付きで呼ぶ関数と、TanStack Query のフックを作る。

### 【作成・編集対象ファイル】

* `client/src/api/types.ts`、`client/src/api/client.ts`、`client/src/api/hooks.ts`
* `client/src/api/client.test.ts`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §3(全体)、§1.3

### 【実装内容】

* `types.ts`: P002 §3.2〜§3.7 のレスポンスを TypeScript の型で定義(`ErView`、`SnapshotSummary`、`ErTable`、`ErColumn`、`Relation`、`RefreshResult`、`TableDetail`、`RowsPage`、`Health`)。エラー本文 `ApiErrorBody`。
* `client.ts`:
  * `class ApiError extends Error { code: string; status: number; oraCode?: string }`。`displayMessage` ゲッター: `oraCode` があれば `[ORA-xxxxx] message`(message がすでに `ORA-xxxxx:` で始まる場合も `[..]` は付ける)。
  * `async function request<T>(path, init?)`: `fetch("/api" + path)`。ネットワークエラー(fetch の reject)→ `ApiError(code="NETWORK_ERROR", status=0, message="サーバに接続できません")`。2xx でなければ本文を JSON として読み `error.code`・`error.message`・`error.ora_code` から `ApiError`。JSON でなければ `code="INTERNAL_ERROR"`、message `"サーバでエラーが発生しました (HTTP {status})"`。
  * 関数: `getSchema()`、`refreshSchema()`(POST)、`getTableDetail(owner, table)`、`getTableRows(owner, table, offset, limit)`、`getHealth()`。パスの owner・table は `encodeURIComponent`。
* `hooks.ts`: `useSchema()`(キー `["schema"]`)、`useRefreshSchema()`(useMutation。成功時に `["schema"]` を invalidate)、`useHealth()`(`refetchInterval: 60_000`)、`useTableDetail(owner, table)`、`useTableRows(owner, table, offset, limit, enabled)`(キー `["rows", owner, table, offset, limit]`、`enabled` で呼ぶかどうかを制御)。

### 【実装してはいけないこと】

* axios 等の HTTP ライブラリを追加しない。

### 【Unit Test内容】

* テスト対象: `client.ts`(`globalThis.fetch` を `vi.fn` で差し替える)
* 正常系: `getSchema` が `/api/schema` を GET して本文を返す/`getTableRows("HR","MY TABLE",50,50)` の URL が `/api/schema/tables/HR/MY%20TABLE/rows?offset=50&limit=50`/`refreshSchema` が POST。
* 異常系: 502 + `{"error":{"code":"ORACLE_ERROR","message":"ORA-00942: ...","ora_code":"ORA-00942"}}` → `ApiError` の code・status・oraCode、`displayMessage` が `[ORA-00942] ORA-00942: ...`/fetch が reject → `NETWORK_ERROR`、「サーバに接続できません」/500 で本文が HTML → `INTERNAL_ERROR`。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npx vitest run src/api`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## U004-T3: ER 図の組み立てとレイアウト

### 【目的】

* API の ER 図データから React Flow のノード・エッジを作る純粋関数と、elkjs による自動レイアウトを作る。

### 【作成・編集対象ファイル】

* `client/src/er/buildGraph.ts`、`client/src/er/layout.ts`
* `client/src/er/buildGraph.test.ts`、`client/src/er/layout.test.ts`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §2.1.2

### 【実装内容】

* `buildGraph.ts`:
  * 定数 `MAX_VISIBLE_COLUMNS = 30`、`ROW_HEIGHT = 22`、`HEADER_HEIGHT = 32`、`CHAR_WIDTH = 7.5`、`MIN_WIDTH = 180`、`PADDING_X = 40`。
  * 型 `TableNodeData = { owner, name, comment, columns: ErColumn[] (先頭 30), hiddenCount: number }`。
  * `function nodeSize(table): { width, height }`: 幅 = max(MIN_WIDTH, (最長の「列名 + 型表記」の文字数、テーブル名の文字数の大きい方) × CHAR_WIDTH + PADDING_X)、高さ = HEADER_HEIGHT + 表示行数 × ROW_HEIGHT(+ 省略行があれば 1 行)。
  * `function buildGraph(view: ErView): { nodes: Node<TableNodeData>[], edges: Edge[] }`:
    * ノード ID は `${owner}.${name}`、`type: "table"`、`position: {x:0,y:0}`、`width`・`height` は `nodeSize`。
    * エッジは `relations` ごとに 1 本。ID は `rel:${name}`、`source` は from、`target` は to、`label` は制約名、`markerEnd` は矢印(`MarkerType.ArrowClosed`)。**`to` のノードが存在しない場合(別スキーマ)は作らない。** 自己参照は `source === target` のまま作り、`type: "selfLoop"` にする(描画は T4)。
* `layout.ts`:
  * `async function layoutGraph(nodes, edges): Promise<Node[]>`: elkjs(`elkjs/lib/elk.bundled.js`)で `algorithm: "layered"`、`elk.direction: "RIGHT"`、`elk.spacing.nodeNode: "60"`、`elk.layered.spacing.nodeNodeBetweenLayers: "100"`。子→親の向きでエッジを渡す(親が右に来る)。自己参照エッジはレイアウトに渡さない。戻り値は `position` を設定した新しいノード配列(入力を変更しない)。

### 【実装してはいけないこと】

* ノードの位置を保存しない(localStorage 等に書かない)。

### 【Unit Test内容】

* buildGraph — 正常系: ノード数 = テーブル数、エッジ数 = relations 数(別スキーマ参照を除く)/自己参照のエッジが `type: "selfLoop"`/35 列のテーブルは columns 30 と hiddenCount 5/nodeSize の幅が最小幅以上で、長い列名ほど広い。異常系: tables 0 件で空配列。
* layout — 正常系(elkjs を実際に使う): 7 ノード・9 エッジ + 自己参照 1 本の HR 相当の入力で、全ノードに有限の座標が付く/どの 2 ノードの矩形も重ならない/親(DEPARTMENTS)の x が子(EMPLOYEES)より大きい、は循環(EMPLOYEES↔DEPARTMENTS)があるので確かめず、REGIONS の x > COUNTRIES の x を確かめる/入力のノード配列が変更されていない。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npx vitest run src/er`

### 【完了条件】

* 上記がすべて合格。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。elkjs が jsdom で動かない場合は、Node 環境で動かす(該当テストファイルの先頭に `// @vitest-environment node`)。

---

## U004-T4: 共通ヘッダと SC-01 ER 図画面

### 【目的】

* 共通ヘッダと ER 図画面(拡大縮小・ミニマップ・クリックで遷移・検索・再読み込み)を作る。

### 【作成・編集対象ファイル】

* `client/src/components/AppShell.tsx`、`client/src/components/OracleStatus.tsx`
* `client/src/pages/ErDiagramPage.tsx`、`client/src/er/TableNode.tsx`、`client/src/er/SelfLoopEdge.tsx`、`client/src/er/TableSearch.tsx`
* `client/src/App.tsx`(AppShell で包む)
* `client/src/components/AppShell.test.tsx`、`client/src/pages/ErDiagramPage.test.tsx`、`client/src/er/TableSearch.test.tsx`

### 【参照すべき仕様箇所】

* `docs/P002-frontend-spec.md` §1.1、§1.3、§2.1

### 【実装内容】

* `AppShell`: Mantine の `AppShell`(header 高さ 48)。ヘッダ: 「DbFAQ」(`/` へのリンク)、「スキーマ: {owner|未取得}」、「取得日時: {ローカル時刻 YYYY-MM-DD HH:mm:ss}」(未取得なら非表示)、「ER 図」リンク、`OracleStatus`。日時の整形は `src/format.ts` の `formatLocalDateTime(iso: string): string`(純粋関数。テスト対象に含める)。
* `OracleStatus`: `useHealth()`。取得中=灰、`oracle.status==="ok"` =緑、それ以外=赤の丸(`data-testid="oracle-status"`、`data-status` 属性に `loading|ok|error`)。`Tooltip` に ok なら `Oracle {version} / {host}:{port}/{service_name} ({user})`、error なら `oracle.message`。
* `ErDiagramPage`:
  * ツールバー: `TableSearch`、[Oracle から再読み込み] ボタン(`useRefreshSchema`。実行中は `loading` で無効)、「テーブル N / 関連 M」。
  * 状態: 取得中スピナー/`loaded=false` → 「スキーマ情報がありません」+ [Oracle から読み込む]/テーブル 0 件 → 「テーブルがありません(スキーマ: {owner})」+ [Oracle から再読み込み]/それ以外は ER 図。
  * ER 図: `buildGraph` → `layoutGraph`(`useEffect`。計算中はスピナー)→ `<ReactFlow nodes edges nodeTypes={{table: TableNode}} edgeTypes={{selfLoop: SelfLoopEdge}} minZoom={0.1} maxZoom={2} fitView onNodeClick>` に `<Controls />`(左下、+/−/全体表示)、`<MiniMap pannable zoomable />`(右下)、`<Background />`。ノードのドラッグは `onNodesChange` + `applyNodeChanges` で許可(保存しない)。
  * `onNodeClick`: `navigate(`/tables/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`)`。React Flow はドラッグ後にクリックを発火しない(`nodeDragThreshold` 既定 1)ので、`nodeDragThreshold={5}` を指定する。
  * 再読み込み成功: `notifications.show` で「スキーマ情報を更新しました(テーブル N / 関連 M)」。失敗: `notifications.show({color: "red", message: err.displayMessage, autoClose: 10000})`。ER 図は前回のまま。
* `TableNode`: 見出し(テーブル名。`title` 属性にコメント)、列の行(🔑=主キー、🔗=外部キー、NOT NULL は太字、右に `data_type_display`)、`hiddenCount>0` なら「… 他 N 列」。React Flow の `Handle`(左=target、右=source)を置く。`data-testid="er-node-{name}"`。強調中(検索で選択)は枠を太く色付けする(`data.highlighted`)。
* `SelfLoopEdge`: ノードの右辺から出て右に 40px 張り出して戻る SVG パス(`BaseEdge`)とラベル。
* `TableSearch`: Mantine `Autocomplete` 相当(入力 max 128 文字、trim、大文字小文字を区別しない部分一致、候補最大 20 件)。候補を選ぶ(クリック/Enter で先頭)と `onFocusTable(id)` を呼ぶ。候補の右端に「開く」ボタン → `onOpenTable(owner, name)`。`ErDiagramPage` は `onFocusTable` で `reactFlow.setCenter(x + w/2, y + h/2, { zoom: 1, duration: 300 })` し、そのノードの `highlighted` を 2 秒だけ true にする。

### 【実装してはいけないこと】

* ノード位置の保存、ビューの表示、テーブル詳細の内容(U005)を実装しない。

### 【Unit Test内容】

* `formatLocalDateTime`: `2026-09-23T01:15:02Z` をタイムゾーン `UTC` で `2026-09-23 01:15:02`(テストは `process.env.TZ = "UTC"` を vitest の設定 `test.env` で固定)。
* AppShell: スキーマ名・取得日時の表示/未取得で「未取得」/OracleStatus の `data-status` が health の結果で ok・error になる(`fetch` を偽物に)。
* ErDiagramPage(`fetch` を偽物に、HR 相当の ErView を返す):
  * 正常系: ノード `er-node-EMPLOYEES` などが表示される(レイアウト完了を `findBy` で待つ)/ミニマップ(`.react-flow__minimap`)とコントロール(`.react-flow__controls`)が存在する/ノードをクリックすると `/tables/HR/EMPLOYEES` に遷移する(`MemoryRouter` 内のテスト用ルートで遷移先を表示して確認)/「テーブル 7 / 関連 10」/再読み込み成功で通知文言が出て `/api/schema` を取り直す。
  * 異常系: `loaded=false` で「スキーマ情報がありません」とボタン/0 件で「テーブルがありません」/再読み込みが 502 で `[ORA-01017] ...` の通知が出て、ノードは残る。
* TableSearch: 「emp」で EMPLOYEES が候補に出る/129 文字以上は入力できない(maxLength)/Enter で `onFocusTable` が先頭候補で呼ばれる/「開く」で `onOpenTable`。
* 合格条件: すべて合格。

### 【実行コマンド】

* `cd client && npm test`
* `cd client && npm run build`

### 【完了条件】

* テストがすべて合格し、ビルドが成功する。さらに backend(U003)を `DBFAQ_CONFIG=../config.yaml` で 8000 番に起動し、`npm run dev` で開いた `http://localhost:5173/` で [Oracle から読み込む] → HR の ER 図が表示されることを目視またはスクリーンショット(Playwright の単発スクリプトでよい)で確認する。

### 【次タスクに進む前の停止条件】

* 3 回自己修正しても合格しない場合は停止して報告する。

---

## 重要

* 各タスクの範囲外のファイルは編集しないでください。
* タスクの実装後、実行したテストコマンドと結果を報告してください。
* タスクが完了したら、上記「タスク一覧」の該当行を `[x]` に更新してください。
* 全タスクが完了したら、`docs/P007-impl-direction.md` の本スプリント行を `[x]` に更新してください。
* Executor Stepの停止条件に該当しない限り、次のタスクに自動的に進んでください。
