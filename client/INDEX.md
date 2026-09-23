# client/ INDEX

フロントエンド(React 19 + TypeScript + Vite、Mantine、TanStack Query、React Router、@xyflow/react、elkjs。ADR-009・ADR-010)。

- package.json — 依存とスクリプト(`dev`・`build`・`test`)
- vite.config.ts — 開発時の `/api` 中継(→ localhost:8000)と Vitest の設定(jsdom、TZ=UTC)
- index.html — エントリの HTML
- src/main.tsx — Provider(Mantine・通知・TanStack Query・Router)の組み立て
- src/App.tsx — ルーティング(`/`、`/tables/:owner/:table`、それ以外)
- src/index.css — 全体のスタイル(`(null)` の表示など)
- src/format.ts — 日時のローカル表示
- src/api/ — backend API
  - types.ts — レスポンスの型
  - client.ts — `fetch` のラッパと `ApiError`
  - hooks.ts — TanStack Query のフック
- src/components/ — 共通部品
  - AppShell.tsx — 共通ヘッダ(スキーマ名、取得日時、ER 図リンク、Oracle 状態)
  - OracleStatus.tsx — Oracle 状態の丸(`/api/health` を 60 秒ごとに取得)
- src/er/ — ER 図
  - buildGraph.ts — API の結果 → ノード・エッジ(30 列超の省略、別スキーマの線を除外)
  - layout.ts — elkjs による自動レイアウト
  - TableNode.tsx — テーブルのノード
  - SelfLoopEdge.tsx — 自己参照の線
  - TableSearch.tsx — テーブル名検索
- src/pages/ — 画面
  - ErDiagramPage.tsx — SC-01 ER 図(拡大縮小・ミニマップ・クリックで遷移・再読み込み)
  - TableDetailPage.tsx — SC-02 テーブル詳細(タブ、URL の `tab`・`page`)
  - SchemaTab.tsx — スキーマ情報タブ
  - DataTab.tsx — データタブ(50 行ずつのページ送り)
  - urlState.ts — URL クエリの解釈
  - NotFoundPage.tsx — ページが見つからない
- src/test/ — テスト用の部品(`render.tsx`、`fetchMock.ts`、HR 相当のデータ `hr.ts`・`detail.ts`、`setup.ts`)
- src/**/*.test.ts(x) — 単体テスト(Vitest + Testing Library)
