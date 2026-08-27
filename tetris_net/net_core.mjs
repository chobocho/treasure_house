// net_core.mjs — Node 에서 tetris_net.wasm 을 열고 선형 메모리에 창을 내는 로더.
// 2편의 core.mjs 와 하는 일이 같고, 멀티플레이 층의 익스포트만 더 알고 있다.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));

// C++ enum 과 1:1. 2편에서 그대로 이어받은 계약이다.
export const ACT = { LEFT: 0, RIGHT: 1, SOFT: 2, CW: 3, CCW: 4, HARD: 5, HOLD: 6, PAUSE: 7, FLIP: 8 };
export const ST = {
  SCORE: 0, LINES: 1, LEVEL: 2, COMBO: 3, B2B: 4, STATE: 5, HOLD: 6,
  NEXT0: 7, NEXT1: 8, NEXT2: 9, NEXT3: 10, NEXT4: 11,
  CLEAR: 12, TSPIN: 13, GAIN: 14, PIECES: 15, ELAPSED: 16, GRAVITY: 17,
  PIECE: 18, ROT: 19, X: 20, Y: 21, GHOST: 22, EVENT: 23, ROWMASK: 24,
  PERFECT: 25, LOCKPCT: 26, ATTACK: 27, PENDING: 28, GARBAGE_RECV: 29, COUNT: 30,
};
export const STATE = { PLAY: 0, OVER: 1, PAUSE: 2 };
export const GARBAGE = 8;

// 프로토콜의 s[] 12칸 — protocol.md §5 와 같은 표다.
export const S = {
  STATE: 0, SCORE: 1, LINES: 2, PIECES: 3, HEIGHT: 4, PENDING: 5,
  PIECE: 6, ROT: 7, X: 8, Y: 9, GHOST: 10, HOLD: 11, COUNT: 12,
};

let cachedModule = null;
export function wasmBytes(path = join(HERE, 'tetris_net.wasm')) { return readFileSync(path); }

export async function loadNet(seed = 1, bytes = null) {
  if (!cachedModule) cachedModule = await WebAssembly.compile(bytes ?? wasmBytes());
  const inst = await WebAssembly.instantiate(cachedModule, {});
  const e = inst.exports;
  const dims = e.ts_dims(), rows = e.ts_rows();
  const core = { e, W: dims >>> 16, VIS: dims & 0xffff, H: rows >>> 16, HIDDEN: rows & 0xffff, views: null };
  core.refresh = () => makeViews(core);
  e.ng_init(seed >>> 0);
  core.refresh();
  return core;
}

// wasm 이 메모리를 늘리면 기존 TypedArray 는 detach 된다. 그래서 뷰를 다시 만드는
// 함수를 따로 두고, 메모리를 건드릴 만한 호출 뒤에는 refresh() 를 부른다.
function makeViews(core) {
  const { e } = core;
  const buf = e.memory.buffer;
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

// ── 프로토콜 조각 ──
// 보드 스냅샷: wasm 이 만든 RLE 바이트열을 base64 로. protocol.md §6.
export function snapshot(core) {
  const n = core.e.ng_snapshot();
  return Buffer.from(core.views.snap.subarray(0, n)).toString('base64');
}
// 되돌리기 — 관전 화면과 테스트가 쓴다.
export function unsnapshot(b64, out) {
  const raw = Buffer.from(b64, 'base64');
  let k = 0;
  for (const byte of raw) {
    const run = (byte >> 4) + 1, v = byte & 15;
    for (let i = 0; i < run && k < out.length; i++) out[k++] = v;
  }
  return k;
}
// 상태 12칸 만들기 — 서버가 읽는 건 s[0] 과 s[4] 뿐이지만 나머지는 관전용이다.
export function packState(core) {
  const s = core.views.stats;
  return [
    s[ST.STATE], s[ST.SCORE], s[ST.LINES], s[ST.PIECES], core.e.ng_height(), s[ST.PENDING],
    s[ST.PIECE], s[ST.ROT], s[ST.X], s[ST.Y], s[ST.GHOST], s[ST.HOLD],
  ];
}
