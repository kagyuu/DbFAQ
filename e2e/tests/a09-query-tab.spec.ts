import { readFile, rm } from 'node:fs/promises'
import { expect, test } from '@playwright/test'

// A09: Query タブのシナリオ(docs/P009-acceptance-direction/A09-query-tab-scenario.md)。※CR-004により追加
// 前提: A01 がスナップショットを作っている
const CROSS = 'SELECT a.EMPLOYEE_ID A_ID, b.EMPLOYEE_ID B_ID FROM HR.EMPLOYEES a CROSS JOIN HR.EMPLOYEES b ORDER BY 1, 2'

test('ひな形 → JOIN → 実行 → 打ち切り → CSV → エラー位置 → 拒否', async ({ page }) => {
  const editor = page.getByRole('textbox', { name: 'SELECT 文' })
  const result = page.getByRole('table', { name: 'Query の結果' })

  // 1
  await page.goto('/tables/HR/EMPLOYEES')
  await page.getByRole('tab', { name: 'Query' }).click()
  await expect(page).toHaveURL(/tab=query/)
  await expect(editor).toHaveValue(/^SELECT\n/)
  await expect(editor).toHaveValue(/t0\.EMPLOYEE_ID/)
  await expect(editor).toHaveValue(/FROM HR\.EMPLOYEES t0/)
  await expect(editor).toHaveValue(/ORDER BY t0\.EMPLOYEE_ID/)

  // 2
  await page.reload()
  await expect(page.getByRole('tab', { name: 'Query' })).toHaveAttribute('aria-selected', 'true')

  // 3
  await page.getByRole('checkbox', { name: /→ DEPARTMENTS EMP_DEPT_FK/ }).check()
  await expect(editor).toHaveValue(/LEFT JOIN HR\.DEPARTMENTS t1 ON t1\.DEPARTMENT_ID = t0\.DEPARTMENT_ID/)
  await expect(editor).toHaveValue(/t1\.DEPARTMENT_NAME/)

  // 4
  await page.getByRole('button', { name: /実行/ }).click()
  await expect(page.getByTestId('query-row-count')).toHaveText('107 行')
  await expect(page.getByText(/^取得 \d+ ms$/)).toBeVisible()
  await expect(result.locator('tbody tr')).toHaveCount(107)
  await expect(result.locator('tbody tr').first().locator('td').first()).toHaveText('100')
  await expect(result.getByRole('columnheader', { name: 'DEPARTMENT_NAME' })).toBeVisible()
  await expect(result.getByRole('cell', { name: 'Executive', exact: true }).first()).toBeVisible()
  await expect(result.locator('[data-null="true"]').first()).toBeVisible()

  // 5
  await editor.fill(CROSS)
  await editor.press('Control+Enter')
  await expect(page.getByTestId('query-truncated')).toContainText('500 行で打ち切り')
  await expect(result.locator('tbody tr')).toHaveCount(500)

  // 6
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'CSV ダウンロード' }).click(),
  ])
  expect(download.suggestedFilename()).toMatch(/^EMPLOYEES_query_\d{8}-\d{6}\.csv$/)
  const path = await download.path()
  try {
    const raw = await readFile(path)
    expect([...raw.subarray(0, 3)]).toEqual([0xef, 0xbb, 0xbf])
    const lines = raw.toString('utf-8').slice(1).split('\r\n')
    expect(lines[0]).toBe('A_ID,B_ID')
    expect(lines.filter((l) => l !== '').length - 1).toBe(11_449)
  } finally {
    await rm(path, { force: true })
  }

  // 7
  await editor.fill('SELECT 1\nFROM HR.EMPLOYEES\nWHERE BAR = 1')
  await page.getByRole('button', { name: /実行/ }).click()
  await expect(page.getByTestId('query-error')).toContainText('[ORA-00904]')
  await expect(page.getByTestId('query-error-position')).toHaveText('エラー位置: 3 行目 7 文字目')
  await page.getByRole('button', { name: 'エラー位置へ移動' }).click()
  expect(await editor.evaluate((el) => (el as HTMLTextAreaElement).selectionStart)).toBe(33)

  // 8
  await editor.fill('DELETE FROM HR.EMPLOYEES')
  await page.getByRole('button', { name: /実行/ }).click()
  await expect(page.getByTestId('query-error')).toContainText('実行できない SQL です')

  // 9
  await page.getByRole('tab', { name: 'スキーマ情報' }).click()
  await expect(page.getByRole('table', { name: '列' })).toBeVisible()
  await page.getByRole('tab', { name: 'データ' }).click()
  await expect(page.getByRole('table', { name: 'データ' }).locator('tbody tr')).toHaveCount(50)
  await page.getByRole('tab', { name: 'Query' }).click()
  await expect(editor).toHaveValue('DELETE FROM HR.EMPLOYEES')
})
