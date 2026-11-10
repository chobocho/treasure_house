// node 로 진짜 .wasm 을 돌려 보는 시험 — 브라우저 없이 exports 와 글루를 본다.
//   node wasm/test/node_test.mjs target-wasm/wasm32-unknown-unknown/wasm/tetris_wasm.wasm
import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';
import vm from 'node:vm';

const path = process.argv[2];
const bytes = readFileSync(path);
let passed = 0;
const test = async (name, fn) => {
  try { await fn(); passed++; console.log('ok  ', name); }
  catch (e) { console.log('FAIL', name, '\n   ', e.message); process.exitCode = 1; }
};

const { instance, module } = await WebAssembly.instantiate(bytes, {});
const ex = instance.exports;

await test('가져오는 함수가 없다(imports 0개)', () => {
  assert.deepEqual(WebAssembly.Module.imports(module), []);
});

// ANCHOR: exports
await test('내보내기 목록', () => {
  const names = WebAssembly.Module.exports(module)
    .map(e => e.name).sort();
  for (const n of ['memory', 'tt_init', 'tt_input', 'tt_tick',
                   'tt_render', 'tt_width', 'tt_height', 'tt_stat']) {
    assert.ok(names.includes(n), n + ' 없음: ' + names.join(','));
  }
});
// ANCHOR_END: exports

await test('init 전 호출은 0/널', () => {
  assert.equal(ex.tt_render(), 0);
  assert.equal(ex.tt_input(3), 0);
  assert.equal(ex.tt_width(), 0);
});

await test('잘못된 칸 크기는 0', () => {
  assert.equal(ex.tt_init(1, 0, 7), 0);
  assert.equal(ex.tt_init(1, 0, 65), 0);
});

await test('그리고 RGBA 를 읽는다', () => {
  assert.equal(ex.tt_init(42, 0, 24), 1);
  const w = ex.tt_width(), h = ex.tt_height();
  assert.deepEqual([w, h], [396, 504]);
  const ptr = ex.tt_render();
  assert.ok(ptr > 0);
  const px = new Uint8Array(ex.memory.buffer, ptr, w * h * 4);
  for (let i = 3; i < px.length; i += 4) assert.equal(px[i], 255);
  // (0,0) 픽셀은 배경색 0x10131A
  assert.deepEqual([...px.slice(0, 3)], [0x10, 0x13, 0x1a]);
});

await test('하드 드롭으로 점수, 시간으로 중력', () => {
  ex.tt_init(42, 0, 24);
  assert.equal(ex.tt_input(3), 1);
  assert.ok(ex.tt_stat(0) > 0);
  ex.tt_tick(5000);
  ex.tt_tick(5000); // 다음 조각이 바닥에 닿고 고정
  assert.equal(ex.tt_stat(3), 0, '아직 안 끝났다');
});

await test('게임 오버 뒤 다시 시작', () => {
  ex.tt_init(3, 0, 16);
  assert.equal(ex.tt_input(8), 0);
  for (let i = 0; i < 500 && !ex.tt_stat(3); i++) ex.tt_input(3);
  assert.equal(ex.tt_stat(3), 1);
  assert.equal(ex.tt_input(8), 1);
  assert.equal(ex.tt_stat(0), 0);
});

await test('글루: keyName 과 mount (가짜 캔버스)', async () => {
  const src = readFileSync(new URL('../web/tetris.js', import.meta.url), 'utf8');
  // 가짜 rAF: 예약 번호 → 콜백. cancel 이 진짜로 지워야 sleep 을 시험할 수 있다
  const frames = new Map();
  let seq = 0, puts = 0;
  const step = t => { const [id, fn] = frames.entries().next().value; frames.delete(id); fn(t); };
  const ctx = {
    globalThis: {}, performance: { now: () => 0 },
    requestAnimationFrame: fn => { frames.set(++seq, fn); return seq; },
    cancelAnimationFrame: id => { frames.delete(id); },
    ImageData: class { constructor(d, w, h) { this.data = d; this.width = w; this.height = h; } },
    WebAssembly, Uint8ClampedArray, Math, Object, Set, Error, Date,
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  const RT = ctx.RustTetris;
  assert.equal(RT.keyName({ key: 'ArrowLeft', repeat: true }), 'left');
  assert.equal(RT.keyName({ key: ' ', repeat: true }), null, '드롭은 반복 안 함');
  assert.equal(RT.keyName({ key: 'q' }), null);

  const ex2 = await RT.load(bytes);
  // ANCHOR: glue_mount
  const canvas = {
    getContext: () => ({ putImageData: () => { puts++; } }),
  };
  let last;
  const g = RT.mount(canvas, ex2, {
    seed: 2 ** 40 + 7, cell: 20, onStats: s => { last = s; },
  });
  assert.deepEqual([canvas.width, canvas.height], [330, 420]);
  step(16);
  step(33);
  assert.equal(puts, 2);
  assert.equal(last.score, 0);
  assert.ok(g.press('hard'));
  assert.equal(g.press('nope'), false);
  step(50);
  assert.ok(last.score > 0);
  // ANCHOR_END: glue_mount
  g.sleep();
  assert.equal(g.running, false);
  assert.equal(frames.size, 0, '자는 동안은 프레임 예약이 없다');
  g.wake();
  g.wake(); // 두 번 깨워도 루프는 하나
  assert.equal(frames.size, 1);
  // onFrame 안에서 재워도 다음 wake 가 먹힌다(남은 예약이 없어야)
  let napNow = true;
  const g2 = RT.mount(canvas, ex2, { cell: 20, onFrame: () => { if (napNow) g2.sleep(); } });
  g.stop();
  step(60); // g2 의 첫 프레임: onFrame 이 재운다
  assert.equal(frames.size, 0);
  napNow = false;
  g2.wake();
  assert.equal(frames.size, 1, '깨우면 다시 돈다');
  g2.stop();
  assert.equal(g.running, false);
});

console.log(`${passed} passed`);
