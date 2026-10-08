import { Alert, Button, Checkbox, Code, Group, Loader, Stack, Text, Textarea } from '@mantine/core'
import { type Dispatch, type SetStateAction, useCallback, useMemo, useRef } from 'react'
import { ApiError, fetchQueryCsv, runQuery } from '../api/client'
import { useSchema } from '../api/hooks'
import type { QueryResult, SavedQuery, SavedQueryTarget, TableDetail } from '../api/types'
import ResultTable from '../components/ResultTable'
import SavedQueries, { type LoadedQuery } from '../components/SavedQueries'
import { buildSelectTemplate, candidateLabel, listJoinCandidates } from '../query/template'

export const MAX_SQL_CHARS = 100_000

/** Query タブの状態。TableDetailPage が持ち、タブを切り替えても保つ(P002 §2.2.1) */
export interface QueryState {
  sql: string
  /** 最後に入力欄へ入れたひな形(これと sql が違えば利用者が編集している) */
  template: string
  /** チェックボックスで選んだ候補の key */
  selected: string[]
  /** template を作ったときの selected */
  appliedSelected: string[]
  running: 'run' | 'csv' | null
  /** 復元中の保存済み Query(※CR-005により追加) */
  loaded?: LoadedQuery | null
  /** 最後にひな形・復元・保存した SQL(これと sql が違えば編集中。※CR-005により追加) */
  baseline?: string
  result?: QueryResult
  error?: { kind: 'run' | 'csv'; error: ApiError; sql: string }
}

type Props = {
  /** 表示中のテーブル。省略すると PDB の Query タブ(SC-03。JOIN・ひな形なし。※CR-005により追加) */
  detail?: TableDetail
  state: QueryState | null
  setState: Dispatch<SetStateAction<QueryState | null>>
}

const toApiError = (e: unknown) =>
  e instanceof ApiError ? e : new ApiError('INTERNAL_ERROR', 0, '内部エラーが発生しました')

const sameSet = (a: string[], b: string[]) => a.length === b.length && a.every((x) => b.includes(x))

const pad = (n: number) => String(n).padStart(2, '0')
export function csvFileName(table: string, now: Date): string {
  const d = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`
  const t = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
  return `${table}_query_${d}-${t}.csv`
}

// 全角の文字は等幅フォントで 2 文字分の幅になるため、^ の位置合わせに全角空白を使う
const WIDE = /[ᄀ-ᅟ⺀-꓏가-힣豈-﫿︰-﹏＀-｠￠-￦]/u
const isWide = (c: string) => WIDE.test(c) || (c.codePointAt(0) ?? 0) >= 0x20000

/** エラー位置の行と、その下に置く ^ の行 */
export function caretLines(sql: string, line: number, column: number): [string, string] {
  const text = sql.split('\n')[line - 1] ?? ''
  const pad = Array.from(text)
    .slice(0, column - 1)
    .map((c) => (c === '\t' ? '\t' : isWide(c) ? '　' : ' '))
    .join('')
  return [text, pad + '^']
}

/** コードポイント単位の位置を JS の文字列(UTF-16)の位置に直す */
export function toUtf16Index(sql: string, offset: number): number {
  return Array.from(sql).slice(0, offset).join('').length
}

// SC-02 Query タブ(P002 §2.2.6)。SC-03 の Query タブ(P002 §2.3.3)でも使う(※CR-005により追加)
export default function QueryTab({ detail, state, setState }: Props) {
  const { data: schema, isPending: schemaPending } = useSchema()
  const editor = useRef<HTMLTextAreaElement>(null)
  const candidates = useMemo(() => (detail ? listJoinCandidates(detail, schema) : []), [detail, schema])

  const initial = useMemo<QueryState>(() => {
    const t = detail ? buildSelectTemplate(detail, []) : ''
    return { sql: t, template: t, selected: [], appliedSelected: [], running: null, loaded: null, baseline: t }
  }, [detail])
  const s = state ?? initial
  const update = (patch: Partial<QueryState>) => setState((prev) => ({ ...(prev ?? initial), ...patch }))

  const templateFor = (keys: string[]) =>
    detail ? buildSelectTemplate(detail, candidates.filter((c) => keys.includes(c.key))) : ''
  const edited = s.sql !== s.template
  const dirty = s.sql.trim() !== '' && s.sql !== (s.baseline ?? s.template)

  const toggle = (key: string, on: boolean) => {
    const selected = on ? [...s.selected, key] : s.selected.filter((k) => k !== key)
    if (edited) {
      update({ selected })
    } else {
      const t = templateFor(selected)
      update({ selected, sql: t, template: t, appliedSelected: selected, baseline: t })
    }
  }
  const applyTemplate = () => {
    const t = templateFor(s.selected)
    update({ sql: t, template: t, appliedSelected: s.selected, baseline: t })
  }

  // 保存済み Query(P002 §2.2.8。※CR-005により追加)
  const target = useMemo<SavedQueryTarget>(
    () => (detail ? { scope: 'table', owner: detail.table.owner, table: detail.table.name } : { scope: 'pdb' }),
    [detail],
  )
  const loadedOf = (q: SavedQuery): LoadedQuery => ({ id: q.id, name: q.name, description: q.description })
  const restore = (q: SavedQuery) => update({ sql: q.sql, baseline: q.sql, loaded: loadedOf(q) })
  const saved = (q: SavedQuery, sqlChanged: boolean) =>
    update(sqlChanged ? { loaded: loadedOf(q), baseline: q.sql } : { loaded: loadedOf(q) })
  const unload = useCallback(
    () => setState((prev) => ({ ...(prev ?? initial), loaded: null })),
    [setState, initial],
  )

  const tooLong = s.sql.length > MAX_SQL_CHARS
  const canRun = s.sql.trim() !== '' && !tooLong && s.running === null

  const run = async () => {
    if (!canRun) return
    const sql = s.sql
    update({ running: 'run' })
    try {
      const result = await runQuery(sql)
      update({ running: null, result, error: undefined })
    } catch (e) {
      update({ running: null, result: undefined, error: { kind: 'run', error: toApiError(e), sql } })
    }
  }

  const downloadCsv = async () => {
    if (!canRun) return
    const sql = s.sql
    update({ running: 'csv' })
    try {
      const { blob } = await fetchQueryCsv(sql)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = csvFileName(detail ? detail.table.name : 'PDB', new Date())
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      // 前回の CSV のエラーだけを消す(実行のエラーは残す)
      setState((prev) => {
        const cur = prev ?? initial
        return { ...cur, running: null, error: cur.error?.kind === 'csv' ? undefined : cur.error }
      })
    } catch (e) {
      update({ running: null, error: { kind: 'csv', error: toApiError(e), sql } })
    }
  }

  const gotoError = () => {
    const pos = s.error?.error.position
    const el = editor.current
    if (!pos || !el) return
    const start = toUtf16Index(s.sql, pos.offset)
    const end = Math.min(s.sql.length, toUtf16Index(s.sql, pos.offset + 1))
    el.focus()
    el.setSelectionRange(start, Math.max(start, end))
  }

  return (
    <Stack p="md" gap="sm" data-testid="query-tab">
      {detail && (
      <Stack gap={4}>
        <Text size="sm" fw={600}>JOIN するテーブル(外部キー)</Text>
        {schemaPending ? (
          <Loader size="xs" aria-label="スキーマ情報を読み込み中" />
        ) : candidates.length === 0 ? (
          <Text size="sm" c="dimmed">外部キーでつながるテーブルはありません</Text>
        ) : (
          candidates.map((c) => (
            <Checkbox
              key={c.key}
              size="xs"
              label={candidateLabel(c, detail.table.owner)}
              description={c.available ? undefined : '列情報なし'}
              disabled={!c.available}
              checked={s.selected.includes(c.key)}
              onChange={(e) => toggle(c.key, e.currentTarget.checked)}
              styles={{ label: { whiteSpace: 'pre', fontFamily: 'var(--mantine-font-family-monospace)' } }}
            />
          ))
        )}
        <Group gap="sm">
          <Button size="xs" variant="default" onClick={applyTemplate}>
            ひな形を作成
          </Button>
          {edited && !sameSet(s.selected, s.appliedSelected) && (
            <Text size="xs" c="orange" data-testid="edited-notice">
              SQL が編集されているため自動では置き換えません。「ひな形を作成」で置き換えられます
            </Text>
          )}
        </Group>
      </Stack>
      )}

      <SavedQueries
        target={target}
        targetLabel={detail ? `${detail.table.owner}.${detail.table.name}` : 'PDB'}
        sql={s.sql}
        loaded={s.loaded ?? null}
        dirty={dirty}
        onRestore={restore}
        onSaved={saved}
        onUnload={unload}
      />

      <Textarea
        ref={editor}
        aria-label="SELECT 文"
        value={s.sql}
        onChange={(e) => update({ sql: e.currentTarget.value })}
        onKeyDown={(e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault()
            void run()
          }
        }}
        placeholder={detail ? undefined : 'SELECT 文を入力するか、保存済み Query(ひな型)を復元してください'}
        autosize
        minRows={8}
        maxRows={20}
        spellCheck={false}
        styles={{ input: { fontFamily: 'var(--mantine-font-family-monospace)', fontSize: 13 } }}
        error={tooLong ? `${MAX_SQL_CHARS.toLocaleString()} 文字以内で入力してください` : undefined}
      />

      <Group gap="md">
        <Button size="xs" onClick={() => void run()} disabled={!canRun} loading={s.running === 'run'}>
          実行 (Ctrl+Enter)
        </Button>
        <Button size="xs" variant="default" onClick={() => void downloadCsv()} disabled={!canRun} loading={s.running === 'csv'}>
          CSV ダウンロード
        </Button>
        {!s.error && s.result && (
          <>
            <Text size="sm" data-testid="query-row-count">{`${s.result.row_count} 行`}</Text>
            <Text size="sm" c="dimmed">取得 {s.result.elapsed_ms} ms</Text>
          </>
        )}
      </Group>

      {s.error ? (
        <QueryErrorView error={s.error} onGoto={gotoError} />
      ) : (
        s.result && (
          <Stack gap="xs">
            {s.result.has_more && (
              <Text size="sm" c="orange" data-testid="query-truncated">
                {`先頭 ${s.result.max_rows} 行を表示しています(${s.result.max_rows} 行で打ち切り)。全行は CSV でダウンロードできます`}
              </Text>
            )}
            <ResultTable
              label="Query の結果"
              columns={s.result.columns}
              rows={s.result.rows}
              truncated={s.result.truncated}
              maxHeight="calc(100vh - 320px)"
            />
            {s.result.row_count === 0 && <Text c="dimmed" size="sm">結果は 0 行です</Text>}
          </Stack>
        )
      )}
    </Stack>
  )
}

function QueryErrorView({ error, onGoto }: { error: NonNullable<QueryState['error']>; onGoto: () => void }) {
  const e = error.error
  const title = error.kind === 'csv' ? 'CSV を作成できませんでした' : 'SQL を実行できませんでした'
  const message = e.code === 'SQL_REJECTED' ? `実行できない SQL です: ${e.message}` : e.displayMessage
  const pos = e.position
  return (
    <Alert color="red" variant="outline" title={title} data-testid="query-error">
      <Stack gap="xs" align="flex-start">
        <Text size="sm">{message}</Text>
        {pos && (
          <>
            <Text size="sm" data-testid="query-error-position">{`エラー位置: ${pos.line} 行目 ${pos.column} 文字目`}</Text>
            <Code block data-testid="query-error-caret">{caretLines(error.sql, pos.line, pos.column).join('\n')}</Code>
            <Button size="xs" variant="light" color="red" onClick={onGoto}>
              エラー位置へ移動
            </Button>
          </>
        )}
      </Stack>
    </Alert>
  )
}
