import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  reporter: 'line',
  use: {
    baseURL: 'http://localhost:8100',
  },
  webServer: {
    command: 'cd ../../backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_s2 uv run uvicorn app.main:app --host 0.0.0.0 --port 8100',
    url: 'http://localhost:8100/api/health',
    reuseExistingServer: false,
    timeout: 30000,
    env: {
      DATABASE_URL: 'postgresql://postgres:postgres@localhost:5432/test_s2',
    },
  },
});
