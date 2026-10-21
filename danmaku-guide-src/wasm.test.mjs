import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { browserOptions } from './browser-options.mjs';
const { chromium } = await import('playwright');

const src = new URL('.', import.meta.url);
import { attachPositions } from './examples/cpp-wasm/memory-glue.mjs';
import { attachGame } from './examples/cpp-wasm/lv1/replay.mjs';
import { inspectBytes } from './examples/cpp-wasm/inspect.mjs';
const verifiedPaths = new Set();
function recordTested(paths) {
  for (const path of paths) verifiedPaths.add('cpp-wasm/' + path);
  writeFileSync(new URL('examples/cpp-wasm/TESTED.txt', src), [...verifiedPaths].sort().join('\n') + '\n');
}

test('wasm 설치는 같은 C++를 네이티브와 wasm으로 빌드해 실행한다', () => {
  assert.ok(existsSync(new URL('examples/cpp-wasm/setup.cpp', src)), '설치 C++ 예제가 있어야 한다');
  const build = spawnSync('bash', ['examples/cpp-wasm/commands.sh', 'build'], { cwd: src, encoding: 'utf8' });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const report = JSON.parse(build.stdout);
  assert.match(report.clang, /clang version/);
  assert.match(report.linker, /LLD/);
  assert.equal(report.native, 'passed');
  assert.equal(report.abiVersion, 1);
  assert.ok(report.bytes > 8);
  const bytes = readFileSync(new URL('dist/wasm-setup.wasm', src));
  assert.equal(report.bytes, bytes.length);
  const module = new WebAssembly.Module(bytes);
  assert.deepEqual(WebAssembly.Module.imports(module), []);
  assert.deepEqual(WebAssembly.Module.exports(module).map(({ name }) => name).sort(),
    ['dm_abi_version', 'dm_advance', 'memory']);
  const { exports } = new WebAssembly.Instance(module);
  assert.equal(exports.dm_abi_version(), 1);
  for (const [position, speed, expected] of [[240, 0, 240], [240, 4, 244], [0, -4, -4], [-10, 2.5, -7.5], [0.25, 0.5, 0.75]]) {
    assert.equal(exports.dm_advance(position, speed), expected);
  }
  assert.equal(exports.memory.buffer.byteLength, 131072);
  assert.throws(() => exports.memory.grow(1), RangeError);
  assert.throws(() => new WebAssembly.Module(bytes.subarray(0, 7)), WebAssembly.CompileError);
  recordTested(['setup.cpp', 'test_setup.cpp', 'build.mjs', 'commands.sh']);
});

test('wasm 위치 ABI는 포화·초기화·공유 뷰·경계 오류를 검사한다', async () => {
  const build = spawnSync(process.execPath, ['examples/cpp-wasm/memory-build.mjs'], { cwd: src, encoding: 'utf8' });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const bytes = readFileSync(new URL('dist/wasm-memory.wasm', src));
  const { instance } = await WebAssembly.instantiate(bytes, {});
  const api = instance.exports;
  assert.deepEqual(WebAssembly.Module.imports(new WebAssembly.Module(bytes)), []);
  api.dm_init();
  const snapshot = attachPositions(api);
  assert.deepEqual(snapshot(), []);
  for (let i = 0; i < 4; ++i) assert.equal(api.dm_push(i, -2.5), 1);
  assert.equal(api.dm_push(99, 99), 0);
  const before = snapshot();
  api.dm_shift(-0.5, 4);
  assert.deepEqual(snapshot(), [[-0.5, 1.5], [0.5, 1.5], [1.5, 1.5], [2.5, 1.5]]);
  assert.deepEqual(before[0], [0, -2.5]);
  api.dm_init();
  assert.deepEqual(snapshot(), []);
  assert.throws(() => api.memory.grow(1), RangeError);
  assert.throws(() => attachPositions({ ...api, dm_stride: () => 8 }), /ABI/);
  assert.throws(() => attachPositions({ ...api, dm_positions: () => 1 }), /범위/);
  assert.throws(() => attachPositions({ ...api, dm_positions: () => 131072 }), /범위/);
  assert.throws(() => attachPositions({ ...api, dm_count: () => 5 })(), /개수/);
  const growable = new WebAssembly.Memory({ initial: 2, maximum: 3 });
  const stale = attachPositions({ ...api, memory: growable });
  growable.grow(1);
  assert.throws(stale, /다시 연결/);
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({ offline: true });
    const glue = readFileSync(new URL('examples/cpp-wasm/memory-glue.mjs', src), 'utf8');
    const result = await page.evaluate(async ({ base64, glue }) => {
      const { attachPositions } = await import('data:text/javascript;base64,' + btoa(glue));
      const { instance } = await WebAssembly.instantiate(Uint8Array.from(atob(base64), (c) => c.charCodeAt(0)), {});
      instance.exports.dm_init();
      const snapshot = attachPositions(instance.exports);
      instance.exports.dm_push(240, 560);
      instance.exports.dm_shift(-4, 0.5);
      return snapshot();
    }, { base64: bytes.toString('base64'), glue: Buffer.from(glue).toString('binary') });
    assert.deepEqual(result, [[236, 560.5]]);
  } finally { await browser.close(); }
  recordTested(['memory.cpp', 'test_memory.cpp', 'memory-build.mjs', 'memory-glue.mjs']);
});

test('wasm 명령은 알 수 없는 동작을 거부한다', () => {
  assert.ok(existsSync(new URL('examples/cpp-wasm/commands.sh', src)), 'wasm 명령 스크립트가 있어야 한다');
  const result = spawnSync('bash', ['examples/cpp-wasm/commands.sh', 'unknown'], { cwd: src, encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /build/);
});

test('wasm 설치 페이지는 오프라인 파일에서 실행하고 손상 바이트 오류를 표시한다', async () => {
  const browser = await chromium.launch(browserOptions);
  try {
    const context = await browser.newContext({ offline: true });
    const page = await context.newPage();
    const errors = [];
    const requests = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
    await page.goto(new URL('dist/wasm-setup.html', src).href);
    await page.waitForSelector('#result[data-state="ready"]');
    assert.equal(await page.locator('#result').textContent(), 'ABI 1 · 240 + 4 = 244');
    assert.deepEqual(await page.evaluate(async () => {
      const api = await loadSetup(document.querySelector('#wasm-bytes').textContent.trim());
      return [api.dm_advance(-10, 2.5), api.memory.buffer.byteLength];
    }), [-7.5, 131072]);
    await page.evaluate(async () => {
      document.querySelector('#wasm-bytes').textContent = 'AAAA';
      await showSetup();
    });
    assert.equal(await page.locator('#result').getAttribute('data-state'), 'error');
    assert.match(await page.locator('#result').textContent(), /wasm 로딩 실패/);
    assert.deepEqual(errors, []);
    assert.deepEqual(requests, []);
  } finally {
    await browser.close();
  }
  recordTested(['setup.js']);
});

test('C++ Lv1은 네이티브와 wasm에서 기존 pygame 기준 기록과 일치한다', async () => {
  const build = spawnSync(process.execPath, ['examples/cpp-wasm/lv1/build.mjs'], { cwd: src, encoding: 'utf8' });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const bytes = readFileSync(new URL('dist/wasm-lv1.wasm', src));
  const module = new WebAssembly.Module(bytes);
  assert.deepEqual(WebAssembly.Module.imports(module), []);
  const api = new WebAssembly.Instance(module).exports;
  const golden = JSON.parse(readFileSync(new URL('spec/golden/lv1.json', src)));
  const game = attachGame(api, golden.seed);
  assert.throws(() => game.step(1.5), /입력/);
  assert.throws(() => game.step(-1), /입력/);
  assert.throws(() => game.step(512), /입력/);
  assert.equal(api.dm_step(512), 0);
  assert.equal(api.dm_frame(), 0);
  let cursor = 0, bits = 0;
  const checkpoints = [], inputs = [];
  for (let frame = 0; frame < 1800; ++frame) {
    if (cursor < golden.inputs.length && golden.inputs[cursor].frame === frame) bits = golden.inputs[cursor++].bits;
    inputs.push(bits);
    game.step(bits);
    if ([60, 600, 1800].includes(api.dm_frame())) checkpoints.push(game.snapshot());
  }
  assert.deepEqual(checkpoints, golden.checkpoints);
  const native = spawnSync(fileURLToPath(new URL('dist/wasm-lv1-native', src)), ['replay'],
    { encoding: 'utf8', input: inputs.join('\n') });
  assert.equal(native.status, 0, native.stderr);
  assert.deepEqual(native.stdout.trim().split('\n').map((line) => line.split(' ').map(Number)),
    golden.checkpoints.map((s) => [s.frame, s.bullets, s.checksum]));
  attachGame(api, golden.seed);
  assert.equal(api.dm_count(), 0);
  assert.equal(api.dm_player_x(), 240);
  assert.equal(api.dm_player_y(), 560);
  assert.equal(api.memory.buffer.byteLength, 1048576);
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({ offline: true });
    const errors = [], requests = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
    await page.goto(new URL('dist/wasm-lv1.html', src).href);
    await page.waitForSelector('#status[data-state="ready"]');
    const canvas = page.locator('canvas');
    await page.waitForFunction(() => Number(document.querySelector('canvas').dataset.frames) >= 120);
    await canvas.focus();
    await page.keyboard.down('ArrowRight');
    await page.keyboard.down('z');
    await page.waitForFunction(() => {
      const c = document.querySelector('canvas');
      return Number(c.dataset.x) > 250 && Number(c.dataset.bullets) > 0;
    });
    await page.keyboard.up('ArrowRight'); await page.keyboard.up('z');
    assert.ok(await canvas.evaluate((c) => {
      const data = c.getContext('2d').getImageData(0, 0, 480, 640).data;
      let player = false, shot = false;
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] === 94 && data[i + 1] === 234) player = true;
        if (data[i] === 251 && data[i + 1] === 191) shot = true;
      }
      return player && shot;
    }));
    await page.keyboard.down('ArrowRight');
    await canvas.evaluate((c) => c.blur());
    await page.waitForFunction(() => Number(document.querySelector('canvas').dataset.frames) >= 130);
    const stopped = await canvas.getAttribute('data-step');
    const frames = Number(await canvas.getAttribute('data-frames'));
    await page.waitForFunction((n) => Number(document.querySelector('canvas').dataset.frames) >= n + 5, frames);
    assert.equal(await canvas.getAttribute('data-step'), stopped);
    await page.keyboard.up('ArrowRight');
    await canvas.focus();
    const position = await canvas.getAttribute('data-x');
    await page.waitForFunction((n) => Number(document.querySelector('canvas').dataset.step) > n + 3, Number(stopped));
    assert.equal(await canvas.getAttribute('data-x'), position);
    assert.deepEqual(errors, []); assert.deepEqual(requests, []);
  } finally { await browser.close(); }
  recordTested(['lv1/game.hpp', 'lv1/game.cpp', 'lv1/test_game.cpp', 'lv1/build.mjs', 'lv1/replay.mjs', 'lv1/main.js']);
});

for (const level of [2, 3, 4, 5, 6, 7]) test(`C++ Lv${level}은 네이티브·Node·Chromium에서 기존 pygame 기준과 일치한다`, async () => {
  const { attachGame: attachLevel } = await import(`./examples/cpp-wasm/lv${level}/replay.mjs`);
  const build = spawnSync(process.execPath, [`examples/cpp-wasm/lv${level}/build.mjs`], { cwd: src, encoding: 'utf8' });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const bytes = readFileSync(new URL(`dist/wasm-lv${level}.wasm`, src));
  const module = new WebAssembly.Module(bytes);
  assert.deepEqual(WebAssembly.Module.imports(module), []);
  const api = new WebAssembly.Instance(module).exports;
  const golden = JSON.parse(readFileSync(new URL(`spec/golden/lv${level}.json`, src)));
  const stage = level >= 6 ? JSON.parse(readFileSync(new URL(`examples/cpp-wasm/lv${level}/stage.json`, src))) : [];
  const game = attachLevel(api, golden.seed, stage);
  if (level >= 6) {
    const { validateStage } = await import(`./examples/cpp-wasm/lv${level}/replay.mjs`);
    const original = [{ frame: 0, kind: 'enemy', pattern: 2 }];
    const copy = validateStage(original);
    original[0].pattern = 3;
    assert.deepEqual(copy, [[0, 'enemy', 2]]);
    assert.ok(Object.isFrozen(copy) && Object.isFrozen(copy[0]));
    for (const invalid of [null, {}, [true], [{ frame: true, kind: 'boss' }],
      [{ frame: -1, kind: 'boss' }], [{ frame: 0.5, kind: 'boss' }],
      [{ frame: 0, kind: 'enemy', pattern: 4 }], [{ frame: 0, kind: 'boss', extra: 1 }],
      [{ frame: 2, kind: 'boss' }, { frame: 1, kind: 'boss' }], Array(4097).fill({ frame: 0, kind: 'boss' })]) {
      assert.throws(() => validateStage(invalid));
    }
    assert.deepEqual(validateStage([]), []);
    assert.equal(readFileSync(new URL(`examples/cpp-wasm/lv${level}/stage.json`, src), 'utf8'),
      readFileSync(new URL(`examples/canvas-ts/lv${level}/stage.json`, src), 'utf8'));
  }
  const actual = [], inputs = [];
  let bits = 0, cursor = 0;
  for (let frame = 0; frame < 1800; ++frame) {
    if (cursor < golden.inputs.length && golden.inputs[cursor].frame === frame) bits = golden.inputs[cursor++].bits;
    inputs.push(bits); game.step(bits);
    if ([60, 600, 1800].includes(api.dm_frame())) actual.push(game.snapshot());
  }
  assert.deepEqual(actual, golden.checkpoints);
  const native = spawnSync(fileURLToPath(new URL(`dist/wasm-lv${level}-native`, src)), ['replay'],
    { encoding: 'utf8', input: (level >= 6 ? stage.length + '\n' + stage.map((e) =>
      `${e.frame} ${e.kind === 'enemy' ? 0 : 1} ${e.pattern ?? 0}`).join('\n') + '\n' : '') + inputs.join('\n') });
  assert.equal(native.status, 0, native.stderr);
  assert.deepEqual(native.stdout.trim().split('\n').map((line) => line.split(' ').map(Number)),
    golden.checkpoints.map((s) => [s.frame, s.bullets, s.enemies, s.score, s.lives, s.phase, s.checksum]));
  attachLevel(api, golden.seed, stage);
  assert.equal(api.dm_enemies(), 0);
  assert.equal(api.dm_lives(), 3);
  assert.equal(api.dm_invulnerable(), 0);
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage({ offline: true });
    const errors = [], requests = [];
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
    const adapter = readFileSync(new URL(`examples/cpp-wasm/lv${level}/replay.mjs`, src)).toString('base64');
    const browserRecords = await page.evaluate(async ({ base64, adapter, inputs, seed, stage }) => {
      const { attachGame } = await import('data:text/javascript;base64,' + adapter);
      const { instance } = await WebAssembly.instantiate(Uint8Array.from(atob(base64), (c) => c.charCodeAt(0)), {});
      const game = attachGame(instance.exports, seed, stage), records = [];
      for (let i = 0; i < inputs.length; ++i) {
        game.step(inputs[i]);
        if ([60, 600, 1800].includes(i + 1)) records.push(game.snapshot());
      }
      return records;
    }, { base64: bytes.toString('base64'), adapter, inputs, seed: golden.seed, stage });
    assert.deepEqual(browserRecords, golden.checkpoints);
    await page.goto(new URL(`dist/wasm-lv${level}.html`, src).href);
    await page.waitForSelector('#status[data-state="ready"]');
    const canvas = page.locator('canvas');
    await canvas.focus();
    if (level === 7) {
      assert.equal(await canvas.getAttribute('data-game-status'), '0');
      assert.ok(await canvas.evaluate((c) => c.getContext('2d').getImageData(80, 250, 1, 1).data[0] === 15));
      await page.keyboard.press('Enter');
      await page.waitForFunction(() => document.querySelector('canvas').dataset.gameStatus === '1');
    }
    await page.keyboard.down('ArrowRight'); await page.keyboard.down('z');
    await page.waitForFunction(() => Number(document.querySelector('canvas').dataset.x) > 260);
    await page.keyboard.up('ArrowRight');
    await page.waitForFunction(() => {
      const c = document.querySelector('canvas');
      return Number(c.dataset.step) >= 100 && Number(c.dataset.enemyBullets) > 0;
    });
    await page.keyboard.up('z');
    if (level === 7) {
      assert.ok(Number(await canvas.getAttribute('data-particles')) > 0);
      await page.keyboard.press('p');
      await page.waitForFunction(() => document.querySelector('canvas').dataset.paused === 'true');
      const time = Number(await canvas.getAttribute('data-time'));
      const frame = Number(await canvas.getAttribute('data-frames'));
      await page.waitForFunction((n) => Number(document.querySelector('canvas').dataset.frames) > n + 5, frame);
      assert.equal(Number(await canvas.getAttribute('data-time')), time);
      await page.keyboard.press('p');
      await page.waitForFunction(() => document.querySelector('canvas').dataset.paused === 'false');
      assert.equal(await canvas.getAttribute('data-audio'), 'true');
    }
    assert.ok(await canvas.evaluate((c) => {
      const data = c.getContext('2d').getImageData(0, 0, 480, 640).data;
      let enemy = false, hostile = false;
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] === 251 && data[i + 1] === 113) enemy = true;
        if (data[i] === 167 && data[i + 1] === 139) hostile = true;
      }
      return enemy && hostile;
    }));
    assert.match(await page.locator('#hud').textContent(), /점수 \d+ · 목숨 \d+/);
    if (level >= 5) {
      await page.keyboard.down('x');
      await page.waitForFunction(() => document.querySelector('canvas').dataset.bombs === '2');
      const step = Number(await canvas.getAttribute('data-step'));
      await page.waitForFunction((step) => Number(document.querySelector('canvas').dataset.step) > step + 5, step);
      assert.equal(await canvas.getAttribute('data-bombs'), '2');
      await page.keyboard.up('x');
      assert.match(await page.locator('#rewards').textContent(), /파워 1 · 폭탄 2 · 그레이즈 \d+/);
    }
    if (level >= 4) {
      await page.waitForFunction(() => Number(document.querySelector('canvas').dataset.bossHp) > 0);
      assert.ok(await canvas.evaluate((c) => {
        const ctx = c.getContext('2d');
        const body = ctx.getImageData(Math.round(Number(c.dataset.bossX)), 100, 1, 1).data;
        const bar = ctx.getImageData(25, 24, 1, 1).data;
        return body[0] === 251 && body[1] === 146 && bar[0] === 251 && bar[1] === 146;
      }));
      assert.match(await page.locator('#phase').textContent(), /보스 단계 [123]/);
    }
    if (level === 7) {
      await page.goto('about:blank');
      await page.setContent('<article><div data-demo="wasm-game"></div></article>');
      await page.evaluate(() => {
        window.__demo = (_id, mount) => mount(document.querySelector('[data-demo="wasm-game"]'));
        window.__initDemos = () => {};
      });
      await page.addScriptTag({ content: readFileSync(new URL('dist/wasm-demo.js', src), 'utf8') });
      await page.waitForSelector('#status[data-state="ready"]');
      await page.locator('canvas').focus(); await page.keyboard.press('Enter');
      await page.waitForFunction(() => document.querySelector('canvas').dataset.gameStatus === '1');
    }
    assert.deepEqual(errors, []); assert.deepEqual(requests, []);
  } finally { await browser.close(); }
  recordTested([`lv${level}/game.hpp`, `lv${level}/game.cpp`, `lv${level}/test_game.cpp`, `lv${level}/build.mjs`, `lv${level}/replay.mjs`, `lv${level}/main.js`]);
  if (level >= 6) recordTested([`lv${level}/stage.json`]);
  if (level === 7) recordTested(['lv7/audio.ts', 'lv7/storage.ts', 'demo.mjs']);
});

test('wasm Lv7 소리 합성과 최고 점수는 손상·거부를 처리한다', async () => {
  const { loadBest, saveBest } = await import('./dist/wasm-lv7-modules/storage.mjs');
  const { tone, Audio } = await import('./dist/wasm-lv7-modules/audio.mjs');
  const storage = { value: null, getItem() { return this.value; }, setItem(_key, value) { this.value = value; } };
  assert.equal(loadBest(storage), 0);
  assert.ok(saveBest(storage, 123)); assert.equal(loadBest(storage), 123);
  for (const value of [NaN, -1, 1.5, Infinity, Number.MAX_SAFE_INTEGER + 1]) assert.equal(saveBest(storage, value), false);
  for (const value of ['broken', '{"best":-1}', '{"best":"123"}', 'null']) {
    storage.value = value; assert.equal(loadBest(storage), 0);
  }
  assert.equal(loadBest({ getItem() { throw new Error('denied'); } }), 0);
  assert.equal(saveBest({ setItem() { throw new Error('denied'); } }, 1), false);
  const samples = tone(440, .08);
  assert.equal(samples.length, 1764);
  assert.ok(samples.some((v) => Math.abs(v) > .01));
  assert.ok(samples.every((v) => Number.isFinite(v) && Math.abs(v) <= .14));
  const audio = new Audio(() => { throw new Error('no audio'); });
  await audio.unlock(); assert.equal(audio.enabled, false);
  audio.consume({ eventCount: 0, eventKind: new Int32Array(64), status: 1, paused: false });
  audio.setActive(false); audio.close();
});

test('wasm 진단은 내보내기·메모리·컴파일 오류·실행 트랩을 구분한다', async () => {
  const bytes = readFileSync(new URL('dist/wasm-lv7.wasm', src));
  const report = await inspectBytes(bytes);
  assert.equal(report.memoryBytes, 1048576);
  assert.equal(report.abiVersion, 1);
  assert.deepEqual(report.imports, []);
  assert.ok(report.exports.some((e) => e.name === 'dm_step' && e.kind === 'function'));
  await assert.rejects(inspectBytes(bytes.subarray(0, 7)), WebAssembly.CompileError);
  const cli = spawnSync(process.execPath, ['examples/cpp-wasm/inspect.mjs', 'dist/wasm-lv7.wasm'], { cwd: src, encoding: 'utf8' });
  assert.equal(cli.status, 0, cli.stderr);
  assert.deepEqual(JSON.parse(cli.stdout), report);
  for (const args of [[], ['dist/missing-wasm-file.wasm']]) {
    const failed = spawnSync(process.execPath, ['examples/cpp-wasm/inspect.mjs', ...args], { cwd: src, encoding: 'utf8' });
    assert.equal(failed.status, 1); assert.ok(failed.stderr.trim());
  }
  const build = spawnSync(process.execPath, ['examples/cpp-wasm/diagnostics-build.mjs'], { cwd: src, encoding: 'utf8' });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const { instance } = await WebAssembly.instantiate(readFileSync(new URL('dist/wasm-traps.wasm', src)), {});
  assert.throws(() => instance.exports.dm_trap(), WebAssembly.RuntimeError);
  assert.throws(() => instance.exports.dm_read(0xfffffff0), WebAssembly.RuntimeError);
  recordTested(['inspect.mjs', 'traps.cpp', 'diagnostics-build.mjs']);
});
