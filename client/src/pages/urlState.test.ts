import { expect, test } from 'vitest'
import { parsePage, parseTab } from './urlState'

test('parseTab', () => {
  expect(parseTab('data')).toBe('data')
  expect(parseTab('query')).toBe('query')
  expect(parseTab('schema')).toBe('schema')
  expect(parseTab('x')).toBe('schema')
  expect(parseTab(null)).toBe('schema')
})

test.each([
  ['3', 3],
  ['2001', 2001],
  ['0', 1],
  ['-1', 1],
  ['abc', 1],
  ['2.5', 1],
  ['2002', 1],
  [null, 1],
])('parsePage(%s) = %s', (v, expected) => {
  expect(parsePage(v)).toBe(expected)
})
