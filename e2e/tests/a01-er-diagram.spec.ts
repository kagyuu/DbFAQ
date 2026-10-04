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
    await expect(page.getByText('スキーマ情報を更新しました(テーブル 8 / 関連 11)')).toBeVisible({ timeout: 60_000 })
    await waitForNodes(page, 8)
    await expect(page.getByText('テーブル 8 / 関連 11', { exact: true })).toBeVisible()
    await expect(page.getByTestId('header-schema')).toHaveText('スキーマ: HR')
    await expect(page.getByTestId('header-fetched-at')).toContainText('取得日時: ')

    // 3
    await expect(page.locator('.react-flow__minimap')).toBeVisible()
    await expect(page.locator('.react-flow__controls')).toBeVisible()
    await expect(page.locator('.react-flow__edge')).toHaveCount(11)

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
    await waitForNodes(page, 8)
  })

  // ※CR-001 により追加(REQ-SCREEN-009 ノードのドラッグ)。前のテストが作ったスナップショットを使う
  test('ノードのドラッグ(クリック扱いにならず、位置は保存しない)', async ({ page }) => {
    const box = async (name: string) => (await page.getByTestId(`er-node-${name}`).boundingBox())!
    // 表示倍率に左右されないよう、LOCATIONS からの相対位置を scale で割ったものを比べる
    const relative = async () => {
      const [d, l, s] = [await box('DEPARTMENTS'), await box('LOCATIONS'), await viewportScale(page)]
      return { x: (d.x - l.x) / s, y: (d.y - l.y) / s }
    }

    // 8
    await page.goto('/')
    await waitForNodes(page, 8)
    await page.waitForTimeout(500)
    const before = await box('DEPARTMENTS')
    const loc = await box('LOCATIONS')
    const rel0 = await relative()
    await page.mouse.move(before.x + before.width / 2, before.y + 12)
    await page.mouse.down()
    await page.mouse.move(before.x + before.width / 2 + 120, before.y + 12 + 80, { steps: 10 })
    await page.mouse.up()
    await page.waitForTimeout(300)
    await expect(page).toHaveURL(/\/$/)
    const after = await box('DEPARTMENTS')
    // ドラッグ判定のしきい値(nodeDragThreshold)を超えるまでの最初の移動分は動かないため、範囲で見る
    expect(after.x - before.x).toBeGreaterThan(90)
    expect(after.x - before.x).toBeLessThan(125)
    expect(after.y - before.y).toBeGreaterThan(55)
    expect(after.y - before.y).toBeLessThan(85)
    const loc2 = await box('LOCATIONS')
    expect(Math.abs(loc2.x - loc.x)).toBeLessThan(1)
    expect(Math.abs(loc2.y - loc.y)).toBeLessThan(1)

    // 9
    await page.reload()
    await waitForNodes(page, 8)
    await page.waitForTimeout(500)
    const rel1 = await relative()
    expect(Math.abs(rel1.x - rel0.x)).toBeLessThan(2)
    expect(Math.abs(rel1.y - rel0.y)).toBeLessThan(2)
  })
})
