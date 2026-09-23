import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import type { RowsPage } from '../api/types'
import { mockFetch } from '../test/fetchMock'
import { renderWithProviders } from '../test/render'
import DataTab from './DataTab'

afterEach(() => vi.unstubAllGlobals())

function page(offset: number, n: number, extra: Partial<RowsPage> = {}): RowsPage {
  return {
    owner: 'HR',
    table: 'EMPLOYEES',
    columns: [
      { name: 'EMPLOYEE_ID', data_type: 'NUMBER' },
      { name: 'NOTE', data_type: 'CLOB' },
      { name: 'COMMISSION_PCT', data_type: 'NUMBER' },
    ],
    rows: Array.from({ length: n }, (_, i) => [String(100 + offset + i), i === 0 ? 'x'.repeat(1000) + '…' : '(null)', i === 0 ? null : '0.1']),
    truncated: Array.from({ length: n }, (_, i) => (i === 0 ? [1] : [])),
    offset,
    limit: 50,
    has_next: true,
    order_basis: 'PRIMARY_KEY',
    order_by: ['EMPLOYEE_ID'],
    elapsed_ms: 38,
    ...extra,
  }
}

const URL_P1 = '/api/schema/tables/HR/EMPLOYEES/rows?offset=0&limit=50'
const URL_P2 = '/api/schema/tables/HR/EMPLOYEES/rows?offset=50&limit=50'

function renderTab(p = 1, onPageChange = vi.fn()) {
  renderWithProviders(<DataTab owner="HR" table="EMPLOYEES" page={p} onPageChange={onPageChange} />)
  return onPageChange
}

test('50 行、並び順、取得時間、ページ範囲、次へ', async () => {
  mockFetch({ [URL_P1]: { body: page(0, 50) } })
  const onPageChange = renderTab(1)
  const grid = await screen.findByRole('table', { name: 'データ' })
  expect(within(grid).getAllByRole('row')).toHaveLength(51)
  expect(screen.getByText('並び順: EMPLOYEE_ID(主キー)')).toBeInTheDocument()
  expect(screen.getByText('取得 38 ms')).toBeInTheDocument()
  expect(screen.getByTestId('page-range')).toHaveTextContent('1 ページ目 (1〜50 行)')
  expect(screen.getByRole('button', { name: '< 前へ' })).toBeDisabled()
  const next = screen.getByRole('button', { name: '次へ >' })
  expect(next).toBeEnabled()
  fireEvent.click(next)
  expect(onPageChange).toHaveBeenCalledWith(2)
})

test('null と文字列 "(null)" を区別し、切り詰めたセルに title', async () => {
  mockFetch({ [URL_P1]: { body: page(0, 3) } })
  renderTab(1)
  const grid = await screen.findByRole('table', { name: 'データ' })
  const rows = within(grid).getAllByRole('row')
  const firstCells = within(rows[1]).getAllByRole('cell')
  expect(firstCells[2].querySelector('[data-null="true"]')).not.toBeNull()
  expect(firstCells[1]).toHaveAttribute('title', '先頭 1,000 文字のみ表示')
  const secondCells = within(rows[2]).getAllByRole('cell')
  expect(secondCells[1]).toHaveTextContent('(null)')
  expect(secondCells[1].querySelector('[data-null]')).toBeNull()
})

test('page=2 は offset=50 を呼ぶ', async () => {
  const fetchMock = mockFetch({ [URL_P2]: { body: page(50, 50, { has_next: false }) } })
  renderTab(2)
  await waitFor(() => expect(screen.getByTestId('page-range')).toHaveTextContent('2 ページ目 (51〜100 行)'))
  expect(fetchMock.mock.calls[0][0]).toBe(URL_P2)
  await waitFor(() => expect(screen.getByRole('button', { name: '次へ >' })).toBeDisabled())
  expect(screen.getByRole('button', { name: '< 前へ' })).toBeEnabled()
})

test('再読み込みで同じ URL を取り直す', async () => {
  const fetchMock = mockFetch({ [URL_P1]: { body: page(0, 2) } })
  renderTab(1)
  await screen.findByRole('table', { name: 'データ' })
  fireEvent.click(screen.getByRole('button', { name: '再読み込み' }))
  await waitFor(() => expect(fetchMock.mock.calls.filter(([u]) => u === URL_P1)).toHaveLength(2))
})

test('ROWID の並び順', async () => {
  mockFetch({ [URL_P1]: { body: page(0, 1, { order_basis: 'ROWID', order_by: ['ROWID'] }) } })
  renderTab(1)
  expect(await screen.findByText('並び順: ROWID(主キーなし)')).toBeInTheDocument()
})

test('エラー表示と再試行', async () => {
  const fetchMock = mockFetch({
    [URL_P1]: { status: 502, body: { error: { code: 'ORACLE_ERROR', message: 'ORA-00942: table or view does not exist', ora_code: 'ORA-00942' } } },
  })
  renderTab(1)
  expect(await screen.findByText('[ORA-00942] ORA-00942: table or view does not exist')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: '再試行' }))
  await waitFor(() => expect(fetchMock.mock.calls.filter(([u]) => u === URL_P1)).toHaveLength(2))
})

test('0 行なら「データがありません」', async () => {
  mockFetch({ [URL_P1]: { body: page(0, 0, { has_next: false }) } })
  renderTab(1)
  expect(await screen.findByText('データがありません')).toBeInTheDocument()
})
