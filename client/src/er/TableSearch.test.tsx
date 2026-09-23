import { fireEvent, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import TableSearch from './TableSearch'

function setup() {
  const onFocusTable = vi.fn()
  const onOpenTable = vi.fn()
  renderWithProviders(<TableSearch tables={HR_VIEW.tables} onFocusTable={onFocusTable} onOpenTable={onOpenTable} />)
  return { onFocusTable, onOpenTable, input: screen.getByLabelText('テーブル名で検索') }
}

test('部分一致・大文字小文字を区別しない候補', async () => {
  const { input } = setup()
  await userEvent.type(input, 'emp')
  expect(screen.getByRole('option')).toHaveTextContent('EMPLOYEES')
})

test('129 文字以上は入力できない', () => {
  const { input } = setup()
  expect(input).toHaveAttribute('maxLength', '128')
})

test('Enter で先頭候補にフォーカス', async () => {
  const { input, onFocusTable } = setup()
  await userEvent.type(input, 'job{Enter}')
  expect(onFocusTable).toHaveBeenCalledWith(expect.objectContaining({ name: 'JOBS' }))
})

test('「開く」で onOpenTable', async () => {
  const { input, onOpenTable } = setup()
  await userEvent.type(input, 'job_h')
  fireEvent.click(screen.getByRole('button', { name: 'JOB_HISTORY を開く' }))
  expect(onOpenTable).toHaveBeenCalledWith(expect.objectContaining({ name: 'JOB_HISTORY' }))
})

test('空白だけなら候補を出さない', async () => {
  const { input } = setup()
  await userEvent.type(input, '   ')
  expect(screen.queryByRole('option')).toBeNull()
})
