// SC-02 の URL クエリ(tab・page)と SC-03 の tab の解釈(P002 §1.2・§2.2.4)
export const PAGE_SIZE = 50
export const MAX_OFFSET = 100_000

export type Tab = 'schema' | 'data' | 'query'

export function parseTab(v: string | null): Tab {
  return v === 'data' || v === 'query' ? v : 'schema'
}

export function parsePage(v: string | null): number {
  if (v === null || !/^\d+$/.test(v)) return 1
  const n = Number(v)
  if (n < 1 || (n - 1) * PAGE_SIZE > MAX_OFFSET) return 1
  return n
}

export type PdbTab = 'info' | 'query'

/** SC-03 の tab(※CR-005により追加)。省略時・不正値は info */
export function parsePdbTab(v: string | null): PdbTab {
  return v === 'query' ? 'query' : 'info'
}
