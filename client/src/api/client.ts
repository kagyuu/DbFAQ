import type { ApiErrorBody, ErView, Health, RefreshResult, RowsPage, TableDetail } from './types'

export class ApiError extends Error {
  code: string
  status: number
  oraCode?: string

  constructor(code: string, status: number, message: string, oraCode?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.oraCode = oraCode
  }

  /** 画面に出す文言。ORA コードがあれば先頭に [ORA-xxxxx] を付ける(P002 §1.3) */
  get displayMessage(): string {
    return this.oraCode ? `[${this.oraCode}] ${this.message}` : this.message
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
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
      throw new ApiError(body.error.code, res.status, body.error.message, body.error.ora_code ?? undefined)
    }
    throw new ApiError('INTERNAL_ERROR', res.status, `サーバでエラーが発生しました (HTTP ${res.status})`)
  }
  return (await res.json()) as T
}

const seg = (s: string) => encodeURIComponent(s)

export const getSchema = () => request<ErView>('/schema')
export const refreshSchema = () => request<RefreshResult>('/schema/refresh', { method: 'POST' })
export const getTableDetail = (owner: string, table: string) =>
  request<TableDetail>(`/schema/tables/${seg(owner)}/${seg(table)}`)
export const getTableRows = (owner: string, table: string, offset: number, limit: number) =>
  request<RowsPage>(`/schema/tables/${seg(owner)}/${seg(table)}/rows?offset=${offset}&limit=${limit}`)
export const getHealth = () => request<Health>('/health')
