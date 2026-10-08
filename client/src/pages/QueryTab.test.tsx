import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { type ReactNode, useState } from 'react'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import type { TableDetail } from '../api/types'
import { EMPLOYEES_DETAIL } from '../test/detail'
import { mockFetch } from '../test/fetchMock'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import QueryTab, { caretLines, csvFileName, type QueryState, toUtf16Index } from './QueryTab'

const RESULT = {
  columns: [
    { name: 'EMPLOYEE_ID', data_type: 'NUMBER' },
    { name: 'COMMISSION_PCT', data_type: 'NUMBER' },
  ],
  rows: [
    ['100', null],
    ['101', '0.2'],
  ],
  truncated: [[], []],
  row_count: 2,
  has_more: false,
  max_rows: 500,
  elapsed_ms: 41,
}

function Host({ detail = EMPLOYEES_DETAIL, extra }: { detail?: TableDetail; extra?: ReactNode }) {
  const [state, setState] = useState<QueryState | null>(null)
  const [shown, setShown] = useState(true)
  return (
    <>
      <button onClick={() => setShown((v) => !v)}>切替</button>
      {shown && <QueryTab detail={detail} state={state} setState={setState} />}
      {extra}
    </>
  )
}

const editor = () => screen.getByRole('textbox', { name: 'SELECT 文' }) as HTMLTextAreaElement
const runButton = () => screen.getByRole('button', { name: /実行/ })

afterEach(() => vi.unstubAllGlobals())

describe('ひな形とチェックボックス', () => {
  beforeEach(() => {
    mockFetch({ '/api/schema': { body: HR_VIEW } })
  })

  test('初期値は外部キーを選んでいないひな形', async () => {
    renderWithProviders(<Host />)
    expect(editor().value).toMatch(/^SELECT\n {2}t0\.EMPLOYEE_ID,/)
    expect(editor().value).toContain('FROM HR.EMPLOYEES t0\nORDER BY t0.EMPLOYEE_ID')
    expect(await screen.findByRole('checkbox', { name: /→ DEPARTMENTS EMP_DEPT_FK/ })).toBeEnabled()
    expect(screen.getByRole('checkbox', { name: /→ OTHER\.DEPTS EMP_EXT_FK/ })).toBeDisabled()
    expect(screen.getByText('列情報なし')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /← DEPARTMENTS DEPT_MGR_FK/ })).toBeEnabled()
  })

  test('未編集ならチェックで自動的に置き換え、外すと元に戻る', async () => {
    renderWithProviders(<Host />)
    const cb = await screen.findByRole('checkbox', { name: /→ DEPARTMENTS EMP_DEPT_FK/ })
    fireEvent.click(cb)
    expect(editor().value).toContain('  LEFT JOIN HR.DEPARTMENTS t1 ON t1.DEPARTMENT_ID = t0.DEPARTMENT_ID')
    expect(editor().value).toContain('  t1.DEPARTMENT_NAME,')
    fireEvent.click(screen.getByRole('checkbox', { name: /← DEPARTMENTS DEPT_MGR_FK/ }))
    expect(editor().value).toContain('  LEFT JOIN HR.DEPARTMENTS t2 ON t2.MANAGER_ID = t0.EMPLOYEE_ID')
    fireEvent.click(cb)
    expect(editor().value).not.toContain('t2.')
    expect(editor().value).toContain('  LEFT JOIN HR.DEPARTMENTS t1 ON t1.MANAGER_ID = t0.EMPLOYEE_ID')
  })

  test('編集済みなら置き換えず、ひな形を作成で置き換える', async () => {
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: 'SELECT 1 FROM DUAL' } })
    fireEvent.click(await screen.findByRole('checkbox', { name: /→ DEPARTMENTS EMP_DEPT_FK/ }))
    expect(editor().value).toBe('SELECT 1 FROM DUAL')
    expect(screen.getByTestId('edited-notice')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'ひな形を作成' }))
    expect(editor().value).toContain('LEFT JOIN HR.DEPARTMENTS t1')
    expect(screen.queryByTestId('edited-notice')).not.toBeInTheDocument()
  })

  test('外部キーが無いとき', async () => {
    renderWithProviders(<Host detail={{ ...EMPLOYEES_DETAIL, foreign_keys: [], referenced_by: [] }} />)
    expect(await screen.findByText('外部キーでつながるテーブルはありません')).toBeInTheDocument()
  })

  test('空白だけ・100,000 文字超では実行できない', async () => {
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: '  \n ' } })
    expect(runButton()).toBeDisabled()
    expect(screen.getByRole('button', { name: 'CSV ダウンロード' })).toBeDisabled()
    fireEvent.change(editor(), { target: { value: 'x'.repeat(100_001) } })
    expect(runButton()).toBeDisabled()
    expect(screen.getByText('100,000 文字以内で入力してください')).toBeInTheDocument()
  })
})

describe('実行', () => {
  test('結果の表・行数・取得時間・(null)、タブを切り替えても残る', async () => {
    const fetchMock = mockFetch({ '/api/schema': { body: HR_VIEW }, 'POST /api/query': { body: RESULT } })
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: 'SELECT EMPLOYEE_ID, COMMISSION_PCT FROM HR.EMPLOYEES' } })
    fireEvent.click(runButton())
    const table = await screen.findByRole('table', { name: 'Query の結果' })
    expect(within(table).getAllByRole('row')).toHaveLength(3)
    expect(within(table).getByText('(null)')).toHaveAttribute('data-null', 'true')
    expect(screen.getByTestId('query-row-count')).toHaveTextContent('2 行')
    expect(screen.getByText('取得 41 ms')).toBeInTheDocument()
    expect(screen.queryByTestId('query-truncated')).not.toBeInTheDocument()
    const call = fetchMock.mock.calls.find(([u]) => u === '/api/query')!
    expect(JSON.parse(String(call[1]!.body))).toEqual({ sql: 'SELECT EMPLOYEE_ID, COMMISSION_PCT FROM HR.EMPLOYEES' })

    fireEvent.click(screen.getByRole('button', { name: '切替' }))
    fireEvent.click(screen.getByRole('button', { name: '切替' }))
    expect(editor().value).toBe('SELECT EMPLOYEE_ID, COMMISSION_PCT FROM HR.EMPLOYEES')
    expect(screen.getByRole('table', { name: 'Query の結果' })).toBeInTheDocument()
  })

  test('Ctrl+Enter で実行、500 行で打ち切りの表示', async () => {
    const rows = Array.from({ length: 500 }, (_, i) => [String(i), null])
    mockFetch({
      '/api/schema': { body: HR_VIEW },
      'POST /api/query': { body: { ...RESULT, rows, truncated: rows.map(() => []), row_count: 500, has_more: true } },
    })
    renderWithProviders(<Host />)
    fireEvent.keyDown(editor(), { key: 'Enter', ctrlKey: true })
    expect(await screen.findByTestId('query-truncated')).toHaveTextContent('先頭 500 行を表示しています(500 行で打ち切り)')
    expect(screen.getByTestId('query-row-count')).toHaveTextContent('500 行')
  })

  test('0 行', async () => {
    mockFetch({ '/api/schema': { body: HR_VIEW }, 'POST /api/query': { body: { ...RESULT, rows: [], truncated: [], row_count: 0 } } })
    renderWithProviders(<Host />)
    fireEvent.click(runButton())
    expect(await screen.findByText('結果は 0 行です')).toBeInTheDocument()
    expect(within(screen.getByRole('table', { name: 'Query の結果' })).getAllByRole('columnheader')).toHaveLength(2)
  })

  test('Oracle のエラーとエラー位置、エラー位置へ移動', async () => {
    const sql = '-- 日本語\nSELECT 1\nFROM T\nWHERE BAR = 1'
    mockFetch({
      '/api/schema': { body: HR_VIEW },
      'POST /api/query': {
        status: 502,
        body: { error: { code: 'ORACLE_ERROR', message: 'ORA-00904: "BAR": invalid identifier', ora_code: 'ORA-00904', position: { offset: 30, line: 4, column: 7 } } },
      },
    })
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: sql } })
    fireEvent.click(runButton())
    const alert = await screen.findByTestId('query-error')
    expect(alert).toHaveTextContent('SQL を実行できませんでした')
    expect(alert).toHaveTextContent('[ORA-00904] ORA-00904: "BAR": invalid identifier')
    expect(screen.getByTestId('query-error-position')).toHaveTextContent('エラー位置: 4 行目 7 文字目')
    expect(screen.getByTestId('query-error-caret').textContent).toBe('WHERE BAR = 1\n      ^')
    fireEvent.click(screen.getByRole('button', { name: 'エラー位置へ移動' }))
    expect(document.activeElement).toBe(editor())
    expect(editor().selectionStart).toBe(30)
    expect(editor().selectionEnd).toBe(31)
  })

  test('SQL_REJECTED の表示(位置なし)', async () => {
    mockFetch({
      '/api/schema': { body: HR_VIEW },
      'POST /api/query': { status: 422, body: { error: { code: 'SQL_REJECTED', message: 'SELECT または WITH で始まる問い合わせだけを実行できます(先頭: DELETE)' } } },
    })
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: 'DELETE FROM T' } })
    fireEvent.click(runButton())
    expect(await screen.findByTestId('query-error')).toHaveTextContent('実行できない SQL です: SELECT または WITH で始まる問い合わせだけを実行できます(先頭: DELETE)')
    expect(screen.queryByTestId('query-error-position')).not.toBeInTheDocument()
  })
})

describe('CSV ダウンロード', () => {
  test('Blob を保存させる', async () => {
    const createObjectURL = vi.fn(() => 'blob:x')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL, revokeObjectURL }))
    const clicks: string[] = []
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      clicks.push(this.download)
    })
    const fetchMock = vi.fn(async (url: string) =>
      url === '/api/query/csv'
        ? new Response('﻿A\r\n1\r\n', { status: 200, headers: { 'X-Row-Count': '1' } })
        : new Response(JSON.stringify(HR_VIEW), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<Host />)
    fireEvent.click(screen.getByRole('button', { name: 'CSV ダウンロード' }))
    await waitFor(() => expect(clicks).toHaveLength(1))
    expect(clicks[0]).toMatch(/^EMPLOYEES_query_\d{8}-\d{6}\.csv$/)
    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:x')
    click.mockRestore()
  })

  test('失敗はタブ内にエラー表示', async () => {
    mockFetch({
      '/api/schema': { body: HR_VIEW },
      'POST /api/query/csv': { status: 504, body: { error: { code: 'ORACLE_TIMEOUT', message: 'Oracle の応答がタイムアウトしました' } } },
    })
    renderWithProviders(<Host />)
    fireEvent.click(screen.getByRole('button', { name: 'CSV ダウンロード' }))
    const alert = await screen.findByTestId('query-error')
    expect(alert).toHaveTextContent('CSV を作成できませんでした')
    expect(alert).toHaveTextContent('Oracle の応答がタイムアウトしました')
  })
})

test('補助関数', () => {
  expect(csvFileName('EMPLOYEES', new Date(2026, 9, 4, 9, 5, 7))).toBe('EMPLOYEES_query_20261004-090507.csv')
  expect(caretLines('a\n\tSELECT ほげ X', 2, 12)).toEqual(['\tSELECT ほげ X', '\t       　　 ^'])
  expect(toUtf16Index('𠮷a', 1)).toBe(2)
})

// ※CR-005により追加: 保存済み Query の組み込み(P002 §2.2.8)
describe('保存済み Query', () => {
  const SAVED = {
    id: 5, scope: 'table' as const, owner: 'HR', table: 'EMPLOYEES', name: '部署50', description: '',
    sql: 'SELECT * FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50', is_template: false,
    created_at: '2026-10-07T12:00:00Z', updated_at: '2026-10-07T12:00:00Z',
  }

  test('このテーブルの一覧を取り、復元すると入力欄が変わって実行できる。チェックボックスで置き換わらない', async () => {
    const fetchMock = mockFetch({
      '/api/schema': { body: HR_VIEW },
      'GET /api/saved-queries': { body: { items: [SAVED] } },
      'POST /api/query': { body: RESULT },
    })
    renderWithProviders(<Host />)
    fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
    expect(editor().value).toBe(SAVED.sql)
    expect(fetchMock.mock.calls.some(([u]) => u === '/api/saved-queries?scope=table&owner=HR&table=EMPLOYEES')).toBe(true)
    // 未編集のひな形ではないので、チェックボックスでは置き換わらない
    fireEvent.click(await screen.findByRole('checkbox', { name: /→ DEPARTMENTS EMP_DEPT_FK/ }))
    expect(editor().value).toBe(SAVED.sql)
    fireEvent.click(runButton())
    await screen.findByRole('table', { name: 'Query の結果' })
    const call = fetchMock.mock.calls.find(([u]) => u === '/api/query')!
    expect(JSON.parse(String(call[1]!.body))).toEqual({ sql: SAVED.sql })
    // タブを切り替えても復元中が残る
    fireEvent.click(screen.getByRole('button', { name: '切替' }))
    fireEvent.click(screen.getByRole('button', { name: '切替' }))
    expect(screen.getByTestId('loaded-query')).toHaveTextContent('復元中: 部署50')
  })

  test('ひな形のままなら確認なしで復元、編集後は確認する', async () => {
    mockFetch({ '/api/schema': { body: HR_VIEW }, 'GET /api/saved-queries': { body: { items: [SAVED] } } })
    renderWithProviders(<Host />)
    fireEvent.click(await screen.findByRole('button', { name: '復元: 部署50' }))
    expect(screen.queryByRole('dialog')).toBeNull()
    fireEvent.change(editor(), { target: { value: 'SELECT 1 FROM DUAL' } })
    fireEvent.click(screen.getByRole('button', { name: '復元: 部署50' }))
    expect(screen.getByRole('dialog')).toHaveTextContent('入力欄の SQL を「部署50」で置き換えますか')
  })

  test('PDB(detail なし)の CSV のファイル名', () => {
    expect(csvFileName('PDB', new Date(2026, 9, 7, 21, 3, 4))).toBe('PDB_query_20261007-210304.csv')
  })
})
