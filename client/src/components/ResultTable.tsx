import { Table } from '@mantine/core'

type Props = {
  label: string
  columns: { name: string; data_type: string }[]
  rows: (string | null)[][]
  truncated: number[][]
  maxHeight: string
}

// データタブと Query タブの結果の表(P002 §2.2.3・§2.2.6)。null は (null)、切り詰めたセルはツールチップ
export default function ResultTable({ label, columns, rows, truncated, maxHeight }: Props) {
  return (
    <Table.ScrollContainer minWidth={600} maxHeight={maxHeight}>
      <Table stickyHeader striped withTableBorder withColumnBorders fz="xs" aria-label={label}>
        <Table.Thead>
          <Table.Tr>
            {columns.map((c, j) => (
              <Table.Th key={j} title={c.data_type} style={{ whiteSpace: 'nowrap' }}>
                {c.name}
              </Table.Th>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {rows.map((row, i) => (
            <Table.Tr key={i}>
              {row.map((cell, j) => (
                <Table.Td
                  key={j}
                  title={truncated[i]?.includes(j) ? '先頭 1,000 文字のみ表示' : undefined}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {cell === null ? (
                    <span className="null-cell" data-null="true">(null)</span>
                  ) : (
                    cell
                  )}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  )
}
