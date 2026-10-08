import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, expect, test, vi } from 'vitest'
import type { SavedQuery, SavedQueryTarget } from '../api/types'
import { mockFetch } from '../test/fetchMock'
import { renderWithProviders } from '../test/render'
import { savedQuery, savedQueryServer } from '../test/savedQueries'
import SavedQueries, { descriptionError, type LoadedQuery, nameError } from './SavedQueries'

afterEach(() => vi.unstubAllGlobals())

const EMP: SavedQueryTarget = { scope: 'table', owner: 'HR', table: 'EMPLOYEES' }

/** Query タブの代わりに、入力欄と復元中の状態を持つ */
function Host({ initialSql = 'SELECT 1 FROM DUAL', dirty = false }: { initialSql?: string; dirty?: boolean }) {
  const [sql, setSql] = useState(initialSql)
  const [loaded, setLoaded] = useState<LoadedQuery | null>(null)
  const [isDirty, setDirty] = useState(dirty)
  const load = (q: SavedQuery) => setLoaded({ id: q.id, name: q.name, description: q.description })
  return (
    <>
      <textarea aria-label="SQL" value={sql} onChange={(e) => { setSql(e.currentTarget.value); setDirty(true) }} />
      <SavedQueries
        target={EMP}
        targetLabel="HR.EMPLOYEES"
        sql={sql}
        loaded={loaded}
        dirty={isDirty}
        onRestore={(q) => { setSql(q.sql); load(q); setDirty(false) }}
        onSaved={(q) => { load(q); setDirty(false) }}
        onUnload={() => setLoaded(null)}
      />
    </>
  )
}

const sqlBox = () => screen.getByRole('textbox', { name: 'SQL' }) as HTMLTextAreaElement
const dialog = () => screen.getByRole('dialog')

test('0 件の表示', async () => {
  mockFetch(savedQueryServer().routes)
  renderWithProviders(<Host />)
  expect(await screen.findByText('保存済みの Query はありません')).toBeInTheDocument()
  expect(screen.getByText('保存済み Query (0)')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '上書き保存' })).toBeDisabled()
})

test('一覧(名前順、ひな型の印)', async () => {
  mockFetch(savedQueryServer([
    savedQuery({ id: 1, name: 'b' }),
    savedQuery({ id: 2, name: 'a', is_template: true }),
    savedQuery({ id: 3, name: 'x', table: 'DEPARTMENTS' }),
  ]).routes)
  renderWithProviders(<Host />)
  await screen.findByText('保存済み Query (2)')
  const rows = screen.getAllByTestId('saved-query-row')
  expect(rows.map((r) => within(r).getAllByText(/^[ab]$/)[0].textContent)).toEqual(['a', 'b'])
  expect(within(rows[0]).getByText('ひな型')).toBeInTheDocument()
  expect(within(rows[1]).queryByText('ひな型')).toBeNull()
})

test('名前を付けて保存すると一覧に出て復元中になる。同じ名前は 409 をダイアログに表示', async () => {
  const server = savedQueryServer()
  const fetchMock = mockFetch(server.routes)
  renderWithProviders(<Host initialSql="SELECT 50 FROM DUAL" />)
  await screen.findByText('保存済み Query (0)')
  fireEvent.click(screen.getByRole('button', { name: '名前を付けて保存' }))
  expect(within(dialog()).getByText('保存先: HR.EMPLOYEES')).toBeInTheDocument()
  fireEvent.change(within(dialog()).getByRole('textbox', { name: /名前/ }), { target: { value: '  部署50  ' } })
  fireEvent.change(within(dialog()).getByRole('textbox', { name: '説明' }), { target: { value: '説明文' } })
  fireEvent.click(within(dialog()).getByRole('button', { name: '保存' }))
  expect(await screen.findByText('保存しました: 部署50')).toBeInTheDocument()
  expect(await screen.findByText('保存済み Query (1)')).toBeInTheDocument()
  expect(screen.getByTestId('loaded-query')).toHaveTextContent('復元中: 部署50')
  const post = fetchMock.mock.calls.find((c) => c[1]?.method === 'POST')!
  expect(JSON.parse(String(post[1]!.body))).toEqual({
    scope: 'table', owner: 'HR', table: 'EMPLOYEES', name: '部署50', description: '説明文', sql: 'SELECT 50 FROM DUAL',
  })
  // 同じ名前(復元中なら初期値は「 のコピー」)
  fireEvent.click(screen.getByRole('button', { name: '名前を付けて保存' }))
  const nameBox = within(dialog()).getByRole('textbox', { name: /名前/ }) as HTMLInputElement
  expect(nameBox.value).toBe('部署50 のコピー')
  fireEvent.change(nameBox, { target: { value: '部署50' } })
  fireEvent.click(within(dialog()).getByRole('button', { name: '保存' }))
  expect(await within(dialog()).findByTestId('dialog-error')).toHaveTextContent('同じ名前の Query が既にあります')
  fireEvent.click(within(dialog()).getByRole('button', { name: 'キャンセル' }))
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  expect(server.items).toHaveLength(1)
})

test('名前が空白だけ・101 文字では保存できない', async () => {
  mockFetch(savedQueryServer().routes)
  renderWithProviders(<Host />)
  await screen.findByText('保存済み Query (0)')
  fireEvent.click(screen.getByRole('button', { name: '名前を付けて保存' }))
  const save = within(dialog()).getByRole('button', { name: '保存' })
  expect(save).toBeDisabled()
  fireEvent.change(within(dialog()).getByRole('textbox', { name: /名前/ }), { target: { value: '   ' } })
  expect(save).toBeDisabled()
  expect(within(dialog()).getByText('名前を入力してください')).toBeInTheDocument()
  fireEvent.change(within(dialog()).getByRole('textbox', { name: /名前/ }), { target: { value: 'あ'.repeat(101) } })
  expect(save).toBeDisabled()
  expect(nameError('あ'.repeat(100))).toBeNull()
  expect(descriptionError('x'.repeat(1001))).not.toBeNull()
  expect(descriptionError('x'.repeat(1000))).toBeNull()
})

test('入力欄が空白だけなら保存できない', async () => {
  mockFetch(savedQueryServer().routes)
  renderWithProviders(<Host initialSql="  " />)
  await screen.findByText('保存済み Query (0)')
  expect(screen.getByRole('button', { name: '名前を付けて保存' })).toBeDisabled()
})

test('復元: 未編集ならすぐ置き換え、編集中なら確認する', async () => {
  mockFetch(savedQueryServer([savedQuery()]).routes)
  renderWithProviders(<Host />)
  fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
  expect(sqlBox().value).toBe('SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50')
  expect(screen.getByTestId('loaded-query')).toHaveTextContent('復元中: 部署50')
  expect(screen.getAllByTestId('saved-query-row')[0]).toHaveTextContent('●')
  // 編集してから復元 → 確認 → キャンセルで変わらない
  fireEvent.change(sqlBox(), { target: { value: 'SELECT 2 FROM DUAL' } })
  fireEvent.click(screen.getByRole('button', { name: '復元: 部署50' }))
  expect(within(dialog()).getByText(/入力欄の SQL を「部署50」で置き換えますか/)).toBeInTheDocument()
  fireEvent.click(within(dialog()).getByRole('button', { name: 'キャンセル' }))
  expect(sqlBox().value).toBe('SELECT 2 FROM DUAL')
  fireEvent.click(screen.getByRole('button', { name: '復元: 部署50' }))
  fireEvent.click(within(dialog()).getByRole('button', { name: '置き換える' }))
  expect(sqlBox().value).toBe('SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50')
})

test('上書き保存は復元中の Query の名前・説明と入力欄の SQL を PUT する', async () => {
  const server = savedQueryServer([savedQuery()])
  const fetchMock = mockFetch(server.routes)
  renderWithProviders(<Host />)
  fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
  fireEvent.change(sqlBox(), { target: { value: 'SELECT 60 FROM DUAL' } })
  fireEvent.click(screen.getByRole('button', { name: '上書き保存' }))
  expect(await screen.findByText('上書き保存しました: 部署50')).toBeInTheDocument()
  const put = fetchMock.mock.calls.find((c) => c[1]?.method === 'PUT')!
  expect(put[0]).toBe('/api/saved-queries/1')
  expect(JSON.parse(String(put[1]!.body))).toEqual({ name: '部署50', description: '部署 50 の社員', sql: 'SELECT 60 FROM DUAL' })
  expect(server.items[0].sql).toBe('SELECT 60 FROM DUAL')
})

test('編集で名前と説明を変える(SQL は元のまま)。復元中なら表示も変わる', async () => {
  const server = savedQueryServer([savedQuery()])
  mockFetch(server.routes)
  renderWithProviders(<Host />)
  fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
  fireEvent.change(sqlBox(), { target: { value: 'SELECT 999 FROM DUAL' } })
  fireEvent.click(screen.getByRole('button', { name: '編集: 部署50' }))
  fireEvent.change(within(dialog()).getByRole('textbox', { name: /名前/ }), { target: { value: '部署60' } })
  fireEvent.click(within(dialog()).getByRole('button', { name: '保存' }))
  expect(await screen.findByRole('button', { name: '復元: 部署60' })).toBeInTheDocument()
  expect(screen.getByTestId('loaded-query')).toHaveTextContent('復元中: 部署60')
  expect(server.items[0].sql).toBe('SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50')
  expect(sqlBox().value).toBe('SELECT 999 FROM DUAL')
})

test('削除は確認してから。復元中なら解除する', async () => {
  const server = savedQueryServer([savedQuery()])
  mockFetch(server.routes)
  renderWithProviders(<Host />)
  fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
  fireEvent.click(screen.getByRole('button', { name: '削除: 部署50' }))
  expect(within(dialog()).getByText('「部署50」を削除しますか? 元に戻せません')).toBeInTheDocument()
  fireEvent.click(within(dialog()).getByRole('button', { name: '削除' }))
  expect(await screen.findByText('保存済みの Query はありません')).toBeInTheDocument()
  expect(screen.queryByTestId('loaded-query')).toBeNull()
  expect(server.items).toEqual([])
  expect(sqlBox().value).toBe('SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50') // 入力欄はそのまま
})

test('別の画面で削除済みなら上書き保存は 404 を通知し、一覧を取り直して復元中を解除する', async () => {
  const server = savedQueryServer([savedQuery()])
  mockFetch(server.routes)
  renderWithProviders(<Host />)
  fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
  server.items.splice(0, 1)
  fireEvent.click(screen.getByRole('button', { name: '上書き保存' }))
  expect(await screen.findByText('上書き保存できませんでした')).toBeInTheDocument()
  expect(await screen.findByText('保存済みの Query はありません')).toBeInTheDocument()
  await waitFor(() => expect(screen.queryByTestId('loaded-query')).toBeNull())
})
