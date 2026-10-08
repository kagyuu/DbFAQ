import { afterEach, expect, test, vi } from 'vitest'
import {
  ApiError,
  createSavedQuery,
  deleteSavedQuery,
  fetchQueryCsv,
  getPdbInfo,
  getSchema,
  getTableRows,
  listSavedQueries,
  refreshSchema,
  runQuery,
  updateSavedQuery,
} from './client'

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

test('runQuery は SQL を JSON で POST し、エラー位置を ApiError に入れる', async () => {
  const position = { offset: 33, line: 3, column: 7 }
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(json(200, { rows: [] }))
    .mockResolvedValueOnce(json(502, { error: { code: 'ORACLE_ERROR', message: 'ORA-00904: x', ora_code: 'ORA-00904', position } }))
  vi.stubGlobal('fetch', fetchMock)
  await runQuery('SELECT 1 FROM DUAL')
  expect(fetchMock.mock.calls[0][0]).toBe('/api/query')
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: 'POST', body: '{"sql":"SELECT 1 FROM DUAL"}' })
  const err = (await runQuery('x').catch((e) => e)) as ApiError
  expect(err.position).toEqual(position)
  expect(err.displayMessage).toBe('[ORA-00904] ORA-00904: x')
})

test('fetchQueryCsv は Blob と行数を返し、失敗は ApiError', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(new Response('A\r\n1\r\n', { status: 200, headers: { 'Content-Type': 'text/csv', 'X-Row-Count': '1' } }))
    .mockResolvedValueOnce(json(422, { error: { code: 'SQL_REJECTED', message: '複数の文は実行できません' } }))
  vi.stubGlobal('fetch', fetchMock)
  const r = await fetchQueryCsv('SELECT 1 FROM DUAL')
  expect(fetchMock.mock.calls[0][0]).toBe('/api/query/csv')
  expect(r.rowCount).toBe(1)
  expect(await r.blob.text()).toBe('A\r\n1\r\n')
  const err = (await fetchQueryCsv('x').catch((e) => e)) as ApiError
  expect(err.code).toBe('SQL_REJECTED')
})

// ※CR-005により追加
test('保存済み Query の API: 一覧のクエリ、POST・PUT の本文、DELETE の 204、409 は ApiError', async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(json(200, { items: [] }))
    .mockResolvedValueOnce(json(200, { items: [] }))
    .mockResolvedValueOnce(json(201, { id: 1 }))
    .mockResolvedValueOnce(json(200, { id: 1 }))
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
    .mockResolvedValueOnce(json(409, { error: { code: 'QUERY_NAME_CONFLICT', message: 'dup' } }))
  vi.stubGlobal('fetch', fetchMock)
  await listSavedQueries({ scope: 'table', owner: 'HR', table: 'MY TABLE' })
  expect(fetchMock.mock.calls[0][0]).toBe('/api/saved-queries?scope=table&owner=HR&table=MY+TABLE')
  await listSavedQueries({ scope: 'pdb' })
  expect(fetchMock.mock.calls[1][0]).toBe('/api/saved-queries?scope=pdb')
  await createSavedQuery({ scope: 'pdb' }, { name: 'n', description: '', sql: 'SELECT 1 FROM DUAL' })
  expect(fetchMock.mock.calls[2][1].method).toBe('POST')
  expect(JSON.parse(fetchMock.mock.calls[2][1].body)).toEqual({ scope: 'pdb', name: 'n', description: '', sql: 'SELECT 1 FROM DUAL' })
  await updateSavedQuery(1, { name: 'n', description: 'd', sql: 's' })
  expect(fetchMock.mock.calls[3][0]).toBe('/api/saved-queries/1')
  expect(fetchMock.mock.calls[3][1].method).toBe('PUT')
  await expect(deleteSavedQuery(1)).resolves.toBeUndefined()
  expect(fetchMock.mock.calls[4][1]).toEqual({ method: 'DELETE' })
  const err = await createSavedQuery({ scope: 'pdb' }, { name: 'n', description: '', sql: 's' }).catch((e) => e)
  expect(err).toBeInstanceOf(ApiError)
  expect(err.code).toBe('QUERY_NAME_CONFLICT')
  expect(err.status).toBe(409)
})

test('getPdbInfo は /api/pdb を GET する', async () => {
  const fetchMock = vi.fn().mockResolvedValue(json(200, { sections: [], fetched_at: 'x', elapsed_ms: 1 }))
  vi.stubGlobal('fetch', fetchMock)
  await getPdbInfo()
  expect(fetchMock).toHaveBeenCalledWith('/api/pdb', undefined)
})
