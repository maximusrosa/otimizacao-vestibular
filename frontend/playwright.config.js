const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
});
