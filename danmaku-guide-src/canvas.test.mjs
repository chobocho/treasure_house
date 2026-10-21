import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, writeFileSync, rmSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { browserOptions } from './browser-options.mjs';
const { chromium } = await import('playwright');
import { inspectDeck } from './validate.mjs';

test('Canvas 설치는 엄격 타입 검사와 번들·오프라인 화면을 실행한다', { timeout: 45000 }, async () => {
  assert.ok(existsSync(new URL('tsc.mjs', import.meta.url)), '같은 버전의 실행기 어댑터가 있어야 한다');
  const command = spawnSync('bash', ['examples/canvas-ts/commands.sh', 'build'], { cwd: new URL('.', import.meta.url), encoding: 'utf8' });
  assert.equal(command.status, 0, command.stdout + command.stderr);
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(new URL('dist/canvas-setup.html', import.meta.url).href);
    await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.frames) >= 120);
    assert.equal(await page.locator('canvas').getAttribute('width'), '480');
    assert.ok(await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c.getContext('2d').getImageData(0, 0, 480, 640).data.some((v, i) => i % 4 !== 3 && v > 100);
    }));
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
  const paths = readdirSync(new URL('examples/canvas-ts/', import.meta.url), { recursive: true }).filter((name) => /\.(ts|mjs|json|sh)$/.test(name)).sort().map((name) => 'canvas-ts/' + name);
  writeFileSync(new URL('examples/canvas-ts/TESTED.txt', import.meta.url), paths.join('\n') + '\n');
});

test('TypeScript strict는 잘못된 대입을 실제로 거부한다', () => {
  const file = new URL('.cache/type-error.ts', import.meta.url);
  assert.ok(existsSync(new URL('tsc.mjs', import.meta.url)), '실제 tsc 어댑터가 있어야 한다');
  writeFileSync(file, 'const value: number = "wrong";\n');
  try {
    const result = spawnSync(process.execPath, ['tsc.mjs', '--strict', '--noEmit', '--ignoreConfig', '--types', '', file.pathname], { cwd: new URL('.', import.meta.url), encoding: 'utf8' });
    assert.notEqual(result.status, 0);
    assert.match(result.stdout + result.stderr, /TS2322/);
  } finally { rmSync(file, { force: true }); }
});

test('Canvas 설치 장은 20장과 부 표지를 제공한다', () => {
  const path = new URL('parts/30-canvas-setup.html', import.meta.url);
  assert.ok(existsSync(path), 'Canvas 설치 장이 있어야 한다');
  assert.equal(inspectDeck('<main class="prose">' + readFileSync(path, 'utf8') + '</main>').slides.length, 21);
});

const levels = [1, 2, 3, 4, 5, 6, 7];
for (const level of levels) {
  test('Canvas Lv' + level + '는 순수 로직과 pygame 기준을 재현한다', async () => {
    const path = new URL('examples/canvas-ts/lv' + level + '/game.ts', import.meta.url);
    assert.ok(existsSync(path), '독립 레벨 로직이 있어야 한다');
    const { Game, Pool } = await import(new URL('dist/canvas-lv' + level + '-logic.mjs', import.meta.url));
    const golden = JSON.parse(readFileSync(new URL('spec/golden/lv' + level + '.json', import.meta.url)));
    const stagePath = new URL('examples/canvas-ts/lv' + level + '/stage.json', import.meta.url);
    const stage = existsSync(stagePath) ? JSON.parse(readFileSync(stagePath)) : undefined;
    const g = new Game(golden.seed, stage);
    let bits = 0, cursor = 0;
    const actual = [];
    for (let frame = 0; frame < 1800; frame++) {
      if (cursor < golden.inputs.length && golden.inputs[cursor].frame === frame) bits = golden.inputs[cursor++].bits;
      g.step(bits);
      if ([60, 600, 1800].includes(g.frame)) actual.push(g.snapshot());
    }
    assert.deepEqual(actual, golden.checkpoints);
    const move = new Game();
    move.step(2 | 4);
    assert.ok(Math.abs(Math.hypot(move.playerX - 240, move.playerY - 560) - 4) < 1e-10);
    const x = move.playerX;
    move.step(3);
    assert.equal(move.playerX, x);
    move.step(2 | 32);
    assert.equal(move.playerX, x + 1.6);
    for (const input of [-1, 512, 1.5, null, '16']) assert.throws(() => move.step(input));
    const pool = new Pool(1);
    assert.equal(pool.add(1, 2, 3, 4), 0);
    assert.equal(pool.add(0, 0, 0, 0), -1);
    assert.equal(pool.erase(-1), false);
    assert.equal(pool.erase(0), true);
    assert.equal(new Pool(0).add(0, 0, 0, 0), -1);
    assert.throws(() => new Pool(-1));
  });

  test('Canvas Lv' + level + '는 120화면과 키 입력을 처리한다', { timeout: 30000 }, async () => {
    assert.ok(existsSync(new URL('examples/canvas-ts/lv' + level + '/main.ts', import.meta.url)), '브라우저 어댑터가 있어야 한다');
    const browser = await chromium.launch(browserOptions);
    try {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', (error) => errors.push(error.message));
      await page.goto(new URL('dist/canvas-lv' + level + '.html', import.meta.url).href);
      const canvas = page.locator('canvas');
      await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.frames) >= 120);
      await canvas.focus();
      if (level === 7) await page.keyboard.press('Enter');
      await page.keyboard.down('ArrowRight');
      await page.keyboard.down('z');
      await page.waitForFunction(() => Number(document.querySelector('canvas')?.dataset.x) > 250);
      await page.keyboard.up('ArrowRight');
      await page.keyboard.up('z');
      assert.ok(Number(await canvas.getAttribute('data-bullets')) > 0);
      assert.ok(await page.evaluate(() => {
        const c = document.querySelector('canvas');
        return c.getContext('2d').getImageData(0, 0, 480, 640).data.some((v, i) => i % 4 !== 3 && v > 100);
      }));
      assert.deepEqual(errors, []);
    } finally { await browser.close(); }
  });

  // Lv3·Lv4에는 수학 그림 슬라이드(Lv3 3장, Lv4 2장)가 더해졌다.
  const slideCount = { 3: 43, 4: 42 }[level] ?? 40;
  test('Canvas Lv' + level + '는 출처가 있는 ' + slideCount + '장을 제공한다', () => {
    const path = new URL('parts/3' + level + '-canvas-lv' + level + '.html', import.meta.url);
    assert.ok(existsSync(path), '레벨별 장이 있어야 한다');
    const html = readFileSync(path, 'utf8');
    assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, slideCount);
    assert.ok(html.includes('captures/canvas-lv' + level + '.txt'));
  });
}

test('Canvas Lv2는 난수·충돌·무적·중복 점수 경계를 지킨다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv2/game.ts', import.meta.url)), 'Lv2 충돌 로직이 있어야 한다');
  const { Game, Rng, overlaps } = await import(new URL('dist/canvas-lv2-logic.mjs', import.meta.url));
  const rng = new Rng(1);
  assert.deepEqual([rng.next(), rng.next(), rng.next()], [270369, 67634689, 2647435461]);
  assert.equal(new Rng(0).next(), 0);
  assert.equal(overlaps(0, 0, 2, 5, 0, 3), true);
  assert.equal(overlaps(0, 0, 2, 5.01, 0, 3), false);
  const g = new Game();
  g.enemies.add(100, 100, 0, 0, 12, 0, 1);
  g.bullets.add(100, 100, 0, 0);
  g.bullets.add(100, 100, 0, 0);
  g.playerBulletHits();
  assert.equal(g.score, 100);
  assert.equal(g.enemies.count, 0);
  assert.equal(g.bullets.count, 1);
  g.bullets.count = 0;
  g.bullets.add(240, 560, 0, 0, 4, 1);
  g.bullets.add(240, 560, 0, 0, 4, 1);
  g.enemyBulletHits();
  assert.equal(g.lives, 2);
  assert.equal(g.invulnerable, 120);
  assert.equal(g.bullets.count, 1);
  g.invulnerable = 1;
  g.step(0);
  assert.equal(g.lives, 1);
  g.lives = 0; g.invulnerable = 0;
  assert.equal(g.hurt(), false);
  assert.equal(g.lives, 0);
});

test('Canvas Lv3는 사분면·주기·네 패턴·영벡터·포화 경계를 지킨다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv3/game.ts', import.meta.url)), 'Lv3 패턴 로직이 있어야 한다');
  const { Game, dsin, dcos, Pool } = await import(new URL('dist/canvas-lv3-logic.mjs', import.meta.url));
  for (const turn of [-2.75, -1, -.25, 0, .25, .5, .75, 1, 2.25]) {
    assert.ok(Math.abs(dsin(turn) - Math.sin(turn * 2 * Math.PI)) < 1e-8);
    assert.ok(Math.abs(dcos(turn) - Math.cos(turn * 2 * Math.PI)) < 1e-8);
  }
  for (let mode = 0; mode < 4; mode++) {
    const g = new Game();
    g.firePattern(240, 560, mode, 7, 2.5, 60);
    assert.equal(g.bullets.count, 7);
    for (let i = 0; i < 7; i++) assert.ok(Math.abs(Math.hypot(g.bullets.vx[i], g.bullets.vy[i]) - 2.5) < 1e-8);
  }
  const g = new Game();
  g.aimedFan(240, 560, 3, 2);
  assert.ok(Math.abs(g.bullets.vx[1]) < 1e-10);
  // 자체 코사인은 0에서도 근삿값이므로 수학적 이상값 대신 기존 pygame 연산 결과와 엄격히 비교한다.
  const oracle = spawnSync('python3', ['-c',
    'from test_snapshots import load_game; g=load_game(3).Game(); g.aimed_fan(240,560,3,2); print(g.bullets.vy[1])'],
    { cwd: new URL('examples/pygame/', import.meta.url), encoding: 'utf8' });
  assert.equal(oracle.status, 0, oracle.stderr);
  assert.equal(g.bullets.vy[1], Number(oracle.stdout));
  assert.ok(Math.abs(g.bullets.vx[0] + g.bullets.vx[2]) < 1e-10);
  g.bullets = new Pool(1);
  g.firePattern(0, 0, 0, 0);
  assert.equal(g.bullets.count, 0);
  g.firePattern(0, 0, 0, 20);
  assert.equal(g.bullets.count, 1);
  assert.throws(() => g.firePattern(0, 0, 4));
});

test('Canvas Lv4는 보스 전환·포화 재시도·지연 삭제를 지킨다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv4/game.ts', import.meta.url)), 'Lv4 보스 로직이 있어야 한다');
  const { Game } = await import(new URL('dist/canvas-lv4-logic.mjs', import.meta.url));
  const g = new Game();
  g.spawnBoss();
  assert.equal(g.spawnBoss(), -1);
  g.phaseTime = 299;
  g.bullets.add(50, 50, 0, 0, 4, 1);
  g.step(0);
  assert.equal(g.phase, 2);
  assert.equal(g.phaseTime, 0);
  g.enemies.hp[g.findBoss()] = 60;
  g.step(0);
  assert.equal(g.phase, 3);
  const kill = new Game();
  const boss = kill.spawnBoss();
  kill.enemies.hp[boss] = 1;
  kill.bullets.add(240, 100, 0, 0);
  kill.bullets.add(300, 300, 0, 0, 4, 1);
  kill.bullets.add(0, 0, 0, 0);
  kill.step(0);
  assert.deepEqual([kill.phase, kill.score, kill.enemies.count, kill.bullets.count, kill.bullets.kind[0]], [4, 1000, 0, 1, 0]);
  assert.equal(kill.clearPending, false);
  const hit = new Game();
  hit.bullets.add(240, 560, 0, 0, 4, 1);
  hit.enemyBulletHits();
  assert.equal(hit.bullets.count, 0);
  assert.equal(hit.lives, 2);
  const full = new Game();
  for (let i = 0; i < 128; i++) full.enemies.add(0, 0, 0, 0);
  full.frame = 600;
  full.step(0);
  assert.equal(full.bossSpawned, false);
  full.enemies.erase(0);
  full.step(0);
  assert.equal(full.bossSpawned, true);
  for (const [phase, timer, count] of [[1, 44, 12], [2, 31, 7], [3, 19, 9], [3, 3, 3], [3, 4, 0]]) {
    const attack = new Game();
    attack.spawnBoss();
    attack.phase = phase; attack.phaseTime = timer;
    attack.step(0);
    assert.equal(attack.bullets.count, count);
  }
});

test('Canvas Lv4는 실제 체력 막대 픽셀을 그린다', { timeout: 30000 }, async () => {
  const folder = new URL('examples/canvas-ts/lv4/', import.meta.url);
  assert.ok(existsSync(new URL('render.ts', folder)), '보스 렌더러가 있어야 한다');
  const { build } = await import('esbuild');
  const bundle = await build({ stdin: { contents: "export { Game } from './game'; export { Renderer } from './render';",
    resolveDir: folder.pathname, loader: 'ts' }, bundle: true, format: 'iife', globalName: 'BossFixture', write: false });
  const browser = await chromium.launch(browserOptions);
  try {
    const page = await browser.newPage();
    await page.addScriptTag({ content: bundle.outputFiles[0].text });
    const pixels = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      document.body.append(canvas);
      const game = new BossFixture.Game();
      const boss = game.spawnBoss();
      game.enemies.hp[boss] = 90;
      new BossFixture.Renderer(canvas).draw(game, 1);
      const c = canvas.getContext('2d');
      return [Array.from(c.getImageData(20, 62, 1, 1).data).slice(0, 3),
        Array.from(c.getImageData(460, 62, 1, 1).data).slice(0, 3)];
    });
    assert.deepEqual(pixels, [[255, 100, 120], [30, 40, 60]]);
  } finally { await browser.close(); }
});

test('Canvas Lv5는 근접 보상·폭탄 눌림·아이템·큐 포화를 지킨다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv5/game.ts', import.meta.url)), 'Lv5 보상 로직이 있어야 한다');
  const { Game } = await import(new URL('dist/canvas-lv5-logic.mjs', import.meta.url));
  const g = new Game();
  g.bullets.add(255, 560, 0, 0, 4, 1);
  g.graze(); g.graze();
  assert.deepEqual([g.grazeCount, g.score], [1, 10]);
  g.bullets.add(240, 560, 0, 0, 4, 1);
  g.graze();
  assert.equal(g.grazeCount, 1);
  g.invulnerable = 1;
  g.bullets.add(225, 560, 0, 0, 4, 1);
  g.graze();
  assert.equal(g.grazeCount, 1);
  const bomb = new Game();
  bomb.spawnBoss();
  for (const x of [50, 100, 150]) bomb.enemies.add(x, 200, 0, 0, 12, 0, 3);
  bomb.bullets.add(0, 0, 0, 0);
  bomb.bullets.add(10, 10, 0, 0, 4, 1);
  bomb.step(64);
  assert.deepEqual([bomb.bombs, bomb.score, bomb.killCount, bomb.items.count, bomb.bullets.count], [2, 305, 3, 1, 1]);
  assert.equal(bomb.enemies.hp[bomb.findBoss()], 150);
  assert.equal(bomb.invulnerable, 180);
  bomb.step(64); assert.equal(bomb.bombs, 2);
  bomb.step(0); bomb.step(64); assert.equal(bomb.bombs, 1);
  const pickup = new Game();
  for (let i = 0; i < 3; i++) { pickup.items.add(240, 558.5, 0, 1.5, 6); pickup.moveItems(); }
  assert.deepEqual([pickup.power, pickup.score], [3, 150]);
  pickup.shoot(16);
  assert.deepEqual(Array.from(pickup.bullets.x.slice(0, 3)), [232, 240, 248]);
  const full = new Game();
  for (let i = 0; i < 70; i++) full.emit(4, 0, 0);
  full.bullets.add(255, 560, 0, 0, 4, 1);
  full.graze();
  assert.deepEqual([full.eventCount, full.score], [64, 10]);
  full.step(0); assert.equal(full.eventCount, 0);
  full.lives = 0; full.step(64);
  assert.equal(full.bombs, 3);
});

test('Canvas Lv6는 JSON 검증·동시 이벤트·복사 격리·재시도를 지킨다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv6/game.ts', import.meta.url)), 'Lv6 타임라인 로직이 있어야 한다');
  const { Game, validateStage, Rng } = await import(new URL('dist/canvas-lv6-logic.mjs', import.meta.url));
  const empty = new Game();
  for (let i = 0; i < 700; i++) empty.step(0);
  assert.equal(empty.enemies.count, 0);
  const data = [{ frame: 0, kind: 'enemy', pattern: 3 }, { frame: 0, kind: 'enemy', pattern: 1 }, { frame: 1, kind: 'boss' }];
  const g = new Game(undefined, data);
  data[0].frame = 999; data.length = 0;
  g.step(0);
  assert.deepEqual(Array.from(g.enemies.mark.slice(0, 2)), [3, 1]);
  assert.equal(g.stageCursor, 2);
  g.step(0); g.step(0);
  assert.deepEqual([g.stageCursor, g.enemies.count, g.phase], [3, 3, 1]);
  assert.equal(Object.isFrozen(g.stage), true);
  assert.equal(Object.isFrozen(g.stage[0]), true);
  const invalid = [null, {}, [null], [{ frame: -1, kind: 'boss' }], [{ frame: true, kind: 'boss' }],
    [{ frame: 1.5, kind: 'boss' }], [{ frame: 1, kind: 'boss' }, { frame: 0, kind: 'boss' }],
    [{ frame: 0, kind: 'other' }], [{ frame: 0, kind: 'enemy' }], [{ frame: 0, kind: 'enemy', pattern: true }],
    [{ frame: 0, kind: 'enemy', pattern: 4 }], [{ frame: 0, kind: 'boss', extra: 1 }],
    Array(4097).fill({ frame: 0, kind: 'boss' })];
  for (const input of invalid) assert.throws(() => validateStage(input));
  assert.equal(validateStage(Array(4096).fill({ frame: 0, kind: 'boss' })).length, 4096);
  const full = new Game(undefined, [{ frame: 0, kind: 'enemy', pattern: 0 }, { frame: 0, kind: 'boss' }]);
  for (let i = 0; i < 128; i++) full.enemies.add(0, 0, 0, 0);
  full.step(0);
  assert.equal(full.rng.state, new Rng(full.seed).next());
  assert.equal(full.stageBossPending, true);
  full.enemies.erase(0);
  full.step(0);
  assert.equal(full.bossSpawned, true);
  assert.equal(full.stageBossPending, false);
});

test('Canvas Lv7는 화면·정지·재시작·효과 난수를 분리한다', async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/lv7/game.ts', import.meta.url)), 'Lv7 완성 로직이 있어야 한다');
  const { Game } = await import(new URL('dist/canvas-lv7-logic.mjs', import.meta.url));
  const title = new Game(undefined, [], false);
  title.step(18);
  assert.deepEqual([title.status, title.playerX, title.time], [0, 240, 0]);
  title.step(130);
  assert.deepEqual([title.status, title.playerX, title.time], [1, 244, 1]);
  title.step(258);
  assert.deepEqual([title.paused, title.playerX, title.time], [true, 244, 1]);
  title.step(256); assert.equal(title.paused, true);
  title.step(0); title.step(258);
  assert.deepEqual([title.paused, title.playerX, title.time], [false, 248, 2]);
  const g = new Game();
  g.score = 1234; g.lives = 1;
  g.bullets.add(240, 560, 0, 0, 4, 1);
  g.step(0);
  assert.deepEqual([g.status, g.lives, g.highScore], [2, 0, 1234]);
  const time = g.time;
  g.step(18); assert.equal(g.time, time);
  g.step(128);
  assert.deepEqual([g.status, g.lives, g.score, g.highScore], [1, 3, 0, 1234]);
  const effect = new Game();
  const state = effect.rng.state;
  effect.emit(3, 100, 100); effect.updateEffects();
  assert.equal(effect.particles.count, 6);
  assert.equal(effect.rng.state, state);
  effect.eventCount = 0;
  for (let i = 0; i < 31; i++) effect.updateEffects();
  assert.equal(effect.particles.count, 0);
  const clear = new Game();
  clear.enemies.hp[clear.spawnBoss()] = 1;
  clear.bullets.add(240, 100, 0, 0);
  clear.step(0);
  assert.deepEqual([clear.status, clear.phase, clear.highScore], [3, 4, 1000]);
});

test('Canvas Lv7는 소리 실패와 손상된 최고 점수를 처리한다', async () => {
  const folder = new URL('examples/canvas-ts/lv7/', import.meta.url);
  assert.ok(existsSync(new URL('audio.ts', folder)), '오디오 어댑터가 있어야 한다');
  const { build } = await import('esbuild');
  for (const name of ['audio', 'storage']) {
    assert.ok(existsSync(new URL(name + '.ts', folder)));
    await build({ entryPoints: [new URL(name + '.ts', folder).pathname], bundle: true, format: 'esm',
      platform: 'node', outfile: new URL('dist/canvas-lv7-' + name + '.mjs', import.meta.url).pathname });
  }
  const { Audio, tone } = await import(new URL('dist/canvas-lv7-audio.mjs', import.meta.url));
  let resumes = 0;
  const pending = new Audio(() => ({ resume: () => { resumes++; return Promise.reject(new Error('장치 실패')); } }));
  await Promise.all([pending.unlock(), pending.unlock()]);
  assert.equal(resumes, 1);
  const samples = tone(440, .1);
  assert.equal(samples.length, 2205);
  assert.ok(samples.some((value) => value > 0));
  assert.ok(samples.every((value) => Math.abs(value) <= 1));
  const silent = new Audio(() => { throw new Error('없는 장치'); });
  await silent.unlock();
  assert.equal(silent.enabled, false);
  silent.consume({ eventCount: 0, status: 1, paused: false });
  silent.close();
  const { loadBest, saveBest } = await import(new URL('dist/canvas-lv7-storage.mjs', import.meta.url));
  let text = null;
  const memory = { getItem: () => text, setItem: (_key, value) => { text = value; } };
  assert.equal(loadBest(memory), 0);
  assert.equal(saveBest(memory, 1234), true);
  assert.equal(loadBest(memory), 1234);
  for (const value of ['bad json', '{"best":true}', '{"best":-1}', '{"best":1.5}', '{"best":9007199254740992}']) {
    text = value; assert.equal(loadBest(memory), 0);
  }
  for (const value of [-1, true, 1.5, 9007199254740992]) assert.equal(saveBest(memory, value), false);
  assert.equal(loadBest(null), 0);
  assert.equal(saveBest(null, 1), false);
  assert.equal(saveBest({ setItem: () => { throw new Error('권한'); } }, 1), false);
});

test('Canvas 배포 파일·로컬 HTTP·측정 결과를 실제 실행한다', { timeout: 30000 }, async () => {
  assert.ok(existsSync(new URL('examples/canvas-ts/tools.mjs', import.meta.url)), '배포·측정 도구가 있어야 한다');
  const { deploy, serve, profile } = await import('./examples/canvas-ts/tools.mjs');
  const target = new URL('dist/release/canvas.html', import.meta.url);
  // 캡처가 덱에 실리므로 작성자 컴퓨터의 절대 경로 대신 가이드 소스 기준 상대 경로를 보고한다.
  assert.equal(deploy(target).file, 'dist/release/canvas.html');
  assert.equal(readFileSync(target, 'utf8'), readFileSync(new URL('dist/canvas-lv7.html', import.meta.url), 'utf8'));
  const server = await serve(0);
  try {
    const base = 'http://127.0.0.1:' + server.address().port;
    const response = await fetch(base + '/');
    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /text\/html.*utf-8/);
    assert.equal(await response.text(), readFileSync(target, 'utf8'));
    assert.equal((await fetch(base + '/template.html')).status, 404);
  } finally { await new Promise((resolve) => server.close(resolve)); }
  const report = await profile(3);
  assert.equal(report.samplesMs.length, 3);
  assert.ok(report.medianMs > 0);
  // 자동 조종으로 다시 만든 기록 입력은 1800스텝 내내 살아남는다(pygame Lv7 기준과 같은 값).
  assert.equal(report.activeSteps, 1800);
  const golden = JSON.parse(readFileSync(new URL('spec/golden/lv7.json', import.meta.url)));
  assert.deepEqual(report.state, golden.checkpoints.at(-1));
  const pair = await profile(2);
  assert.equal(pair.medianMs, (pair.samplesMs[0] + pair.samplesMs[1]) / 2);
  for (const value of [0, -1, true, 1.5, 21]) await assert.rejects(() => profile(value));
});

test('Canvas 마무리는 실행 출처가 있는 25장이다', () => {
  const file = new URL('parts/38-canvas-wrap.html', import.meta.url);
  assert.ok(existsSync(file), 'Canvas 마무리 장이 있어야 한다');
  const html = readFileSync(file, 'utf8');
  assert.equal(inspectDeck('<main class="prose">' + html + '</main>').slides.length, 25);
  assert.ok(html.includes('captures/canvas-profile.txt'));
});
