import { fireEvent, screen, within } from '@testing-library/react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, expect, test, vi } from 'vitest'
import type { PdbInfo } from '../api/types'
import { HEALTH_OK, NOT_LOADED, mockFetch } from '../test/fetchMock'
import { renderWithProviders } from '../test/render'
import { savedQuery, savedQueryServer } from '../test/savedQueries'
import PdbPage from './PdbPage'

afterEach(() => vi.unstubAllGlobals())

const INFO: PdbInfo = {
  sections: [
    { key: 'overview', title: '概要', columns: [{ name: 'ITEM', data_type: 'VARCHAR' }, { name: 'VALUE', data_type: 'VARCHAR' }],
      rows: [['コンテナ名(PDB)', 'FREEPDB1'], ['接続ユーザー', 'HR']], truncated: [[], []], error: null },
    { key: 'ts_quotas', title: '表領域の割り当て(接続ユーザー)', columns: [{ name: 'TABLESPACE_NAME', data_type: 'VARCHAR' }, { name: 'USED_MB', data_type: 'NUMBER' }],
      rows: [['USERS', '154']], truncated: [[]], error: null },
    { key: 'segments', title: 'セグメントの使用量(接続ユーザー)', columns: [{ name: 'SEGMENT_TYPE', data_type: 'VARCHAR' }], rows: [], truncated: [], error: null },
    { key: 'tablespaces', title: '表領域の使用状況', columns: [], rows: [], truncated: [],
      error: { code: 'ORACLE_ERROR', message: 'ORA-00942: table or view does not exist', ora_code: 'ORA-00942' } },
  ],
  fetched_at: '2026-10-07T12:15:02Z',
  elapsed_ms: 85,
}

const TEMPLATE = savedQuery({ id: 7, scope: 'pdb', owner: null, table: null, name: '03. LOB 領域', description: 'LOB', sql: 'SELECT 3 FROM DUAL', is_template: true })

function Where() {
  const loc = useLocation()
  return <div data-testid="where">{loc.pathname + loc.search}</div>
}

function renderPage(route = '/pdb') {
  return renderWithProviders(
    <>
      <Routes>
        <Route path="/pdb" element={<PdbPage />} />
      </Routes>
      <Where />
    </>,
    { route },
  )
}

test('PDB 情報タブ: 見出しの PDB 名、セクション、権限のエラー、0 行', async () => {
  const fetchMock = mockFetch({ '/api/health': { body: HEALTH_OK }, '/api/schema': { body: NOT_LOADED }, '/api/pdb': { body: INFO } })
  renderPage()
  expect(await screen.findByRole('heading', { name: 'PDB: FREEPDB1' })).toBeInTheDocument()
  expect(await screen.findByTestId('pdb-section-overview')).toHaveTextContent('コンテナ名(PDB)FREEPDB1')
  expect(within(screen.getByTestId('pdb-section-ts_quotas')).getByRole('table', { name: '表領域の割り当て(接続ユーザー)' })).toHaveTextContent('USERS')
  expect(screen.getByTestId('pdb-section-segments')).toHaveTextContent('該当する行はありません')
  const err = screen.getByTestId('pdb-section-error-tablespaces')
  expect(err).toHaveTextContent('権限が無いため取得できません')
  expect(err).toHaveTextContent('[ORA-00942] ORA-00942: table or view does not exist')
  expect(screen.getByText('取得 85 ms')).toBeInTheDocument()
  // 再読み込み
  const before = fetchMock.mock.calls.filter((c) => c[0] === '/api/pdb').length
  fireEvent.click(screen.getByRole('button', { name: '再読み込み' }))
  await vi.waitFor(() => expect(fetchMock.mock.calls.filter((c) => c[0] === '/api/pdb').length).toBe(before + 1))
})

test('PDB 情報タブ: 全体のエラーと再試行', async () => {
  let fail = true
  mockFetch({
    '/api/health': { body: HEALTH_OK },
    '/api/schema': { body: NOT_LOADED },
    '/api/pdb': () => (fail ? { status: 502, body: { error: { code: 'ORACLE_ERROR', message: 'ORA-12541: no listener', ora_code: 'ORA-12541' } } } : { body: INFO }),
  })
  renderPage()
  expect(await screen.findByTestId('pdb-error')).toHaveTextContent('[ORA-12541] ORA-12541: no listener')
  fail = false
  fireEvent.click(screen.getByRole('button', { name: '再試行' }))
  expect(await screen.findByTestId('pdb-section-overview')).toBeInTheDocument()
})

test('Query タブ: JOIN なし・初期値は空、ひな型を復元して実行、タブを切り替えても保つ', async () => {
  const server = savedQueryServer([TEMPLATE])
  const fetchMock = mockFetch({
    '/api/health': { body: HEALTH_OK },
    '/api/schema': { body: NOT_LOADED },
    '/api/pdb': { body: INFO },
    'POST /api/query': { body: { columns: [{ name: 'X', data_type: 'NUMBER' }], rows: [['3']], truncated: [[]], row_count: 1, has_more: false, max_rows: 500, elapsed_ms: 3 } },
    ...server.routes,
  })
  renderPage('/pdb?tab=query')
  const editor = (await screen.findByRole('textbox', { name: 'SELECT 文' })) as HTMLTextAreaElement
  expect(editor.value).toBe('')
  expect(editor.placeholder).toContain('保存済み Query(ひな型)を復元してください')
  expect(screen.queryByText('JOIN するテーブル(外部キー)')).toBeNull()
  expect(screen.queryByRole('button', { name: 'ひな形を作成' })).toBeNull()
  expect(fetchMock.mock.calls.some((c) => c[0] === '/api/saved-queries?scope=pdb')).toBe(true)
  expect(fetchMock.mock.calls.some((c) => c[0] === '/api/pdb')).toBe(false) // PDB 情報タブを開くまで呼ばない
  fireEvent.click(await screen.findByRole('button', { name: '復元: 03. LOB 領域' }))
  expect(editor.value).toBe('SELECT 3 FROM DUAL')
  expect(screen.getByText('ひな型')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /実行/ }))
  expect(await screen.findByTestId('query-row-count')).toHaveTextContent('1 行')
  // PDB 情報タブへ行って戻る
  fireEvent.click(screen.getByRole('tab', { name: 'PDB 情報' }))
  expect(screen.getByTestId('where')).toHaveTextContent('/pdb?tab=info')
  await screen.findByTestId('pdb-section-overview')
  fireEvent.click(screen.getByRole('tab', { name: 'Query' }))
  expect(screen.getByTestId('where')).toHaveTextContent('/pdb?tab=query')
  expect((screen.getByRole('textbox', { name: 'SELECT 文' }) as HTMLTextAreaElement).value).toBe('SELECT 3 FROM DUAL')
  expect(screen.getByTestId('loaded-query')).toHaveTextContent('復元中: 03. LOB 領域')
  expect(screen.getByTestId('query-row-count')).toHaveTextContent('1 行')
})

test('PDB の Query の保存先は pdb', async () => {
  const server = savedQueryServer()
  const fetchMock = mockFetch({ '/api/health': { body: HEALTH_OK }, '/api/schema': { body: NOT_LOADED }, ...server.routes })
  renderPage('/pdb?tab=query')
  fireEvent.change(await screen.findByRole('textbox', { name: 'SELECT 文' }), { target: { value: 'SELECT 1 FROM DUAL' } })
  fireEvent.click(screen.getByRole('button', { name: '名前を付けて保存' }))
  const dialog = screen.getByRole('dialog')
  expect(within(dialog).getByText('保存先: PDB')).toBeInTheDocument()
  fireEvent.change(within(dialog).getByRole('textbox', { name: /名前/ }), { target: { value: 'PDB名' } })
  fireEvent.click(within(dialog).getByRole('button', { name: '保存' }))
  expect(await screen.findByRole('button', { name: '復元: PDB名' })).toBeInTheDocument()
  const post = fetchMock.mock.calls.find((c) => c[1]?.method === 'POST')!
  expect(JSON.parse(String(post[1]!.body))).toMatchObject({ scope: 'pdb', name: 'PDB名', sql: 'SELECT 1 FROM DUAL' })
  expect(JSON.parse(String(post[1]!.body)).owner).toBeUndefined()
})
