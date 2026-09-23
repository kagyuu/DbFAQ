import { Alert, Button, Group, LoadingOverlay, Stack, Table, Text } from '@mantine/core'
import { useTableRows } from '../api/hooks'
import { PAGE_SIZE } from './urlState'

type Props = { owner: string; table: string; page: number; onPageChange: (page: number) => void }

// SC-02 データタブ(P002 §2.2.3)。件数は数えず、has_next で「次へ」を決める
export default function DataTab({ owner, table, page, onPageChange }: Props) {
  const offset = (page - 1) * PAGE_SIZE
  const { data, error, isFetching, refetch } = useTableRows(owner, table, offset, PAGE_SIZE, true)

  if (error && !isFetching) {
    return (
      <Stack p="md" data-testid="data-tab">
        <Alert color="red" variant="outline" title="データを取得できませんでした">
          <Stack gap="xs" align="flex-start">
            <Text size="sm">{error.displayMessage}</Text>
            <Button size="xs" variant="light" color="red" onClick={() => refetch()}>
              再試行
            </Button>
          </Stack>
        </Alert>
      </Stack>
    )
  }

  const order =
    data?.order_basis === 'ROWID' ? '並び順: ROWID(主キーなし)' : data ? `並び順: ${data.order_by.join(', ')}(主キー)` : ''
  const rowCount = data?.rows.length ?? 0

  return (
    <Stack p="md" gap="xs" data-testid="data-tab" style={{ height: '100%', boxSizing: 'border-box' }}>
      <Group gap="md">
        <Text size="sm">{order}</Text>
        {data && <Text size="sm" c="dimmed">取得 {data.elapsed_ms} ms</Text>}
        <Button size="xs" variant="default" onClick={() => refetch()} disabled={isFetching}>
          再読み込み
        </Button>
        <Group gap="xs" ml="auto">
          <Button size="xs" variant="default" onClick={() => onPageChange(page - 1)} disabled={isFetching || page <= 1}>
            &lt; 前へ
          </Button>
          <Text size="sm" data-testid="page-range">
            {data && rowCount > 0 && data.offset === offset
              ? `${page} ページ目 (${offset + 1}〜${offset + rowCount} 行)`
              : `${page} ページ目`}
          </Text>
          <Button size="xs" variant="default" onClick={() => onPageChange(page + 1)} disabled={isFetching || !data?.has_next}>
            次へ &gt;
          </Button>
        </Group>
      </Group>
      <div style={{ position: 'relative', flex: 1, minHeight: 200 }}>
        <LoadingOverlay visible={isFetching} zIndex={5} />
        {data && rowCount === 0 ? (
          <Text c="dimmed" p="md">データがありません</Text>
        ) : (
          data && (
            <Table.ScrollContainer minWidth={600} maxHeight="calc(100vh - 260px)">
              <Table stickyHeader striped withTableBorder withColumnBorders fz="xs" aria-label="データ">
                <Table.Thead>
                  <Table.Tr>
                    {data.columns.map((c) => (
                      <Table.Th key={c.name} title={c.data_type} style={{ whiteSpace: 'nowrap' }}>
                        {c.name}
                      </Table.Th>
                    ))}
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.rows.map((row, i) => (
                    <Table.Tr key={offset + i}>
                      {row.map((cell, j) => (
                        <Table.Td
                          key={j}
                          title={data.truncated[i]?.includes(j) ? '先頭 1,000 文字のみ表示' : undefined}
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
        )}
      </div>
    </Stack>
  )
}
