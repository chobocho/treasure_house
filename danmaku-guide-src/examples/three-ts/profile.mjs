import { pathToFileURL } from 'node:url';
import { webglBrowserOptions } from '../../browser-options.mjs';
const { chromium } = await import('playwright');

// #region profile
export async function profile(count = 1000, rounds = 5) {
  if (!Number.isInteger(count) || count < 0 || count > 4096) throw new RangeError('탄환 수는 0~4096 정수');
  if (!Number.isInteger(rounds) || rounds < 1 || rounds > 20) throw new RangeError('표본 수는 1~20 정수');
  const browser = await chromium.launch(webglBrowserOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(new URL('../../dist/three-performance.html', import.meta.url).href);
    const report = await page.evaluate(({ count, rounds }) => window.benchmark(count, rounds), { count, rounds });
    if (errors.length) throw new Error(errors.join('\n'));
    return { node: process.version, machine: process.arch, browser: browser.version(), ...report };
  } finally { await browser.close(); }
}
// #endregion

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify(await profile(), null, 2));
}
