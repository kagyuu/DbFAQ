import { expect, test } from 'vitest'
import { HR_VIEW } from '../test/hr'
import { buildGraph } from './buildGraph'
import { layoutGraph } from './layout'

test('HR 相当の入力で全ノードに座標が付き、重ならない', async () => {
  const { nodes, edges } = buildGraph(HR_VIEW)
  const snapshot = JSON.stringify(nodes)
  const laid = await layoutGraph(nodes, edges)
  expect(JSON.stringify(nodes)).toBe(snapshot) // 入力を変更しない
  for (const n of laid) {
    expect(Number.isFinite(n.position.x)).toBe(true)
    expect(Number.isFinite(n.position.y)).toBe(true)
  }
  for (let i = 0; i < laid.length; i++) {
    for (let j = i + 1; j < laid.length; j++) {
      const a = laid[i]
      const b = laid[j]
      const overlap =
        a.position.x < b.position.x + b.width! &&
        b.position.x < a.position.x + a.width! &&
        a.position.y < b.position.y + b.height! &&
        b.position.y < a.position.y + a.height!
      expect(overlap, `${a.id} と ${b.id} が重なる`).toBe(false)
    }
  }
  const x = (id: string) => laid.find((n) => n.id === id)!.position.x
  expect(x('HR.REGIONS')).toBeGreaterThan(x('HR.COUNTRIES'))
})
