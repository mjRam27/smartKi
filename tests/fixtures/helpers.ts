import { Page, expect } from '@playwright/test';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'https://culinary-dash-15.preview.emergentagent.com';

export async function waitForAppReady(page: Page) {
  await page.waitForLoadState('domcontentloaded');
}

export async function dismissToasts(page: Page) {
  await page.addLocatorHandler(
    page.locator('[data-sonner-toast], .Toastify__toast, [role="status"].toast, .MuiSnackbar-root'),
    async () => {
      const close = page.locator('[data-sonner-toast] [data-close], [data-sonner-toast] button[aria-label="Close"], .Toastify__close-button, .MuiSnackbar-root button');
      await close.first().click({ timeout: 2000 }).catch(() => {});
    },
    { times: 10, noWaitAfter: true }
  );
}

export async function loginUser(page: Page, email = 'admin@kitchen.com', password = 'Admin123!') {
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.getByTestId('login-email').fill(email);
  await page.getByTestId('login-password').fill(password);
  await page.getByTestId('login-submit').click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
}

export async function checkForErrors(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const errorElements = Array.from(
      document.querySelectorAll('.error, [class*="error"], [id*="error"]')
    );
    return errorElements.map(el => el.textContent || '').filter(Boolean);
  });
}

/**
 * Click a submit button inside a Radix UI Dialog.
 * Standard locator.click() doesn't trigger form submit in Playwright+Radix dialogs.
 * Using page.mouse.click() with bounding box coordinates works correctly.
 */
export async function clickDialogSubmit(page: Page, testId: string) {
  const btn = page.getByTestId(testId);
  await expect(btn).toBeVisible();
  const box = await btn.boundingBox();
  if (!box) throw new Error(`Button ${testId} has no bounding box`);
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
}

export async function getAuthToken(): Promise<string> {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'admin@kitchen.com', password: 'Admin123!' }),
  });
  const data = await response.json();
  return data.access_token;
}
