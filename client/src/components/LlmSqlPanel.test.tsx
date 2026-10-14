import { fireEvent, screen, within } from '@testing-library/react'
import { useState } from 'react'
import { afterEach, describe, expect, test, vi } from 'vitest'
import type { LlmHealth } from '../api/types'
import { EMPLOYEES_DETAIL } from '../test/detail'
import { HEALTH_OK, mockFetch } from '../test/fetchMock'
import { HR_VIEW } from '../test/hr'
import { renderWithProviders } from '../test/render'
import QueryTab, { type QueryState } from '../pages/QueryTab'

afterEach(() => vi.unstubAllGlobals())

const GENERATED = {
  sql: 'SELECT LAST_NAME, SALARY FROM HR.EMPLOYEES ORDER BY SALARY DESC FETCH FIRST 5 ROWS ONLY',
  guard: { ok: true, message: null },
  model: 'gemma4:e2b-it-qat',
  elapsed_ms: 16600,
  context: { tables: ['HR.EMPLOYEES', 'HR.DEPARTMENTS'], sample_rows: 3, truncated: false },
  exchange: { system: 'You are an expert in Oracle SQL.', user: '# Database\nOracle\n\n# Request\n給与の高い社員を上位5人\n', reply: '```sql\nSELECT 1\n```' },
}

function Host({ pdb = false }: { pdb?: boolean }) {
  const [state, setState] = useState<QueryState | null>(null)
  return <QueryTab detail={pdb ? undefined : EMPLOYEES_DETAIL} state={state} setState={setState} />
}

const routes = (llm: LlmHealth = HEALTH_OK.llm as LlmHealth, gen: unknown = { body: GENERATED }) => ({
  '/api/health': { body: { ...HEALTH_OK, llm } },
  '/api/schema': { body: HR_VIEW },
  'GET /api/saved-queries': { body: { items: [] } },
  'POST /api/llm/sql': gen as { body: unknown },
})
const editor = () => screen.getByRole('textbox', { name: 'SELECT 文' }) as HTMLTextAreaElement
const requestBox = () => screen.getByRole('textbox', { name: 'LLM への要求' })
const genButton = () => screen.getByRole('button', { name: 'LLM で SQL を作成' })

describe('LLM で SQL を作成(※CR-007)', () => {
  test('LLM が使えないとボタンを押せず、理由を表示する', async () => {
    mockFetch(routes({ status: 'error', model: 'm', base_url: 'u', message: 'LLM に接続できません' }))
    renderWithProviders(<Host />)
    fireEvent.change(requestBox(), { target: { value: '社員の数' } })
    expect(await screen.findByTestId('llm-unavailable')).toHaveTextContent('LLM が使えないため作成できません')
    expect(genButton()).toBeDisabled()
  })

  test('要求が空白だけ・2,001 文字では押せない', async () => {
    mockFetch(routes())
    renderWithProviders(<Host />)
    await vi.waitFor(() => expect(screen.queryByTestId('llm-unavailable')).toBeNull())
    expect(genButton()).toBeDisabled()
    fireEvent.change(requestBox(), { target: { value: '   ' } })
    expect(genButton()).toBeDisabled()
    fireEvent.change(requestBox(), { target: { value: 'あ'.repeat(2001) } })
    expect(genButton()).toBeDisabled()
    expect(screen.getByText('2,000 文字以内で入力してください')).toBeInTheDocument()
    fireEvent.change(requestBox(), { target: { value: '社員の数' } })
    expect(genButton()).toBeEnabled()
  })

  test('作成すると入力欄に入り、結果の情報を出す。自動では実行しない', async () => {
    const fetchMock = mockFetch(routes())
    renderWithProviders(<Host />)
    fireEvent.change(requestBox(), { target: { value: '  給与の高い社員を上位5人  ' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    expect(await screen.findByTestId('llm-result')).toHaveTextContent('LLM(gemma4:e2b-it-qat)が作成しました(16.6 秒)。内容を確かめてから実行してください')
    expect(editor().value).toBe(GENERATED.sql)
    const post = fetchMock.mock.calls.find((c) => c[0] === '/api/llm/sql')!
    expect(JSON.parse(String(post[1]!.body))).toEqual({ scope: 'table', owner: 'HR', table: 'EMPLOYEES', request: '給与の高い社員を上位5人' })
    expect(fetchMock.mock.calls.some((c) => c[0] === '/api/query')).toBe(false)
    expect(screen.queryByTestId('llm-guard-error')).toBeNull()
  })

  test('入力欄が編集中なら置き換える前に確認する', async () => {
    mockFetch(routes())
    renderWithProviders(<Host />)
    fireEvent.change(editor(), { target: { value: 'SELECT 1 FROM DUAL' } })
    fireEvent.change(requestBox(), { target: { value: '社員の数' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    const dialog = await screen.findByRole('dialog')
    expect(dialog).toHaveTextContent('入力欄の SQL を LLM が作成した SQL で置き換えますか')
    fireEvent.click(within(dialog).getByRole('button', { name: 'キャンセル' }))
    expect(editor().value).toBe('SELECT 1 FROM DUAL')
    expect(screen.getByTestId('llm-result')).toBeInTheDocument()
    fireEvent.click(genButton())
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: '置き換える' }))
    expect(editor().value).toBe(GENERATED.sql)
  })

  test('検査に通らない SQL・省略の表示', async () => {
    mockFetch(routes(undefined, { body: { ...GENERATED, sql: 'DELETE FROM HR.EMPLOYEES', guard: { ok: false, message: '更新系' }, context: { ...GENERATED.context, truncated: true } } }))
    renderWithProviders(<Host />)
    fireEvent.change(requestBox(), { target: { value: 'x' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    expect(await screen.findByTestId('llm-guard-error')).toHaveTextContent('Query の検査で実行できない SQL です: 更新系')
    expect(screen.getByText('スキーマの情報が長いため、一部のテーブルを省いて LLM に渡しました')).toBeInTheDocument()
    expect(editor().value).toBe('DELETE FROM HR.EMPLOYEES')
  })

  test.each([
    [503, 'LLM_UNAVAILABLE', 'LLM を使えません: LLM に接続できません'],
    [504, 'LLM_TIMEOUT', 'LLM の応答がタイムアウトしました'],
    [502, 'LLM_ERROR', 'LLM の応答から SQL を作れませんでした: LLM に接続できません'],
  ])('エラー %s は部品の中に表示し、入力欄は変えない', async (status, code, text) => {
    const fetchMock = mockFetch(routes(undefined, { status, body: { error: { code, message: 'LLM に接続できません' } } }))
    renderWithProviders(<Host />)
    const before = editor().value
    fireEvent.change(requestBox(), { target: { value: 'x' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    const healthCalls = () => fetchMock.mock.calls.filter((c) => c[0] === '/api/health').length
    const h0 = healthCalls()
    fireEvent.click(genButton())
    expect(await screen.findByTestId('llm-error')).toHaveTextContent(text)
    expect(editor().value).toBe(before)
    if (code === 'LLM_UNAVAILABLE') await vi.waitFor(() => expect(healthCalls()).toBeGreaterThan(h0)) // health を取り直す
  })

  test('PDB(detail なし)は scope=pdb で送る', async () => {
    const fetchMock = mockFetch(routes())
    renderWithProviders(<Host pdb />)
    fireEvent.change(requestBox(), { target: { value: 'USERS 表領域' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    await screen.findByTestId('llm-result')
    const post = fetchMock.mock.calls.find((c) => c[0] === '/api/llm/sql')!
    expect(JSON.parse(String(post[1]!.body))).toEqual({ scope: 'pdb', request: 'USERS 表領域' })
  })
})


// ※CR-008により追加: LLM とのやりとり(P002 §2.2.9)
describe('LLM とのやりとり(※CR-008)', () => {
  const exchangeButton = () => screen.getByRole('button', { name: 'LLM とのやりとり' })

  test('作成するまで押せず、作成後はリクエストとリプライを表示してコピーできる', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    mockFetch(routes())
    renderWithProviders(<Host />)
    expect(exchangeButton()).toBeDisabled()
    fireEvent.change(requestBox(), { target: { value: '給与の高い社員を上位5人' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    await screen.findByTestId('llm-result')
    expect(exchangeButton()).toBeEnabled()
    fireEvent.click(exchangeButton())
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('モデル: gemma4:e2b-it-qat / 16.6 秒')).toBeInTheDocument()
    expect(within(dialog).getByTestId('llm-exchange-system')).toHaveTextContent('You are an expert in Oracle SQL.')
    expect(within(dialog).getByTestId('llm-exchange-user')).toHaveTextContent('# Request 給与の高い社員を上位5人')
    expect(within(dialog).getByTestId('llm-exchange-reply')).toHaveTextContent('SELECT 1')
    fireEvent.click(within(dialog).getByRole('button', { name: 'コピー: リプライ' }))
    await vi.waitFor(() => expect(writeText).toHaveBeenCalledWith('```sql\nSELECT 1\n```'))
    fireEvent.click(within(dialog).getByRole('button', { name: '閉じる' }))
    await vi.waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  })

  test('エラーのときも表示でき、リプライが無いことが分かる', async () => {
    mockFetch(routes(undefined, {
      status: 504,
      body: { error: { code: 'LLM_TIMEOUT', message: 'timeout', exchange: { system: 'S', user: 'U', reply: null } } },
    }))
    renderWithProviders(<Host />)
    fireEvent.change(requestBox(), { target: { value: 'x' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    await screen.findByTestId('llm-error')
    fireEvent.click(exchangeButton())
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByTestId('llm-exchange-user')).toHaveTextContent('U')
    expect(within(dialog).getByTestId('llm-exchange-reply')).toHaveTextContent('リプライはありません(LLM から応答が返りませんでした)')
    expect(within(dialog).queryByRole('button', { name: 'コピー: リプライ' })).toBeNull()
  })

  test('exchange の無いエラー(設定なしなど)では押せない', async () => {
    mockFetch(routes(undefined, { status: 503, body: { error: { code: 'LLM_UNAVAILABLE', message: 'LLM は設定されていません' } } }))
    renderWithProviders(<Host />)
    fireEvent.change(requestBox(), { target: { value: 'x' } })
    await vi.waitFor(() => expect(genButton()).toBeEnabled())
    fireEvent.click(genButton())
    await screen.findByTestId('llm-error')
    expect(exchangeButton()).toBeDisabled()
  })
})
