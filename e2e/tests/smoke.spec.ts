import { expect, test } from '@playwright/test'

test('トップを開くとヘッダに DbFAQ が表示される', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('link', { name: 'DbFAQ' })).toBeVisible()
})

test('/api/health が 200', async ({ request }) => {
  const res = await request.get('/api/health')
  expect(res.status()).toBe(200)
})
