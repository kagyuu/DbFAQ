import { screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { HEALTH_OK, NOT_LOADED, mockFetch } from '../test/fetchMock'
import { renderWithProviders } from '../test/render'
import AppShell from './AppShell'

afterEach(() => vi.unstubAllGlobals())

// ※CR-007により追加: ヘッダの LLM の丸(P002 §1.1)
test.each([
  ['ok', HEALTH_OK.llm, 'LLM gemma4:e2b-it-qat / http://localhost:11434'],
  ['error', { status: 'error', model: 'gemma4:e2b-it-qat', base_url: 'http://x:11434', message: 'LLM に接続できません: refused' },
    'LLM に接続できません: refused / http://x:11434'],
  ['disabled', { status: 'disabled', model: null, base_url: null, message: 'LLM は設定されていません' }, 'LLM は設定されていません'],
])('LLM の丸(%s)は Oracle の丸の並びに出る', async (status, llm, label) => {
  mockFetch({ '/api/health': { body: { ...HEALTH_OK, llm } }, '/api/schema': { body: NOT_LOADED } })
  renderWithProviders(<AppShell><div /></AppShell>)
  const dot = await screen.findByTestId('llm-status')
  await vi.waitFor(() => expect(dot).toHaveAttribute('data-status', status))
  expect(dot).toHaveAttribute('aria-label', `LLM: ${label}`)
  expect(screen.getByText('LLM')).toBeInTheDocument()
  expect(screen.getByTestId('oracle-status')).toHaveAttribute('data-status', 'ok') // Oracle は影響を受けない
})
