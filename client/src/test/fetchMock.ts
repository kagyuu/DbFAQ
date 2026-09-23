import { vi } from 'vitest'

type Handler = (url: string, init?: RequestInit) => { status?: number; body: unknown } | Promise<{ status?: number; body: unknown }>

/** URL(/api 以降、クエリを含む)の前方一致で応答を返す偽の fetch。呼び出しは mock.calls で確認する */
export function mockFetch(routes: Record<string, Handler | { status?: number; body: unknown }>) {
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET'
    const key = Object.keys(routes)
      .sort((a, b) => b.length - a.length)
      .find((k) => {
        const [m, p] = k.includes(' ') ? k.split(' ') : ['GET', k]
        return m === method && url.startsWith(p)
      })
    if (!key) return new Response(JSON.stringify({ error: { code: 'INTERNAL_ERROR', message: `no route ${method} ${url}` } }), { status: 500 })
    const r = routes[key]
    const { status = 200, body } = typeof r === 'function' ? await r(url, init) : r
    return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export const HEALTH_OK = {
  status: 'ok',
  backend: { status: 'ok', version: '0.1.0' },
  mcp: { status: 'ok', message: null },
  oracle: { status: 'ok', version: '23.26.3.0.0', user: 'HR', message: null },
  config: { host: 'localhost', port: 1521, service_name: 'FREEPDB1', user: 'hr', schema: 'HR', query_timeout_sec: 30 },
  checked_at: '2026-09-23T01:20:00Z',
}

export const NOT_LOADED = { loaded: false, snapshot: null, tables: [], relations: [] }
