// test_browser.mjs — 브라우저 없이 브라우저 코드를 돌린다.
// DOM·캔버스는 최소 스텁으로 바꾸고, wasm 과 room 엔진은 진짜를 쓴다.
// 이 하니스가 통과하면 "덱 안의 데모가 실제로 돈다"는 뜻이다.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SRC = new URL('.', import.meta.url).pathname;
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? ' → ' + x : '')); } };

function ctx2d() {
  const g = {};
  for (const k of ['clearRect', 'fillRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill',
                   'closePath', 'fillText', 'setTransform', 'strokeRect', 'save', 'restore', 'translate'])
    g[k] = () => {};
  g.measureText = () => ({ width: 10 });
  return g;
}
function el(tag = 'div') {
  const node = {
    tagName: tag.toUpperCase(), children: [], dataset: {}, style: {},
    classList: { add() {}, remove() {}, contains() { return false; } },
    clientWidth: 900, clientHeight: 600, width: 900, height: 600, textContent: '', tabIndex: 0,
    addEventListener() {}, removeEventListener() {}, focus() {},
    appendChild(c) { this.children.push(c); return c; },
    getContext() { return ctx2d(); },
    setAttribute() {}, getAttribute() { return null; },
  };
  Object.defineProperty(node, 'innerHTML', { get() { return ''; }, set() {} });
  return node;
}

let CLOCK = 0;
const rafQ = [];
const sandbox = {
  console, WebAssembly, Math, JSON, Date, Promise, Object, Array, Number, String, Boolean,
  Uint8Array, Int32Array, Float32Array, Error, TypeError, Set, Map, isNaN, parseInt, parseFloat,
  atob: (s) => Buffer.from(s, 'base64').toString('binary'),
  btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
  performance: { now: () => CLOCK },
  requestAnimationFrame: (fn) => { rafQ.push(fn); return rafQ.length; },
  cancelAnimationFrame: () => {},
  navigator: { getGamepads: () => [null, null] },
  devicePixelRatio: 1, innerWidth: 1280, innerHeight: 800,
  setTimeout, clearTimeout, setInterval, clearInterval,
  document: { createElement: (t) => el(t) },
  addEventListener() {},
  WASM_B64: readFileSync(SRC + 'tetris_net.wasm').toString('base64'),
  WEIGHTS: JSON.parse(readFileSync(SRC + '../tetris_ai/weights.json', 'utf8')).levels,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

console.log('\n── S1 스크립트 로드 (덱이 인라인하는 것과 같은 순서)');
for (const f of ['room.mjs', 'netcore_browser.js', 'net_client.js', 'seats.js', 'arena.js', 'match.js']) {
  let code = readFileSync(SRC + f, 'utf8');
  if (f.endsWith('.mjs')) code = code.replace(/^export /gm, '');   // 덱 빌더가 하는 일과 같다
  try { vm.runInContext(code, sandbox, { filename: f }); ok(true, f); }
  catch (e) { ok(false, f, e.message); }
}
const G = (expr) => vm.runInContext(expr, sandbox);

console.log('\n── S2 스냅샷 코덱 (btoa/atob 경로)');
{
  G(`var _c = null;`);
  const r = await G(`loadNet(WASM_B64, 7).then(c => { _c = c; return 1; })`);
  ok(r === 1, 'wasm 인스턴스 생성');
  G(`_c.e.ts_garbage(4, 3); _c.refresh();`);
  const b64 = G(`snapshot(_c)`);
  ok(typeof b64 === 'string' && b64.length > 0, 'snapshot 이 base64 를 낸다', b64.length + '자');
  const same = G(`(() => { const out = new Uint8Array(200); unsnapshot(${JSON.stringify(b64)}, out);
    for (let i = 0; i < 200; i++) if (out[i] !== _c.views.cells[i]) return i; return -1; })()`);
  ok(same === -1, '왕복 복원이 cells 와 완전히 같다', same);
  const s = G(`packState(_c)`);
  ok(s.length === 12 && s[4] === 4, 's[] 12칸 · s[4]=높이 4', JSON.stringify(s));
}

console.log('\n── S3 키맵이 겹치지 않는가 (한 PC 2인의 첫 번째 함정)');
{
  const dup = G(`Object.keys(KEYMAP_P1).filter(k => k in KEYMAP_P2)`);
  ok(dup.length === 0, '1P·2P 키가 하나도 겹치지 않는다', JSON.stringify(dup));
  ok(G(`Object.keys(KEYMAP_P1).length`) >= 8 && G(`Object.keys(KEYMAP_P2).length`) >= 8, '양쪽 다 8키 이상');
}

console.log('\n── S4 좁은 화면·넓은 화면에서 그리기가 터지지 않는가');
{
  const r = G(`(() => {
    const host = document.createElement('div');
    const a = new Arena(host);
    a.setSeats([{i:0,pid:1,name:'나',kind:'human',lv:'',ready:true,alive:true},
                {i:1,pid:1,name:'옆',kind:'human',lv:'',ready:true,alive:true},
                {i:2,pid:2,name:'봇',kind:'ai',lv:'hard',ready:true,alive:true},
                {i:3,pid:2,name:'봇2',kind:'ai',lv:'max',ready:true,alive:true},
                {i:4,pid:3,name:'봇3',kind:'ai',lv:'hard',ready:true,alive:true},
                {i:5,pid:3,name:'봇4',kind:'ai',lv:'easy',ready:true,alive:true},
                {i:6,pid:4,name:'봇5',kind:'ai',lv:'hard',ready:true,alive:true},
                {i:7,pid:4,name:'봇6',kind:'ai',lv:'normal',ready:true,alive:true}], [0,1]);
    a.attach(0, _c); a.attach(1, _c);
    a.onState(3, snapshot(_c), packState(_c));
    a.onGarbage(3, 4, 0);
    const sizes = [374, 768, 1280];
    for (const w of sizes) { host.clientWidth = w; host.clientHeight = 640; a.draw(); }
    a.onKo(3, 8); a.banner = '테스트'; a.draw();
    return 'ok';
  })()`);
  ok(r === 'ok', '374 / 768 / 1280px 전부 예외 없이 그린다', r);
}

console.log('\n── S5 루프백 8인 대전 — PC 4대 × 2석을 한 페이지에서');
{
  G(`
    var W = { end: null, grb: 0, ko: [], clients: [], matches: [] };
    var hub = new LoopbackHub({ max: 8, perPeer: 2, target: 'random' }, 20260827);
    for (let pid = 1; pid <= 4; pid++) {
      const host = document.createElement('div');
      const arena = new Arena(host);
      const c = new NetClient(hub.connect(pid), 'PC' + pid);
      const m = wireMatch(c, new Match({
        client: c, arena, wasmB64: WASM_B64, weights: WEIGHTS,
        cfg: { delay: 900, cap: 8 }, onEnd: (e) => { if (!W.end) W.end = e; },
      }));
      c.on('hi', () => { pid === 1 ? c.create({}) : c.join('LOCAL1'); });
      c.on('joined', () => {
        c.takeSeat((pid - 1) * 2, 'ai', 'A' + pid, 'hard');
        c.takeSeat((pid - 1) * 2 + 1, 'ai', 'B' + pid, 'normal');
      });
      c.on('grb', () => { if (pid === 1) W.grb++; });
      c.on('ko', (msg) => { if (pid === 1) W.ko.push(msg.i); });
      c.on('start', (msg) => {
        const mine = msg.seats.filter(s => s.pid === c.pid)
          .map(s => ({ i: s.i, kind: 'ai', lv: s.lv, name: s.name, slot: 0 }));
        m.begin(msg, mine);
      });
      c.open();
      W.clients.push(c); W.matches.push(m);
    }
  `);
  const settle = () => new Promise((r) => setTimeout(r, 0));
  for (let i = 0; i < 8; i++) await settle();
  ok(G(`hub.room.occupied().length`) === 8, '좌석 8석이 채워졌다', G(`hub.room.occupied().length`));
  ok(G(`hub.room.seats.map(s=>s.pid)`).join(',') === '1,1,2,2,3,3,4,4', 'PC 1대당 정확히 2석');

  G(`W.clients[0].startRound()`);
  for (let i = 0; i < 20; i++) await settle();
  ok(G(`hub.room.phase`) === 'play', '라운드가 시작됐다', G(`hub.room.phase`));

  let frames = 0;
  while (!G(`!!W.end`) && frames < 60000) {
    const q = rafQ.splice(0);
    if (!q.length) { await settle(); if (frames > 100) break; continue; }
    CLOCK += 16; frames++;
    for (const fn of q) fn(CLOCK);
    if ((frames & 63) === 0) await settle();
  }
  const end = G(`W.end`);
  ok(!!end, `${frames}프레임 만에 end 까지 갔다`);
  ok(end && end.order.length === 8, '등수가 8석 전부 매겨졌다', end && JSON.stringify(end.order));
  ok(G(`W.ko.length`) === 7, '탈락 통보는 7번 (우승자는 ko 를 받지 않는다)', G(`W.ko.length`));
  ok(G(`W.grb`) > 0, `가비지가 실제로 오갔다 (grb ${G(`W.grb`)}회)`);
  const recv = G(`W.matches.map(m => [...m.seats.values()].map(s => s.core.views.stats[29]))`).flat();
  ok(recv.reduce((a, b) => a + b, 0) > 0, `누적으로 밀려 올라온 줄 ${recv.reduce((a, b) => a + b, 0)}줄`);
}

console.log(`\n브라우저 코드: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
