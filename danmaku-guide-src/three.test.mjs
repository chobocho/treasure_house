import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { webglBrowserOptions } from './browser-options.mjs';
import { inspectDeck } from './validate.mjs';
const { chromium } = await import('playwright');
const webglOptions = webglBrowserOptions;

test('Three 설치는 strict와 WebGL2 실제 렌더를 검사한다', { timeout: 45000 }, async () => {
  const file = new URL('examples/three-ts/setup.ts', import.meta.url);
  assert.ok(existsSync(file), 'Three 장면 예제가 있어야 한다');
  const result = spawnSync('bash', ['examples/three-ts/commands.sh', 'build'], { cwd: new URL('.', import.meta.url), encoding: 'utf8' });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(new URL('dist/three-setup.html', import.meta.url).href);
    await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.frames) >= 120);
    assert.ok(Number(await page.locator('canvas').getAttribute('data-calls')) > 0);
    assert.ok(await page.evaluate(() => {
      const canvas = document.querySelector('canvas'), gl = canvas.getContext('webgl2');
      if (!gl) return false;
      const pixels = new Uint8Array(480 * 640 * 4);
      gl.readPixels(0, 0, 480, 640, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      return pixels.some((v, i) => i % 4 !== 3 && v > 150);
    }));
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
  const folder = new URL('examples/three-ts/', import.meta.url);
  const paths = readdirSync(folder, { recursive: true }).filter((name) => /\.(ts|mjs|json|sh|glsl)$/.test(name)).sort().map((name) => 'three-ts/' + name);
  writeFileSync(new URL('TESTED.txt', folder), paths.join('\n') + '\n');
});

test('Three 설치 장은 20장과 부 표지·MIT 원문을 제공한다', () => {
  const path = new URL('parts/40-three-setup.html', import.meta.url);
  assert.ok(existsSync(path), 'Three 설치 장이 있어야 한다');
  assert.equal(inspectDeck('<main class="prose">' + readFileSync(path, 'utf8') + '</main>').slides.length, 21);
  assert.equal(readFileSync(new URL('examples/three-ts/LICENSE-THREE.txt', import.meta.url), 'utf8'),
    readFileSync(new URL('node_modules/three/LICENSE', import.meta.url), 'utf8'));
  assert.ok(readFileSync(new URL('dist/three-setup.html', import.meta.url), 'utf8').includes('Permission is hereby granted'));
});

const levels = [1, 2, 3, 4, 5, 6, 7];
for (const level of levels) {
  test('Three Lv' + level + '는 pygame 기준과 순수 로직을 유지한다', async () => {
    const folder = new URL('examples/three-ts/lv' + level + '/', import.meta.url);
    assert.ok(existsSync(new URL('game.ts', folder)), '독립 게임 로직이 있어야 한다');
    assert.ok(!/from ['"]three['"]|document\.|window\./.test(readFileSync(new URL('game.ts', folder), 'utf8')));
    const { Game, Pool } = await import(new URL('dist/three-lv' + level + '-logic.mjs', import.meta.url));
    const golden = JSON.parse(readFileSync(new URL('spec/golden/lv' + level + '.json', import.meta.url)));
    const stageFile = new URL('stage.json', folder);
    const stage = existsSync(stageFile) ? JSON.parse(readFileSync(stageFile)) : undefined;
    const game = new Game(golden.seed, stage);
    const actual = [];
    let bits = 0, cursor = 0;
    for (let frame = 0; frame < 1800; frame++) {
      if (cursor < golden.inputs.length && golden.inputs[cursor].frame === frame) bits = golden.inputs[cursor++].bits;
      game.step(bits);
      if ([60, 600, 1800].includes(game.frame)) actual.push(game.snapshot());
    }
    assert.deepEqual(actual, golden.checkpoints);
    const move = new Game();
    move.step(2 | 4);
    assert.ok(Math.abs(Math.hypot(move.playerX - 240, move.playerY - 560) - 4) < 1e-10);
    for (const value of [-1, 512, 1.5, null]) assert.throws(() => move.step(value));
    const pool = new Pool(1);
    pool.add(1, 2, 3, 4);
    assert.equal(pool.add(0, 0, 0, 0), -1);
    assert.equal(pool.erase(0), true);
  });

  test('Three Lv' + level + '는 실제 WebGL 120화면·이동·발사를 처리한다', { timeout: 45000 }, async () => {
    assert.ok(existsSync(new URL('examples/three-ts/lv' + level + '/render.ts', import.meta.url)), 'Three 렌더러가 있어야 한다');
    const browser = await chromium.launch(webglOptions);
    try {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', (error) => errors.push(error.message));
      page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
      await page.goto(new URL('dist/three-lv' + level + '.html', import.meta.url).href);
      await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.frames) >= 120);
      const canvas = page.locator('canvas').first();
      await canvas.focus();
      if (level === 7) await page.keyboard.press('Enter');
      await page.keyboard.down('ArrowRight'); await page.keyboard.down('z');
      await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.x) > 250);
      await page.keyboard.up('ArrowRight'); await page.keyboard.up('z');
      assert.ok(Number(await canvas.getAttribute('data-bullets')) > 0);
      assert.ok(Number(await canvas.getAttribute('data-calls')) > 0);
      assert.ok(await canvas.evaluate((canvas) => {
        const gl = canvas.getContext('webgl2'), pixels = new Uint8Array(480 * 640 * 4);
        gl.readPixels(0, 0, 480, 640, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
        return !gl.isContextLost() && pixels.some((v, i) => i % 4 !== 3 && v > 150);
      }));
      assert.deepEqual(errors, []);
    } finally { await browser.close(); }
  });

  // Lv3·Lv4에는 수학 그림 슬라이드(Lv3 3장, Lv4 2장)가 더해졌다.
  const slideCount = { 3: 43, 4: 42 }[level] ?? 40;
  test('Three Lv' + level + '는 출처가 있는 ' + slideCount + '장을 제공한다', () => {
    const file = new URL('parts/4' + level + '-three-lv' + level + '.html', import.meta.url);
    assert.ok(existsSync(file), '레벨별 설명 장이 있어야 한다');
    const html = readFileSync(file, 'utf8');
    assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, slideCount);
    assert.ok(html.includes('captures/three-lv' + level + '.txt'));
  });
}

test('Three Lv2는 천 발을 한 인스턴스 호출로 그린다', { timeout: 45000 }, async () => {
  const folder = new URL('examples/three-ts/lv2/', import.meta.url);
  assert.ok(existsSync(new URL('render.ts', folder)), '인스턴스 렌더러가 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, bundle: true, format: 'iife', globalName: 'InstanceFixture', write: false });
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const result = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      document.body.append(canvas);
      const game = new InstanceFixture.Game();
      for (let i = 0; i < 1000; i++) game.bullets.add(20 + i % 40 * 11, 100 + Math.floor(i / 40) * 10, 0, 0);
      const view = new InstanceFixture.Renderer(canvas);
      view.draw(game, 1);
      const count = view.bulletInstances.count;
      const calls = view.renderer.info.render.calls;
      game.bullets.count = 0;
      view.draw(game, 1);
      const empty = view.bulletInstances.count;
      view.dispose();
      return { count, calls, empty };
    });
    assert.equal(result.count, 1000);
    assert.ok(result.calls <= 4);
    assert.equal(result.empty, 0);
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});

test('Three Lv3는 활성 행렬·색 범위와 영 발 갱신을 처리한다', { timeout: 45000 }, async () => {
  const folder = new URL('examples/three-ts/lv3/', import.meta.url);
  assert.ok(existsSync(new URL('render.ts', folder)), '활성 범위 렌더러가 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, bundle: true, format: 'iife', globalName: 'RangeFixture', write: false });
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const result = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      const game = new RangeFixture.Game(), view = new RangeFixture.Renderer(canvas);
      game.ring(240, 200, 7, 2);
      view.drawBullets(game, 1);
      const matrix = view.bulletInstances.instanceMatrix, color = view.bulletInstances.instanceColor;
      const first = matrix.updateRanges[0];
      const populated = [first.count, color.updateRanges[0].count];
      game.bullets.count = 1;
      view.drawBullets(game, 1);
      const reused = matrix.updateRanges[0] === first;
      const single = [matrix.updateRanges[0].count, color.updateRanges[0].count];
      const version = matrix.version;
      game.bullets.count = 0;
      view.drawBullets(game, 1);
      const empty = [matrix.updateRanges.length, color.updateRanges.length, matrix.version === version];
      game.ring(240, 200, 20, 2);
      view.draw(game, 1);
      const restored = view.bulletInstances.count;
      view.dispose();
      return { populated, single, reused, empty, restored };
    });
    assert.deepEqual(result.populated, [112, 21]);
    assert.deepEqual(result.single, [16, 3]);
    assert.equal(result.reused, true);
    assert.deepEqual(result.empty, [0, 0, true]);
    assert.equal(result.restored, 20);
  } finally { await browser.close(); }
});

test('Three Lv4는 보스 Sprite와 체력 막대 WebGL 픽셀을 표시한다', { timeout: 45000 }, async () => {
  const folder = new URL('examples/three-ts/lv4/', import.meta.url);
  assert.ok(existsSync(new URL('render.ts', folder)), '보스 렌더러가 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, bundle: true, format: 'iife', globalName: 'BossThreeFixture', write: false });
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const result = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      const game = new BossThreeFixture.Game(), view = new BossThreeFixture.Renderer(canvas);
      const index = game.spawnBoss();
      game.enemies.hp[index] = 90;
      view.draw(game, 1);
      const gl = canvas.getContext('webgl2');
      const pixel = (x) => {
        const values = new Uint8Array(4);
        gl.readPixels(x, 640 - 62 - 1, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, values);
        return Array.from(values).slice(0, 3);
      };
      const half = [pixel(20), pixel(460)], size = view.enemySprites[index].scale.x;
      game.enemies.hp[index] = 1;
      game.bullets.add(240, 100, 0, 0);
      game.step(0); view.draw(game, 1);
      const cleared = pixel(20), phase = game.phase;
      view.dispose();
      return { half, size, cleared, phase };
    });
    assert.deepEqual(result.half, [[255, 100, 120], [30, 40, 60]]);
    assert.equal(result.size, 64);
    assert.deepEqual(result.cleared, [8, 21, 35]);
    assert.equal(result.phase, 4);
  } finally { await browser.close(); }
});

test('Three Lv5는 아이템·집중 링 픽셀과 HUD 자원 변경을 표시한다', { timeout: 45000 }, async () => {
  const folder = new URL('examples/three-ts/lv5/', import.meta.url);
  assert.ok(existsSync(new URL('render.ts', folder)), '보상 렌더러가 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, bundle: true, format: 'iife', globalName: 'RewardThreeFixture', write: false });
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const result = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      const game = new RewardThreeFixture.Game(), view = new RewardThreeFixture.Renderer(canvas);
      game.items.add(100, 200, 0, 0, 6);
      game.previousInput = 32;
      view.draw(game, 1);
      const gl = canvas.getContext('webgl2');
      const pixel = (x, y) => {
        const values = new Uint8Array(4);
        gl.readPixels(x, 640 - y - 1, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, values);
        return Array.from(values).slice(0, 3);
      };
      const item = pixel(100, 200), focus = pixel(255, 560), count = view.itemInstances.count;
      const previous = view.hudKey;
      game.bombs--;
      view.drawHud(game);
      const changed = view.hudKey !== previous;
      game.items.count = 0; view.draw(game, 1);
      const empty = view.itemInstances.count;
      view.dispose();
      return { item, focus, count, changed, empty };
    });
    assert.deepEqual(result.item, [255, 210, 80]);
    assert.deepEqual(result.focus, [80, 150, 180]);
    assert.equal(result.count, 1);
    assert.equal(result.changed, true);
    assert.equal(result.empty, 0);
  } finally { await browser.close(); }
});

test('Three Lv6는 불변 스테이지와 같은 시점의 순서를 유지한다', async () => {
  const folder = new URL('examples/three-ts/lv6/', import.meta.url);
  assert.ok(existsSync(new URL('game.ts', folder)), '스테이지 로직이 있어야 한다');
  const { Game, validateStage } = await import(new URL('dist/three-lv6-logic.mjs', import.meta.url));
  const data = [{ frame: 0, kind: 'enemy', pattern: 3 }, { frame: 0, kind: 'enemy', pattern: 1 }, { frame: 1, kind: 'boss' }];
  const game = new Game(undefined, data);
  data[0].frame = 99;
  data.length = 0;
  game.step(0);
  assert.deepEqual(Array.from(game.enemies.mark.slice(0, 2)), [3, 1]);
  game.step(0);
  assert.equal(game.phase, 1);
  assert.equal(game.stageCursor, 3);
  assert.equal(Object.isFrozen(game.stage), true);
  assert.equal(Object.isFrozen(game.stage[0]), true);
  for (const value of [null, {}, [{ frame: true, kind: 'boss' }], [{ frame: 0, kind: 'enemy', pattern: 4 }]]) {
    assert.throws(() => validateStage(value));
  }
  const empty = new Game();
  for (let i = 0; i < 700; i++) empty.step(0);
  assert.equal(empty.enemies.count, 0);
});

test('Three Lv7는 입자·화면 상태를 순수 로직으로 유지한다', async () => {
  assert.ok(existsSync(new URL('examples/three-ts/lv7/game.ts', import.meta.url)), '완성 로직이 있어야 한다');
  const { Game } = await import(new URL('dist/three-lv7-logic.mjs', import.meta.url));
  const game = new Game(undefined, [], false);
  game.step(18); assert.equal(game.time, 0);
  game.step(128); assert.equal(game.status, 1);
  game.step(256); assert.equal(game.paused, true);
  const state = game.rng.state;
  game.emit(3, 100, 100); game.updateEffects();
  assert.equal(game.particles.count, 6);
  assert.equal(game.rng.state, state);
  game.eventCount = 0;
  for (let i = 0; i < 31; i++) game.updateEffects();
  assert.equal(game.particles.count, 0);
});

test('Three Lv7는 실제 셰이더·입자·패널 픽셀을 그린다', { timeout: 45000 }, async () => {
  const folder = new URL('examples/three-ts/lv7/', import.meta.url);
  assert.ok(existsSync(new URL('bullet.frag.glsl', folder)), '실제 컴파일할 셰이더 파일이 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, loader: { '.glsl': 'text' }, bundle: true, format: 'iife', globalName: 'PolishThreeFixture', write: false });
  const browser = await chromium.launch(webglOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const result = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      const game = new PolishThreeFixture.Game(), view = new PolishThreeFixture.Renderer(canvas);
      game.bullets.add(100, 200, 0, 0, 10, 1);
      game.particles.add(150, 300, 0, 0, 2, 3, 30);
      view.draw(game, 1);
      const gl = canvas.getContext('webgl2');
      const pixel = (x, y) => {
        const values = new Uint8Array(4);
        gl.readPixels(x, 640 - y - 1, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, values);
        return Array.from(values).slice(0, 3);
      };
      const center = pixel(100, 200), corner = pixel(109, 209), particle = pixel(150, 300);
      const shader = view.bulletMaterial.isShaderMaterial, particles = view.particleInstances.count;
      game.status = 0; view.draw(game, 1);
      const panel = pixel(80, 280);
      view.dispose();
      return { center, corner, particle, shader, particles, panel };
    });
    assert.ok(result.center[0] > 150 && result.center[1] < 150);
    assert.deepEqual(result.corner, [8, 21, 35]);
    assert.deepEqual(result.particle, [255, 190, 90]);
    assert.equal(result.shader, true);
    assert.equal(result.particles, 1);
    assert.deepEqual(result.panel, [20, 40, 60]);
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
});

test('Three 번들은 내부 셰이더 문자열의 끝 공백을 HTML 줄로 노출하지 않는다', () => {
  const file = new URL('dist/three-demo.js', import.meta.url);
  assert.ok(existsSync(file), '실행할 최종 번들이 있어야 한다');
  assert.equal(/[ \t]+$/m.test(readFileSync(file, 'utf8')), false);
});

test('Three 성능 도구는 동일 장면의 Mesh와 인스턴스 호출을 측정한다', { timeout: 45000 }, async () => {
  const file = new URL('examples/three-ts/profile.mjs', import.meta.url);
  assert.ok(existsSync(file), '실제 WebGL 측정 도구가 있어야 한다');
  const { profile } = await import('./examples/three-ts/profile.mjs');
  const report = await profile(7, 2);
  assert.equal(report.count, 7);
  assert.deepEqual(report.results.map((row) => row.calls), [7, 1]);
  for (const row of report.results) {
    assert.equal(row.samplesMs.length, 2);
    assert.ok(row.medianMs >= 0);
    assert.equal(row.medianMs, (row.samplesMs[0] + row.samplesMs[1]) / 2);
  }
  assert.ok(report.renderer.length > 0);
  assert.ok(report.browser.length > 0);
  for (const count of [-1, 4097, true, 1.5, null]) await assert.rejects(() => profile(count, 1));
  for (const rounds of [0, 21, true, 1.5, null]) await assert.rejects(() => profile(1, rounds));
  const empty = await profile(0, 1);
  assert.deepEqual(empty.results.map((row) => row.calls), [0, 0]);
  for (const row of empty.results) assert.equal(row.medianMs, row.samplesMs[0]);
});

test('Three 마무리는 실제 측정 출처가 있는 35장이다', () => {
  const file = new URL('parts/48-three-wrap.html', import.meta.url);
  assert.ok(existsSync(file), 'Three 마무리 장이 있어야 한다');
  const html = readFileSync(file, 'utf8');
  assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, 35);
  assert.ok(html.includes('captures/three-profile.txt'));
});
