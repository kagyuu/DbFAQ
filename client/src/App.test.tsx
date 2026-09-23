import { screen } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import App from './App'
import { HEALTH_OK, NOT_LOADED, mockFetch } from './test/fetchMock'
import { renderWithProviders } from './test/render'

// U004-T4 で / のプレースホルダを ER 図画面に置き換えたため、/ の確認を ER 図画面の表示に更新した
afterEach(() => vi.unstubAllGlobals())

test('/ は ER 図画面(共通ヘッダ付き)を表示する', async () => {
  mockFetch({ '/api/schema': { body: NOT_LOADED }, '/api/health': { body: HEALTH_OK } })
  renderWithProviders(<App />, { route: '/' })
  expect(await screen.findByText('スキーマ情報がありません')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'DbFAQ' })).toHaveAttribute('href', '/')
})

test('存在しない URL は「ページが見つかりません」', () => {
  renderWithProviders(<App />, { route: '/nope' })
  expect(screen.getByText('ページが見つかりません')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'ER 図へ' })).toHaveAttribute('href', '/')
})
