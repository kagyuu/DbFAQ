import { Anchor, Group, Stack, Tabs, Title } from '@mantine/core'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import AppShell from '../components/AppShell'
import { DrumSvg, usePdbName } from '../components/PdbIcon'
import PdbInfoTab from './PdbInfoTab'
import QueryTab, { type QueryState } from './QueryTab'
import { parsePdbTab } from './urlState'

// SC-03 PDB(P002 §2.3。※CR-005により追加)
export default function PdbPage() {
  const [params, setParams] = useSearchParams()
  const tab = parsePdbTab(params.get('tab'))
  const name = usePdbName()
  // Query タブの入力・結果・復元中の Query はタブを切り替えても保つ
  const [queryState, setQueryState] = useState<QueryState | null>(null)
  const setTab = (next: string | null) => setParams({ tab: parsePdbTab(next) }, { replace: true })

  return (
    <AppShell>
      <Stack gap={0} style={{ flex: 1, minHeight: 0 }}>
        <Group gap="lg" px="md" pt="sm">
          <Anchor component={Link} to="/">← ER 図へ</Anchor>
          <Group gap={6}>
            <DrumSvg size={22} />
            <Title order={3}>{name ? `PDB: ${name}` : 'PDB'}</Title>
          </Group>
        </Group>
        <Tabs value={tab} onChange={setTab} keepMounted={false} style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <Tabs.List px="md">
            <Tabs.Tab value="info">PDB 情報</Tabs.Tab>
            <Tabs.Tab value="query">Query</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value="info" style={{ overflow: 'auto' }}>
            <PdbInfoTab />
          </Tabs.Panel>
          <Tabs.Panel value="query" style={{ overflow: 'auto' }}>
            <QueryTab state={queryState} setState={setQueryState} />
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </AppShell>
  )
}
