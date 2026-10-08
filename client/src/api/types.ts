// backend API のレスポンス型(docs/P002-frontend-spec.md §3)

export interface SnapshotSummary {
  owner: string
  fetched_at: string
  oracle_version: string
  table_count: number
  relation_count: number
}

export interface ErColumn {
  name: string
  column_id: number
  data_type_display: string
  nullable: boolean
  is_pk: boolean
  is_fk: boolean
}

export interface ErTable {
  owner: string
  name: string
  comment: string | null
  num_rows: number | null
  columns: ErColumn[]
}

export interface Relation {
  name: string
  from_owner: string
  from_table: string
  from_columns: string[]
  to_owner: string | null
  to_table: string | null
  to_columns: (string | null)[]
}

export interface ErView {
  loaded: boolean
  snapshot: SnapshotSummary | null
  tables: ErTable[]
  relations: Relation[]
}

export interface RefreshResult {
  snapshot: SnapshotSummary
}

export interface DetailColumn {
  column_id: number
  name: string
  data_type: string
  data_type_display: string
  data_length: number | null
  data_precision: number | null
  data_scale: number | null
  nullable: boolean
  data_default: string | null
  comment: string | null
  pk_position: number | null
  is_fk: boolean
}

export interface KeyConstraint {
  name: string
  columns: string[]
}

export interface ForeignKey {
  name: string
  columns: string[]
  ref_owner: string | null
  ref_table: string | null
  ref_columns: (string | null)[]
  delete_rule: string | null
  ref_in_snapshot: boolean
}

export interface ReferencedBy {
  name: string
  from_owner: string
  from_table: string
  from_columns: string[]
  columns: (string | null)[]
}

export interface IndexInfo {
  name: string
  unique: boolean
  index_type: string
  columns: { name: string; descending: boolean }[]
}

export interface TableDetail {
  snapshot: { owner: string; fetched_at: string }
  table: {
    owner: string
    name: string
    comment: string | null
    num_rows: number | null
    last_analyzed: string | null
    iot: boolean
  }
  columns: DetailColumn[]
  primary_key: KeyConstraint | null
  unique_keys: KeyConstraint[]
  foreign_keys: ForeignKey[]
  referenced_by: ReferencedBy[]
  indexes: IndexInfo[]
}

export interface RowsPage {
  owner: string
  table: string
  columns: { name: string; data_type: string }[]
  rows: (string | null)[][]
  truncated: number[][]
  offset: number
  limit: number
  has_next: boolean
  order_basis: 'PRIMARY_KEY' | 'ROWID'
  order_by: string[]
  elapsed_ms: number
}

export interface Health {
  status: 'ok' | 'degraded'
  backend: { status: string; version: string }
  oracle: { status: 'ok' | 'error'; version: string | null; user: string | null; message: string | null }
  config: {
    host: string
    port: number
    service_name: string
    user: string
    schema: string
    query_timeout_sec: number
  }
  checked_at: string
}

/** Query の SQL のエラー位置(P002 §3.1。offset・column はコードポイント単位、line・column は 1 始まり) */
export interface ErrorPosition {
  offset: number
  line: number
  column: number
}

export interface ApiErrorBody {
  error: { code: string; message: string; ora_code?: string; position?: ErrorPosition }
}

/** POST /api/query の結果(P002 §3.8) */
export interface QueryResult {
  columns: { name: string; data_type: string }[]
  rows: (string | null)[][]
  truncated: number[][]
  row_count: number
  has_more: boolean
  max_rows: number
  elapsed_ms: number
}

/** 保存済み Query の保存先(P002 §2.2.8。※CR-005により追加) */
export type SavedQueryTarget = { scope: 'table'; owner: string; table: string } | { scope: 'pdb' }

/** 保存済み Query(P002 §3.10) */
export interface SavedQuery {
  id: number
  scope: 'table' | 'pdb'
  owner: string | null
  table: string | null
  name: string
  description: string
  sql: string
  is_template: boolean
  created_at: string
  updated_at: string
}

export interface SavedQueryList {
  items: SavedQuery[]
}

/** GET /api/pdb のセクション(P002 §3.14) */
export interface PdbSection {
  key: string
  title: string
  columns: { name: string; data_type: string }[]
  rows: (string | null)[][]
  truncated: number[][]
  error: { code: string; message: string; ora_code?: string | null } | null
}

export interface PdbInfo {
  sections: PdbSection[]
  fetched_at: string
  elapsed_ms: number
}
