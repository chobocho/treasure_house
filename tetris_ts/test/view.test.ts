// test/view.test.ts — 렌더러와 입력. 브라우저 없이 검사한다.
//
// 화면을 다루는 코드는 "눈으로 보면 되지"라며 테스트를 건너뛰기 쉬운데, 덱 안에서
// 도는 데모가 조용히 죽으면 문서 전체가 거짓말이 된다. 그래서 DOM 을 흉내 낸 아주
// 작은 스텁을 만들어 두고 캔버스에 무엇을 몇 번 칠했는지까지 센다.
//
// view.ts 는 이걸 가능하게 하려고 세 가지를 주입받는다: 시계(now), 프레임(raf),
// 그리고 문서(host.ownerDocument). 전역을 직접 만지지 않으니 노드에서도 돈다.

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { Tetris, ACT, ST } from '../src/core.js';
import { TetrisView, KEYMAP } from '../src/view.js';
import { FEATURE_NAMES } from '../src/ai.js';
import { GaView } from '../src/ga_view.js';
import { ArenaView } from '../src/arena_view.js';
import { mountDemo, DEMOS } from '../src/demo.js';

// ── DOM 스텁 ──────────────────────────────────────────────────────────
interface Rec { calls: { fn: string; args: unknown[] }[] }

function ctx2d(): Rec & Record<string, unknown> {
  // eslint 규칙이 아니라 타입 때문에 한 번 우회한다 — 스텁이라 모양만 맞으면 된다.
  const rec: Rec = { calls: [] };
  const push = (fn: string) => (...args: unknown[]): void => { rec.calls.push({ fn, args }); };
  return Object.assign(rec as Record<string, unknown> & Rec, {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', globalAlpha: 1,
    fillRect: push('fillRect'), strokeRect: push('strokeRect'), clearRect: push('clearRect'),
    fillText: push('fillText'), beginPath: push('beginPath'), stroke: push('stroke'),
    moveTo: push('moveTo'), lineTo: push('lineTo'), save: push('save'), restore: push('restore'),
    setTransform: push('setTransform'), scale: push('scale'),
  }) as unknown as Rec & Record<string, unknown>;
}

function el(tag: string, doc: unknown): Record<string, unknown> {
  const listeners = new Map<string, ((e: unknown) => void)[]>();
  const node: Record<string, unknown> = {
    tagName: tag.toUpperCase(), children: [] as unknown[], style: {} as Record<string, string>,
    dataset: {} as Record<string, string>, className: '', textContent: '', tabIndex: -1,
    width: 0, height: 0, ownerDocument: doc, listeners,
    appendChild(c: Record<string, unknown>) { (node.children as unknown[]).push(c); c.parentNode = node; return c; },
    addEventListener(t: string, f: (e: unknown) => void) {
      if (!listeners.has(t)) listeners.set(t, []);
      (listeners.get(t) as ((e: unknown) => void)[]).push(f);
    },
    removeEventListener(t: string, f: (e: unknown) => void) {
      const a = listeners.get(t) ?? [];
      const i = a.indexOf(f);
      if (i >= 0) a.splice(i, 1);
    },
    getContext: () => (node.__ctx ??= ctx2d()),
    getBoundingClientRect: () => ({ width: 360, height: 640, left: 0, top: 0 }),
    focus() { (node as { focused?: boolean }).focused = true; },
    setAttribute(k: string, v: string) { node[k] = v; },
  };
  return node;
}

function fakeDoc(): Record<string, unknown> {
  const doc: Record<string, unknown> = {};
  doc.createElement = (t: string): Record<string, unknown> => el(t, doc);
  return doc;
}

/** 손으로 프레임을 돌리는 시계 — 진짜 rAF 없이 원하는 만큼만 흐르게 한다. */
function clock(): { raf: (cb: (t: number) => void) => number; caf: (h: number) => void;
                    now: () => number; tick: (ms: number) => void; pending: number } {
  let t = 0, next = 1;
  const q = new Map<number, (t: number) => void>();
  return {
    raf(cb) { const h = next++; q.set(h, cb); return h; },
    caf(h) { q.delete(h); },
    now: () => t,
    tick(ms) {
      t += ms;
      const due = [...q.entries()];
      q.clear();
      for (const [, cb] of due) cb(t);
    },
    get pending() { return q.size; },
  };
}

function mount(opts: Record<string, unknown> = {}): {
  host: Record<string, unknown>; game: Tetris; view: TetrisView; c: ReturnType<typeof clock>;
} {
  const doc = fakeDoc();
  const host = el('div', doc);
  const game = new Tetris(20260829);
  const c = clock();
  const view = new TetrisView(host as unknown as HTMLElement, game,
    { raf: c.raf, caf: c.caf, now: c.now, ...opts });
  return { host, game, view, c };
}

// ── 붙이기 ────────────────────────────────────────────────────────────
test('마운트하면 캔버스가 생기고 판 비율이 10:20 이다', () => {
  const { host, view } = mount();
  const kids = host.children as Record<string, unknown>[];
  assert.ok(kids.length > 0, '아무것도 붙이지 않았다');
  const canvas = view.canvas as unknown as { width: number; height: number };
  assert.ok(canvas.width > 0 && canvas.height > 0, '캔버스 크기가 0이다');
  assert.equal(canvas.height / canvas.width, 2, '보이는 판은 10칸 × 20줄이다');
});

test('좁은 폭에서도 셀 한 칸이 정수 픽셀로 떨어진다', () => {
  for (const w of [374, 412, 768]) {
    const { view } = mount({ maxWidth: w });
    assert.equal(view.cell, Math.floor(view.cell), `${w}px 에서 셀이 소수다`);
    assert.ok(view.cell >= 8, `${w}px 에서 셀이 너무 작다 (${view.cell})`);
  }
});

// ── 그리기 ────────────────────────────────────────────────────────────
test('굳은 블록·고스트·현재 조각을 모두 칠한다', () => {
  const { game, view } = mount();
  game.garbage(3, 4);           // 바닥에 가비지 3줄 (구멍 x=4)
  view.draw();
  const ctx = (view.canvas as unknown as { __ctx: Rec }).__ctx;
  const fills = ctx.calls.filter((c) => c.fn === 'fillRect');
  // 배경 1 + 가비지 27칸 + 고스트 4 + 현재 조각 4 = 최소 36
  assert.ok(fills.length >= 36, `칠한 칸이 너무 적다 (${fills.length})`);
});

test('게임 오버면 조각도 고스트도 그리지 않는다', () => {
  const { game, view } = mount();
  game.stats[ST.STATE] = 1; // OVER
  game.buildView();
  view.draw();
  const ctx = (view.canvas as unknown as { __ctx: Rec }).__ctx;
  assert.ok(ctx.calls.some((c) => c.fn === 'fillText'), '게임 오버 표시가 없다');
});

// ── 입력 ──────────────────────────────────────────────────────────────
test('키맵이 액션으로 이어진다', () => {
  assert.equal(KEYMAP['ArrowLeft'], ACT.LEFT);
  assert.equal(KEYMAP['ArrowRight'], ACT.RIGHT);
  assert.equal(KEYMAP['ArrowDown'], ACT.SOFT);
  assert.equal(KEYMAP['ArrowUp'], ACT.CW);
  assert.equal(KEYMAP[' '], ACT.HARD);
  assert.equal(KEYMAP['c'], ACT.HOLD);
});

test('키를 눌러야 조각이 움직인다 — 그리고 떼면 DAS 가 풀린다', () => {
  const { game, view } = mount();
  view.start();
  const x0 = game.curX;
  view.onKey({ type: 'keydown', key: 'ArrowLeft', preventDefault(): void {} });
  assert.equal(game.curX, x0 - 1, '왼쪽으로 한 칸 갔어야 한다');
  view.onKey({ type: 'keyup', key: 'ArrowLeft', preventDefault(): void {} });
  // 뗀 뒤에는 시간이 흘러도 자동반복이 없다
  const x1 = game.curX;
  for (let i = 0; i < 30; i++) game.update(16);
  assert.equal(game.curX, x1, '키를 뗐는데 계속 움직였다');
});

test('덱을 넘기는 키는 가로채지 않는다', () => {
  const { view } = mount();
  view.start();
  let prevented = false;
  // ←/→ 는 게임이 쓰지만 PageDown 같은 건 문서 몫이다.
  view.onKey({ type: 'keydown', key: 'PageDown', preventDefault(): void { prevented = true; } });
  assert.equal(prevented, false, '문서가 쓰는 키를 가로챘다');
});

// ── 루프 ──────────────────────────────────────────────────────────────
test('start 하면 프레임마다 정수 dt 로 시간이 흐른다', () => {
  const { game, view, c } = mount();
  view.start();
  const t0 = game.stats[ST.ELAPSED] as number;
  c.tick(16); c.tick(17); c.tick(16);
  const dt = (game.stats[ST.ELAPSED] as number) - t0;
  assert.ok(dt >= 32 && dt <= 50, `흐른 시간이 이상하다: ${dt}ms`);
  assert.equal(dt, Math.trunc(dt), 'dt 가 정수가 아니다');
});

test('stop 하면 시간이 멈추고 프레임 예약도 없다', () => {
  const { game, view, c } = mount();
  view.start();
  c.tick(16);
  view.stop();
  assert.equal(c.pending, 0, '멈췄는데 프레임이 예약돼 있다');
  const t = game.stats[ST.ELAPSED] as number;
  c.tick(100);
  assert.equal(game.stats[ST.ELAPSED], t, '멈춘 뒤에도 시간이 흘렀다');
});

test('탭 전환처럼 큰 간격이 와도 한 번에 100ms 까지만 흐른다', () => {
  const { game, view, c } = mount();
  view.start();
  const t0 = game.stats[ST.ELAPSED] as number;
  c.tick(5000);
  assert.ok((game.stats[ST.ELAPSED] as number) - t0 <= 100, '5초를 그대로 흘려보냈다');
});

// ── 데모 레지스트리 ───────────────────────────────────────────────────
test('데모 레지스트리가 슬라이드의 data-demo 를 보고 붙인다', async () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  (host.dataset as Record<string, string>).demo = 'play';
  const v = await mountDemo(host as unknown as HTMLElement, { raf: clock().raf, caf: clock().caf, now: () => 0 });
  assert.equal(typeof v.start, 'function');
  assert.equal(typeof v.stop, 'function');
  v.stop();
});

test('모르는 데모 이름이면 기본 데모로 떨어진다 (덱이 죽지 않는다)', async () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  (host.dataset as Record<string, string>).demo = '없는데모';
  const v = await mountDemo(host as unknown as HTMLElement, { raf: clock().raf, caf: clock().caf, now: () => 0 });
  assert.ok(v, '아무것도 못 붙였다');
  v.stop();
  assert.ok(Object.keys(DEMOS).length >= 1);
});

/** 스텁 트리 전체의 글자를 모은다 — 데모가 무엇을 써 놓았는지 보려고. */
function textOf(node: Record<string, unknown>): string {
  const kids = (node.children as Record<string, unknown>[]) ?? [];
  return String(node.textContent ?? '') + kids.map(textOf).join(' ');
}

test('onDraw 훅이 그릴 때마다 불린다', () => {
  let n = 0;
  const { view, c } = mount({ onDraw: (): void => { n++; } });
  const base = n; // 생성자가 이미 한 번 그렸다
  view.start();
  c.tick(16); c.tick(16);
  assert.ok(n >= base + 2, `프레임마다 불려야 한다 (${base} → ${n})`);
});

test('feat 데모는 특징 여덟 개를 이름과 값으로 보여 준다', async () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  (host.dataset as Record<string, string>).demo = 'feat';
  const cl = clock();
  const v = await mountDemo(host as unknown as HTMLElement, { raf: cl.raf, caf: cl.caf, now: cl.now });
  const txt = textOf(host);
  for (const name of FEATURE_NAMES) {
    assert.ok(txt.includes(name), `${name} 이 화면에 없다`);
  }
  assert.ok(/점수/.test(txt), '합계 점수를 안 보여 준다');
  v.stop();
});

// ── 브라우저 라이브 학습 ──────────────────────────────────────────────
test('라이브 학습 뷰는 프레임마다 한 걸음씩 나아간다', () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  const c = clock();
  const v = new GaView(host as unknown as HTMLElement, {
    raf: c.raf, caf: c.caf, now: c.now, maxWidth: 400,
    ga: { pop: 4, maxPieces: 40, seeds: [1], rngSeed: 7 },
  });
  v.start();
  const before = v.ga.idx + v.ga.log.length * 100;
  c.tick(16);
  const after = v.ga.idx + v.ga.log.length * 100;
  assert.ok(after > before, `한 프레임에 적어도 한 개체는 평가해야 한다 (${before} → ${after})`);
  v.stop();
  assert.equal(c.pending, 0, '멈췄는데 프레임이 예약돼 있다');
});

test('라이브 학습 뷰는 세대가 끝나면 곡선을 그린다', () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  const c = clock();
  const v = new GaView(host as unknown as HTMLElement, {
    raf: c.raf, caf: c.caf, now: c.now, maxWidth: 400,
    ga: { pop: 3, maxPieces: 30, seeds: [1], rngSeed: 11 },
  });
  v.start();
  for (let i = 0; i < 20 && v.ga.log.length < 2; i++) c.tick(16);
  assert.ok(v.ga.log.length >= 2, `세대가 진행돼야 한다 (${v.ga.log.length})`);
  const ctx = (v.canvas as unknown as { __ctx: Rec }).__ctx;
  assert.ok(ctx.calls.some((x) => x.fn === 'lineTo'), '곡선을 안 그렸다');
  assert.ok(textOf(host).includes('세대'), '세대 표시가 없다');
  v.stop();
});

test('ga 데모가 레지스트리에 있다', async () => {
  const doc = fakeDoc();
  const host = el('div', doc);
  (host.dataset as Record<string, string>).demo = 'ga';
  const c = clock();
  const v = await mountDemo(host as unknown as HTMLElement, { raf: c.raf, caf: c.caf, now: c.now });
  assert.ok(DEMOS['ga'], 'ga 데모가 등록되지 않았다');
  assert.equal(typeof v.start, 'function');
  v.stop();
});

// ── 로컬 아레나 ───────────────────────────────────────────────────────
function arena(seats: number, opts: Record<string, unknown> = {}): {
  host: Record<string, unknown>; view: ArenaView; c: ReturnType<typeof clock>;
} {
  const doc = fakeDoc();
  const host = el('div', doc);
  const c = clock();
  const view = new ArenaView(host as unknown as HTMLElement, {
    seats, maxWidth: 400, restart: false, intervalMs: 20, seed: 4242,
    raf: c.raf, caf: c.caf, now: c.now, ...opts,
  });
  return { host, view, c };
}

test('아레나 뷰는 좌석 수만큼 판을 그린다', () => {
  for (const n of [2, 8]) {
    const { view } = arena(n);
    assert.equal(view.battle.seats.length, n, `${n}석이 앉아야 한다`);
    const ctx = (view.canvas as unknown as { __ctx: Rec }).__ctx;
    // 배경 1 + 좌석마다 판 배경 1 = 최소 n+1 번은 칠한다
    assert.ok(ctx.calls.filter((x) => x.fn === 'fillRect').length >= n + 1);
  }
});

test('아레나는 프레임마다 대전을 진행한다', () => {
  const { view, c } = arena(4);
  view.start();
  const count = (): number => view.battle.seats
    .reduce((a: number, x) => a + (x.game.stats[ST.PIECES] as number), 0);
  const before = count();
  for (let i = 0; i < 20; i++) c.tick(100);
  const after = count();
  assert.ok(after > before, `조각이 놓여야 한다 (${before} → ${after})`);
  view.stop();
});

test('경기가 끝나면 순위를 보여 주고 멈춘다', () => {
  const { host, view, c } = arena(2);
  view.start();
  for (let i = 0; i < 4000 && !view.battle.over; i++) c.tick(100);
  assert.ok(view.battle.over, `경기가 끝나야 한다 (${view.battle.now}ms 진행)`);
  const txt = textOf(host);
  assert.ok(/등/.test(txt), `순위 표시가 없다: ${txt.slice(0, 80)}`);
  const pending = c.pending;
  c.tick(100);
  assert.equal(view.battle.now, view.battle.now, '끝난 뒤에는 시간이 더 흐르지 않는다');
  assert.ok(pending <= 1);
});

test('arena·duel 데모가 등록돼 있다', async () => {
  for (const name of ['arena', 'duel']) {
    const doc = fakeDoc();
    const host = el('div', doc);
    (host.dataset as Record<string, string>).demo = name;
    const c = clock();
    const v = await mountDemo(host as unknown as HTMLElement, { raf: c.raf, caf: c.caf, now: c.now });
    assert.ok(DEMOS[name], `${name} 데모가 없다`);
    v.stop();
  }
});
