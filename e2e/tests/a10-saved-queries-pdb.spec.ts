import { type APIRequestContext, expect, type Page, test } from '@playwright/test'

// A10: 保存済み Query と PDB 画面のシナリオ(docs/P009-acceptance-direction/A10-saved-queries-pdb-scenario.md)。※CR-005により追加
// 前提: A01 がスナップショットを作っている。作る Query の名前には A10- を付け、前後で消す
const SQL50 = 'SELECT EMPLOYEE_ID, LAST_NAME FROM HR.EMPLOYEES WHERE DEPARTMENT_ID = 50 ORDER BY LAST_NAME'
const TARGETS = ['scope=table&owner=HR&table=EMPLOYEES', 'scope=table&owner=HR&table=DEPARTMENTS', 'scope=pdb']

async function cleanup(request: APIRequestContext) {
  for (const t of TARGETS) {
    const { items } = await (await request.get(`/api/saved-queries?${t}`)).json()
    for (const q of items) if (q.name.startsWith('A10-')) await request.delete(`/api/saved-queries/${q.id}`)
  }
}

test.beforeEach(async ({ request }) => cleanup(request))
test.afterEach(async ({ request }) => cleanup(request))

const editor = (page: Page) => page.getByRole('textbox', { name: 'SELECT 文' })
const dialog = (page: Page) => page.getByRole('dialog')

async function saveAs(page: Page, name: string, description = '') {
  await page.getByRole('button', { name: '名前を付けて保存' }).click()
  await dialog(page).getByRole('textbox', { name: /名前/ }).fill(name)
  if (description) await dialog(page).getByRole('textbox', { name: '説明' }).fill(description)
  await dialog(page).getByRole('button', { name: '保存' }).click()
}

test('テーブルの Query の保存・復元・上書き・変更・削除', async ({ page }) => {
  // 1
  await page.goto('/tables/HR/EMPLOYEES?tab=query')
  await expect(page.getByText('保存済み Query (0)')).toBeVisible()
  await expect(page.getByText('保存済みの Query はありません')).toBeVisible()

  // 2
  await editor(page).fill(SQL50)
  await saveAs(page, 'A10-部署50', '部署 50 の社員')
  await expect(page.getByText('保存しました: A10-部署50')).toBeVisible()
  await expect(page.getByText('保存済み Query (1)')).toBeVisible()
  await expect(page.getByTestId('loaded-query')).toHaveText('復元中: A10-部署50')

  // 3
  await saveAs(page, 'A10-部署50')
  await expect(dialog(page).getByTestId('dialog-error')).toHaveText('同じ名前の Query が既にあります')
  await dialog(page).getByRole('button', { name: 'キャンセル' }).click()
  await expect(dialog(page)).toHaveCount(0)

  // 4
  await page.goto('/tables/HR/DEPARTMENTS?tab=query')
  await expect(page.getByText('保存済み Query (0)')).toBeVisible()

  // 5
  await page.goto('/tables/HR/EMPLOYEES?tab=query')
  await expect(editor(page)).toHaveValue(/^SELECT\n {2}t0\.EMPLOYEE_ID/)
  await page.getByRole('button', { name: '復元: A10-部署50' }).click()
  await expect(editor(page)).toHaveValue(SQL50)
  await page.getByRole('button', { name: '実行 (Ctrl+Enter)' }).click()
  await expect(page.getByTestId('query-row-count')).toHaveText('45 行')

  // 6
  await editor(page).fill(SQL50.replace('= 50', '= 60'))
  await page.getByRole('button', { name: '上書き保存' }).click()
  await expect(page.getByText('上書き保存しました: A10-部署50')).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: '復元: A10-部署50' }).click()
  await expect(editor(page)).toHaveValue(/DEPARTMENT_ID = 60/)

  // 7
  await editor(page).fill('SELECT 1 FROM DUAL')
  await page.getByRole('button', { name: '復元: A10-部署50' }).click()
  await expect(dialog(page)).toContainText('入力欄の SQL を「A10-部署50」で置き換えますか')
  await dialog(page).getByRole('button', { name: 'キャンセル' }).click()
  await expect(editor(page)).toHaveValue('SELECT 1 FROM DUAL')

  // 8
  await page.getByRole('button', { name: '編集: A10-部署50' }).click()
  await dialog(page).getByRole('textbox', { name: /名前/ }).fill('A10-部署60')
  await dialog(page).getByRole('button', { name: '保存' }).click()
  await expect(page.getByRole('button', { name: '復元: A10-部署60' })).toBeVisible()
  await page.getByRole('button', { name: '削除: A10-部署60' }).click()
  await dialog(page).getByRole('button', { name: '削除' }).click()
  await expect(page.getByText('保存済みの Query はありません')).toBeVisible()
})

test('ドラム缶のアイコン → PDB 情報 → ひな型の実行・保存', async ({ page }) => {
  // 9
  await page.goto('/')
  const icon = page.getByRole('button', { name: 'PDB を開く' })
  await expect(icon).toContainText('PDB')
  await expect(page.getByTestId('pdb-icon-name')).toHaveText('FREEPDB1')
  await icon.click()
  await expect(page).toHaveURL(/\/pdb$/)
  await expect(page.getByRole('heading', { name: 'PDB: FREEPDB1' })).toBeVisible()

  // 10
  await expect(page.getByTestId('pdb-section-overview')).toContainText('コンテナ名(PDB)FREEPDB1')
  await expect(page.getByTestId('pdb-section-overview')).toContainText('接続ユーザーHR')
  await expect(page.getByTestId('pdb-section-ts_quotas')).toContainText('USERS')
  await expect(page.getByTestId('pdb-section-segments')).toContainText('LOBSEGMENT')
  const denied = page.getByTestId('pdb-section-error-tablespaces')
  await expect(denied).toContainText('権限が無いため取得できません')
  await expect(denied).toContainText('[ORA-00942]')

  // 11
  await page.getByRole('tab', { name: 'Query' }).click()
  await expect(page).toHaveURL(/tab=query/)
  await expect(page.getByText('JOIN するテーブル(外部キー)')).toHaveCount(0)
  await expect(editor(page)).toHaveValue('')
  await expect(page.getByText('保存済み Query (17)')).toBeVisible()
  const t01 = page.getByTestId('saved-query-row').filter({ hasText: '01. USERS 表領域の大きさ' })
  await expect(t01).toContainText('ひな型')
  await expect(page.getByTestId('saved-query-row').filter({ hasText: '03. LOB 領域の大きさと実データの合計(テーブル.カラムごと)' })).toBeVisible()

  // 12
  await page.getByRole('button', { name: '復元: 03. LOB 領域の大きさと実データの合計(テーブル.カラムごと)' }).click()
  await page.getByRole('button', { name: '実行 (Ctrl+Enter)' }).click()
  const result = page.getByRole('table', { name: 'Query の結果' })
  await expect(result.getByRole('cell', { name: 'EMPLOYEE_FIGURE.FIGURE', exact: true })).toBeVisible({ timeout: 30_000 })
  await expect(result.getByRole('cell', { name: 'BLOB', exact: true })).toBeVisible()

  // 13
  await page.getByRole('button', { name: '復元: 01. USERS 表領域の大きさ' }).click()
  await page.getByRole('button', { name: '実行 (Ctrl+Enter)' }).click()
  await expect(page.getByTestId('query-error')).toContainText('[ORA-00942]')

  // 14
  await editor(page).fill("SELECT SYS_CONTEXT('USERENV','CON_NAME') AS CON FROM DUAL")
  await saveAs(page, 'A10-PDB名')
  await expect(page.getByText('保存済み Query (18)')).toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: '復元: A10-PDB名' }).click()
  await page.getByRole('button', { name: '実行 (Ctrl+Enter)' }).click()
  await expect(page.getByRole('table', { name: 'Query の結果' }).getByRole('cell', { name: 'FREEPDB1', exact: true })).toBeVisible()

  // 15
  await page.getByRole('button', { name: '削除: A10-PDB名' }).click()
  await dialog(page).getByRole('button', { name: '削除' }).click()
  await expect(page.getByText('保存済み Query (17)')).toBeVisible()
})
