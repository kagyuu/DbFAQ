import { Alert, Button, Center, Group, Loader, Stack, Table, Text, Title } from '@mantine/core'
import { usePdbInfo } from '../api/hooks'
import type { PdbSection } from '../api/types'
import ResultTable from '../components/ResultTable'
import { formatLocalDateTime } from '../format'

const PRIVILEGE_ERRORS = ['ORA-00942', 'ORA-01031']

function SectionBody({ section }: { section: PdbSection }) {
  const e = section.error
  if (e) {
    const display = e.ora_code ? `[${e.ora_code}] ${e.message}` : e.message // P002 §1.3 と同じ形
    return (
      <Alert color="yellow" variant="outline" data-testid={`pdb-section-error-${section.key}`}>
        <Text size="sm" fw={600}>
          {e.ora_code && PRIVILEGE_ERRORS.includes(e.ora_code) ? '権限が無いため取得できません' : '取得できませんでした'}
        </Text>
        <Text size="sm">{display}</Text>
      </Alert>
    )
  }
  if (section.rows.length === 0) return <Text size="sm" c="dimmed">該当する行はありません</Text>
  if (section.key === 'overview') {
    return (
      <Table withTableBorder fz="sm" maw={640} aria-label={section.title}>
        <Table.Tbody>
          {section.rows.map(([item, value], i) => (
            <Table.Tr key={i}>
              <Table.Th w={200}>{item}</Table.Th>
              <Table.Td>{value === null ? <span className="null-cell">(null)</span> : value}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    )
  }
  return <ResultTable label={section.title} columns={section.columns} rows={section.rows} truncated={section.truncated} maxHeight="400px" />
}

// SC-03 PDB 情報タブ(P002 §2.3.2。※CR-005により追加)
export default function PdbInfoTab() {
  const { data, error, isPending, isFetching, refetch } = usePdbInfo(true)
  if (isPending) return <Center p="xl"><Loader aria-label="PDB の情報を読み込み中" /></Center>
  if (error) {
    return (
      <Stack p="md">
        <Alert color="red" variant="outline" title="PDB の情報を取得できませんでした" data-testid="pdb-error">
          <Stack gap="xs" align="flex-start">
            <Text size="sm">{error.displayMessage}</Text>
            <Button size="xs" variant="light" color="red" onClick={() => void refetch()} loading={isFetching}>再試行</Button>
          </Stack>
        </Alert>
      </Stack>
    )
  }
  return (
    <Stack p="md" gap="md" data-testid="pdb-info">
      <Group gap="md">
        <Text size="sm" c="dimmed">{`取得 ${formatLocalDateTime(data.fetched_at)}`}</Text>
        <Text size="sm" c="dimmed">{`取得 ${data.elapsed_ms} ms`}</Text>
        <Button size="xs" variant="default" onClick={() => void refetch()} loading={isFetching} disabled={isFetching}>
          再読み込み
        </Button>
      </Group>
      {data.sections.map((s) => (
        <Stack key={s.key} gap={4} data-testid={`pdb-section-${s.key}`}>
          <Title order={5}>{s.title}</Title>
          <SectionBody section={s} />
        </Stack>
      ))}
    </Stack>
  )
}
