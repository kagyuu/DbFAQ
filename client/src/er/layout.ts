import type { Edge, Node } from '@xyflow/react'
import ELK from 'elkjs/lib/elk.bundled.js'

const elk = new ELK()

// elkjs の layered で左→右に配置する。子→親の向きのエッジを渡すので親が右に来る(P002 §2.1.2)
export async function layoutGraph<N extends Node>(nodes: N[], edges: Edge[]): Promise<N[]> {
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.spacing.nodeNode': '60',
      'elk.layered.spacing.nodeNodeBetweenLayers': '100',
    },
    children: nodes.map((n) => ({ id: n.id, width: n.width ?? 200, height: n.height ?? 100 })),
    edges: edges
      .filter((e) => e.source !== e.target) // 自己参照はレイアウトに渡さない
      .map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] })),
  }
  const result = await elk.layout(graph)
  const pos = new Map((result.children ?? []).map((c) => [c.id, { x: c.x ?? 0, y: c.y ?? 0 }]))
  return nodes.map((n) => ({ ...n, position: pos.get(n.id) ?? { x: 0, y: 0 } }))
}
