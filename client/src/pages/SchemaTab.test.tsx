import { screen, within } from '@testing-library/react'
import { expect, test } from 'vitest'
import { EMPLOYEES_DETAIL } from '../test/detail'
import { renderWithProviders } from '../test/render'
import SchemaTab from './SchemaTab'

const table = (name: string) => screen.getByRole('table', { name })

test('列・主キー・一意制約・統計', () => {
  renderWithProviders(<SchemaTab detail={EMPLOYEES_DETAIL} />)
  const rows = within(table('列')).getAllByRole('row').slice(1)
  expect(rows.map((r) => within(r).getAllByRole('cell')[1].textContent)).toEqual([
    'EMPLOYEE_ID', 'LAST_NAME', 'SALARY', 'MANAGER_ID', 'DEPARTMENT_ID', 'DEPT_CODE',
  ])
  const first = within(rows[0]).getAllByRole('cell').map((c) => c.textContent)
  expect(first.slice(2, 6)).toEqual(['NUMBER(6)', '不可', '', '🔑 1'])
  expect(within(table('主キー')).getByText('EMP_EMP_ID_PK')).toBeInTheDocument()
  expect(within(table('一意制約')).getByText('EMP_EMAIL_UK')).toBeInTheDocument()
  expect(screen.getByTestId('num-rows')).toHaveTextContent('107')
})

test('外部キーのリンク(参照先・自己参照・参照元)', () => {
  renderWithProviders(<SchemaTab detail={EMPLOYEES_DETAIL} />)
  const fks = table('外部キー(参照先)')
  expect(within(fks).getByRole('link', { name: 'DEPARTMENTS' })).toHaveAttribute('href', '/tables/HR/DEPARTMENTS')
  expect(within(fks).getByRole('link', { name: 'EMPLOYEES' })).toHaveAttribute('href', '/tables/HR/EMPLOYEES')
  // 別スキーマ(スナップショットに無い)参照先はリンクにしない
  expect(within(fks).queryByRole('link', { name: 'DEPTS' })).toBeNull()
  expect(within(fks).getByText(/DEPTS/)).toBeInTheDocument()
  const refs = table('外部キー(参照元)')
  expect(within(refs).getByRole('link', { name: 'DEPARTMENTS' })).toHaveAttribute('href', '/tables/HR/DEPARTMENTS')
})

test('インデックスの DESC', () => {
  renderWithProviders(<SchemaTab detail={EMPLOYEES_DETAIL} />)
  expect(within(table('インデックス')).getByText('SALARY DESC')).toBeInTheDocument()
})

test('主キーなし・統計なし・インデックスなし', () => {
  renderWithProviders(
    <SchemaTab
      detail={{ ...EMPLOYEES_DETAIL, primary_key: null, indexes: [], table: { ...EMPLOYEES_DETAIL.table, num_rows: null } }}
    />,
  )
  expect(screen.getByText('主キーなし')).toBeInTheDocument()
  expect(screen.getByTestId('num-rows')).toHaveTextContent('統計なし')
  expect(screen.queryByRole('table', { name: 'インデックス' })).toBeNull()
  expect(screen.getAllByText('なし').length).toBeGreaterThanOrEqual(1)
})
