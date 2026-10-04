import { expect, test } from '@playwright/test'
import { waitForNodes } from './helpers'

// A03: Oracle に届かないときのシナリオ(docs/P009-acceptance-direction/A03-oracle-down-scenario.md)
// 前提: api を DBFAQ_ORACLE_HOST=oracle-unreachable.invalid で作り直してから "unreachable" を、
//       既定の接続先に戻してから "recovered" を実行する
test('unreachable: 保存済みで閲覧でき、エラーが表示される', async ({ page, request }) => {
  test.setTimeout(240_000)
  // 1
  const h = await (await request.get('/api/health', { timeout: 60_000 })).json()
  expect(h.status).toBe('degraded')
  expect(h.oracle.status).toBe('error')

  // 2
  await page.goto('/')
  await waitForNodes(page, 8)
  await expect(page.getByTestId('oracle-status')).toHaveAttribute('data-status', 'error', { timeout: 60_000 })
  const fetched = await page.getByTestId('header-fetched-at').textContent()

  // 3
  await page.getByRole('button', { name: 'Oracle から再読み込み' }).click()
  await expect(page.getByText('再読み込みに失敗しました')).toBeVisible({ timeout: 150_000 })
  await waitForNodes(page, 8)
  await expect(page.getByTestId('header-fetched-at')).toHaveText(fetched!)

  // 4
  await page.goto('/tables/HR/EMPLOYEES')
  await expect(page.getByRole('table', { name: '列' })).toBeVisible()

  // 5
  await page.getByRole('tab', { name: 'データ' }).click()
  await expect(page.getByText('データを取得できませんでした')).toBeVisible({ timeout: 150_000 })
  await expect(page.getByRole('button', { name: '再試行' })).toBeVisible()
})

test('recovered: 既定の接続先に戻すとデータが表示される', async ({ page }) => {
  // 6
  await page.goto('/tables/HR/EMPLOYEES?tab=data')
  await expect(page.getByRole('table', { name: 'データ' }).locator('tbody tr')).toHaveCount(50, { timeout: 60_000 })
})
