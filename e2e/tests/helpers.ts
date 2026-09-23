import { expect, type Page } from '@playwright/test'

/** .react-flow__viewport の transform から scale を読む */
export async function viewportScale(page: Page): Promise<number> {
  const t = await page.locator('.react-flow__viewport').evaluate((el) => (el as HTMLElement).style.transform)
  const m = t.match(/scale\(([\d.]+)\)/)
  return m ? Number(m[1]) : NaN
}

export async function waitForNodes(page: Page, count: number) {
  await expect(page.locator('[data-testid^=er-node-]')).toHaveCount(count, { timeout: 30_000 })
}
