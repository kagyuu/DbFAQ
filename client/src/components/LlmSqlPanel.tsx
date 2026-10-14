import { Button, Code, CopyButton, Group, Modal, ScrollArea, Stack, Text, Textarea, Title } from '@mantine/core'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { ApiError, generateSql } from '../api/client'
import type { LlmExchange, LlmSqlResult, SavedQueryTarget } from '../api/types'
import { useLlmAvailable } from './LlmStatus'

export const MAX_LLM_REQUEST_CHARS = 2_000

/** LLM で SQL を作成する部品の状態。Query タブの状態の一部として保つ(P002 §2.2.9) */
export interface LlmPanelState {
  request: string
  running: boolean
  result?: LlmSqlResult
  /** 入力欄が編集中のため、置き換えの確認を待っている結果 */
  pending?: LlmSqlResult
  error?: ApiError
}

export const initialLlmState: LlmPanelState = { request: '', running: false }

type Props = {
  target: SavedQueryTarget
  state: LlmPanelState
  /** 非同期の処理の後でも最新の状態に当てられるよう、関数で更新する */
  update: (fn: (prev: LlmPanelState) => LlmPanelState) => void
  /** 最後のひな形・復元・保存・LLM の作成の後に入力欄が編集されているか */
  dirty: boolean
  /** 作った SQL を入力欄に入れる(自動では実行しない) */
  onApply: (sql: string) => void
}

const toApiError = (e: unknown) =>
  e instanceof ApiError ? e : new ApiError('INTERNAL_ERROR', 0, '内部エラーが発生しました')

function errorText(e: ApiError): string {
  if (e.code === 'LLM_UNAVAILABLE') return `LLM を使えません: ${e.message}`
  if (e.code === 'LLM_TIMEOUT') return 'LLM の応答がタイムアウトしました'
  if (e.code === 'LLM_ERROR') return `LLM の応答から SQL を作れませんでした: ${e.message}`
  return e.displayMessage
}

function ResultInfo({ result }: { result: LlmSqlResult }) {
  return (
    <Stack gap={2} data-testid="llm-result">
      <Text size="xs" c="dimmed">
        {`LLM(${result.model})が作成しました(${(result.elapsed_ms / 1000).toFixed(1)} 秒)。内容を確かめてから実行してください`}
      </Text>
      {!result.guard.ok && (
        <Text size="xs" c="red" data-testid="llm-guard-error">{`Query の検査で実行できない SQL です: ${result.guard.message}`}</Text>
      )}
      {result.context.truncated && (
        <Text size="xs" c="orange">スキーマの情報が長いため、一部のテーブルを省いて LLM に渡しました</Text>
      )}
    </Stack>
  )
}

function ExchangePart({ title, text, testId }: { title: string; text: string | null; testId: string }) {
  return (
    <Stack gap={4}>
      <Group justify="space-between">
        <Title order={6}>{title}</Title>
        {text !== null && (
          <CopyButton value={text}>
            {({ copied, copy }) => (
              <Button size="compact-xs" variant="light" onClick={copy} aria-label={`コピー: ${title}`}>
                {copied ? 'コピーしました' : 'コピー'}
              </Button>
            )}
          </CopyButton>
        )}
      </Group>
      {text === null ? (
        <Text size="sm" c="dimmed" data-testid={testId}>リプライはありません(LLM から応答が返りませんでした)</Text>
      ) : (
        <ScrollArea.Autosize mah={320} type="auto">
          <Code block data-testid={testId} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{text}</Code>
        </ScrollArea.Autosize>
      )}
    </Stack>
  )
}

/** LLM とのやりとりのダイアログ(P002 §2.2.9。※CR-008により追加) */
function ExchangeDialog({ exchange, result, onClose }: { exchange: LlmExchange; result?: LlmSqlResult; onClose: () => void }) {
  return (
    <Modal opened onClose={onClose} title="LLM とのやりとり" size="xl" centered>
      <Stack gap="md" data-testid="llm-exchange">
        {result && (
          <Text size="sm" c="dimmed">{`モデル: ${result.model} / ${(result.elapsed_ms / 1000).toFixed(1)} 秒`}</Text>
        )}
        <ExchangePart title="リクエスト: システムの指示" text={exchange.system} testId="llm-exchange-system" />
        <ExchangePart title="リクエスト: ユーザーの文" text={exchange.user} testId="llm-exchange-user" />
        <ExchangePart title="リプライ" text={exchange.reply} testId="llm-exchange-reply" />
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>閉じる</Button>
        </Group>
      </Stack>
    </Modal>
  )
}

// 自然言語の要求から LLM で SQL を作成する(P002 §2.2.9。※CR-007により追加)
export default function LlmSqlPanel({ target, state, update, dirty, onApply }: Props) {
  const qc = useQueryClient()
  const available = useLlmAvailable()
  const [showExchange, setShowExchange] = useState(false)
  const dirtyRef = useRef(dirty)
  useEffect(() => {
    dirtyRef.current = dirty
  }, [dirty])

  const text = state.request.trim()
  const tooLong = text.length > MAX_LLM_REQUEST_CHARS
  const canGenerate = available && text !== '' && !tooLong && !state.running
  // 直近の作成の LLM とのやりとり(成功、置き換えの確認待ち、またはエラー。※CR-008)
  const exchange = state.running ? undefined : (state.pending ?? state.result)?.exchange ?? state.error?.exchange

  const generate = async () => {
    if (!canGenerate) return
    update((p) => ({ ...p, running: true, error: undefined, pending: undefined }))
    try {
      const result = await generateSql(target, text)
      if (dirtyRef.current) {
        update((p) => ({ ...p, running: false, pending: result }))
      } else {
        onApply(result.sql)
        update((p) => ({ ...p, running: false, result }))
      }
    } catch (e) {
      const err = toApiError(e)
      update((p) => ({ ...p, running: false, error: err }))
      if (err.code === 'LLM_UNAVAILABLE') void qc.invalidateQueries({ queryKey: ['health'] })
    }
  }

  const settle = (apply: boolean) => {
    const pending = state.pending
    if (!pending) return
    if (apply) onApply(pending.sql)
    update((p) => ({ ...p, pending: undefined, result: pending }))
  }

  return (
    <Stack gap={4} data-testid="llm-sql-panel">
      <Text size="sm" fw={600}>自然言語で SQL を作成(LLM)</Text>
      <Textarea
        aria-label="LLM への要求"
        placeholder="作りたい SQL を文章で書いてください(例: 給与の高い社員を上位 5 人、姓と部署名と給与)"
        value={state.request}
        onChange={(e) => {
          const v = e.currentTarget.value
          update((p) => ({ ...p, request: v }))
        }}
        autosize
        minRows={2}
        maxRows={6}
        error={tooLong ? `${MAX_LLM_REQUEST_CHARS.toLocaleString()} 文字以内で入力してください` : undefined}
      />
      <Group gap="sm" align="flex-start">
        <Button size="xs" variant="light" onClick={() => void generate()} disabled={!canGenerate} loading={state.running}>
          LLM で SQL を作成
        </Button>
        <Button size="xs" variant="subtle" onClick={() => setShowExchange(true)} disabled={!exchange}>
          LLM とのやりとり
        </Button>
        <Stack gap={2} style={{ flex: 1 }}>
          {!available && (
            <Text size="xs" c="dimmed" data-testid="llm-unavailable">
              LLM が使えないため作成できません(ヘッダの LLM の状態を確認してください)
            </Text>
          )}
          {state.running && <Text size="xs" c="dimmed">作成中… LLM の応答には時間がかかります(数分かかることもあります)</Text>}
          {!state.running && state.error && (
            <Text size="xs" c="red" data-testid="llm-error">{errorText(state.error)}</Text>
          )}
          {!state.running && !state.error && state.result && <ResultInfo result={state.result} />}
        </Stack>
      </Group>
      {showExchange && exchange && (
        <ExchangeDialog exchange={exchange} result={state.error ? undefined : (state.pending ?? state.result)} onClose={() => setShowExchange(false)} />
      )}
      {state.pending && (
        <Modal opened onClose={() => settle(false)} title="SQL の置き換え" centered>
          <Stack gap="md">
            <Text size="sm">入力欄の SQL を LLM が作成した SQL で置き換えますか? 編集中の内容は失われます</Text>
            <Group justify="flex-end" gap="sm">
              <Button variant="default" onClick={() => settle(false)}>キャンセル</Button>
              <Button onClick={() => settle(true)}>置き換える</Button>
            </Group>
          </Stack>
        </Modal>
      )}
    </Stack>
  )
}
