import { Box, Tooltip } from '@mantine/core'
import { useHealth } from '../api/hooks'

const COLORS = {
  loading: 'var(--mantine-color-gray-5)',
  ok: 'var(--mantine-color-green-6)',
  error: 'var(--mantine-color-red-6)',
  disabled: 'var(--mantine-color-gray-5)',
}

/** LLM が使えるか(作成のボタンの有効・無効に使う。P002 §2.2.9) */
export function useLlmAvailable(): boolean {
  const { data } = useHealth()
  return data?.llm?.status === 'ok'
}

// 共通ヘッダの LLM の状態の丸(P002 §1.1。※CR-007により追加)。Oracle の丸と同じ GET /api/health を使う
export default function LlmStatus() {
  const { data, error, isPending } = useHealth()
  const llm = data?.llm
  const status: keyof typeof COLORS = isPending ? 'loading' : (llm?.status ?? 'error')
  let label = '確認中'
  if (llm?.status === 'ok') label = `LLM ${llm.model} / ${llm.base_url}`
  else if (llm?.status === 'disabled') label = llm.message ?? 'LLM は設定されていません'
  else if (llm) label = `${llm.message ?? 'LLM を使えません'}${llm.base_url ? ` / ${llm.base_url}` : ''}`
  else if (error) label = error.displayMessage
  return (
    <Tooltip label={label} withArrow>
      <Box
        data-testid="llm-status"
        data-status={status}
        aria-label={`LLM: ${label}`}
        style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS[status] }}
      />
    </Tooltip>
  )
}
