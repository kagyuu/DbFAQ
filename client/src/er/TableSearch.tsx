import { Button, Group, Paper, TextInput, UnstyledButton } from '@mantine/core'
import { useMemo, useState } from 'react'
import type { ErTable } from '../api/types'

export const MAX_SEARCH_LENGTH = 128
export const MAX_CANDIDATES = 20

type Props = {
  tables: ErTable[]
  onFocusTable: (table: ErTable) => void
  onOpenTable: (table: ErTable) => void
}

// テーブル名検索(P002 §2.1.3・§2.1.4)。サーバには送らずクライアント内で絞り込む
export default function TableSearch({ tables, onFocusTable, onOpenTable }: Props) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const candidates = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return tables.filter((t) => t.name.toLowerCase().includes(q)).slice(0, MAX_CANDIDATES)
  }, [query, tables])

  const choose = (t: ErTable) => {
    setQuery(t.name)
    setOpen(false)
    onFocusTable(t)
  }

  return (
    <div style={{ position: 'relative', width: 280 }}>
      <TextInput
        placeholder="テーブル名で検索"
        aria-label="テーブル名で検索"
        value={query}
        maxLength={MAX_SEARCH_LENGTH}
        onChange={(e) => {
          setQuery(e.currentTarget.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && candidates.length > 0) {
            e.preventDefault()
            choose(candidates[0])
          } else if (e.key === 'Escape') {
            setOpen(false)
          }
        }}
      />
      {open && candidates.length > 0 && (
        <Paper shadow="md" withBorder role="listbox" style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 20, maxHeight: 360, overflowY: 'auto' }}>
          {candidates.map((t) => (
            <Group key={t.name} role="option" aria-selected={false} gap={4} px="xs" py={4} wrap="nowrap" justify="space-between">
              <UnstyledButton onClick={() => choose(t)} style={{ flex: 1, fontSize: 14 }}>
                {t.name}
              </UnstyledButton>
              <Button size="compact-xs" variant="light" onClick={() => onOpenTable(t)} aria-label={`${t.name} を開く`}>
                開く
              </Button>
            </Group>
          ))}
        </Paper>
      )}
    </div>
  )
}
