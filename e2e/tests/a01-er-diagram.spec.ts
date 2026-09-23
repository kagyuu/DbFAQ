import { expect, test } from '@playwright/test'
import { viewportScale, waitForNodes } from './helpers'

// A01: ER 図のシナリオ(docs/P009-acceptance-direction/A01-er-diagram-scenario.md)
// 前提: e2e/scripts/reset-and-up.sh でベースライン(スナップショット無し)にしてから実行する
test.describe.serial('A01 ER 図', () => {
  test('初回読み込みから詳細への遷移まで', async ({ page }) => {
    // 1
    await page.goto('/')
    await expect(page.getByText('スキーマ情報がありません')).toBeVisible()
    await expect(page.getByTestId('oracle-status')).toHaveAttribute('data-status', 'ok', { timeout: 15_000 })

    // 2
    await page.getByRole('button', { name: 'Oracle から読み込む' }).click()
    await expect(page.getByText('スキーマ情報を更新しました(テーブル 7 / 関連 10)')).toBeVisible({ timeout: 60_000 })
    await waitForNodes(page, 7)
    await expect(page.getByText('テーブル 7 / 関連 10', { exact: true })).toBeVisible()
    await expect(page.getByTestId('header-schema')).toHaveText('スキーマ: HR')
    await expect(page.getByTestId('header-fetched-at')).toContainText('取得日時: ')

    // 3
    await expect(page.locator('.react-flow__minimap')).toBeVisible()
    await expect(page.locator('.react-flow__controls')).toBeVisible()
    await expect(page.locator('.react-flow__edge')).toHaveCount(10)

    // 4
    const s0 = await viewportScale(page)
    const zoomIn = page.locator('.react-flow__controls-zoomin')
    const zoomOut = page.locator('.react-flow__controls-zoomout')
    await zoomIn.click()
    await zoomIn.click()
    await expect.poll(() => viewportScale(page)).toBeGreaterThan(s0)
    const s1 = await viewportScale(page)
    for (let i = 0; i < 4; i++) await zoomOut.click()
    await expect.poll(() => viewportScale(page)).toBeLessThan(s1)
    await page.locator('.react-flow__controls-fitview').click()
    await page.waitForTimeout(500)
    const pane = (await page.locator('.react-flow').boundingBox())!
    for (const node of await page.locator('[data-testid^=er-node-]').all()) {
      const b = (await node.boundingBox())!
      expect(b.x).toBeGreaterThanOrEqual(pane.x - 1)
      expect(b.y).toBeGreaterThanOrEqual(pane.y - 1)
      expect(b.x + b.width).toBeLessThanOrEqual(pane.x + pane.width + 1)
      expect(b.y + b.height).toBeLessThanOrEqual(pane.y + pane.height + 1)
    }

    // 5
    await page.getByLabel('テーブル名で検索').fill('job_h')
    await expect(page.getByRole('option')).toHaveText(/JOB_HISTORY/)
    await page.getByRole('option').getByText('JOB_HISTORY', { exact: true }).click()
    await page.waitForTimeout(600)
    const node = (await page.getByTestId('er-node-JOB_HISTORY').boundingBox())!
    const cx = node.x + node.width / 2
    const cy = node.y + node.height / 2
    expect(Math.abs(cx - (pane.x + pane.width / 2))).toBeLessThan(100)
    expect(Math.abs(cy - (pane.y + pane.height / 2))).toBeLessThan(100)

    // 6
    await page.getByTestId('er-node-EMPLOYEES').click()
    await expect(page).toHaveURL(/\/tables\/HR\/EMPLOYEES$/)
    await expect(page.getByRole('heading', { name: 'HR.EMPLOYEES' })).toBeVisible()

    // 7
    await page.goBack()
    await waitForNodes(page, 7)
  })
})
