import { afterEach, expect, test, vi } from 'vitest'
import { ApiError, getSchema, getTableRows, refreshSchema } from './client'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

afterEach(() => vi.unstubAllGlobals())

test('getSchema は /api/schema を GET する', async () => {
  const fetchMock = vi.fn().mockResolvedValue(json(200, { loaded: false, snapshot: null, tables: [], relations: [] }))
  vi.stubGlobal('fetch', fetchMock)
  const r = await getSchema()
  expect(r.loaded).toBe(false)
  expect(fetchMock).toHaveBeenCalledWith('/api/schema', undefined)
})

test('getTableRows は名前を URL エンコードする', async () => {
  const fetchMock = vi.fn().mockResolvedValue(json(200, {}))
  vi.stubGlobal('fetch', fetchMock)
  await getTableRows('HR', 'MY TABLE', 50, 50)
  expect(fetchMock.mock.calls[0][0]).toBe('/api/schema/tables/HR/MY%20TABLE/rows?offset=50&limit=50')
})

test('refreshSchema は POST', async () => {
  const fetchMock = vi.fn().mockResolvedValue(json(200, { snapshot: {} }))
  vi.stubGlobal('fetch', fetchMock)
  await refreshSchema()
  expect(fetchMock.mock.calls[0][1]).toEqual({ method: 'POST' })
})

test('エラー形式を ApiError に変換する', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      json(502, { error: { code: 'ORACLE_ERROR', message: 'ORA-00942: table or view does not exist', ora_code: 'ORA-00942' } }),
    ),
  )
  const err = (await getSchema().catch((e) => e)) as ApiError
  expect(err).toBeInstanceOf(ApiError)
  expect(err.code).toBe('ORACLE_ERROR')
  expect(err.status).toBe(502)
  expect(err.oraCode).toBe('ORA-00942')
  expect(err.displayMessage).toBe('[ORA-00942] ORA-00942: table or view does not exist')
})

test('ネットワークエラーは NETWORK_ERROR', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  const err = (await getSchema().catch((e) => e)) as ApiError
  expect(err.code).toBe('NETWORK_ERROR')
  expect(err.status).toBe(0)
  expect(err.displayMessage).toBe('サーバに接続できません')
})

test('JSON でないエラー本文は INTERNAL_ERROR', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>bad gateway</html>', { status: 500 })))
  const err = (await getSchema().catch((e) => e)) as ApiError
  expect(err.code).toBe('INTERNAL_ERROR')
  expect(err.message).toBe('サーバでエラーが発生しました (HTTP 500)')
})
