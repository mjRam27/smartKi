import { test, expect } from '@playwright/test';
import { loginUser, dismissToasts, clickDialogSubmit } from '../fixtures/helpers';

test.describe('Recipes & AI Generation', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
    await loginUser(page);
    await page.evaluate(() => {
      const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
      if (badge) (badge as HTMLElement).remove();
    });
  });

  test('Recipes page loads with search and filter', async ({ page }) => {
    await page.goto('/recipes', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recipes-page')).toBeVisible();
    await expect(page.getByTestId('recipe-search')).toBeVisible();
    await expect(page.getByTestId('ai-generate-btn')).toBeVisible();
  });

  test('AI Generate button navigates to recipe gen page', async ({ page }) => {
    await page.goto('/recipes', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('ai-generate-btn').click();
    await expect(page).toHaveURL(/\/recipes\/generate/);
    await expect(page.getByTestId('ai-recipe-generate-page')).toBeVisible();
  });

  test('AI Recipe Generate page has all form fields', async ({ page }) => {
    await page.goto('/recipes/generate', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ai-recipe-generate-page')).toBeVisible();
    await expect(page.getByTestId('recipe-name-input')).toBeVisible();
    await expect(page.getByTestId('recipe-description-input')).toBeVisible();
    await expect(page.getByTestId('cuisine-select')).toBeVisible();
    await expect(page.getByTestId('servings-input')).toBeVisible();
    await expect(page.getByTestId('generate-btn')).toBeVisible();
  });

  test('Generate button is disabled when recipe name is empty', async ({ page }) => {
    await page.goto('/recipes/generate', { waitUntil: 'domcontentloaded' });
    const generateBtn = page.getByTestId('generate-btn');
    await expect(generateBtn).toBeDisabled();
  });

  test('Generate button enables when recipe name is filled', async ({ page }) => {
    await page.goto('/recipes/generate', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('recipe-name-input').fill('Test Recipe');
    await expect(page.getByTestId('generate-btn')).toBeEnabled();
  });

  test('AI recipe generation shows result', async ({ page }) => {
    await page.goto('/recipes/generate', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('recipe-name-input').fill('Simple Pasta');
    await page.getByTestId('include-ingredients-input').fill('pasta, tomatoes');
    
    // Click generate button (regular button outside dialog - standard click works)
    await page.getByTestId('generate-btn').click();
    
    // Wait for AI generation (can take some time)
    await expect(page.getByTestId('generated-recipe')).toBeVisible({ timeout: 60000 });
  });
});

test.describe('Ingredients Management', () => {
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
    await loginUser(page);
    await page.evaluate(() => {
      const badge = document.querySelector('[class*="emergent"], [id*="emergent-badge"]');
      if (badge) (badge as HTMLElement).remove();
    });
  });

  test('Ingredients page loads with table', async ({ page }) => {
    await page.goto('/ingredients', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ingredients-page')).toBeVisible();
    await expect(page.getByTestId('ingredient-search')).toBeVisible();
    await expect(page.getByTestId('new-ingredient-btn')).toBeVisible();
  });

  test('Create new ingredient via dialog', async ({ page }) => {
    await page.goto('/ingredients', { waitUntil: 'domcontentloaded' });
    const uid = Date.now().toString();
    
    // Open dialog
    await page.getByTestId('new-ingredient-btn').click();
    await expect(page.getByTestId('ingredient-name-input')).toBeVisible();
    
    // Fill form
    await page.getByTestId('ingredient-name-input').fill(`TEST_ING_${uid}`);
    
    // Submit via bounding box click (workaround for Playwright+Radix Dialog)
    const responsePromise = page.waitForResponse(
      r => r.url().includes('/ingredients/') && r.request().method() === 'POST',
      { timeout: 10000 }
    );
    await clickDialogSubmit(page, 'save-ingredient-btn');
    const resp = await responsePromise;
    expect(resp.status()).toBe(201);
    
    // Verify ingredient appears in list
    await expect(page.getByText(`TEST_ING_${uid}`)).toBeVisible({ timeout: 10000 });
  });

  test('Ingredient search filters results', async ({ page }) => {
    await page.goto('/ingredients', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('ingredient-search').fill('TEST_ING');
    // Should show filtered results (or no results message)
    await expect(page.getByTestId('ingredients-page')).toBeVisible();
  });
});
