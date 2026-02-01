import { test, expect, type Page } from '@playwright/test';

/**
 * GaiaLink Main App E2E Tests
 * Tests the main application after launching from landing page
 */
test.describe('Main Application', () => {
  // Launch the app before each test
  test.beforeEach(async ({ page }: { page: Page }) => {
    await page.goto('/');
    // Click Launch OS to enter the app (force click due to animation)
    const launchButton = page.getByRole('button', { name: /Launch OS/i }).first();
    await launchButton.click({ force: true });
    // Wait for app to load - use exact match for the app header
    await expect(page.getByRole('heading', { name: 'GAIALINK', exact: true })).toBeVisible({ timeout: 10000 });
  });

  test('should display the GAIALINK brand header', async ({ page }: { page: Page }) => {
    const brand = page.getByRole('heading', { name: 'GAIALINK', exact: true });
    await expect(brand).toBeVisible();

    // Verify the tagline
    const tagline = page.getByText('Decentralized Humanitarian Aid Network', { exact: false });
    await expect(tagline).toBeVisible();
  });

  test('should display Connect Wallet button from RainbowKit', async ({ page }: { page: Page }) => {
    // RainbowKit ConnectButton should be visible
    // The button text varies based on connection state
    const connectButton = page.getByRole('button', { name: /Connect|Wallet/i });
    await expect(connectButton.first()).toBeVisible();
  });

  test('should display Portfolio button', async ({ page }: { page: Page }) => {
    // The history/portfolio button should be visible
    const portfolioButton = page.locator('button[title="My Donations"]');
    await expect(portfolioButton).toBeVisible();
  });

  test('should display SpoonOS instruction in footer', async ({ page }: { page: Page }) => {
    // Footer instruction about SpoonOS
    const instruction = page.getByText('Press', { exact: false });
    await expect(instruction.first()).toBeVisible();
  });

  test('should open Portfolio modal when portfolio button is clicked', async ({ page }: { page: Page }) => {
    // Click the portfolio button
    const portfolioButton = page.locator('button[title="My Donations"]');
    await portfolioButton.click();

    // The modal should appear - look for portfolio-related content
    // Based on UserPortfolioModal component, it should show "Portfolio" or donation history
    await expect(page.getByText(/Portfolio|My Donations|Your Contributions/i).first()).toBeVisible({ timeout: 3000 });
  });
});
