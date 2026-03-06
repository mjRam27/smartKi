import { test, expect } from '@playwright/test';
import { loginUser, dismissToasts, clickDialogSubmit } from '../fixtures/helpers';

/**
 * Golden Path: End-to-end user journey
 * Login → Dashboard → Check metrics → Navigate to Recipes → 
 * AI Generate Recipe → View Ingredients → Create Ingredient → 
 * Navigate to Kitchens → Logout
 */
test.describe('Golden Path - End-to-End Journey', () => {
  test('Full user journey: Login to feature exploration', async ({ page }) => {
    await dismissToasts(page);
    
    // Step 1: Login
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('login-page')).toBeVisible();
    await page.getByTestId('login-email').fill('admin@kitchen.com');
    await page.getByTestId('login-password').fill('Admin123!');
    await page.getByTestId('login-submit').click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    
    // Step 2: Dashboard loaded with metrics
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    await expect(page.locator('[data-testid^="stat-"]').first()).toBeVisible({ timeout: 10000 });
    
    // Step 3: Navigate to Recipes
    await page.getByTestId('nav-recipes').click();
    await expect(page).toHaveURL(/\/recipes/);
    await expect(page.getByTestId('recipes-page')).toBeVisible();
    
    // Step 4: Go to AI Recipe Generator
    await page.getByTestId('ai-generate-btn').click();
    await expect(page).toHaveURL(/\/recipes\/generate/);
    await expect(page.getByTestId('ai-recipe-generate-page')).toBeVisible();
    await expect(page.getByTestId('recipe-name-input')).toBeVisible();
    
    // Step 5: Navigate to Ingredients
    await page.getByTestId('nav-ingredients').click();
    await expect(page).toHaveURL(/\/ingredients/);
    await expect(page.getByTestId('ingredients-page')).toBeVisible();
    
    // Step 6: Navigate to Kitchens
    await page.getByTestId('nav-kitchens').click();
    await expect(page).toHaveURL(/\/kitchens/);
    await expect(page.getByTestId('kitchens-page')).toBeVisible();
    
    // Step 7: Navigate to Waste Log
    await page.getByTestId('nav-waste-log').click();
    await expect(page).toHaveURL(/\/waste/);
    await expect(page.getByTestId('waste-page')).toBeVisible();
    
    // Step 8: Go back to Dashboard via nav
    await page.getByTestId('nav-dashboard').click();
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByTestId('dashboard-page')).toBeVisible();
    
    // Step 9: Logout
    await page.evaluate(() => {
      const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
      if (badge) (badge as HTMLElement).remove();
    });
    await page.getByTestId('user-menu-btn').click();
    await page.getByTestId('logout-btn').click();
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    await expect(page.getByTestId('login-page')).toBeVisible();
  });

  test('Ingredient CRUD flow', async ({ page }) => {
    await dismissToasts(page);
    await loginUser(page);
    await page.evaluate(() => {
      const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
      if (badge) (badge as HTMLElement).remove();
    });
    
    const uid = Date.now().toString();
    const ingName = `GOLDEN_ING_${uid}`;
    
    // Navigate to ingredients
    await page.goto('/ingredients', { waitUntil: 'domcontentloaded' });
    
    // Create ingredient
    await page.getByTestId('new-ingredient-btn').click();
    await expect(page.getByTestId('ingredient-name-input')).toBeVisible();
    await page.getByTestId('ingredient-name-input').fill(ingName);
    
    const postRespPromise = page.waitForResponse(
      r => r.url().includes('/ingredients/') && r.request().method() === 'POST',
      { timeout: 10000 }
    );
    await clickDialogSubmit(page, 'save-ingredient-btn');
    const postResp = await postRespPromise;
    expect(postResp.status()).toBe(201);
    
    // Verify in list
    await expect(page.getByText(ingName)).toBeVisible({ timeout: 10000 });
    
    // Search for it
    await page.getByTestId('ingredient-search').fill(ingName.substring(0, 10));
    await expect(page.getByText(ingName)).toBeVisible({ timeout: 5000 });
    
    // Clear search
    await page.getByTestId('ingredient-search').clear();
  });
});
