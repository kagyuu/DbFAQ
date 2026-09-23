import { expect, test } from '@playwright/test'

// A02: テーブル詳細のシナリオ(docs/P009-acceptance-direction/A02-table-detail-scenario.md)
// 前提: A01 がスナップショットを作っている
test('スキーマ情報 → 外部キーで移動 → データタブのページ送り', async ({ page }) => {
  // 1
  await page.goto('/tables/HR/EMPLOYEES')
  await expect(page.getByRole('tab', { name: 'スキーマ情報' })).toHaveAttribute('aria-selected', 'true')
  const cols = page.getByRole('table', { name: '列' })
  // 列名セルの完全一致で行を特定する(コメントに列名を含む別の行と区別するため。F003)
  const rowOf = (name: string) => cols.getByRole('row').filter({ has: page.getByRole('cell', { name, exact: true }) })
  const empRow = rowOf('EMPLOYEE_ID')
  await expect(empRow).toContainText('NUMBER(6)')
  await expect(empRow).toContainText('不可')
  await expect(empRow).toContainText('🔑 1')
  await expect(rowOf('SALARY')).toContainText('NUMBER(8,2)')
  await expect(page.getByRole('table', { name: '主キー' })).toContainText('EMP_EMP_ID_PK')
  await expect(page.getByRole('table', { name: '一意制約' })).toContainText('EMP_EMAIL_UK')
  await expect(page.getByRole('table', { name: 'インデックス' }).getByRole('row')).toHaveCount(7) // 見出し + 6
  await expect(page.getByTestId('num-rows')).toHaveText('107')

  // 2
  await page.getByRole('table', { name: '外部キー(参照先)' }).getByRole('link', { name: 'DEPARTMENTS' }).click()
  await expect(page).toHaveURL(/\/tables\/HR\/DEPARTMENTS$/)
  await expect(page.getByRole('heading', { name: 'HR.DEPARTMENTS' })).toBeVisible()
  const refs = page.getByRole('table', { name: '外部キー(参照元)' })
  await expect(refs).toContainText('EMP_DEPT_FK')
  await expect(refs).toContainText('JHIST_DEPT_FK')

  // 3
  await page.goBack()
  await expect(page.getByRole('heading', { name: 'HR.EMPLOYEES' })).toBeVisible()

  // 4
  await page.getByRole('tab', { name: 'データ' }).click()
  await expect(page).toHaveURL(/tab=data/)
  await expect(page.getByText('並び順: EMPLOYEE_ID(主キー)')).toBeVisible()
  await expect(page.getByTestId('page-range')).toHaveText('1 ページ目 (1〜50 行)')
  const grid = page.getByRole('table', { name: 'データ' })
  await expect(grid.locator('tbody tr')).toHaveCount(50)
  await expect(grid.locator('tbody tr').first().locator('td').first()).toHaveText('100')
  await expect(grid.locator('[data-null="true"]').first()).toBeVisible()

  // 5
  const next = page.getByRole('button', { name: '次へ >' })
  await next.click()
  await expect(page.getByTestId('page-range')).toHaveText('2 ページ目 (51〜100 行)')
  await expect(page).toHaveURL(/page=2/)
  await next.click()
  await expect(page.getByTestId('page-range')).toHaveText('3 ページ目 (101〜107 行)')
  await expect(next).toBeDisabled()
  await page.getByRole('button', { name: '< 前へ' }).click()
  await expect(page.getByTestId('page-range')).toHaveText('2 ページ目 (51〜100 行)')

  // 6
  await page.reload()
  await expect(page.getByRole('tab', { name: 'データ' })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByTestId('page-range')).toHaveText('2 ページ目 (51〜100 行)')

  // 7
  await page.goto('/tables/HR/JOB_HISTORY?tab=data')
  await expect(page.getByText('並び順: EMPLOYEE_ID, START_DATE(主キー)')).toBeVisible()
  await expect(page.getByRole('table', { name: 'データ' }).locator('tbody tr')).toHaveCount(10)

  // 8
  await page.goto('/tables/HR/NO_SUCH')
  await expect(page.getByText('テーブルが見つかりません: HR.NO_SUCH')).toBeVisible()
  await expect(page.getByRole('link', { name: 'ER 図へ' })).toHaveAttribute('href', '/')

  // 9
  await page.getByRole('banner').getByRole('link', { name: 'ER 図' }).click()
  await expect(page).toHaveURL(/\/$/)
})
