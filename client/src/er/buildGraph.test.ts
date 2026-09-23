import { expect, test } from 'vitest'
import type { ErView } from '../api/types'
import { HR_VIEW } from '../test/hr'
import { MIN_WIDTH, buildGraph, nodeSize } from './buildGraph'

test('ノードはテーブル数、エッジは外部キー数', () => {
  const { nodes, edges } = buildGraph(HR_VIEW)
  expect(nodes).toHaveLength(7)
  expect(edges).toHaveLength(10)
  expect(nodes[0].id).toBe('HR.COUNTRIES')
  expect(edges.find((e) => e.id === 'rel:COUNTR_REG_FK')).toMatchObject({ source: 'HR.COUNTRIES', target: 'HR.REGIONS', label: 'COUNTR_REG_FK' })
})

test('自己参照は selfLoop', () => {
  const { edges } = buildGraph(HR_VIEW)
  const self = edges.find((e) => e.id === 'rel:EMP_MANAGER_FK')!
  expect(self.source).toBe(self.target)
  expect(self.type).toBe('selfLoop')
})

test('別スキーマへの外部キーは線を作らない', () => {
  const view: ErView = {
    ...HR_VIEW,
    relations: [...HR_VIEW.relations, { ...HR_VIEW.relations[0], name: 'EXT_FK', to_owner: 'OTHER', to_table: 'X' }],
  }
  expect(buildGraph(view).edges).toHaveLength(10)
})

test('30 列を超えると省略する', () => {
  const columns = Array.from({ length: 35 }, (_, i) => ({ ...HR_VIEW.tables[0].columns[1], name: `C${i}`, column_id: i + 1 }))
  const view: ErView = { ...HR_VIEW, tables: [{ ...HR_VIEW.tables[0], columns }], relations: [] }
  const node = buildGraph(view).nodes[0]
  expect(node.data.columns).toHaveLength(30)
  expect(node.data.hiddenCount).toBe(5)
})

test('nodeSize は最小幅以上で、長い列名ほど広い', () => {
  const t = HR_VIEW.tables[6]
  const small = nodeSize(t)
  const long = nodeSize({ ...t, columns: [{ ...t.columns[0], name: 'A_VERY_LONG_COLUMN_NAME_FOR_TESTING_WIDTH' }] })
  expect(small.width).toBeGreaterThanOrEqual(MIN_WIDTH)
  expect(long.width).toBeGreaterThan(small.width)
})

test('テーブル 0 件なら空', () => {
  expect(buildGraph({ ...HR_VIEW, tables: [], relations: [] })).toEqual({ nodes: [], edges: [] })
})
