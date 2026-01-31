import { test, expect } from '@playwright/test';

/**
 * GaiaLink Landing Page E2E Tests
 * Tests the initial landing experience before app launch
 */
test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the hero section with GaiaLink title', async ({ page }) => {
    // Verify the main title is visible (landing page uses "GaiaLink")
    const title = page.getByRole('heading', { name: 'GaiaLink', exact: true });
    await expect(title).toBeVisible();

    // Verify tagline is present
    const tagline = page.getByText('Intent-Centric Spatial OS', { exact: false });
    await expect(tagline).toBeVisible();
  });

  test('should display Launch OS button', async ({ page }) => {
    // Find the Launch OS button
    const launchButton = page.getByRole('button', { name: /Launch OS/i }).first();
    await expect(launchButton).toBeVisible();
    await expect(launchButton).toBeEnabled();
  });

  test('should display scroll indicator', async ({ page }) => {
    // Verify scroll instruction text
    const scrollText = page.getByText('Scroll to initialize', { exact: false });
    await expect(scrollText).toBeVisible({ timeout: 5000 });
  });

  test('should transition to app when Launch OS is clicked', async ({ page }) => {
    // Click the Launch OS button (force click due to animation)
    const launchButton = page.getByRole('button', { name: /Launch OS/i }).first();
    await launchButton.click({ force: true });

    // Wait for transition and verify app UI appears
    // The GAIALINK brand in the top bar should appear
    const appBrand = page.getByRole('heading', { name: 'GAIALINK', exact: true });
    await expect(appBrand).toBeVisible({ timeout: 10000 });
  });
});
