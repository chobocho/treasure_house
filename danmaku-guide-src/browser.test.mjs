import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readFileSync, writeFileSync } from 'node:fs';
import { browserOptions, webglBrowserOptions } from './browser-options.mjs';

const src = fileURLToPath(new URL('.', import.meta.url));

test('브라우저에서 오프라인 덱·키보드·목차·퀴즈가 동작한다', { timeout: 60000 }, async () => {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href);
    await page.waitForFunction(() => document.querySelector('article.card .pno'));
    assert.match(await page.title(), /탄막 슈팅/);
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(() => location.hash === '#ch0-start');
    await page.locator('#tocBtn').click();
    assert.ok(await page.locator('#deckToc').evaluate((element) => element.classList.contains('on')));
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#deckToc').evaluate((element) => element.classList.contains('on')), false);
    await page.selectOption('#nav', 'part0');
    await page.waitForFunction(() => location.hash === '#part0');
    await page.selectOption('#nav', 'ch0-start');
    await page.evaluate(() => { location.hash = 'p0-start-replay'; });
    await page.locator('#p0-start-replay button').click();
    assert.ok(await page.locator('#p0-start-replay .a').isVisible());
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});

test('내장 wasm Lv7은 시작·조작·정지·오디오·이탈 정지가 동작한다', { timeout: 60000 }, async () => {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({ offline: true });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href + '#p5-lv7-demo');
    const canvas = page.locator('[data-demo="wasm-game"] canvas');
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="wasm-game"] canvas')?.dataset.frames) >= 120);
    assert.equal(await canvas.getAttribute('data-game-status'), '0');
    await canvas.focus(); await page.keyboard.press('Enter');
    await page.keyboard.down('ArrowRight'); await page.keyboard.down('z');
    await page.waitForFunction(() => {
      const c = document.querySelector('[data-demo="wasm-game"] canvas');
      return Number(c.dataset.x) > 250 && Number(c.dataset.bullets) > 0;
    });
    await page.keyboard.up('ArrowRight'); await page.keyboard.up('z');
    assert.equal(new URL(page.url()).hash, '#p5-lv7-demo');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="wasm-game"] canvas').dataset.paused === 'true');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="wasm-game"] canvas').dataset.paused === 'false');
    assert.equal(await canvas.getAttribute('data-audio'), 'true');
    await page.screenshot({ path: resolve(src, 'captures/wasm-lv7.png') });
    await page.evaluate(() => { location.hash = 'p5-lv7-quiz'; });
    await page.waitForFunction(() => document.querySelector('[data-demo="wasm-game"] canvas').dataset.audioState === 'suspended');
    assert.deepEqual(errors, []);
    const manifest = resolve(src, 'examples/cpp-wasm/TESTED.txt');
    const paths = new Set(readFileSync(manifest, 'utf8').trim().split('\n'));
    paths.add('cpp-wasm/demo.mjs');
    writeFileSync(manifest, [...paths].sort().join('\n') + '\n');
  } finally { await browser.close(); }
});

test('패턴 뷰어는 해시로 직접 열려도 네 패턴을 120프레임 이상 그린다', { timeout: 60000 }, async () => {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href + '#p1-vectors-viewer');
    assert.equal(await page.locator('[data-demo="pattern-viewer"]').count(), 1);
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="pattern-viewer"] canvas').dataset.frames) >= 120);
    for (const mode of ['ring', 'fan', 'spiral', 'wave']) {
      await page.selectOption('[data-pattern]', mode);
      await page.waitForFunction(() => Number(document.querySelector('[data-demo="pattern-viewer"] canvas').dataset.bullets) > 0);
      assert.ok(await page.locator('[data-demo="pattern-viewer"] canvas').evaluate((canvas) => {
        const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
        for (let i = 0; i < pixels.length; i += 4) if (pixels[i] > 150 && pixels[i + 1] < 150) return true;
        return false;
      }));
    }
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});

test('내장 Canvas Lv7은 직접 해시 진입·시작·이동·발사·정지가 동작한다', { timeout: 60000 }, async () => {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href + '#p3-lv7-37');
    assert.equal(await page.locator('[data-demo="canvas-game"]').count(), 1);
    const canvas = page.locator('[data-demo="canvas-game"] canvas');
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.frames) >= 120);
    await canvas.focus();
    await page.keyboard.press('Enter');
    await page.keyboard.down('ArrowRight');
    await page.keyboard.down('z');
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.x) > 250);
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.bullets) > 0);
    await page.keyboard.up('ArrowRight');
    await page.keyboard.up('z');
    assert.ok(Number(await canvas.getAttribute('data-bullets')) > 0);
    assert.equal(new URL(page.url()).hash, '#p3-lv7-37');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.paused === 'true');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.paused === 'false');
    assert.equal(await canvas.getAttribute('data-audio'), 'true');
    await page.evaluate(() => { location.hash = 'p3-lv7-quiz'; });
    await page.waitForFunction(() => document.querySelector('[data-demo="canvas-game"] canvas')?.dataset.audioState === 'suspended');
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});

test('내장 Three Lv7은 WebGL·조작·오디오·이탈 정지가 동작한다', { timeout: 60000 }, async () => {
  const { chromium } = await import('playwright');
  const browser = await chromium.launch(webglBrowserOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(pathToFileURL(resolve(src, '../탄막-슈팅-가이드.html')).href + '#p4-lv7-37');
    assert.equal(await page.locator('[data-demo="three-game"]').count(), 1);
    const canvas = page.locator('[data-demo="three-game"] canvas');
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="three-game"] canvas')?.dataset.frames) >= 120);
    await canvas.focus(); await page.keyboard.press('Enter');
    await page.keyboard.down('ArrowRight'); await page.keyboard.down('z');
    await page.waitForFunction(() => Number(document.querySelector('[data-demo="three-game"] canvas')?.dataset.x) > 250);
    await page.keyboard.up('ArrowRight'); await page.keyboard.up('z');
    assert.ok(Number(await canvas.getAttribute('data-calls')) > 0);
    assert.equal(new URL(page.url()).hash, '#p4-lv7-37');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="three-game"] canvas')?.dataset.paused === 'true');
    await page.keyboard.press('p');
    await page.waitForFunction(() => document.querySelector('[data-demo="three-game"] canvas')?.dataset.paused === 'false');
    assert.equal(await canvas.getAttribute('data-audio'), 'true');
    await page.evaluate(() => { location.hash = 'p4-lv7-quiz'; });
    await page.waitForFunction(() => document.querySelector('[data-demo="three-game"] canvas')?.dataset.audioState === 'suspended');
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});
