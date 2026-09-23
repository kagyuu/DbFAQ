import { BaseEdge, EdgeLabelRenderer, type EdgeProps } from '@xyflow/react'

// 自己参照の外部キー: ノードの右辺から出て右に張り出して戻るループ(P002 §2.1.2)
export default function SelfLoopEdge({ id, sourceX, sourceY, label, markerEnd, style }: EdgeProps) {
  const out = 40
  const rise = 30
  const path = `M ${sourceX} ${sourceY} C ${sourceX + out} ${sourceY - rise}, ${sourceX + out} ${sourceY + rise}, ${sourceX} ${sourceY + 1}`
  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />
      {label && (
        <EdgeLabelRenderer>
          <div
            className="nodrag nopan"
            style={{
              position: 'absolute',
              transform: `translate(0, -50%) translate(${sourceX + out}px, ${sourceY}px)`,
              fontSize: 10,
              background: 'white',
              padding: '0 2px',
            }}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}
