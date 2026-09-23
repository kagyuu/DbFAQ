import { fireEvent, screen, waitFor } from '@testing-library/react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, expect, test, vi } from 'vitest'
import { HEALTH_OK, mockFetch } from '../test/fetchMock'
import { EMPLOYEES_DETAIL } from '../test/detail'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import TableDetailPage from './TableDetailPage'

afterEach(() => vi.unstubAllGlobals())

function Location() {
  const loc = useLocation()
  return <div data-testid="location">{loc.pathname + loc.search}</div>
}

function renderAt(route: string) {
  return renderWithProviders(
    <>
      <Routes>
        <Route path="/tables/:owner/:table" element={<TableDetailPage />} />
      </Routes>
      <Location />
    </>,
    { route },
  )
}

const routes = {
  '/api/schema/tables/HR/EMPLOYEES/rows': { body: { owner: 'HR', table: 'EMPLOYEES', columns: [], rows: [], truncated: [], offset: 0, limit: 50, has_next: false, order_basis: 'PRIMARY_KEY', order_by: ['EMPLOYEE_ID'], elapsed_ms: 1 } },
  '/api/schema/tables/HR/EMPLOYEES': { body: EMPLOYEES_DETAIL },
  '/api/schema/tables/HR/NOPE': { status: 404, body: { error: { code: 'TABLE_NOT_FOUND', message: 'x' } } },
  '/api/schema': { body: HR_VIEW },
  '/api/health': { body: HEALTH_OK },
}

test('見出しとコメント、既定はスキーマ情報タブで rows を呼ばない', async () => {
  const fetchMock = mockFetch(routes)
  renderAt('/tables/HR/EMPLOYEES')
  expect(await screen.findByRole('heading', { name: 'HR.EMPLOYEES' })).toBeInTheDocument()
  // U005-T2 でスキーマ情報タブにもコメントが出るようになったため、見出し直下とタブの 2 か所を許容する
  expect(screen.getAllByText('employees table').length).toBeGreaterThanOrEqual(1)
  expect(screen.getByRole('tab', { name: 'スキーマ情報' })).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByTestId('schema-tab')).toBeInTheDocument()
  expect(fetchMock.mock.calls.some(([u]) => String(u).includes('/rows'))).toBe(false)
})

test('?tab=data でデータタブ', async () => {
  mockFetch(routes)
  renderAt('/tables/HR/EMPLOYEES?tab=data')
  expect(await screen.findByRole('tab', { name: 'データ' })).toHaveAttribute('aria-selected', 'true')
  expect(screen.getByTestId('data-tab')).toBeInTheDocument()
})

test('タブのクリックで URL の tab が変わる', async () => {
  mockFetch(routes)
  renderAt('/tables/HR/EMPLOYEES')
  fireEvent.click(await screen.findByRole('tab', { name: 'データ' }))
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/tables/HR/EMPLOYEES?tab=data&page=1'))
  fireEvent.click(screen.getByRole('tab', { name: 'スキーマ情報' }))
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/tables/HR/EMPLOYEES?tab=schema'))
})

test('TABLE_NOT_FOUND', async () => {
  mockFetch(routes)
  renderAt('/tables/HR/NOPE')
  expect(await screen.findByText('テーブルが見つかりません: HR.NOPE')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'ER 図へ' })).toHaveAttribute('href', '/')
})

test('SCHEMA_NOT_LOADED', async () => {
  mockFetch({ ...routes, '/api/schema/tables/HR/EMPLOYEES': { status: 404, body: { error: { code: 'SCHEMA_NOT_LOADED', message: 'x' } } } })
  renderAt('/tables/HR/EMPLOYEES')
  expect(await screen.findByText('スキーマ情報がありません')).toBeInTheDocument()
})
