// Query タブの SELECT 文のひな形(P002 §2.2.6・§2.2.7)。スキーマ情報(SQLite のスナップショット)だけから作る
import type { ErColumn, ErView, TableDetail } from '../api/types'

/** JOIN するテーブルの候補(外部キー 1 制約 = 1 件) */
export interface JoinCandidate {
  /** `parent:制約名` / `child:制約名`(同じ自己参照の制約が両方向に出るため向きを含める) */
  key: string
  /** parent = このテーブルが参照するテーブル(→)、child = このテーブルを参照するテーブル(←) */
  direction: 'parent' | 'child'
  constraint: string
  owner: string | null
  table: string | null
  /** このテーブル側の列(位置順) */
  ownColumns: (string | null)[]
  /** 相手のテーブル側の列(位置順) */
  otherColumns: (string | null)[]
  /** 相手のテーブルの列(column_id 順)。列情報が無ければ空 */
  columns: ErColumn[]
  /** 相手の列情報がスナップショットにあり、JOIN の列がすべて分かる */
  available: boolean
}

const MAX_IDENTIFIER = 128

// Oracle の予約語(V$RESERVED_WORDS の RESERVED='Y' 相当)。これに当たる名前は " で囲む
const RESERVED = new Set(
  (
    'ACCESS ADD ALL ALTER AND ANY AS ASC AUDIT BETWEEN BY CHAR CHECK CLUSTER COLUMN COMMENT COMPRESS CONNECT CREATE ' +
    'CURRENT DATE DECIMAL DEFAULT DELETE DESC DISTINCT DROP ELSE EXCLUSIVE EXISTS FILE FLOAT FOR FROM GRANT GROUP ' +
    'HAVING IDENTIFIED IMMEDIATE IN INCREMENT INDEX INITIAL INSERT INTEGER INTERSECT INTO IS LEVEL LIKE LOCK LONG ' +
    'MAXEXTENTS MINUS MLSLABEL MODE MODIFY NOAUDIT NOCOMPRESS NOT NOWAIT NULL NUMBER OF OFFLINE ON ONLINE OPTION OR ' +
    'ORDER PCTFREE PRIOR PUBLIC RAW RENAME RESOURCE REVOKE ROW ROWID ROWNUM ROWS SELECT SESSION SET SHARE SIZE ' +
    'SMALLINT START SUCCESSFUL SYNONYM SYSDATE TABLE THEN TO TRIGGER UID UNION UNIQUE UPDATE USER VALIDATE VALUES ' +
    'VARCHAR VARCHAR2 VIEW WHENEVER WHERE WITH'
  ).split(' '),
)

/** 引用符なしで書ける名前はそのまま、それ以外は " で囲む */
export function quoteIdent(name: string): string {
  return /^[A-Z][A-Z0-9_$#]*$/.test(name) && !RESERVED.has(name) ? name : `"${name.replace(/"/g, '""')}"`
}

const qualified = (owner: string, table: string) => `${quoteIdent(owner)}.${quoteIdent(table)}`

function findColumns(schema: ErView | undefined, owner: string | null, table: string | null): ErColumn[] {
  if (!schema || owner === null || table === null) return []
  const t = schema.tables.find((x) => x.owner === owner && x.name === table)
  return t ? [...t.columns].sort((a, b) => a.column_id - b.column_id) : []
}

const byName = <T extends { name: string }>(a: T, b: T) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)

/** → の制約(制約名の昇順)、続いて ← の制約(制約名の昇順) */
export function listJoinCandidates(detail: TableDetail, schema: ErView | undefined): JoinCandidate[] {
  const make = (c: Omit<JoinCandidate, 'columns' | 'available'>): JoinCandidate => {
    const columns = findColumns(schema, c.owner, c.table)
    const known = [...c.ownColumns, ...c.otherColumns].every((x) => x !== null)
    return { ...c, columns, available: columns.length > 0 && known && c.ownColumns.length > 0 }
  }
  const parents = [...detail.foreign_keys].sort(byName).map((fk) =>
    make({
      key: `parent:${fk.name}`,
      direction: 'parent',
      constraint: fk.name,
      owner: fk.ref_owner,
      table: fk.ref_table,
      ownColumns: fk.columns,
      otherColumns: fk.ref_columns,
    }),
  )
  const children = [...detail.referenced_by].sort(byName).map((rb) =>
    make({
      key: `child:${rb.name}`,
      direction: 'child',
      constraint: rb.name,
      owner: rb.from_owner,
      table: rb.from_table,
      ownColumns: rb.columns,
      otherColumns: rb.from_columns,
    }),
  )
  return [...parents, ...children]
}

/** チェックボックスの表示文言(例: `→ DEPARTMENTS  EMP_DEPT_FK (DEPARTMENT_ID)`) */
export function candidateLabel(c: JoinCandidate, thisOwner: string): string {
  const name = c.table === null ? '(不明)' : c.owner && c.owner !== thisOwner ? `${c.owner}.${c.table}` : c.table
  const cols =
    c.direction === 'parent'
      ? c.ownColumns.map((x) => x ?? '?').join(', ')
      : `${c.otherColumns.map((x) => x ?? '?').join(', ')} → ${c.ownColumns.map((x) => x ?? '?').join(', ')}`
  return `${c.direction === 'parent' ? '→' : '←'} ${name}  ${c.constraint} (${cols})`
}

/** P002 §2.2.7 のひな形。selected は listJoinCandidates の順に並べたもの(使えない候補は無視する) */
export function buildSelectTemplate(detail: TableDetail, selected: JoinCandidate[]): string {
  const owner = detail.table.owner
  const used = new Set<string>()
  const select: string[] = []
  for (const c of [...detail.columns].sort((a, b) => a.column_id - b.column_id)) {
    select.push(`t0.${quoteIdent(c.name)}`)
    used.add(c.name)
  }
  const joins: string[] = []
  selected
    .filter((c) => c.available && c.owner !== null && c.table !== null)
    .forEach((c, i) => {
      const alias = `t${i + 1}`
      for (const col of c.columns) {
        let item = `${alias}.${quoteIdent(col.name)}`
        if (used.has(col.name)) {
          const as = `T${i + 1}_${col.name}`
          if (as.length <= MAX_IDENTIFIER) item += ` AS ${quoteIdent(as)}`
        }
        used.add(col.name)
        select.push(item)
      }
      const on = c.ownColumns
        .map((own, k) => `${alias}.${quoteIdent(c.otherColumns[k] as string)} = t0.${quoteIdent(own as string)}`)
        .join(' AND ')
      joins.push(`  LEFT JOIN ${qualified(c.owner as string, c.table as string)} ${alias} ON ${on}`)
    })
  const lines = ['SELECT', select.map((s, k) => `  ${s}${k < select.length - 1 ? ',' : ''}`).join('\n')]
  lines.push(`FROM ${qualified(owner, detail.table.name)} t0`, ...joins)
  if (detail.primary_key && detail.primary_key.columns.length > 0) {
    lines.push(`ORDER BY ${detail.primary_key.columns.map((c) => `t0.${quoteIdent(c)}`).join(', ')}`)
  }
  return lines.join('\n')
}
