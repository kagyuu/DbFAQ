import { expect, test } from '@playwright/test'
import { viewportScale, waitForNodes } from './helpers'

// A05: 性能(docs/P009-acceptance-direction/A05-performance.md)
test('hr: ER 図の表示が 1 秒未満', async ({ page }) => {
  await page.goto('/')
  await waitForNodes(page, 8)
  const t0 = Date.now()
  await page.reload()
  await waitForNodes(page, 8)
  const ms = Date.now() - t0
  console.log(`HR ER 図の表示: ${ms} ms`)
  expect(ms).toBeLessThan(1000)
})

test('large: 300 表の ER 図の表示が 3 秒未満で、拡大縮小できる', async ({ page }) => {
  const t0 = Date.now()
  await page.goto('/')
  await expect(page.locator('.react-flow__node')).toHaveCount(300, { timeout: 30_000 })
  const ms = Date.now() - t0
  console.log(`大規模 ER 図の表示: ${ms} ms`)
  expect(ms).toBeLessThan(3000)
  const s0 = await viewportScale(page)
  const pane = page.locator('.react-flow__pane')
  await pane.hover()
  await page.mouse.wheel(0, -300)
  await expect.poll(() => viewportScale(page), { timeout: 1000 }).not.toBe(s0)
})
