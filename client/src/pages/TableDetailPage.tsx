import { Anchor, Center, Group, Loader, Stack, Tabs, Text, Title } from '@mantine/core'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useTableDetail } from '../api/hooks'
import AppShell from '../components/AppShell'
import DataTab from './DataTab'
import QueryTab, { type QueryState } from './QueryTab'
import SchemaTab from './SchemaTab'
import { parsePage, parseTab } from './urlState'

function Detail({ owner, table }: { owner: string; table: string }) {
  const [params, setParams] = useSearchParams()
  const tab = parseTab(params.get('tab'))
  const page = parsePage(params.get('page'))
  const { data, error, isPending } = useTableDetail(owner, table)
  // Query タブの入力・結果はタブを切り替えても保つ(別のテーブルでは key で作り直されて初期化される)
  const [queryState, setQueryState] = useState<QueryState | null>(null)

  const setTab = (next: string | null) => {
    const value = parseTab(next)
    setParams(value === 'data' ? { tab: 'data', page: String(page) } : { tab: value }, { replace: true })
  }
  const setPage = (next: number) => setParams({ tab: 'data', page: String(next) }, { replace: true })

  if (isPending) {
    return <Center h="100%"><Loader aria-label="読み込み中" /></Center>
  }
  if (error) {
    const message =
      error.code === 'SCHEMA_NOT_LOADED'
        ? 'スキーマ情報がありません'
        : error.code === 'TABLE_NOT_FOUND'
          ? `テーブルが見つかりません: ${owner}.${table}`
          : error.displayMessage
    return (
      <Stack p="xl" gap="sm">
        <Text fw={700}>{message}</Text>
        <Anchor component={Link} to="/">ER 図へ</Anchor>
      </Stack>
    )
  }

  return (
    <Stack gap={0} style={{ flex: 1, minHeight: 0 }}>
      <Stack gap={4} px="md" pt="sm">
        <Group gap="lg">
          <Anchor component={Link} to="/">← ER 図へ</Anchor>
          <Title order={3}>{`${data.table.owner}.${data.table.name}`}</Title>
        </Group>
        {data.table.comment && <Text size="sm" c="dimmed">{data.table.comment}</Text>}
      </Stack>
      <Tabs value={tab} onChange={setTab} keepMounted={false} style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        <Tabs.List px="md">
          <Tabs.Tab value="schema">スキーマ情報</Tabs.Tab>
          <Tabs.Tab value="data">データ</Tabs.Tab>
          <Tabs.Tab value="query">Query</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="schema" style={{ overflow: 'auto' }}>
          <SchemaTab detail={data} />
        </Tabs.Panel>
        <Tabs.Panel value="data" style={{ flex: 1, minHeight: 0 }}>
          <DataTab owner={owner} table={table} page={page} onPageChange={setPage} />
        </Tabs.Panel>
        <Tabs.Panel value="query" style={{ overflow: 'auto' }}>
          <QueryTab detail={data} state={queryState} setState={setQueryState} />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}

export default function TableDetailPage() {
  const { owner = '', table = '' } = useParams()
  return (
    <AppShell>
      <Detail key={`${owner}.${table}`} owner={owner} table={table} />
    </AppShell>
  )
}
