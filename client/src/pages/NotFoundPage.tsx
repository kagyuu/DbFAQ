import { Anchor, Stack, Text } from '@mantine/core'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <Stack p="xl" gap="sm">
      <Text fw={700}>ページが見つかりません</Text>
      <Anchor component={Link} to="/">
        ER 図へ
      </Anchor>
    </Stack>
  )
}
