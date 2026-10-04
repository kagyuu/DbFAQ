import type { ApiErrorBody, ErrorPosition, ErView, Health, QueryResult, RefreshResult, RowsPage, TableDetail } from './types'

export class ApiError extends Error {
  code: string
  status: number
  oraCode?: string
  position?: ErrorPosition

  constructor(code: string, status: number, message: string, oraCode?: string, position?: ErrorPosition) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.oraCode = oraCode
    this.position = position
  }

  /** 画面に出す文言。ORA コードがあれば先頭に [ORA-xxxxx] を付ける(P002 §1.3) */
  get displayMessage(): string {
    return this.oraCode ? `[${this.oraCode}] ${this.message}` : this.message
  }
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  let res: Response
  try {
    res = await fetch('/api' + path, init)
  } catch {
    throw new ApiError('NETWORK_ERROR', 0, 'サーバに接続できません')
  }
  if (!res.ok) {
    let body: ApiErrorBody | undefined
    try {
      body = (await res.json()) as ApiErrorBody
    } catch {
      body = undefined
    }
    if (body?.error?.code) {
      const e = body.error
      throw new ApiError(e.code, res.status, e.message, e.ora_code ?? undefined, e.position ?? undefined)
    }
    throw new ApiError('INTERNAL_ERROR', res.status, `サーバでエラーが発生しました (HTTP ${res.status})`)
  }
  return res
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return (await (await send(path, init)).json()) as T
}

const postSql = (sql: string): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ sql }),
})

const seg = (s: string) => encodeURIComponent(s)

export const getSchema = () => request<ErView>('/schema')
export const refreshSchema = () => request<RefreshResult>('/schema/refresh', { method: 'POST' })
export const getTableDetail = (owner: string, table: string) =>
  request<TableDetail>(`/schema/tables/${seg(owner)}/${seg(table)}`)
export const getTableRows = (owner: string, table: string, offset: number, limit: number) =>
  request<RowsPage>(`/schema/tables/${seg(owner)}/${seg(table)}/rows?offset=${offset}&limit=${limit}`)
export const getHealth = () => request<Health>('/health')
export const runQuery = (sql: string) => request<QueryResult>('/query', postSql(sql))

/** 全行の CSV(P002 §3.9)を Blob で受け取る */
export async function fetchQueryCsv(sql: string): Promise<{ blob: Blob; rowCount: number | null }> {
  const res = await send('/query/csv', postSql(sql))
  const n = res.headers.get('X-Row-Count')
  return { blob: await res.blob(), rowCount: n === null ? null : Number(n) }
}
