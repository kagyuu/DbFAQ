import { Badge, Button, Group, Modal, ScrollArea, Stack, Table, Text, TextInput, Textarea, Tooltip } from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { ApiError, createSavedQuery, deleteSavedQuery, updateSavedQuery } from '../api/client'
import { savedQueriesKey, useSavedQueries } from '../api/hooks'
import type { SavedQuery, SavedQueryTarget } from '../api/types'

export const MAX_NAME_CHARS = 100
export const MAX_DESCRIPTION_CHARS = 1_000
const MAX_SQL_CHARS = 100_000
const ROW_HEIGHT = 34
const VISIBLE_ROWS = 10

/** 復元中(最後に復元・保存した)の保存済み Query */
export interface LoadedQuery {
  id: number
  name: string
  description: string
}

type Props = {
  target: SavedQueryTarget
  /** 保存先の表示(「HR.EMPLOYEES」/「PDB」) */
  targetLabel: string
  /** 入力欄の SQL */
  sql: string
  loaded: LoadedQuery | null
  /** 最後のひな形・復元・保存の後に入力欄が編集されているか */
  dirty: boolean
  onRestore: (item: SavedQuery) => void
  /** 保存・上書き保存・名前の変更に成功した(sqlChanged は入力欄の SQL を保存したとき) */
  onSaved: (item: SavedQuery, sqlChanged: boolean) => void
  onUnload: () => void
}

type Dialog =
  | { kind: 'create' }
  | { kind: 'edit'; item: SavedQuery }
  | { kind: 'restore'; item: SavedQuery }
  | { kind: 'delete'; item: SavedQuery }
  | null

const pad = (n: number) => String(n).padStart(2, '0')
function shortDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const toApiError = (e: unknown) =>
  e instanceof ApiError ? e : new ApiError('INTERNAL_ERROR', 0, '内部エラーが発生しました')

function dialogError(e: ApiError): string {
  if (e.code === 'QUERY_NAME_CONFLICT') return '同じ名前の Query が既にあります'
  if (e.status === 422) return e.message
  return e.displayMessage
}

export function nameError(name: string): string | null {
  const v = name.trim()
  if (v === '') return '名前を入力してください'
  if (v.length > MAX_NAME_CHARS) return `${MAX_NAME_CHARS} 文字以内で入力してください`
  return null
}

export function descriptionError(description: string): string | null {
  return description.trim().length > MAX_DESCRIPTION_CHARS ? `${MAX_DESCRIPTION_CHARS.toLocaleString()} 文字以内で入力してください` : null
}

// 保存済み Query の一覧と保存・復元・上書き保存・変更・削除(P002 §2.2.8。※CR-005により追加)
export default function SavedQueries({ target, targetLabel, sql, loaded, dirty, onRestore, onSaved, onUnload }: Props) {
  const qc = useQueryClient()
  const key = savedQueriesKey(target)
  const { data, error } = useSavedQueries(target)
  const items = data?.items
  const [dialog, setDialog] = useState<Dialog>(null)
  const [overwriting, setOverwriting] = useState(false)

  useEffect(() => {
    if (error) notifications.show({ color: 'red', title: '保存済み Query を取得できませんでした', message: error.displayMessage, autoClose: 10000 })
  }, [error])

  // 復元中の Query が一覧から消えたら(削除・取り直し)解除する
  useEffect(() => {
    if (loaded && items && !items.some((q) => q.id === loaded.id)) onUnload()
  }, [items, loaded, onUnload])

  const refresh = () => qc.invalidateQueries({ queryKey: key })
  const sqlOk = sql.trim() !== '' && sql.length <= MAX_SQL_CHARS
  const failed = (title: string, e: unknown) => {
    const err = toApiError(e)
    notifications.show({ color: 'red', title, message: err.displayMessage, autoClose: 10000 })
    if (err.code === 'SAVED_QUERY_NOT_FOUND') void refresh()
  }

  const restore = (item: SavedQuery) => {
    if (dirty) setDialog({ kind: 'restore', item })
    else onRestore(item)
  }

  const overwrite = async () => {
    if (!loaded) return
    setOverwriting(true)
    try {
      const item = await updateSavedQuery(loaded.id, { name: loaded.name, description: loaded.description, sql })
      await refresh()
      onSaved(item, true)
      notifications.show({ color: 'green', message: `上書き保存しました: ${item.name}` })
    } catch (e) {
      failed('上書き保存できませんでした', e)
    } finally {
      setOverwriting(false)
    }
  }

  const remove = async (item: SavedQuery) => {
    setDialog(null)
    try {
      await deleteSavedQuery(item.id)
      await refresh()
      if (loaded?.id === item.id) onUnload()
      notifications.show({ color: 'green', message: `削除しました: ${item.name}` })
    } catch (e) {
      failed('削除できませんでした', e)
    }
  }

  return (
    <Stack gap={4} data-testid="saved-queries">
      <Group gap="sm">
        <Text size="sm" fw={600}>{`保存済み Query (${items?.length ?? 0})`}</Text>
        <Button size="xs" variant="default" disabled={!sqlOk} onClick={() => setDialog({ kind: 'create' })}>
          名前を付けて保存
        </Button>
        <Button size="xs" variant="default" disabled={!sqlOk || !loaded} loading={overwriting} onClick={() => void overwrite()}>
          上書き保存
        </Button>
        {loaded && (
          <Text size="xs" c="blue" data-testid="loaded-query">{`復元中: ${loaded.name}`}</Text>
        )}
      </Group>
      {items && items.length === 0 && <Text size="sm" c="dimmed">保存済みの Query はありません</Text>}
      {items && items.length > 0 && (
        <ScrollArea.Autosize mah={ROW_HEIGHT * VISIBLE_ROWS} type="auto">
          <Table verticalSpacing={2} highlightOnHover aria-label="保存済み Query の一覧" style={{ tableLayout: 'fixed' }}>
            <Table.Tbody>
              {items.map((q) => (
                <Table.Tr key={q.id} data-testid="saved-query-row">
                  <Table.Td w={18}>{loaded?.id === q.id ? '●' : ''}</Table.Td>
                  <Table.Td w="30%">
                    <Group gap={4} wrap="nowrap">
                      <Text size="sm" fw={700} truncate="end">{q.name}</Text>
                      {q.is_template && <Badge size="xs" variant="light">ひな型</Badge>}
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Tooltip label={q.description} disabled={!q.description} multiline maw={480} openDelay={300}>
                      <Text size="xs" c="dimmed" truncate="end">{q.description}</Text>
                    </Tooltip>
                  </Table.Td>
                  <Table.Td w={120}><Text size="xs" c="dimmed">{shortDateTime(q.updated_at)}</Text></Table.Td>
                  <Table.Td w={190}>
                    <Group gap={4} wrap="nowrap">
                      <Button size="compact-xs" variant="light" onClick={() => restore(q)} aria-label={`復元: ${q.name}`}>復元</Button>
                      <Button size="compact-xs" variant="subtle" onClick={() => setDialog({ kind: 'edit', item: q })} aria-label={`編集: ${q.name}`}>編集</Button>
                      <Button size="compact-xs" variant="subtle" color="red" onClick={() => setDialog({ kind: 'delete', item: q })} aria-label={`削除: ${q.name}`}>削除</Button>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </ScrollArea.Autosize>
      )}

      {(dialog?.kind === 'create' || dialog?.kind === 'edit') && (
        <NameDialog
          title={dialog.kind === 'create' ? 'Query を保存' : 'Query の名前と説明を変更'}
          targetLabel={targetLabel}
          initialName={dialog.kind === 'edit' ? dialog.item.name : loaded ? `${loaded.name} のコピー` : ''}
          initialDescription={dialog.kind === 'edit' ? dialog.item.description : (loaded?.description ?? '')}
          onClose={() => setDialog(null)}
          onSubmit={async (name, description) => {
            const item =
              dialog.kind === 'create'
                ? await createSavedQuery(target, { name, description, sql })
                : await updateSavedQuery(dialog.item.id, { name, description, sql: dialog.item.sql })
            await refresh()
            setDialog(null)
            if (dialog.kind === 'create') {
              onSaved(item, true)
              notifications.show({ color: 'green', message: `保存しました: ${item.name}` })
            } else if (loaded?.id === item.id) {
              onSaved(item, false)
            }
          }}
        />
      )}
      {dialog?.kind === 'restore' && (
        <ConfirmDialog
          title="SQL の置き換え"
          message={`入力欄の SQL を「${dialog.item.name}」で置き換えますか? 編集中の内容は失われます`}
          confirmLabel="置き換える"
          onCancel={() => setDialog(null)}
          onConfirm={() => {
            setDialog(null)
            onRestore(dialog.item)
          }}
        />
      )}
      {dialog?.kind === 'delete' && (
        <ConfirmDialog
          title="Query の削除"
          message={`「${dialog.item.name}」を削除しますか? 元に戻せません`}
          confirmLabel="削除"
          color="red"
          onCancel={() => setDialog(null)}
          onConfirm={() => void remove(dialog.item)}
        />
      )}
    </Stack>
  )
}

function NameDialog(props: {
  title: string
  targetLabel: string
  initialName: string
  initialDescription: string
  onClose: () => void
  onSubmit: (name: string, description: string) => Promise<void>
}) {
  const [name, setName] = useState(props.initialName)
  const [description, setDescription] = useState(props.initialDescription)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const nErr = nameError(name)
  const dErr = descriptionError(description)
  const submit = async () => {
    if (nErr || dErr || saving) return
    setSaving(true)
    setError(null)
    try {
      await props.onSubmit(name.trim(), description.trim())
    } catch (e) {
      setError(dialogError(toApiError(e)))
      setSaving(false)
    }
  }
  return (
    <Modal opened onClose={props.onClose} title={props.title} centered>
      <Stack gap="sm">
        <Text size="sm" c="dimmed">{`保存先: ${props.targetLabel}`}</Text>
        <TextInput
          label="名前"
          required
          data-autofocus
          value={name}
          onChange={(e) => setName(e.currentTarget.value)}
          error={name !== '' ? nErr : null}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void submit()
          }}
        />
        <Textarea label="説明" autosize minRows={2} maxRows={6} value={description} onChange={(e) => setDescription(e.currentTarget.value)} error={dErr} />
        {error && <Text size="sm" c="red" data-testid="dialog-error">{error}</Text>}
        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={props.onClose}>キャンセル</Button>
          <Button onClick={() => void submit()} disabled={!!nErr || !!dErr} loading={saving}>保存</Button>
        </Group>
      </Stack>
    </Modal>
  )
}

function ConfirmDialog(props: {
  title: string
  message: string
  confirmLabel: string
  color?: string
  onCancel: () => void
  onConfirm: () => void
}) {
  return (
    <Modal opened onClose={props.onCancel} title={props.title} centered>
      <Stack gap="md">
        <Text size="sm">{props.message}</Text>
        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={props.onCancel}>キャンセル</Button>
          <Button color={props.color} onClick={props.onConfirm}>{props.confirmLabel}</Button>
        </Group>
      </Stack>
    </Modal>
  )
}
