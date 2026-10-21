import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { writeFileSync } from 'node:fs';
import { webglBrowserOptions } from './browser-options.mjs';
const { chromium } = await import('playwright');
const src = fileURLToPath(new URL('.', import.meta.url));
const url = pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href;
const browser = await chromium.launch(webglBrowserOptions);
const paths = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, offline: true });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  async function shot(id, name) {
    await page.goto(url + '#' + id);
    await page.waitForFunction((id) => document.getElementById(id)?.classList.contains('on'), id);
    await page.evaluate(() => document.fonts.ready);
    const target = 'captures/' + name + '.png';
    await page.screenshot({ path: resolve(src, target) });
    paths.push(target);
  }
  await shot('part0', 'deck-cover');
  await shot('p5-lv1-04', 'deck-code');
  await shot('p1-design-13', 'deck-diagram');
  await page.locator('#tocBtn').click();
  await page.waitForSelector('#deckToc.on');
  await page.screenshot({ path: resolve(src, 'captures/deck-toc.png') });
  paths.push('captures/deck-toc.png');
  await page.keyboard.press('Escape');
  for (const [id, demo, name] of [
    ['p1-vectors-viewer', 'pattern-viewer', 'deck-pattern'],
    ['p3-lv7-37', 'canvas-game', 'deck-canvas'],
    ['p4-lv7-37', 'three-game', 'deck-three'],
    ['p5-lv7-demo', 'wasm-game', 'deck-wasm']
  ]) {
    await page.goto(url + '#' + id);
    await page.waitForFunction((demo) => Number(document.querySelector(`[data-demo="${demo}"] canvas`)?.dataset.frames) >= 120, demo);
    if (demo !== 'pattern-viewer') {
      await page.locator(`[data-demo="${demo}"] canvas`).focus();
      await page.keyboard.press('Enter');
      await page.keyboard.down('z');
      await page.waitForFunction((demo) => Number(document.querySelector(`[data-demo="${demo}"] canvas`)?.dataset.bullets) > 0, demo);
      await page.keyboard.up('z');
    }
    const target = 'captures/' + name + '.png';
    await page.screenshot({ path: resolve(src, target) });
    paths.push(target);
  }
  if (errors.length) throw new Error(errors.join('\n'));
  writeFileSync(resolve(src, 'captures/DECK-CAPTURES.txt'), paths.join('\n') + '\n');
  console.log(`오프라인 덱 캡처 ${paths.length}개 완료`);
} finally { await browser.close(); }
