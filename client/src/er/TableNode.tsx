import { Handle, Position, type NodeProps } from '@xyflow/react'
import { memo } from 'react'
import { HEADER_HEIGHT, ROW_HEIGHT, type TableNode as TableNodeType } from './buildGraph'

function TableNode({ data }: NodeProps<TableNodeType>) {
  return (
    <div
      data-testid={`er-node-${data.name}`}
      title={data.comment ?? undefined}
      style={{
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        background: 'white',
        border: data.highlighted ? '3px solid var(--mantine-color-orange-6)' : '1px solid var(--mantine-color-gray-5)',
        borderRadius: 6,
        fontSize: 12,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
        overflow: 'hidden',
        cursor: 'pointer',
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div
        style={{
          height: HEADER_HEIGHT,
          lineHeight: `${HEADER_HEIGHT}px`,
          padding: '0 8px',
          background: 'var(--mantine-color-blue-7)',
          color: 'white',
          fontWeight: 700,
          whiteSpace: 'nowrap',
        }}
      >
        {data.name}
      </div>
      {data.columns.map((c) => (
        <div
          key={c.name}
          style={{ height: ROW_HEIGHT, lineHeight: `${ROW_HEIGHT}px`, padding: '0 8px', display: 'flex', gap: 6, whiteSpace: 'nowrap' }}
        >
          <span style={{ width: 30 }}>
            {c.is_pk ? '🔑' : ''}
            {c.is_fk ? '🔗' : ''}
          </span>
          <span style={{ fontWeight: c.nullable ? 400 : 700 }}>{c.name}</span>
          <span style={{ marginLeft: 'auto', color: 'var(--mantine-color-gray-6)' }}>{c.data_type_display}</span>
        </div>
      ))}
      {data.hiddenCount > 0 && (
        <div style={{ height: ROW_HEIGHT, lineHeight: `${ROW_HEIGHT}px`, padding: '0 8px', color: 'var(--mantine-color-gray-6)' }}>
          … 他 {data.hiddenCount} 列
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

export default memo(TableNode)
