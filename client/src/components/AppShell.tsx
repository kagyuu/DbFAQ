import { Anchor, Group, AppShell as MantineAppShell, Text } from '@mantine/core'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useSchema } from '../api/hooks'
import { formatLocalDateTime } from '../format'
import OracleStatus from './OracleStatus'

export const HEADER_HEIGHT = 48

export default function AppShell({ children }: { children: ReactNode }) {
  const { data } = useSchema()
  const snapshot = data?.snapshot
  return (
    <MantineAppShell header={{ height: HEADER_HEIGHT }} padding={0}>
      <MantineAppShell.Header>
        <Group h="100%" px="md" gap="lg" wrap="nowrap">
          <Anchor component={Link} to="/" fw={700} size="lg" underline="never">
            DbFAQ
          </Anchor>
          <Text size="sm" data-testid="header-schema">
            スキーマ: {snapshot?.owner ?? '未取得'}
          </Text>
          {snapshot && (
            <Text size="sm" c="dimmed" data-testid="header-fetched-at">
              取得日時: {formatLocalDateTime(snapshot.fetched_at)}
            </Text>
          )}
          <Anchor component={Link} to="/" size="sm">
            ER 図
          </Anchor>
          <Group ml="auto" gap={6}>
            <Text size="sm">Oracle</Text>
            <OracleStatus />
          </Group>
        </Group>
      </MantineAppShell.Header>
      <MantineAppShell.Main style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>{children}</MantineAppShell.Main>
    </MantineAppShell>
  )
}
