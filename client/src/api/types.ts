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

export interface ApiErrorBody {
  error: { code: string; message: string; ora_code?: string }
}
