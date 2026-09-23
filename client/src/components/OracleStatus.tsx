import { Box, Tooltip } from '@mantine/core'
import { useHealth } from '../api/hooks'

const COLORS = { loading: 'var(--mantine-color-gray-5)', ok: 'var(--mantine-color-green-6)', error: 'var(--mantine-color-red-6)' }

export default function OracleStatus() {
  const { data, error, isPending } = useHealth()
  const status: keyof typeof COLORS = isPending ? 'loading' : data?.oracle.status === 'ok' ? 'ok' : 'error'
  let label = '確認中'
  if (data && status === 'ok') {
    const c = data.config
    label = `Oracle ${data.oracle.version} / ${c.host}:${c.port}/${c.service_name} (${c.user})`
  } else if (data) {
    label = data.oracle.message ?? 'Oracle に接続できません'
  } else if (error) {
    label = error.displayMessage
  }
  return (
    <Tooltip label={label} withArrow>
      <Box
        data-testid="oracle-status"
        data-status={status}
        aria-label={`Oracle: ${label}`}
        style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS[status] }}
      />
    </Tooltip>
  )
}
