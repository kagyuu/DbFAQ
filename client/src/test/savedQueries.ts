import type { SavedQuery } from '../api/types'

/** 保存済み Query の API(P002 §3.10〜§3.13)の偽物。mockFetch に渡す routes と、中身の配列を返す。※CR-005により追加 */
export function savedQueryServer(initial: SavedQuery[] = []) {
  const items = [...initial]
  let nextId = 100
  const now = '2026-10-07T12:00:00Z'
  const conflict = { status: 409, body: { error: { code: 'QUERY_NAME_CONFLICT', message: '同じ名前の Query が既にあります' } } }
  const notFound = { status: 404, body: { error: { code: 'SAVED_QUERY_NOT_FOUND', message: '保存済みの Query が見つかりません' } } }
  const idOf = (url: string) => Number(url.split('/').pop())
  const sameTarget = (a: SavedQuery, b: Partial<SavedQuery>) =>
    a.scope === b.scope && a.owner === (b.owner ?? null) && a.table === (b.table ?? null)
  const routes = {
    'GET /api/saved-queries': (url: string) => {
      const p = new URL(url, 'http://t').searchParams
      const t = { scope: p.get('scope') as SavedQuery['scope'], owner: p.get('owner'), table: p.get('table') }
      const list = items.filter((q) => sameTarget(q, t)).sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
      return { body: { items: list } }
    },
    'POST /api/saved-queries': (_url: string, init?: RequestInit) => {
      const b = JSON.parse(String(init?.body))
      const t = { scope: b.scope, owner: b.owner ?? null, table: b.table ?? null }
      if (items.some((q) => sameTarget(q, t) && q.name === b.name)) return conflict
      const q: SavedQuery = { id: nextId++, ...t, name: b.name, description: b.description, sql: b.sql, is_template: false, created_at: now, updated_at: now }
      items.push(q)
      return { status: 201, body: q }
    },
    'PUT /api/saved-queries/': (url: string, init?: RequestInit) => {
      const b = JSON.parse(String(init?.body))
      const q = items.find((x) => x.id === idOf(url))
      if (!q) return notFound
      if (items.some((x) => x.id !== q.id && sameTarget(x, q) && x.name === b.name)) return conflict
      Object.assign(q, { name: b.name, description: b.description, sql: b.sql, updated_at: '2026-10-07T12:30:00Z' })
      return { body: q }
    },
    'DELETE /api/saved-queries/': (url: string) => {
      const i = items.findIndex((x) => x.id === idOf(url))
      if (i < 0) return notFound
      items.splice(i, 1)
      return { status: 204, body: undefined }
    },
  }
  return { routes, items }
}

export function savedQuery(over: Partial<SavedQuery> = {}): SavedQuery {
  return {
    id: 1,
    scope: 'table',
    owner: 'HR',
    table: 'EMPLOYEES',
    name: '部署50',
    description: '部署 50 の社員',
    sql: 'SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50',
    is_template: false,
    created_at: '2026-10-07T12:00:00Z',
    updated_at: '2026-10-07T12:00:00Z',
    ...over,
  }
}
