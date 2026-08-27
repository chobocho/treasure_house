// 브라우저 없이 battle.js / ga_browser.js 를 돌려 보는 스모크 테스트.
// 캔버스·DOM 은 최소 스텁으로 대체하고, 실제 wasm 은 진짜를 쓴다.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SRC = new URL('.', import.meta.url).pathname;
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? ' → ' + x : '')); } };

// ── 최소 DOM 스텁 ────────────────────────────────────────────────────
function ctx2d() {
  const g = {};
  for (const k of ['clearRect','fillRect','beginPath','moveTo','lineTo','stroke','fill','arcTo',
                   'closePath','fillText','setTransform','strokeRect','save','restore','translate'])
    g[k] = () => {};
  g.createLinearGradient = () => ({ addColorStop: () => {} });
  g.measureText = () => ({ width: 10 });
  return g;
}
function el(tag = 'div') {
  const node = {
    tagName: tag.toUpperCase(), children: [], dataset: {}, style: {}, _html: '',
    classList: { _s: new Set(), add(...c) { c.forEach(x => this._s.add(x)); }, remove(...c) { c.forEach(x => this._s.delete(x)); }, contains(c) { return this._s.has(c); } },
    clientWidth: 640, clientHeight: 480, width: 640, height: 480, textContent: '',
    addEventListener() {}, removeEventListener() {}, focus() {}, setPointerCapture() {},
    appendChild(c) { this.children.push(c); c.parentElement = this; return c; },
    insertAdjacentHTML(_, h) { this._html += h; },
    getContext() { return ctx2d(); },
    setAttribute() {}, getAttribute() { return null; },
    querySelector(sel) { return this._find(sel); },
    querySelectorAll(sel) { return this._findAll(sel); },
    _find(sel) { const n = (this._pool[sel] ||= el(sel.includes('canvas') || sel.includes('chart') ? 'canvas' : 'div')); n.parentElement = this; return n; },
    _findAll(sel) { return (this._poolAll[sel] ||= [el(), el()]); },
  };
  node._pool = {}; node._poolAll = {};
  Object.defineProperty(node, 'innerHTML', { get() { return this._html; }, set(v) { this._html = v; } });
  return node;
}
const rafQ = [];
const sandbox = {
  console, WebAssembly, Math, JSON, Date, Promise, Object, Array, Number, String, Boolean,
  Uint8Array, Int32Array, Float32Array, Error, TypeError, URL, Blob: class {}, Worker: class {},
  atob: (s) => Buffer.from(s, 'base64').toString('binary'),
  performance: { now: () => Date.now() },
  requestAnimationFrame: (fn) => { rafQ.push(fn); return rafQ.length; },
  cancelAnimationFrame: () => {},
  ResizeObserver: class { observe() {} disconnect() {} },
  navigator: { vibrate: () => {} },
  devicePixelRatio: 1, innerWidth: 1280, innerHeight: 800,
  setTimeout, clearTimeout, setInterval, clearInterval,
  document: { createElement: (t) => el(t) },
  WASM_B64: readFileSync(SRC + 'tetris_ai.wasm').toString('base64'),   // 덱이 인라인하는 것과 같은 문자열
  GA_WEIGHTS: JSON.parse(readFileSync(SRC + 'weights.json', 'utf8')),
  GA_LOG: JSON.parse(readFileSync(SRC + 'ga_log.json', 'utf8')),
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

for (const f of ['ga_core.mjs', 'battle.js', 'ga_browser.js']) {
  let code = readFileSync(SRC + f, 'utf8');
  if (f.endsWith('.mjs')) code = code.replace(/^export /gm, '');
  vm.runInContext(code, sandbox, { filename: f });
}

// const/class 는 전역 객체가 아니라 "전역 렉시컬 스코프"에 들어간다(브라우저와 같다).
// 그래서 sandbox 객체로는 안 보이고, 컨텍스트 안에서 식을 평가해 꺼내야 한다.
const G = (expr) => vm.runInContext(expr, sandbox);

console.log('\n── S1 스크립트 로드');
ok(G('typeof loadCore') === 'function', 'loadCore 정의됨');
ok(G('typeof AiDriver') === 'function', 'AiDriver 정의됨');
ok(G('typeof Referee') === 'function', 'Referee 정의됨');
ok(G('typeof TetrisView') === 'function', 'TetrisView 정의됨');
ok(G('typeof BattleView') === 'function', 'BattleView 정의됨');
ok(G('typeof GaRunner') === 'function', 'GaRunner 정의됨');
ok(G('typeof mutate') === 'function', 'ga_core 의 mutate 가 전역으로 노출됨 (export 제거)');
ok(typeof sandbox.window.__mountDemo === 'function', '__mountDemo 등록됨');
const kinds = G('Object.keys(DEMO_MOUNTS).sort().join(",")');
ok(kinds === 'ai,battle-ai,battle-human,features,ga,gachart,solo',
   '데모 마운트 7종 등록: ' + kinds, kinds);
ok(['easy','normal','hard','max'].every(k => sandbox.GA_WEIGHTS.levels[k]),
   '난이도 프리셋 4종이 weights.json 에 있다');
ok(G('COLORS.length') === 9 && G('COLORS[8]') === '#6b7280', '가비지 색(인덱스 8) 정의됨');
ok(G('Object.keys(LEVELS).join(",")') === 'easy,normal,hard,max', 'LEVELS 4종');

// ── S2 AiDriver 가 실제로 판을 둔다 ──────────────────────────────────
console.log('\n── S2 AiDriver');
const run = (expr) => vm.runInContext(`(async () => { ${expr} })()`, sandbox);

const r2 = await run(`
  const core = await loadCore(WASM_B64, 12345);
  const d = new AiDriver(core, { thinkMs: 100, moveMs: 16, weights: GA_WEIGHTS.best });
  const s = V(core).stats;
  let presses = 0;
  const orig = core.e, w = {};
  for (const k of Object.keys(orig)) w[k] = orig[k];
  w.ts_press = (a) => { presses++; return orig.ts_press(a); };
  core.e = w;
  for (let i = 0; i < 6000 && s[5] === 0; i++) { core.e.ts_update(16); d.step(16); }
  return { lines: s[1], pieces: s[15], presses, state: s[5], attack: s[27] };
`);
ok(r2.pieces > 40, `6000스텝(96초)에 조각 ${r2.pieces}개를 놓았다`);
ok(r2.lines > 20, `줄 ${r2.lines}개를 지웠다`);
ok(r2.presses > r2.pieces, `키를 ${r2.presses}번 눌렀다 (조각당 평균 ${(r2.presses / r2.pieces).toFixed(1)}회)`);

const r2b = await run(`
  const core = await loadCore(WASM_B64, 777);
  const d = new AiDriver(core, { thinkMs: 0, moveMs: 0, blunder: 1.0, weights: GA_WEIGHTS.levels.easy });
  const s = V(core).stats;
  for (let i = 0; i < 4000 && s[5] === 0; i++) { core.e.ts_update(16); d.step(16); }
  return { pieces: s[15], state: s[5] };
`);
ok(r2b.pieces > 10, `실수 100% 드라이버도 멈추지 않고 진행한다 (조각 ${r2b.pieces}개)`);

// ── S3 Referee 가 공격을 배달한다 ────────────────────────────────────
console.log('\n── S3 Referee');
const r3 = await run(`
  const seed = 4242;
  const a = await loadCore(WASM_B64, seed), b = await loadCore(WASM_B64, seed);
  setWeights(a, GA_WEIGHTS.best); setWeights(b, GA_WEIGHTS.levels.easy);
  const da = new AiDriver(a, { thinkMs: 0, moveMs: 0, weights: GA_WEIGHTS.best });
  const db = new AiDriver(b, { thinkMs: 0, moveMs: 0, weights: GA_WEIGHTS.levels.easy });
  let winner = -1;
  const ref = new Referee([{ core: a }, { core: b }], { bestOf: 1, onRound: (w) => { winner = w; } });
  let steps = 0;
  for (; steps < 60000 && !ref.over; steps++) {
    a.e.ts_update(16); da.step(16);
    b.e.ts_update(16); db.step(16);
    ref.route();
  }
  return {
    winner, steps, sent: ref.sent,
    recvA: V(a).stats[29], recvB: V(b).stats[29],
    pendA: V(a).stats[28], pendB: V(b).stats[28],
    over: ref.over, wins: ref.wins,
  };
`);
ok(r3.over, `대전이 끝났다 (${r3.steps}스텝 = ${(r3.steps * 16 / 1000).toFixed(0)}초)`);
ok(r3.winner === 0 || r3.winner === 1, `승자 판정: ${r3.winner === 0 ? '학습된 AI' : '1세대 AI'}`);
ok(r3.sent[0] > 0, `강한 쪽이 보낸 줄 ${r3.sent[0]}`);
ok(r3.recvB > 0, `약한 쪽이 실제로 받은 줄 ${r3.recvB}`);
ok(r3.sent[0] > r3.sent[1], `학습된 AI가 더 많이 보냈다 (${r3.sent[0]} vs ${r3.sent[1]})`);
ok(r3.recvA <= r3.sent[1] && r3.recvB <= r3.sent[0], '받은 줄이 보낸 줄을 넘지 않는다 (상쇄가 동작)');
ok(r3.wins[r3.winner] === 1, '라운드 승수가 기록됐다');

// ── S4 뷰가 DOM 스텁 위에서 만들어지고 프레임을 돈다 ────────────────
console.log('\n── S4 뷰와 대전 화면');
const r4 = await run(`
  const host = document.createElement('div');
  const core = await loadCore(WASM_B64, 99);
  const v = new TetrisView(host, core, { driver: new AiDriver(core, { weights: GA_WEIGHTS.best }), manual: true });
  v.sent = 0;
  for (let i = 0; i < 400; i++) { v.step16(); }
  v.frame();
  return { cell: v.cell, layout: host.dataset.layout, lines: V(core).stats[1], html: host.innerHTML.length };
`);
ok(r4.cell > 0, `셀 크기 계산됨 (${r4.cell}px, layout=${r4.layout})`);
ok(r4.html > 200, 'DOM 이 만들어졌다');
ok(r4.lines >= 0, `400스텝 진행 (지운 줄 ${r4.lines})`);

const r5 = await run(`
  const host = document.createElement('div');
  const seed = 31337;
  const a = await loadCore(WASM_B64, seed), b = await loadCore(WASM_B64, seed);
  const bv = new BattleView(host, [a, b], {
    drivers: [new AiDriver(a, { thinkMs: 0, moveMs: 0, weights: GA_WEIGHTS.best }),
              new AiDriver(b, { thinkMs: 0, moveMs: 0, weights: GA_WEIGHTS.levels.easy })],
    names: ['A', 'B'], bestOf: 3,
  });
  let rounds = 0;
  for (let i = 0; i < 120000 && !bv.done; i++) {
    if (!bv.ref.over) { for (const v of bv.views) v.step16(); bv.ref.route(); }
    else if (bv.waiting > 0) { bv.waiting -= 16; if (bv.waiting <= 0 && !bv.done) { bv.startRound(); rounds++; } }
    else break;
  }
  for (const v of bv.views) v.frame();
  return { done: bv.done, wins: bv.ref.wins, round: bv.round, msg: bv.msg.textContent };
`);
ok(r5.done, `3판 2선승이 끝났다 — ${r5.msg}`);
ok(r5.wins[0] + r5.wins[1] === r5.round, `라운드 수(${r5.round})와 승수 합이 일치`);
ok(Math.max(...r5.wins) === 2, `승자가 2승 (${r5.wins.join('-')})`);

// ── S5 브라우저 GA 러너 ──────────────────────────────────────────────
console.log('\n── S5 GaRunner');
const r6 = await run(`
  const host = document.createElement('div');
  const g = new GaRunner(host, { pop: 6, gen: 3, pieces: 60, seeds: [1], budget: 10000 });
  for (let i = 0; i < 50 && !g.ready; i++) await new Promise(r => setTimeout(r, 5));
  g.playing = true;
  for (let i = 0; i < 200 && g.gen < 3; i++) g.work();
  return { gen: g.gen, logs: g.log.length, best: g.bestFit, unit: Math.hypot(...(g.best || [1])) };
`);
ok(r6.gen === 3, `3세대까지 진행 (로그 ${r6.logs}줄)`);
ok(r6.best >= 0, `최고 적합도 ${r6.best}`);
ok(Math.abs(r6.unit - 1) < 1e-6, '최고 유전자가 단위벡터');

console.log('\n' + '='.repeat(50));
console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
