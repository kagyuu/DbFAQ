import { MarkerType, type Edge, type Node } from '@xyflow/react'
import type { ErColumn, ErTable, ErView } from '../api/types'

// ER 図のノード・エッジの組み立て(docs/P002-frontend-spec.md §2.1.2)
export const MAX_VISIBLE_COLUMNS = 30
export const ROW_HEIGHT = 22
export const HEADER_HEIGHT = 32
export const CHAR_WIDTH = 7.5
export const MIN_WIDTH = 180
export const PADDING_X = 40

export type TableNodeData = {
  owner: string
  name: string
  comment: string | null
  columns: ErColumn[]
  hiddenCount: number
  highlighted?: boolean
}

export type TableNode = Node<TableNodeData, 'table'>

export const nodeId = (owner: string, name: string) => `${owner}.${name}`

export function nodeSize(table: ErTable): { width: number; height: number } {
  const visible = table.columns.slice(0, MAX_VISIBLE_COLUMNS)
  const longestColumn = Math.max(0, ...visible.map((c) => c.name.length + c.data_type_display.length + 4))
  const chars = Math.max(longestColumn, table.name.length)
  const width = Math.max(MIN_WIDTH, chars * CHAR_WIDTH + PADDING_X)
  const rows = visible.length + (table.columns.length > MAX_VISIBLE_COLUMNS ? 1 : 0)
  return { width, height: HEADER_HEIGHT + rows * ROW_HEIGHT }
}

export function buildGraph(view: ErView): { nodes: TableNode[]; edges: Edge[] } {
  const nodes: TableNode[] = view.tables.map((t) => {
    const { width, height } = nodeSize(t)
    return {
      id: nodeId(t.owner, t.name),
      type: 'table',
      position: { x: 0, y: 0 },
      width,
      height,
      data: {
        owner: t.owner,
        name: t.name,
        comment: t.comment,
        columns: t.columns.slice(0, MAX_VISIBLE_COLUMNS),
        hiddenCount: Math.max(0, t.columns.length - MAX_VISIBLE_COLUMNS),
      },
    }
  })
  const ids = new Set(nodes.map((n) => n.id))
  const edges: Edge[] = []
  for (const r of view.relations) {
    if (!r.to_owner || !r.to_table) continue
    const source = nodeId(r.from_owner, r.from_table)
    const target = nodeId(r.to_owner, r.to_table)
    if (!ids.has(source) || !ids.has(target)) continue // 別スキーマへの外部キーは線を描かない
    edges.push({
      id: `rel:${r.name}`,
      source,
      target,
      label: r.name,
      markerEnd: { type: MarkerType.ArrowClosed },
      ...(source === target ? { type: 'selfLoop' } : {}),
    })
  }
  return { nodes, edges }
}
