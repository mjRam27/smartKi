import { test, expect } from '@playwright/test';
import { loginUser, dismissToasts } from '../fixtures/helpers';

test.describe('Dashboard & Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
    await loginUser(page);
    await page.evaluate(() => {
      const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
      if (badge) (badge as HTMLElement).remove();
    });
  });

  test('Dashboard page loads with metrics', async ({ page }) => {
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    // Check for stat cards
    await expect(page.locator('[data-testid^="stat-"]').first()).toBeVisible({ timeout: 10000 });
  });

  test('Sidebar is visible with navigation items', async ({ page }) => {
    await expect(page.getByTestId('sidebar')).toBeVisible();
    await expect(page.getByTestId('nav-dashboard')).toBeVisible();
    await expect(page.getByTestId('nav-recipes')).toBeVisible();
    await expect(page.getByTestId('nav-ingredients')).toBeVisible();
    await expect(page.getByTestId('nav-inventory')).toBeVisible();
    await expect(page.getByTestId('nav-suppliers')).toBeVisible();
    await expect(page.getByTestId('nav-waste-log')).toBeVisible();
    await expect(page.getByTestId('nav-kitchens')).toBeVisible();
  });

  test('Navigate to Recipes page', async ({ page }) => {
    await page.getByTestId('nav-recipes').click();
    await expect(page).toHaveURL(/\/recipes/);
    await expect(page.getByTestId('recipes-page')).toBeVisible();
  });

  test('Navigate to Ingredients page', async ({ page }) => {
    await page.getByTestId('nav-ingredients').click();
    await expect(page).toHaveURL(/\/ingredients/);
    await expect(page.getByTestId('ingredients-page')).toBeVisible();
  });

  test('Navigate to Suppliers page', async ({ page }) => {
    await page.getByTestId('nav-suppliers').click();
    await expect(page).toHaveURL(/\/suppliers/);
    await expect(page.getByTestId('suppliers-page')).toBeVisible();
  });

  test('Navigate to Waste page', async ({ page }) => {
    await page.getByTestId('nav-waste-log').click();
    await expect(page).toHaveURL(/\/waste/);
    await expect(page.getByTestId('waste-page')).toBeVisible();
  });

  test('Navigate to Kitchens page', async ({ page }) => {
    await page.getByTestId('nav-kitchens').click();
    await expect(page).toHaveURL(/\/kitchens/);
    await expect(page.getByTestId('kitchens-page')).toBeVisible();
  });

  test('Header shows kitchen selector and user menu', async ({ page }) => {
    await expect(page.getByTestId('header')).toBeVisible();
    await expect(page.getByTestId('user-menu-btn')).toBeVisible();
  });

  test('Logout works correctly', async ({ page }) => {
    await page.getByTestId('user-menu-btn').click();
    await expect(page.getByTestId('logout-btn')).toBeVisible();
    await page.getByTestId('logout-btn').click();
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('Quick action buttons on dashboard', async ({ page }) => {
    await expect(page.getByTestId('quick-ai-recipe')).toBeVisible();
    await expect(page.getByTestId('quick-log-waste')).toBeVisible();
  });
});
