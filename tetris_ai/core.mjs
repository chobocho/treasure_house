// core.mjs — Node 에서 tetris_ai.wasm 을 열고 선형 메모리에 창을 내는 최소 로더.
// 브라우저 쪽 battle.js 와 같은 일을 하지만, base64 대신 파일을 읽고
// atob 대신 fs 를 쓴다. 그 차이가 전부다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));

// C++ enum 과 1:1로 맞춘 상수 — 이 표가 곧 모듈 간 계약(ABI)이다.
export const ACT = { LEFT: 0, RIGHT: 1, SOFT: 2, CW: 3, CCW: 4, HARD: 5, HOLD: 6, PAUSE: 7, FLIP: 8 };
export const ST = {
  SCORE: 0, LINES: 1, LEVEL: 2, COMBO: 3, B2B: 4, STATE: 5, HOLD: 6,
  NEXT0: 7, NEXT1: 8, NEXT2: 9, NEXT3: 10, NEXT4: 11,
  CLEAR: 12, TSPIN: 13, GAIN: 14, PIECES: 15, ELAPSED: 16, GRAVITY: 17,
  PIECE: 18, ROT: 19, X: 20, Y: 21, GHOST: 22, EVENT: 23, ROWMASK: 24,
  PERFECT: 25, LOCKPCT: 26, ATTACK: 27, PENDING: 28, GARBAGE_RECV: 29, COUNT: 30,
};
export const F = { LINES: 0, AGG: 1, HOLES: 2, BUMP: 3, WELLS: 4, ROWT: 5, COLT: 6, LAND: 7, COUNT: 8 };
export const STATE = { PLAY: 0, OVER: 1, PAUSE: 2 };
export const GARBAGE = 8;      // 가비지 줄의 색 인덱스

let cachedModule = null;
export function wasmBytes(path = join(HERE, 'tetris_ai.wasm')) { return readFileSync(path); }

// 모듈(코드)은 한 번만 컴파일하고 인스턴스(상태)는 얼마든지 만든다.
// 1:1 대전이 인스턴스 두 개로 성립하는 이유가 바로 이 분리다.
export async function loadCore(seed = 1, bytes = null) {
  if (!cachedModule) cachedModule = await WebAssembly.compile(bytes ?? wasmBytes());
  const inst = await WebAssembly.instantiate(cachedModule, {});
  const e = inst.exports;
  const dims = e.ts_dims(), rows = e.ts_rows();
  const core = {
    e, W: dims >>> 16, VIS: dims & 0xffff, H: rows >>> 16, HIDDEN: rows & 0xffff,
    views: null,
  };
  core.refresh = () => makeViews(core);
  e.ts_init(seed >>> 0);
  core.refresh();
  return core;
}

function makeViews(core) {
  const { e, W, VIS, H } = core;
  const buf = e.memory.buffer;
  core.views = {
    buf,
    board:    new Uint8Array(buf, e.ts_board(), H * W),
    cells:    new Uint8Array(buf, e.ts_cells(), VIS * W),
    overlay:  new Uint8Array(buf, e.ts_overlay(), VIS * W),
    stats:    new Int32Array(buf, e.ts_stats(), ST.COUNT),
    weights:  new Float32Array(buf, e.ai_weights_ptr(), F.COUNT),
    features: new Float32Array(buf, e.ai_features_ptr(), F.COUNT),
  };
  return core.views;
}

// memory.grow() 가 일어나면 ArrayBuffer 가 detach 되어 기존 창이 무효가 된다.
// 우리 모듈은 자라지 않지만, 습관적으로 길이를 확인하고 다시 만든다.
export function V(core) {
  if (!core.views || core.views.buf.byteLength === 0) makeViews(core);
  return core.views;
}

export function setWeights(core, w) { V(core).weights.set(w); }

// 보드를 문자열로 굳힌다 — 테스트에서 "두 경로가 같은 판을 만들었는가"를 볼 때 쓴다.
export function boardHash(core) {
  const b = V(core).board;
  let h = 2166136261 >>> 0;                    // FNV-1a 32bit
  for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 16777619) >>> 0; }
  return h;
}

// 테스트가 특정 상황을 심을 때 쓰는 도구: 문자열 그림 → board.
// 한 줄이 W 글자, '.' 은 빈칸, 그 외 문자는 채운 칸(색은 아무거나 1).
// 그림의 마지막 줄이 필드의 바닥줄에 놓인다.
export function seedBoard(core, rows, fill = 1) {
  const { W, H } = core;
  const b = V(core).board;
  b.fill(0);
  for (let i = 0; i < rows.length; i++) {
    const y = H - rows.length + i;
    for (let x = 0; x < W; x++) {
      const c = rows[i][x];
      b[y * W + x] = (c && c !== '.') ? (c === '#' ? GARBAGE : fill) : 0;
    }
  }
}

export function dumpBoard(core) {
  const { W, H, HIDDEN } = core;
  const b = V(core).board;
  const out = [];
  for (let y = HIDDEN; y < H; y++) {
    let s = '';
    for (let x = 0; x < W; x++) { const v = b[y * W + x]; s += v === 0 ? '.' : (v === GARBAGE ? '#' : String(v)); }
    out.push(s);
  }
  return out.join('\n');
}
