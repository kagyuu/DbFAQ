import { Anchor, Stack, Table, Text, Title } from '@mantine/core'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { TableDetail } from '../api/types'
import { formatLocalDateTime } from '../format'

const tableLink = (owner: string, table: string) => (
  <Anchor component={Link} to={`/tables/${encodeURIComponent(owner)}/${encodeURIComponent(table)}`}>
    {table}
  </Anchor>
)

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Stack gap={4}>
      <Title order={5}>{title}</Title>
      {children}
    </Stack>
  )
}

function Grid({ head, rows, empty = 'なし', label }: { head: string[]; rows: ReactNode[][]; empty?: string; label: string }) {
  if (rows.length === 0) return <Text size="sm" c="dimmed">{empty}</Text>
  return (
    <Table striped withTableBorder aria-label={label} fz="sm">
      <Table.Thead>
        <Table.Tr>{head.map((h) => <Table.Th key={h}>{h}</Table.Th>)}</Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {rows.map((r, i) => (
          <Table.Tr key={i}>{r.map((c, j) => <Table.Td key={j}>{c}</Table.Td>)}</Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

// SC-02 スキーマ情報タブ(P002 §2.2.2)
export default function SchemaTab({ detail }: { detail: TableDetail }) {
  const t = detail.table
  return (
    <Stack p="md" gap="lg" data-testid="schema-tab">
      <Section title="概要">
        <Table withTableBorder fz="sm" aria-label="概要" style={{ width: 'auto' }}>
          <Table.Tbody>
            <Table.Tr><Table.Th>テーブル名</Table.Th><Table.Td>{t.name}</Table.Td></Table.Tr>
            <Table.Tr><Table.Th>コメント</Table.Th><Table.Td>{t.comment ?? ''}</Table.Td></Table.Tr>
            <Table.Tr>
              <Table.Th>行数の目安</Table.Th>
              <Table.Td data-testid="num-rows">{t.num_rows === null ? '統計なし' : t.num_rows.toLocaleString('en-US')}</Table.Td>
            </Table.Tr>
            <Table.Tr><Table.Th>統計取得日</Table.Th><Table.Td>{t.last_analyzed ? formatLocalDateTime(t.last_analyzed) : ''}</Table.Td></Table.Tr>
          </Table.Tbody>
        </Table>
      </Section>
      <Section title="列">
        <Grid
          label="列"
          head={['#', '列名', 'データ型', 'NULL', 'デフォルト', '主キー', 'コメント']}
          rows={detail.columns.map((c) => [
            c.column_id,
            c.name,
            c.data_type_display,
            c.nullable ? '可' : '不可',
            c.data_default ?? '',
            c.pk_position ? `🔑 ${c.pk_position}` : '',
            c.comment ?? '',
          ])}
        />
      </Section>
      <Section title="主キー">
        <Grid
          label="主キー"
          empty="主キーなし"
          head={['制約名', '列']}
          rows={detail.primary_key ? [[detail.primary_key.name, detail.primary_key.columns.join(', ')]] : []}
        />
      </Section>
      <Section title="一意制約">
        <Grid label="一意制約" head={['制約名', '列']} rows={detail.unique_keys.map((u) => [u.name, u.columns.join(', ')])} />
      </Section>
      <Section title="外部キー(このテーブル → 参照先)">
        <Grid
          label="外部キー(参照先)"
          head={['制約名', '列 → 参照先', '削除時の動作']}
          rows={detail.foreign_keys.map((f) => [
            f.name,
            <span key="ref">
              {f.columns.join(', ')} → {f.ref_owner}.
              {f.ref_in_snapshot && f.ref_owner && f.ref_table ? tableLink(f.ref_owner, f.ref_table) : f.ref_table}(
              {f.ref_columns.join(', ')})
            </span>,
            f.delete_rule ?? '',
          ])}
        />
      </Section>
      <Section title="外部キー(参照元 → このテーブル)">
        <Grid
          label="外部キー(参照元)"
          head={['制約名', '参照元 → 列']}
          rows={detail.referenced_by.map((r) => [
            r.name,
            <span key="ref">
              {tableLink(r.from_owner, r.from_table)}({r.from_columns.join(', ')}) → {r.columns.join(', ')}
            </span>,
          ])}
        />
      </Section>
      <Section title="インデックス">
        <Grid
          label="インデックス"
          head={['インデックス名', '一意', '種類', '列']}
          rows={detail.indexes.map((i) => [
            i.name,
            i.unique ? '一意' : '',
            i.index_type,
            i.columns.map((c) => c.name + (c.descending ? ' DESC' : '')).join(', '),
          ])}
        />
      </Section>
    </Stack>
  )
}
