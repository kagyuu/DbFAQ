import { expect, test } from '@playwright/test'

// A11: LLM で SQL を作成するシナリオ(docs/P009-acceptance-direction/A11-llm-sql-scenario.md)。※CR-007により追加
// 前提: A01 がスナップショットを作っている。available は api から LLM に届く構成、unreachable は api を
// DBFAQ_LLM_BASE_URL=http://llm-unreachable.invalid:11434 で作り直した構成で実行する(run-suite.sh)
test.setTimeout(900_000) // ※CR-009: LLM の性能は求めない。時間がかかっても作成されることだけを判定する

test('available: ヘッダの LLM の丸 → 要求から SQL を作成 → 実行', async ({ page }) => {
  // 1
  await page.goto('/')
  const dot = page.getByTestId('llm-status')
  await expect(dot).toHaveAttribute('data-status', 'ok', { timeout: 30_000 })
  await expect(page.getByTestId('oracle-status')).toHaveAttribute('data-status', 'ok')
  await expect(dot).toHaveAttribute('aria-label', /gemma4:e2b-it-qat/)
  // 2
  await page.goto('/tables/HR/EMPLOYEES?tab=query')
  await page.getByRole('tab', { name: '自然言語で SQL を作成', exact: true }).click() // ※CR-010: 見出しの確認から変更
  const gen = page.getByRole('button', { name: 'LLM で SQL を作成' })
  await expect(gen).toBeDisabled()
  const exchangeButton = page.getByRole('button', { name: 'LLM とのやりとり' })
  await expect(exchangeButton).toBeDisabled() // ※CR-008: まだ作成していない
  // 3
  await page.getByRole('textbox', { name: 'LLM への要求' }).fill('給与の高い社員を上位5人、姓と部署名と給与を表示')
  await expect(gen).toBeEnabled({ timeout: 30_000 })
  await gen.click()
  await expect(page.getByTestId('llm-result')).toContainText('LLM(gemma4:e2b-it-qat)が作成しました', { timeout: 660_000 })
  await expect(page.getByRole('textbox', { name: 'SELECT 文' })).toHaveValue(/^\s*(SELECT|WITH)\b/i)
  await expect(page.getByTestId('llm-guard-error')).toHaveCount(0)
  await expect(page.getByRole('table', { name: 'Query の結果' })).toHaveCount(0) // 自動で実行しない
  // 3b(※CR-008): LLM とのやりとり
  await exchangeButton.click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByTestId('llm-exchange-system')).toContainText('Oracle SQL')
  await expect(dialog.getByTestId('llm-exchange-user')).toContainText('Table HR.EMPLOYEES')
  await expect(dialog.getByTestId('llm-exchange-user')).toContainText('給与の高い社員を上位5人')
  await expect(dialog.getByTestId('llm-exchange-reply')).toContainText('```')
  await dialog.getByRole('button', { name: '閉じる' }).click()
  await expect(dialog).toHaveCount(0)
  // 3c(※CR-011): 保存の初期値は要求の先頭 20 文字と全文(保存はしない)
  await page.getByRole('tab', { name: '保存済み Query', exact: true }).click()
  await page.getByRole('button', { name: '名前を付けて保存' }).click()
  await expect(dialog.getByRole('textbox', { name: /名前/ })).toHaveValue('給与の高い社員を上位5人、姓と部署名と給')
  await expect(dialog.getByRole('textbox', { name: '説明' })).toHaveValue('給与の高い社員を上位5人、姓と部署名と給与を表示')
  await dialog.getByRole('button', { name: 'キャンセル' }).click()
  await expect(dialog).toHaveCount(0)
  // 4
  await page.getByRole('button', { name: '実行 (Ctrl+Enter)' }).click()
  await expect(page.getByTestId('query-row-count')).toHaveText(/^[1-5] 行$/, { timeout: 60_000 })
})

test('unreachable: LLM に届かないときは赤い丸・ボタンを押せない', async ({ page }) => {
  // 5
  await page.goto('/')
  await expect(page.getByTestId('llm-status')).toHaveAttribute('data-status', 'error', { timeout: 30_000 })
  await expect(page.getByTestId('oracle-status')).toHaveAttribute('data-status', 'ok')
  await page.goto('/tables/HR/EMPLOYEES?tab=query')
  await page.getByRole('tab', { name: '自然言語で SQL を作成', exact: true }).click() // ※CR-010
  await page.getByRole('textbox', { name: 'LLM への要求' }).fill('社員の数')
  await expect(page.getByTestId('llm-unavailable')).toContainText('LLM が使えないため作成できません')
  await expect(page.getByRole('button', { name: 'LLM で SQL を作成' })).toBeDisabled()
})
