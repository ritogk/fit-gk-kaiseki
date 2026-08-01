import { chromium } from 'playwright';

const OUT = '../docs/screenshots';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

// Normal mode
await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await page.screenshot({ path: `${OUT}/normal-mode.png`, fullPage: false });
console.log('normal-mode.png saved');

// Normal mode dark
await page.click('button:has-text("🌙")');
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}/normal-mode-dark.png`, fullPage: false });
console.log('normal-mode-dark.png saved');

// Live mode
await page.click('button:has-text("LIVE")');
await page.waitForTimeout(1000);
await page.screenshot({ path: `${OUT}/live-mode.png`, fullPage: false });
console.log('live-mode.png saved');

await browser.close();
