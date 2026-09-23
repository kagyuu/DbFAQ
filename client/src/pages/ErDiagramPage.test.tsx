import { fireEvent, screen, waitFor } from '@testing-library/react'
import { Route, Routes, useParams } from 'react-router-dom'
import { afterEach, expect, test, vi } from 'vitest'
import { HEALTH_OK, NOT_LOADED, mockFetch } from '../test/fetchMock'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import ErDiagramPage from './ErDiagramPage'

afterEach(() => vi.unstubAllGlobals())

function Detail() {
  const { owner, table } = useParams()
  return <div data-testid="detail">{`${owner}.${table}`}</div>
}

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/" element={<ErDiagramPage />} />
      <Route path="/tables/:owner/:table" element={<Detail />} />
    </Routes>,
  )
}

const REFRESHED = { snapshot: { ...HR_VIEW.snapshot } }

test('ER 図のノード・ミニマップ・コントロールを表示する', async () => {
  mockFetch({ '/api/schema': { body: HR_VIEW }, '/api/health': { body: HEALTH_OK } })
  const { container } = renderPage()
  expect(await screen.findByTestId('er-node-EMPLOYEES')).toBeInTheDocument()
  expect(screen.getAllByTestId(/^er-node-/)).toHaveLength(7)
  expect(container.querySelector('.react-flow__minimap')).not.toBeNull()
  expect(container.querySelector('.react-flow__controls')).not.toBeNull()
  expect(screen.getByText('テーブル 7 / 関連 10')).toBeInTheDocument()
})

test('ノードをクリックするとテーブル詳細へ遷移する', async () => {
  mockFetch({ '/api/schema': { body: HR_VIEW }, '/api/health': { body: HEALTH_OK } })
  renderPage()
  fireEvent.click(await screen.findByTestId('er-node-EMPLOYEES'))
  expect(await screen.findByTestId('detail')).toHaveTextContent('HR.EMPLOYEES')
})

test('未取得なら「スキーマ情報がありません」と読み込みボタン。読み込むと通知して取り直す', async () => {
  let loaded = false
  const fetchMock = mockFetch({
    '/api/schema': () => ({ body: loaded ? HR_VIEW : NOT_LOADED }),
    'POST /api/schema/refresh': () => {
      loaded = true
      return { body: REFRESHED }
    },
    '/api/health': { body: HEALTH_OK },
  })
  renderPage()
  fireEvent.click(await screen.findByRole('button', { name: 'Oracle から読み込む' }))
  expect(await screen.findByText('スキーマ情報を更新しました(テーブル 7 / 関連 10)')).toBeInTheDocument()
  expect(await screen.findByTestId('er-node-REGIONS')).toBeInTheDocument()
  expect(fetchMock.mock.calls.filter(([u]) => u === '/api/schema').length).toBeGreaterThanOrEqual(2)
})

test('テーブル 0 件', async () => {
  mockFetch({ '/api/schema': { body: { ...HR_VIEW, tables: [], relations: [] } }, '/api/health': { body: HEALTH_OK } })
  renderPage()
  expect(await screen.findByText('テーブルがありません(スキーマ: HR)')).toBeInTheDocument()
})

test('再読み込みの失敗は通知し、ER 図は残す', async () => {
  mockFetch({
    '/api/schema': { body: HR_VIEW },
    'POST /api/schema/refresh': { status: 502, body: { error: { code: 'ORACLE_ERROR', message: 'ORA-01017: invalid credential', ora_code: 'ORA-01017' } } },
    '/api/health': { body: HEALTH_OK },
  })
  renderPage()
  await screen.findByTestId('er-node-EMPLOYEES')
  fireEvent.click(screen.getByRole('button', { name: 'Oracle から再読み込み' }))
  expect(await screen.findByText('[ORA-01017] ORA-01017: invalid credential')).toBeInTheDocument()
  await waitFor(() => expect(screen.getAllByTestId(/^er-node-/)).toHaveLength(7))
})
