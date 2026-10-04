// SC-02 の URL クエリ(tab・page)の解釈(P002 §1.2・§2.2.4)
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
