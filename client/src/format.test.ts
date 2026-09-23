import { expect, test } from 'vitest'
import { formatLocalDateTime } from './format'

test('UTC のタイムゾーンで整形する(テストは TZ=UTC)', () => {
  expect(formatLocalDateTime('2026-09-23T01:15:02Z')).toBe('2026-09-23 01:15:02')
})

test('不正な値はそのまま返す', () => {
  expect(formatLocalDateTime('x')).toBe('x')
})
