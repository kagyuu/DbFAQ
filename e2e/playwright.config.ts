import { defineConfig, devices } from '@playwright/test'

// 受入テストは compose の web(同一オリジン)に対して実行する(ADR-004)
export default defineConfig({
  testDir: './tests',
  workers: 1,
  fullyParallel: false, // テスト間でスナップショットを共有するため順に実行する
  retries: 0,
  timeout: 60_000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.DBFAQ_BASE_URL ?? 'http://localhost:8088',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1400, height: 900 } } }],
})
