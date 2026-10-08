import { Paper, Stack, Text, Tooltip, UnstyledButton } from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { useHealth } from '../api/hooks'

/** ドラム缶(記憶装置。円柱)の絵 */
export function DrumSvg({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 40 46" aria-hidden="true">
      <path d="M2 7v32c0 3.3 8 6 18 6s18-2.7 18-6V7" fill="var(--mantine-color-blue-1)" stroke="var(--mantine-color-blue-7)" strokeWidth="2" />
      <path d="M2 18c0 3.3 8 6 18 6s18-2.7 18-6M2 29c0 3.3 8 6 18 6s18-2.7 18-6" fill="none" stroke="var(--mantine-color-blue-7)" strokeWidth="1.5" />
      <ellipse cx="20" cy="7" rx="18" ry="6" fill="var(--mantine-color-blue-2)" stroke="var(--mantine-color-blue-7)" strokeWidth="2" />
    </svg>
  )
}

/** PDB 名(GET /api/health の config.service_name を英大文字に)。取得前・失敗時は null */
export function usePdbName(): string | null {
  const { data } = useHealth()
  return data?.config.service_name ? data.config.service_name.toUpperCase() : null
}

// SC-01 のドラム缶のアイコン(P002 §2.1.2。※CR-005により追加)。キャンバス領域の左上に固定で置く
export default function PdbIcon() {
  const navigate = useNavigate()
  const name = usePdbName()
  return (
    <Tooltip label="PDB の情報と Query" position="right">
      <UnstyledButton
        onClick={() => navigate('/pdb')}
        aria-label="PDB を開く"
        data-testid="pdb-icon"
        style={{ position: 'absolute', top: 12, left: 12, zIndex: 10 }}
      >
        <Paper withBorder shadow="xs" px="sm" py={6} radius="md">
          <Stack gap={0} align="center">
            <DrumSvg />
            <Text size="xs" fw={700}>PDB</Text>
            {name && <Text size="xs" c="dimmed" data-testid="pdb-icon-name">{name}</Text>}
          </Stack>
        </Paper>
      </UnstyledButton>
    </Tooltip>
  )
}
