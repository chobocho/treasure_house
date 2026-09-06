// 브라우저 번들이 정말 같은 엔진인지 확인한다.
//
// 묶는 과정(tools/bundle_web.py)에서 무언가 어긋났을 수 있다. 확인 방법은 하나다 —
// 번들로 골든 트레이스를 다시 만들어 **바이트로** 대조하는 것. 줄 수나 마지막 해시만
// 보면 중간에서 갈렸다가 되돌아온 경우를 놓친다.
//
// require() 로 부르면 안 된다. 노드의 모듈 스코프는 __dirname 과 process 를 주는데
// 브라우저에는 그런 것이 없다. require 로 검사하면 브라우저에서만 터지는 버그를
// 놓친다. 그래서 번들을 두 번 싣는다.
//
//   1) vm 컨텍스트 — 노드 전역이 하나도 없는 진짜 브라우저 조건. 최상위에서
//      __dirname 이나 process 를 만지면 ReferenceError 로 즉시 드러난다.
//      대신 느리다. contextify 된 전역 객체를 거쳐 Math·Map·Set 을 찾으므로
//      실측 10배(1200틱에 39초 대 3초)다.
//   2) new Function — 노드 전역을 인자로 가린 사본. 스코프가 진짜 전역이라 빠르다.
//      1200틱짜리 무거운 대조는 이쪽에서 돈다. 코드는 같은 바이트다.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const SRC = fs.readFileSync(path.join(ROOT, 'deck', 'engine.js'), 'utf8');

let bad = 0;
function fail(msg) { console.log('  ' + msg); bad += 1; }

function fakeWindow() {
  const win = { setTimeout: setTimeout, clearTimeout: clearTimeout,
                addEventListener() {} };
  win.window = win;
  win.globalThis = win;
  return win;
}

// 1) 엄격한 사본 — 노드 전역이 없는 컨텍스트.
const strict = fakeWindow();
vm.runInContext(SRC, vm.createContext(strict), { filename: 'deck/engine.js' });

// 2) 빠른 사본 — 노드 전역만 가린다. require·process·__dirname 이 undefined 다.
const fast = fakeWindow();
new Function('window', 'globalThis', 'require', 'module', 'exports',
             '__dirname', '__filename', 'process', 'Buffer', SRC)(
  fast, fast, undefined, undefined, undefined, undefined, undefined,
  undefined, undefined);

const R = fast.__rts.require;

// ── 1. 27개 모듈이 브라우저 조건에서 평가되는가 ────────────────────────────
// 엄격한 사본으로 돈다. 최상위에서 노드 전역을 만지는 모듈이 하나라도 있으면
// 여기서 터진다 — 실제로 형제 덱에서 raster 가 __dirname 을 쓰다 걸린 적이 있다.
let loaded = 0;
for (const name of strict.__rts.names) {
  try {
    strict.__rts.require(name);
    loaded += 1;
  } catch (e) {
    fail(name + ' 평가 실패: ' + e.message);
  }
}
if (loaded === strict.__rts.names.length) {
  console.log('  모듈 ' + loaded + '개 브라우저 조건에서 평가              OK');
}

const C = R('const');
const T = R('tmap');
const SIM = R('sim');
const RS = R('raster');
const RD = R('render');
const FMT = R('fmt');
const D = R('web/data');

// ── 1.5 web/data.ts 가 골든과 같은가 ───────────────────────────────────────
// make web 은 tsc 를 gen_webdata.py 보다 **먼저** 돌린다. 골든이 바뀐 직후의 첫
// 빌드는 낡은 data.ts 를 묶게 되고, 그러면 트레이스 대조가 "왜 틀렸는지" 를
// 엉뚱한 곳에서 찾게 된다. 여기서 먼저 잡는다 — 한 번 더 make web 하면 낫는다.
function golden(name) {
  return fs.readFileSync(path.join(ROOT, 'golden', name), 'utf8');
}
let stale = 0;
if (D.MAP_START_TXT !== golden('map_start.txt')) stale += 1;
if (D.SCRIPT_TXT !== golden('script.txt')) stale += 1;
for (let i = 0; i < 6; i += 1) {
  if (D.MAPS_TXT[i] !== golden('map_' + (i + 1) + '.txt')) stale += 1;
}
if (stale === 0) {
  console.log('  web/data.ts 8벌 == golden/*.txt                  OK');
} else {
  fail('web/data.ts 가 골든과 다르다 (' + stale + '벌) — make web 을 다시 돌릴 것');
}

// ── 2. 골든 트레이스를 번들로 다시 만든다 ──────────────────────────────────
// main.ts 의 cmdTrace 와 같은 절차다. 다른 것은 입력을 파일이 아니라
// web/data.ts 의 문자열에서 받는다는 것뿐이다.
function evJson(e) {
  const v = e.concat([0, 0, 0, 0]);
  return '[' + v[0] + ',' + v[1] + ',' + v[2] + ',' + v[3] + ']';
}

function scenario() {
  const m = T.TMap.loadText(D.MAP_START_TXT);
  const sc = SIM.parseScript(D.SCRIPT_TXT);
  const s = new SIM.Sim(m, 1, sc.players, false);
  s.setupStart(false);                 // §18.6 — 스크립트가 몬다
  return [s, sc, m];
}

function trace() {
  const [s, sc] = scenario();
  const out = [];
  for (let t = 1; t <= sc.ticks; t += 1) {
    const h = s.step(s.scriptOrders(sc, t));
    let alive = 0;
    for (let i = 1; i < C.MAX_ENT; i += 1) if (s.w.alive[i] !== 0) alive += 1;
    const cr = [], su = [], scp = [];
    for (let p = 0; p < sc.players; p += 1) {
      cr.push(String(s.ec.credits[p]));
      su.push(String(s.ec.supplyUsed[p]));
      scp.push(String(s.ec.supplyCap[p]));
    }
    out.push('{"t":' + t + ',"h":"' + FMT.hex8(h) + '","cr":[' + cr.join(',')
             + '],"su":[' + su.join(',') + '],"sc":[' + scp.join(',')
             + '],"n":' + alive + ',"ev":['
             + s.events.map(evJson).join(',') + ']}');
  }
  return out.join('\n') + '\n';
}

const got = trace();
const want = golden('trace.jsonl');
if (got === want) {
  console.log('  브라우저 번들 트레이스 ' + got.length + '바이트'
              + ' == golden/trace.jsonl   OK');
} else {
  const a = got.split('\n');
  const b = want.split('\n');
  let shown = false;
  for (let i = 0; i < Math.max(a.length, b.length); i += 1) {
    if (a[i] !== b[i]) {
      fail((i + 1) + '줄 다름\n    기대 ' + b[i] + '\n    실제 ' + a[i]);
      shown = true;
      break;
    }
  }
  if (!shown) fail('길이만 다르다: ' + got.length + ' / ' + want.length);
}

// ── 3. 프레임 한 장 ────────────────────────────────────────────────────────
// 그림을 눈으로 볼 수는 없다. 확인하는 것은 두 가지다 — 크기가 320×200 이고,
// 색이 한 줌 이상 나오는가(전부 0 이면 "그렸다"가 아니라 "안 그렸다").
function frame() {
  const [s, sc, m] = scenario();
  s.step(s.scriptOrders(sc, 1));
  const pal = RS.buildPalette();
  const light = RS.buildLight(pal);
  const view = new RD.View();
  view.centerOn(m, m.starts[0][0], m.starts[0][1]);
  const f = new RS.Frame();
  RD.draw(f.fb, s, view, 0, pal, light, 0, [], 'TICK 1');
  return f.fb;
}

const fb = frame();
const kinds = new Set(fb).size;
if (fb.length === C.SCR_W * C.SCR_H && kinds > 8) {
  console.log('  프레임버퍼 ' + fb.length + '바이트 · 색 ' + kinds
              + '종                  OK');
} else {
  fail('프레임버퍼가 이상하다: ' + fb.length + '바이트 · 색 ' + kinds + '종');
}

// ── 4. fs 스텁 ─────────────────────────────────────────────────────────────
// 브라우저에서 파일을 읽으려 하면 조용히 빈 값이 아니라 예외가 나와야 한다.
// 빈 문자열이 돌아오면 맵이 없는 채로 게임이 돌고, 그 화면은 그럴듯해 보인다.
try {
  R('fs').readFileSync('golden/map_start.txt', 'utf8');
  fail('fs 스텁이 터지지 않았다 — 브라우저에서 조용히 빈 값이 나올 수 있다');
} catch (e) {
  console.log('  fs 스텁 확인: ' + e.message.slice(0, 24) + '…       OK');
}

process.exit(bad ? 1 : 0);
