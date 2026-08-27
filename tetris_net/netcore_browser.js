// netcore_browser.js — 브라우저에서 wasm 을 열고 선형 메모리에 창을 내는 로더.
// Node 쪽 net_core.mjs 와 하는 일이 같다. 다른 건 두 줄뿐이다:
// 파일 대신 base64 를 읽고, Buffer 대신 atob/btoa 를 쓴다.

const ACT = { LEFT: 0, RIGHT: 1, SOFT: 2, CW: 3, CCW: 4, HARD: 5, HOLD: 6, PAUSE: 7, FLIP: 8 };
const ST = {
  SCORE: 0, LINES: 1, LEVEL: 2, COMBO: 3, B2B: 4, STATE: 5, HOLD: 6,
  NEXT0: 7, NEXT1: 8, NEXT2: 9, NEXT3: 10, NEXT4: 11,
  CLEAR: 12, TSPIN: 13, GAIN: 14, PIECES: 15, ELAPSED: 16, GRAVITY: 17,
  PIECE: 18, ROT: 19, X: 20, Y: 21, GHOST: 22, EVENT: 23, ROWMASK: 24,
  PERFECT: 25, LOCKPCT: 26, ATTACK: 27, PENDING: 28, GARBAGE_RECV: 29, COUNT: 30,
};
const STATE = { PLAY: 0, OVER: 1, PAUSE: 2 };
const GARBAGE = 8;
// 프로토콜의 s[] 12칸 — protocol.md §5 와 같은 표다.
const S = { STATE: 0, SCORE: 1, LINES: 2, PIECES: 3, HEIGHT: 4, PENDING: 5,
            PIECE: 6, ROT: 7, X: 8, Y: 9, GHOST: 10, HOLD: 11, COUNT: 12 };

const COLORS = ['#000000', '#22d3ee', '#3b82f6', '#f59e0b', '#facc15',
                '#22c55e', '#a855f7', '#ef4444', '#64748b'];   // 8 = 가비지(회색)
const PIECE_NAMES = ['I', 'J', 'L', 'O', 'S', 'T', 'Z'];

function b64ToBytes(b64) {
  const s = atob(b64), n = s.length, out = new Uint8Array(n);
  for (let i = 0; i < n; i++) out[i] = s.charCodeAt(i);
  return out;
}

// 모듈(코드)은 한 번만 컴파일하고 인스턴스(상태)는 얼마든지 만든다.
// 8인 대전이 인스턴스 8개로 성립하는 이유가 이 분리다 — 코드는 17KB 한 벌뿐이다.
let _module = null;
// src 는 base64 문자열(덱은 wasm 을 통째로 품고 있다) 또는 Uint8Array(진짜 페이지는
// 파일을 받아 온다). 두 경로가 같은 모듈 캐시를 쓴다.
function compileOnce(src) {
  if (!_module) _module = WebAssembly.compile(typeof src === 'string' ? b64ToBytes(src) : src);
  return _module;
}

function makeViews(core) {
  const { e } = core, buf = e.memory.buffer;
  core.views = {
    board:   new Uint8Array(buf, e.ts_board(),   core.H * core.W),
    cells:   new Uint8Array(buf, e.ts_cells(),   core.VIS * core.W),
    overlay: new Uint8Array(buf, e.ts_overlay(), core.VIS * core.W),
    stats:   new Int32Array(buf, e.ts_stats(),   ST.COUNT),
    weights: new Float32Array(buf, e.ai_weights_ptr(), e.ai_feature_count()),
    snap:    new Uint8Array(buf, e.ng_snap_ptr(), core.VIS * core.W),
    queue:   new Int32Array(buf, e.ng_queue_ptr(), 4 * e.ng_queue_max()),
  };
  return core.views;
}

async function loadNet(src, seed) {
  const mod = await compileOnce(src);
  const inst = await WebAssembly.instantiate(mod, {});
  const e = inst.exports;
  const dims = e.ts_dims(), rows = e.ts_rows();
  const core = { e, W: dims >>> 16, VIS: dims & 0xffff, H: rows >>> 16, HIDDEN: rows & 0xffff, views: null };
  core.refresh = () => makeViews(core);
  e.ng_init(seed >>> 0);
  core.refresh();
  return core;
}

// ── 프로토콜 조각 (protocol.md §5·§6) ──
function snapshot(core) {
  const n = core.e.ng_snapshot(), raw = core.views.snap;
  let s = '';
  for (let i = 0; i < n; i++) s += String.fromCharCode(raw[i]);
  return btoa(s);
}
function unsnapshot(b64, out) {
  const raw = atob(b64);
  let k = 0;
  for (let i = 0; i < raw.length; i++) {
    const byte = raw.charCodeAt(i), run = (byte >> 4) + 1, v = byte & 15;
    for (let j = 0; j < run && k < out.length; j++) out[k++] = v;
  }
  return k;
}
function packState(core) {
  const s = core.views.stats;
  return [s[ST.STATE], s[ST.SCORE], s[ST.LINES], s[ST.PIECES], core.e.ng_height(), s[ST.PENDING],
          s[ST.PIECE], s[ST.ROT], s[ST.X], s[ST.Y], s[ST.GHOST], s[ST.HOLD]];
}
