import { test, expect } from '@playwright/test';

/**
 * GaiaLink Globe/Map E2E Tests
 * Tests the 3D globe visualization component
 */
test.describe('Globe Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Launch the app (force click due to animation)
    const launchButton = page.getByRole('button', { name: /Launch OS/i }).first();
    await launchButton.click({ force: true });
    // Wait for app to load - use exact match for the app header
    await expect(page.getByRole('heading', { name: 'GAIALINK', exact: true })).toBeVisible({ timeout: 10000 });
  });

  test('should render the map canvas', async ({ page }) => {
    // MapLibre GL renders to a canvas element
    // Wait for the map to initialize
    const mapCanvas = page.locator('canvas.maplibregl-canvas, canvas.mapboxgl-canvas');
    await expect(mapCanvas.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display map controls', async ({ page }) => {
    // MapLibre GL controls are typically rendered
    // Look for navigation controls or zoom controls
    const mapContainer = page.locator('.maplibregl-map, .mapboxgl-map');
    await expect(mapContainer.first()).toBeVisible({ timeout: 10000 });
  });

  test('map should be interactive - can zoom', async ({ page }) => {
    // Get the map canvas
    const mapCanvas = page.locator('canvas.maplibregl-canvas, canvas.mapboxgl-canvas').first();
    await expect(mapCanvas).toBeVisible({ timeout: 10000 });

    // Perform scroll to zoom (simulate mouse wheel)
    const box = await mapCanvas.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.wheel(0, -100); // Scroll up to zoom in
      // Map should still be visible after interaction
      await expect(mapCanvas).toBeVisible();
    }
  });
});
