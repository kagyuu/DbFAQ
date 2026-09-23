import { screen, waitFor } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { HEALTH_OK, NOT_LOADED, mockFetch } from '../test/fetchMock'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import AppShell from './AppShell'

afterEach(() => vi.unstubAllGlobals())

test('スキーマ名と取得日時、Oracle の状態 ok', async () => {
  mockFetch({ '/api/schema': { body: HR_VIEW }, '/api/health': { body: HEALTH_OK } })
  renderWithProviders(<AppShell>body</AppShell>)
  expect(await screen.findByText('スキーマ: HR')).toBeInTheDocument()
  expect(screen.getByTestId('header-fetched-at')).toHaveTextContent('取得日時: 2026-09-23 01:15:02')
  await waitFor(() => expect(screen.getByTestId('oracle-status')).toHaveAttribute('data-status', 'ok'))
})

test('未取得なら「未取得」、Oracle エラーなら error', async () => {
  mockFetch({
    '/api/schema': { body: NOT_LOADED },
    '/api/health': { body: { ...HEALTH_OK, status: 'degraded', oracle: { status: 'error', version: null, user: null, message: 'ORA-12541' } } },
  })
  renderWithProviders(<AppShell>body</AppShell>)
  expect(await screen.findByText('スキーマ: 未取得')).toBeInTheDocument()
  expect(screen.queryByTestId('header-fetched-at')).toBeNull()
  await waitFor(() => expect(screen.getByTestId('oracle-status')).toHaveAttribute('data-status', 'error'))
})
