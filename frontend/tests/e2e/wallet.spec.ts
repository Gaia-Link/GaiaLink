import { test, expect } from '@playwright/test';

/**
 * GaiaLink Wallet Connection E2E Tests
 * Tests the wallet connection UI (without actual wallet interaction)
 */
test.describe('Wallet Connection UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Launch the app (force click due to animation)
    const launchButton = page.getByRole('button', { name: /Launch OS/i }).first();
    await launchButton.click({ force: true });
    // Wait for app to load - use exact match for the app header
    await expect(page.getByRole('heading', { name: 'GAIALINK', exact: true })).toBeVisible({ timeout: 10000 });
  });

  test('should display Connect Wallet button', async ({ page }) => {
    // RainbowKit ConnectButton renders a button for wallet connection
    const connectButton = page.getByRole('button', { name: /Connect Wallet/i });
    await expect(connectButton.first()).toBeVisible({ timeout: 5000 });
  });

  test('should open wallet connection modal when clicked', async ({ page }) => {
    // Find and click the connect wallet button
    const connectButton = page.getByRole('button', { name: /Connect Wallet/i });
    await connectButton.first().click();

    // RainbowKit should show wallet options modal
    // Look for modal content with wallet options
    const modal = page.locator('[role="dialog"], [aria-modal="true"]');
    await expect(modal.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show wallet provider options in modal', async ({ page }) => {
    // Open the wallet modal
    const connectButton = page.getByRole('button', { name: /Connect Wallet/i });
    await connectButton.first().click();

    // Wait for modal to appear
    await page.waitForTimeout(500);

    // RainbowKit typically shows popular wallets
    // Check for common wallet names in the modal
    const modalContent = page.locator('[role="dialog"], [aria-modal="true"]');
    await expect(modalContent.first()).toBeVisible({ timeout: 5000 });

    // Should have some wallet option buttons
    const walletButtons = modalContent.locator('button');
    const count = await walletButtons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should close wallet modal when clicking outside or close button', async ({ page }) => {
    // Open the wallet modal
    const connectButton = page.getByRole('button', { name: /Connect Wallet/i });
    await connectButton.first().click();

    // Wait for modal
    const modal = page.locator('[role="dialog"], [aria-modal="true"]');
    await expect(modal.first()).toBeVisible({ timeout: 5000 });

    // Try to close by pressing Escape
    await page.keyboard.press('Escape');

    // Modal should be hidden (or not present)
    await expect(modal.first()).not.toBeVisible({ timeout: 3000 });
  });
});
